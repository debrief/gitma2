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
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, "index.html");
  if (!existsSync(f) && existsSync(f + ".html")) f = f + ".html";
  if (!existsSync(f)) {
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
  if (!report.warning_visible) failures.push("ellipse shown without its warning");
  const shot = await page.screenshot({ fullPage: true });
  writeFileSync(outPath.replace(/\.json$/, ".png"), shot);

  const all = await page.evaluate(() => window.__viewer.checkAll());
  report.load_ms = all.loadMs;
  report.browser = all.userAgent;
  report.rows = all.rows.length;
  report.max_rel_diff = Math.max(...all.rows.map((r) => r.max_rel_diff));
  const byEng = {};
  for (const r of all.rows) {
    byEng[r.engagement] ??= { rows: 0, ms: 0, max_rel_diff: 0 };
    byEng[r.engagement].rows += 1;
    byEng[r.engagement].ms += r.ms;
    byEng[r.engagement].max_rel_diff = Math.max(byEng[r.engagement].max_rel_diff, r.max_rel_diff);
  }
  report.engagements = byEng;
  const ms = all.rows.map((r) => r.ms).sort((a, b) => a - b);
  report.median_ms_per_row = ms[Math.floor(ms.length / 2)];
  report.per_row = all.rows;
  report.digests = await page.evaluate(() => window.__viewer.digests());
  report.manifest_sha_files = Object.keys(await page.evaluate(() => window.__viewer.manifest().files));
  if (!(report.max_rel_diff <= TOL)) failures.push(`max relative difference ${report.max_rel_diff} > ${TOL}`);
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
