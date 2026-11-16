// The browser viewer's conformance leg (spec 020 FR-014, SC-001, SC-002, SC-005): serves the
// built site, opens the viewer page in Chromium (Playwright) and runs every demo row through the
// page's own worker, comparing each output with Python's onnxruntime output shipped beside it.
// Also times the first estimate and checks the ellipse's warning and the digest checks.
//
// Usage: node viewer_leg.mjs --build ../../site/build --out viewer-results.json
import { createServer } from "node:http";
import { readFileSync, writeFileSync, existsSync, statSync } from "node:fs";
import { join, extname, normalize } from "node:path";
import { chromium } from "playwright";

const args = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : dflt;
};
const build = arg("--build", "../../site/build");
const outPath = arg("--out", "viewer-results.json");
// spec 021: engagements to run live ("all", "none", or a comma-separated list)
const liveArg = arg("--live", "all");
const LIVE_MIN_SAME = 0.95; // SC-001, over all live rows
const LIVE_LIMIT_S = 600; // SC-003, the slowest engagement
const BASE = "/gitma2/";
const TOL = 1e-5;
const FIRST_LIMIT_MS = 10000; // SC-002
const ENGAGEMENT_LIMIT_MS = 60000;
const TYPES = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".wasm": "application/wasm",
  ".json": "application/json",
  ".css": "text/css",
  ".svg": "image/svg+xml",
};

const server = createServer((req, res) => {
  let url = decodeURIComponent(req.url.split("?")[0]);
  if (!url.startsWith(BASE)) {
    res.statusCode = 404;
    res.end();
    return;
  }
  let f = normalize(join(build, url.slice(BASE.length)));
  const isFile = (p) => existsSync(p) && statSync(p).isFile();
  // as GitHub Pages: /viewer is viewer.html even though a viewer/ folder exists
  if (!isFile(f)) f = isFile(f + ".html") ? f + ".html" : join(f, "index.html");
  if (!isFile(f)) {
    res.statusCode = 404;
    res.end();
    return;
  }
  res.setHeader("Content-Type", TYPES[extname(f)] || "application/octet-stream");
  res.end(readFileSync(f));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;
const browser = await chromium.launch({
  args: ["--no-sandbox"],
  ...(process.env.PW_EXECUTABLE ? { executablePath: process.env.PW_EXECUTABLE } : {}),
});
const report = { tol: TOL };
const failures = [];
try {
  const page = await browser.newPage();
  page.on("console", (m) => {
    if (m.type() === "error") console.error("[browser]", m.text());
  });
  const t0 = Date.now();
  await page.goto(`http://127.0.0.1:${port}${BASE}viewer`);
  await page.waitForFunction(() => window.__viewerFirstMs !== undefined, null, { timeout: 120000 });
  report.first_estimate_ms = await page.evaluate(() => window.__viewerFirstMs);
  report.first_estimate_wall_ms = Date.now() - t0;
  if (!(report.first_estimate_ms <= FIRST_LIMIT_MS)) failures.push(`first estimate after ${report.first_estimate_ms} ms`);

  // the ellipse is off by default; on, the warning is shown with it
  report.ellipse_default = await page.locator('[data-testid="ellipse"]').count();
  if (report.ellipse_default !== 0) failures.push("ellipse drawn by default");
  await page.locator('[data-testid="ellipse-toggle"]').check();
  await page.waitForTimeout(200);
  report.ellipse_on = await page.locator('[data-testid="ellipse"]').count();
  report.warning_visible = await page.locator('[data-testid="ellipse-warning"]').isVisible();
  if (report.ellipse_on < 1) failures.push("the ellipse toggle drew no ellipse");
  if (!report.warning_visible) failures.push("ellipse shown without its warning");
  const shot = await page.screenshot({ fullPage: true });
  writeFileSync(outPath.replace(/\.json$/, ".png"), shot);

  const all = await page.evaluate(() => window.__viewer.checkAll());
  report.load_ms = all.loadMs;
  report.browser = all.userAgent;
  report.rows = all.rows.length;
  // element-wise, as the other legs (reported); gated: state element-wise, flags exactly, the
  // covariance on its own scale (spec 020 research R6)
  report.max_rel_diff_elementwise = Math.max(...all.rows.map((r) => r.max_rel_diff));
  const of = (name) => Math.max(...all.rows.map((r) => r.outputs[name].max_rel_diff));
  report.max_rel_diff_by_output = {
    state: of("state"),
    cov: of("cov"),
    cov_scaled: of("cov_scaled"),
    plausible: of("plausible"),
    cov_ok: of("cov_ok"),
  };
  report.rows_over_tol_elementwise = all.rows.filter((r) => r.max_rel_diff > TOL).length;
  report.max_rel_diff = Math.max(of("state"), of("cov_scaled"));
  const byEng = {};
  for (const r of all.rows) {
    byEng[r.engagement] ??= { rows: 0, ms: 0, max_rel_diff: 0 };
    byEng[r.engagement].rows += 1;
    byEng[r.engagement].ms += r.ms;
    byEng[r.engagement].max_rel_diff = Math.max(
      byEng[r.engagement].max_rel_diff,
      r.outputs.state.max_rel_diff,
      r.outputs.cov_scaled.max_rel_diff,
    );
  }
  report.engagements = byEng;
  const ms = all.rows.map((r) => r.ms).sort((a, b) => a - b);
  report.median_ms_per_row = ms[Math.floor(ms.length / 2)];
  report.per_row = all.rows;
  // live mode: the whole model from bearings, against Python
  const nEng = (await page.evaluate(() => window.__viewer.manifest().engagements.length)) | 0;
  const liveIds = liveArg === "none" ? [] : liveArg === "all" ? [...Array(nEng).keys()] : liveArg.split(",").map(Number);
  report.live = [];
  for (const i of liveIds) {
    const r = await page.evaluate((j) => window.__viewer.live(j), i);
    console.error(`live ${i}: ${r.segmentation_same}/${r.rows} rows, ${r.seconds.toFixed(0)} s`);
    report.live.push(r);
  }
  if (report.live.length) {
    const rows = report.live.reduce((a, r) => a + r.rows, 0);
    const same = report.live.reduce((a, r) => a + r.segmentation_same, 0);
    report.live_rows = rows;
    report.live_segmentation_same = same;
    report.live_max_seconds = Math.max(...report.live.map((r) => r.seconds));
    if (!(same >= LIVE_MIN_SAME * rows)) failures.push(`live segmentation identical on ${same} of ${rows} rows`);
    // SC-002: where the segmentation matches, the live estimate matches the shipped one
    for (const r of report.live) {
      if (!r.decisions_same) failures.push(`live engagement ${r.engagement}: decisions differ from Python's`);
      if (r.segmentation_same === r.rows && !(r.estimate_max_rel <= TOL)) failures.push(`live engagement ${r.engagement}: estimate differs by ${r.estimate_max_rel}`);
    }
    // SC-003's first scored row: reported (the first estimate waits for confirmation)
    report.live_first_row_seconds = report.live.map((r) => (r.stages.find((x) => x.stage === "estimates") || {}).seconds);
    if (!(report.live_max_seconds <= LIVE_LIMIT_S)) failures.push(`live mode took ${report.live_max_seconds} s`);
  }
  report.digests = await page.evaluate(() => window.__viewer.digests());
  report.manifest_sha_files = Object.keys(await page.evaluate(() => window.__viewer.manifest().files));
  if (!(report.max_rel_diff <= TOL)) failures.push(`max relative difference ${report.max_rel_diff} > ${TOL}`);
  for (const f of ["plausible", "cov_ok"]) {
    if (report.max_rel_diff_by_output[f] !== 0) failures.push(`${f} differs from Python`);
  }
  for (const [e, v] of Object.entries(byEng)) {
    if (!(v.ms <= ENGAGEMENT_LIMIT_MS)) failures.push(`engagement ${e}: ${Math.round(v.ms)} ms`);
  }
  for (const [f, ok] of Object.entries(report.digests)) if (!ok) failures.push(`digest of ${f} is not the manifest's`);
  if (!report.rows) failures.push("no rows were checked");
} finally {
  await browser.close();
  server.close();
}
report.failures = failures;
writeFileSync(outPath, JSON.stringify(report, null, 1));
const brief = { ...report };
delete brief.per_row;
console.log(JSON.stringify(brief, null, 1));
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
