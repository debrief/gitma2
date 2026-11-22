// Spec 035: the built demonstrator page in Chromium (acceptance 1, 4, 5; FR-002, FR-004, FR-022,
// FR-023, FR-043; NFR-1). Serves the Docusaurus build as GitHub Pages does and drives the page
// with the mouse, the keyboard and its window.__demo hooks.
//   node demo_page.mjs --build ../../site/build [--out demo/page.json]
import { createServer } from "node:http";
import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { chromium } from "playwright";

const arg = (k, d) => {
  const i = process.argv.indexOf(k);
  return i >= 0 ? process.argv[i + 1] : d;
};
const build = arg("--build", "../../site/build");
const out = arg("--out", null);
const BASE = "/gitma2/";
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm", ".json": "application/json", ".css": "text/css", ".svg": "image/svg+xml", ".onnx": "application/octet-stream" };
const server = createServer((req, res) => {
  const url = decodeURIComponent(req.url.split("?")[0]);
  if (!url.startsWith(BASE)) return res.writeHead(404).end();
  let f = normalize(join(build, url.slice(BASE.length)));
  const isFile = (p) => existsSync(p) && statSync(p).isFile();
  if (!isFile(f)) f = isFile(f + ".html") ? f + ".html" : join(f, "index.html");
  if (!isFile(f)) return res.writeHead(404).end();
  res.setHeader("Content-Type", TYPES[extname(f)] || "application/octet-stream");
  res.end(readFileSync(f));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${server.address().port}${BASE}demo`;
const browser = await chromium.launch({ args: ["--no-sandbox"], ...(process.env.PW_EXECUTABLE ? { executablePath: process.env.PW_EXECUTABLE } : {}) });
const report = { checks: {} };
const failures = [];
const check = (name, ok, detail) => {
  report.checks[name] = { ok: !!ok, detail };
  console.log(`${ok ? "ok  " : "FAIL"} ${name}${detail !== undefined ? `: ${JSON.stringify(detail)}` : ""}`);
  if (!ok) failures.push(name);
};

try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && !m.text().startsWith("Failed to load resource") && errors.push(m.text()));
  page.on("response", (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.url()}`));
  const settled = () => page.waitForFunction(() => window.__demo && window.__demo.status() !== "solving" && window.__demo.status() !== "idle", null, { timeout: 120000 });
  const state = () => page.evaluate(() => ({ status: window.__demo.status(), sol: window.__demo.solution(), summary: window.__demo.summary(), obs: window.__demo.observability(), mismatch: window.__demo.mismatch(), sc: window.__demo.scenario() }));
  await page.goto(url);
  await settled();

  // acceptance 1: every preset loads, solves and shows every panel
  for (const id of ["good-geometry", "no-zig", "target-turn", "endfire", "short-window"]) {
    await page.selectOption("[data-testid=preset]", id);
    await page.waitForTimeout(50);
    await settled();
    const s = await state();
    const panels = await page.evaluate(() => ["plot", "panel-status", "panel-observability", "panel-errors", "panel-error-time", "panel-bearings", "panel-residuals", "chart-error", "chart-bearings", "chart-residuals", "estimate"].filter((t) => !document.querySelector(`[data-testid=${t}]`)));
    check(`preset ${id} solves with every panel`, s.status === "done" && s.sol && s.sol.status !== "failed" && panels.length === 0, { missing: panels, status: s.sol && s.sol.status, obs: s.obs.level });
    if (id === "no-zig") check("no-zig: observability red (acceptance 3)", s.obs.level === "red", s.obs.level);
    if (id === "target-turn") {
      const flag = await page.locator("[data-testid=panel-mismatch]").count();
      check("target turn: mismatch flag shown (acceptance 4)", s.mismatch && flag === 1);
      const before = s.summary.range_pct.rms;
      // narrow the window with the slider's end (released: the native change event)
      await page.locator("[data-testid=win-end]").fill("3500");
      await page.waitForTimeout(50);
      await settled();
      const t = await state();
      const flag2 = await page.locator("[data-testid=panel-mismatch]").count();
      check("one target leg clears the flag and reduces the error (acceptance 4)", !t.mismatch && flag2 === 0 && t.summary.range_pct.rms < before / 5, { before, after: t.summary.range_pct.rms, window: t.sc.window });
    }
  }

  // FR-002/FR-022: drag a waypoint with the mouse; the solve runs on release
  await page.selectOption("[data-testid=preset]", "good-geometry");
  await settled();
  const wp = page.locator("[data-testid=wp-ownship-2]");
  const box = await wp.boundingBox();
  const before = (await state()).sc.ownship;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + 60, box.y + 30, { steps: 5 });
  const during = await state();
  await page.mouse.up();
  await page.waitForTimeout(50);
  await settled();
  const after = await state();
  check("waypoint drag edits the track and re-solves on release (FR-002, FR-022)", JSON.stringify(during.sc.ownship) === JSON.stringify(before) && JSON.stringify(after.sc.ownship) !== JSON.stringify(before) && after.sc.ownship.legs.length === before.legs.length && after.status === "done");

  // FR-004: Delete removes the selected waypoint; Ctrl+Z restores it (FR-007)
  await page.locator("[data-testid=wp-ownship-2]").click();
  await page.keyboard.press("Delete");
  await page.waitForTimeout(50);
  const del = await state();
  await page.keyboard.press("Control+z");
  await page.waitForTimeout(50);
  const und = await state();
  check("Delete removes a waypoint and undo restores it (FR-004, FR-007)", del.sc.ownship.legs.length === after.sc.ownship.legs.length - 1 && JSON.stringify(und.sc.ownship) === JSON.stringify(after.sc.ownship));

  // spec 036 follow-up: the waypoint drag kept the adjacent legs' speeds; ctrl-click deletes a waypoint
  const keptSpeed = [1, 2].every((i) => Math.abs(after.sc.ownship.legs[i].speed_kt - before.legs[i].speed_kt) < 1e-6) && [1, 2].some((i) => Math.abs(after.sc.ownship.legs[i].duration_s - before.legs[i].duration_s) > 1);
  check("a waypoint drag keeps the adjacent legs' speeds and changes their durations (spec 036 follow-up)", keptSpeed, [1, 2].map((i) => [before.legs[i].duration_s, after.sc.ownship.legs[i].duration_s]));
  await page.locator("[data-testid=wp-ownship-2]").click({ modifiers: ["Control"] });
  await page.waitForTimeout(50);
  const cdel = await state();
  check("ctrl-click deletes a waypoint (spec 036 follow-up)", cdel.sc.ownship.legs.length === und.sc.ownship.legs.length - 1);
  await page.keyboard.press("Control+z");
  await page.waitForTimeout(50);
  await settled();

  // spec 036 follow-up: arrows at the tracks' ends, the preset shown, the error quantity as a drop-down, course and speed
  const arrows = await page.locator("[data-testid=arrow-ownship], [data-testid=arrow-target]").count();
  const shownPreset = await page.locator("[data-testid=preset]").inputValue();
  check("an arrowhead at each track's end; the preset drop-down shows custom after an edit (spec 036 follow-up)", arrows === 2 && shownPreset === "custom", { arrows, shownPreset });
  await page.selectOption("[data-testid=preset]", "good-geometry");
  await settled();
  const shown2 = await page.locator("[data-testid=preset]").inputValue();
  await page.selectOption("[data-testid=error-quantity]", "range");
  const ylab = await page.locator("[data-testid=chart-error]").innerHTML();
  let kin = await page.locator("[data-testid=chart-course]").count();
  await page.selectOption("[data-testid=kinematics-quantity]", "speed");
  kin += await page.locator("[data-testid=chart-speed]").count();
  const hErr = (await page.locator("[data-testid=chart-error]").boundingBox()).height, hBrg = (await page.locator("[data-testid=chart-bearings]").boundingBox()).height;
  check("preset shown; error quantity by drop-down with the chart as tall as its neighbours; course and speed charts (spec 036 follow-up)", shown2 === "good-geometry" && /range error/.test(ylab) && kin === 2 && Math.abs(hErr - hBrg) < 2, { shown2, kin, hErr, hBrg });

  await settled();

  // owner 2026-11-22: bearings lost in ownship's turns; the control turns the loss off and on
  const lostText = async () => page.locator("[data-testid=window-slider]").innerText();
  const withLoss = await lostText();
  await page.locator("[data-testid=turn-loss]").uncheck();
  await page.waitForTimeout(50);
  await settled();
  const without = await lostText();
  const sNo = await state();
  await page.locator("[data-testid=turn-loss]").check();
  await page.waitForTimeout(50);
  await settled();
  const sYes = await state();
  check("bearings lost in ownship turns: stated under the window, and the control turns the loss off", /lost in ownship's turns/.test(withLoss) && !/lost in ownship's turns/.test(without) && sNo.sc.turn_loss_s === null && sYes.sc.turn_loss_s === 120, { withLoss: withLoss.split(";")[1] });

  // acceptance 5: the URL restores the exact scenario and solution
  await page.locator("[data-testid=reseed]").click();
  await page.waitForTimeout(50);
  await settled();
  await page.waitForTimeout(200);
  const a = await state();
  const href = await page.evaluate(() => window.location.href);
  const page2 = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  await page2.goto(href);
  await page2.waitForFunction(() => window.__demo && window.__demo.status() === "done", null, { timeout: 120000 });
  const b = await page2.evaluate(() => ({ sc: window.__demo.scenario(), sol: window.__demo.solution() }));
  check("URL round trip: same scenario, same solution (acceptance 5)", JSON.stringify(a.sc) === JSON.stringify(b.sc) && JSON.stringify(a.sol.x_m) === JSON.stringify(b.sol.x_m), { fragment_chars: href.split("#")[1].length });
  await page2.close();

  // FR-043: JSON import, valid and invalid
  const good = JSON.stringify({ ...a.sc, seed: 7 });
  const okImport = await page.evaluate((t) => window.__demo.importText(t), good);
  const bad = JSON.stringify({ ...a.sc, sigma_deg: 12, colour: "red" });
  const badImport = await page.evaluate((t) => window.__demo.importText(t), bad);
  const msg = await page.locator("[data-testid=import-errors]").innerText().catch(() => "");
  check("JSON import validated against the LinkML schema (FR-043)", okImport && !badImport && msg.includes("sigma_deg") && msg.includes("colour"), msg.slice(0, 200));
  await settled();

  // NFR-1: least squares at 360 bearings
  await page.evaluate(() => {
    const s = window.__demo.scenario();
    window.__demo.set({ ...s, solver: "ls-js", window: { start_s: 0, end_s: 1795 } });
  });
  await page.waitForTimeout(50);
  await settled();
  const n1 = await state();
  check("least squares at 360 bearings within 200 ms (NFR-1)", n1.summary.answered === 360 && n1.sol.runtime_ms <= 200, { n: n1.summary.answered, ms: n1.sol.runtime_ms });

  // the ONNX graphs in the browser's worker; spec 035's names still load (legacy links)
  for (const s of ["layer-cv", "layer-oracle"]) {
    await page.selectOption("[data-testid=preset]", "target-turn");
    await settled();
    await page.evaluate((name) => window.__demo.set({ ...window.__demo.scenario(), solver: name }), s);
    await page.waitForTimeout(50);
    await settled();
    const r = await state();
    const sc = await page.evaluate(() => window.__demo.scenario());
    check(`${s} solves in ONNX Runtime Web (as layer + ${sc.splitter})`, sc.solver === "layer" && r.status === "done" && r.sol && r.sol.status !== "failed", { status: r.sol && r.sol.status, range_pct_rms: r.summary && r.summary.range_pct.rms, ms: r.sol && r.sol.runtime_ms });
    report[s] = r.summary;
  }

  // spec 036: leg splitters feed the segmented layer; the legs panel reads them against the truth
  await page.selectOption("[data-testid=preset]", "two-target-turns");
  await settled();
  for (const sp of ["none", "truth", "arctan-debrief", "arctan-multi", "arctan-joined"]) {
    await page.selectOption("[data-testid=splitter]", sp);
    await page.waitForTimeout(50);
    await settled();
    const r = await state();
    const legs = await page.evaluate(() => window.__demo.legs());
    const panel = await page.locator("[data-testid=panel-legs]").innerText().catch(() => "");
    check(`splitter ${sp} → layer: solved, legs read against the truth`, r.status === "done" && r.sol.status !== "failed" && legs && legs.truth === 2 && r.sol.splitter === sp && /Target legs/.test(panel) && (sp !== "truth" || legs.matched === 2), { legs: legs && { stated: legs.stated, matched: legs.matched, false_: legs.false_ }, range_pct_rms: r.summary && r.summary.range_pct.rms, splitter_ms: r.sol && r.sol.splitter_runtime_ms });
    report[`splitter-${sp}`] = { legs, summary: r.summary };
  }
  const disabled = await (async () => {
    await page.selectOption("[data-testid=solver]", "ls-js");
    await settled();
    return page.locator("[data-testid=splitter]").isDisabled();
  })();
  check("the splitter drop-down is disabled for a solver that takes no legs", disabled);
  await page.selectOption("[data-testid=solver]", "layer");
  await settled();
  // the comparison table (C left out here: it takes minutes; demo_node.mjs runs it)
  await page.evaluate(() => window.__demo.startCompare(["none", "truth", "arctan-debrief", "arctan-multi", "arctan-joined"]));
  await page.waitForFunction(() => { const c = window.__demo.compare(); return c && c.status !== "running"; }, null, { timeout: 180000 });
  const cmpRows = await page.locator("[data-testid=compare-table] tbody tr").count();
  const cmpState = await page.evaluate(() => { const c = window.__demo.compare(); return { status: c.status, done: Object.keys(c.rows) }; });
  check("compare runs each splitter through the layer and tabulates them", cmpState.status === "done" && cmpState.done.length === 5 && cmpRows === 5, cmpState);
  if (process.env.DEMO_SHOT) {
    await page.selectOption("[data-testid=splitter]", "arctan-debrief");
    await page.waitForTimeout(50);
    await settled();
    await page.screenshot({ path: process.env.DEMO_SHOT, fullPage: false });
  }

  // the whole-period learned model in the browser, with its progress shown while it loads
  await page.selectOption("[data-testid=preset]", "target-turn");
  await settled();
  await page.selectOption("[data-testid=solver]", "tlm-s1");
  await page.waitForSelector("[data-testid=solve-progress]", { timeout: 30000 });
  const badge = await page.locator("[data-testid=plot-solving]").count();
  await settled();
  const tl = await state();
  const said = await page.locator("[data-testid=model-manoeuvres]").innerText().catch(() => "");
  check("whole-period learned model: progress while loading, then a time-late track and its manoeuvres", badge === 1 && tl.status === "done" && tl.sol.status === "converged" && tl.summary.answered === tl.sol.t_s.length && /states \d+ target/.test(said), { range_pct_rms: tl.summary && tl.summary.range_pct.rms, ms: tl.sol && tl.sol.runtime_ms, said });
  await page.selectOption("[data-testid=solver]", "ls-js");
  await settled();

  // chart toggles hide each chart
  await page.locator("[data-testid=toggle-bearings]").uncheck();
  const hidden = await page.locator("[data-testid=panel-bearings]").count();
  await page.locator("[data-testid=toggle-bearings]").check();
  check("each lower chart can be hidden", hidden === 0 && (await page.locator("[data-testid=panel-bearings]").count()) === 1);

  check("no page errors", errors.length === 0, errors.slice(0, 5));
} finally {
  await browser.close();
  server.close();
}
report.failures = failures;
if (out) writeFileSync(out, JSON.stringify(report, null, 2) + "\n");
if (failures.length) {
  console.error(`${failures.length} check(s) failed`);
  process.exit(1);
}
