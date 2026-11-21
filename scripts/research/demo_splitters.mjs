// Spec 036: the leg splitters on the demonstrator's presets, with the page's own code (presets,
// bearings, splitters, the segmented physics layer, metrics) and ONNX Runtime Web's Node build.
// Development readings for the slides post, not a result: three presets, a few noise draws.
//   (cd conformance/onnx && npm ci); node scripts/research/demo_splitters.mjs <record dir> <figure dir> [--with-c]
// Writes summary.json (record dir) and SVG figures with .json sidecars (figure dir).
import { writeFileSync, mkdirSync } from "node:fs";
import { execSync } from "node:child_process";
import { createRequire } from "node:module";
import { PRESETS, clone } from "../../site/static/demo-data/js/presets.js";
import { bearings, windowRows, problemOf, targetManoeuvresIn } from "../../site/static/demo-data/js/scenario.js";
import { solverByName } from "../../site/static/demo-data/js/solvers.js";
import { splitterByName } from "../../site/static/demo-data/js/splitters.js";
import { SPLITTER_INFO } from "../../site/static/demo-data/js/solver-info.js";
import { evaluate, compareLegs } from "../../site/static/demo-data/js/metrics.js";
import * as T from "../../site/static/demo-data/js/track.js";

const rec = process.argv[2] || "experiments/20261121-demo-splitters";
const fig = process.argv[3] || "site/static/img/2026-11-21-leg-splitters";
const withC = process.argv.includes("--with-c");
mkdirSync(rec, { recursive: true });
mkdirSync(fig, { recursive: true });
const root = new URL("../../", import.meta.url).pathname;
const req = createRequire(root + "conformance/onnx/package.json");
const ort = await import(req.resolve("onnxruntime-web").replace(/ort\.[^/]*$/, "ort.node.min.mjs"));
ort.env.wasm.numThreads = 1;
const GRAPHS = { "tl-layer": "site/static/demo-data/tl-layer.onnx", "c-layer": "site/static/viewer-data/layer.onnx" };
const sessions = {};
async function run(name, feeds) {
  sessions[name] ??= await ort.InferenceSession.create(root + GRAPHS[name]);
  const f = {};
  for (const [k, v] of Object.entries(feeds)) f[k] = v.dtype === "int64" ? new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape) : new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
  const o = {};
  for (const [k, t] of Object.entries(await sessions[name].run(f))) o[k] = Float64Array.from(t.data, Number);
  return o;
}
const commit = execSync("git rev-parse HEAD", { cwd: root }).toString().trim();
const preset = (id) => clone(PRESETS.find((p) => p.id === id).scenario);

async function trial(sc, name) {
  const b = bearings(sc), rows = windowRows(sc, b);
  const { problem, origin, t0 } = problemOf(sc, b, rows);
  const kn = targetManoeuvresIn(sc, b);
  const sp = splitterByName(name);
  const r = await sp.split(sp.info.told_truth ? problem : { ...problem, knots: [] }, { run });
  const sol = await solverByName("layer").solve({ ...problem, knots: r.spans }, { run });
  const ev = evaluate(sc, b, rows, origin, t0, sol, kn);
  const lg = compareLegs(problem.knots, r.spans);
  return { b, ev, t0, spans: r.spans, truth: problem.knots, legs: { truth: lg.truth, stated: lg.stated, matched: lg.matched, missed: lg.missed, false: lg.false_, median_offset_s: lg.median_offset_s }, range_pct_rms: ev ? ev.summary.range_pct.rms : null, course_deg_rms: ev ? ev.summary.course_deg.rms : null, speed_kt_rms: ev ? ev.summary.speed_kt.rms : null, splitter_ms: r.runtime_ms, status: sol.status };
}

const SPLIT = ["none", "arctan-debrief", "arctan-multi", "arctan-joined", "truth"];
const PRE = ["two-target-turns", "target-turn", "good-geometry"];
const SEEDS = [1, 2, 3, 4, 5];
const rows = [];
for (const id of PRE) for (const seed of SEEDS) {
  const sc = { ...preset(id), seed };
  const names = withC && id === "two-target-turns" && seed <= 3 ? [...SPLIT, "c"] : SPLIT;
  for (const name of names) {
    const r = await trial(sc, name);
    rows.push({ preset: id, seed, splitter: name, legs: r.legs, range_pct_rms: r.range_pct_rms, course_deg_rms: r.course_deg_rms, speed_kt_rms: r.speed_kt_rms, splitter_ms: Math.round(r.splitter_ms), status: r.status, spans_s: r.spans.map((f) => [f.start_s, f.end_s]) });
    console.error(id, seed, name, r.legs, r.range_pct_rms && r.range_pct_rms.toFixed(2), Math.round(r.splitter_ms));
  }
}
const med = (a) => { const s = a.filter(Number.isFinite).sort((x, y) => x - y); return s.length ? s[Math.floor((s.length - 1) / 2)] : null; };
const table = [];
for (const id of PRE) for (const name of [...SPLIT, "c"]) {
  const r = rows.filter((x) => x.preset === id && x.splitter === name);
  if (!r.length) continue;
  table.push({ preset: id, splitter: name, draws: r.length, matched: r.reduce((a, x) => a + x.legs.matched, 0), truth: r.reduce((a, x) => a + x.legs.truth, 0), false: r.reduce((a, x) => a + x.legs.false, 0), median_range_pct_rms: med(r.map((x) => x.range_pct_rms)), median_course_deg_rms: med(r.map((x) => x.course_deg_rms)), median_splitter_s: med(r.map((x) => x.splitter_ms / 1000)) });
}
writeFileSync(`${rec}/summary.json`, JSON.stringify({ script: "scripts/research/demo_splitters.mjs", commit, note: "Development readings on the demonstrator's presets (sigma 1 deg, 5 s bearings, two-hour windows); not a registered result.", rows, table }, null, 2) + "\n");

// ---------- figures ----------
function save(name, svg, meta) {
  writeFileSync(`${fig}/${name}.svg`, svg);
  writeFileSync(`${fig}/${name}.json`, JSON.stringify({ script: "scripts/research/demo_splitters.mjs", commit, ...meta }, null, 2) + "\n");
}
const COL = { none: "#7f7f7f", "arctan-debrief": "#8c564b", "arctan-multi": "#e377c2", "arctan-joined": "#2ca02c", truth: "#9467bd", c: "#17becf" };
const LAB = { none: "none (one leg)", "arctan-debrief": "Debrief 2015 slicing", "arctan-multi": "independent slices", "arctan-joined": "joined legs", truth: "told the truth", c: "C (spec 005)" };

// dot chart: range RMS (%) per splitter, a row per preset, a dot per draw (log scale)
{
  const names = [...SPLIT, ...(withC ? ["c"] : [])];
  const W = 640, rowH = 34, top = 40, left = 170, right = 20;
  const H = top + PRE.length * (names.length * rowH + 24) + 30;
  const lo = 0.1, hi = 200;
  const X = (v) => left + ((Math.log10(Math.max(lo, Math.min(hi, v))) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * (W - left - right);
  let body = `<text x="10" y="18" font-size="13" font-weight="bold">Range error (RMS over the window, % of range) with each leg splitter feeding the physics layer</text>`;
  for (const v of [0.1, 1, 10, 100]) body += `<line x1="${X(v)}" x2="${X(v)}" y1="${top - 6}" y2="${H - 26}" stroke="#ccc"/><text x="${X(v)}" y="${H - 10}" font-size="11" text-anchor="middle">${v}%</text>`;
  let y = top;
  for (const id of PRE) {
    body += `<text x="10" y="${y + 4}" font-size="12" font-weight="bold">${id}</text>`;
    y += 14;
    for (const name of names) {
      const r = rows.filter((x) => x.preset === id && x.splitter === name);
      body += `<text x="${left - 8}" y="${y + 4}" font-size="11" text-anchor="end">${LAB[name]}</text>`;
      for (const x of r) body += `<circle cx="${X(x.range_pct_rms).toFixed(1)}" cy="${y}" r="4" fill="${COL[name]}" fill-opacity="0.75"><title>seed ${x.seed}: ${x.range_pct_rms.toFixed(2)}%; found ${x.legs.matched} of ${x.legs.truth}, false ${x.legs.false}</title></circle>`;
      y += rowH * 0.62;
    }
    y += 18;
  }
  save("range-by-splitter", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="sans-serif" style="background:#fff">${body}</svg>`, { presets: PRE, seeds: SEEDS, splitters: names, sigma_deg: 1 });
}

// track plot: two target turns, seed 1, each splitter's estimated track and its knots
{
  const sc = { ...preset("two-target-turns"), seed: 1 };
  const names = ["none", "arctan-debrief", "arctan-joined", "truth"];
  const res = {};
  for (const n of names) res[n] = await trial(sc, n);
  const b = res.none.b;
  const W = 620, H = 470;
  const NM = T.NM;
  const pts = [...T.waypoints(sc.ownship), ...T.waypoints(sc.target)].map(([x, yy]) => [x * NM, yy * NM]);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) * 1.1;
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2, cy = (Math.max(...ys) + Math.min(...ys)) / 2;
  const s = (H - 60) / span;
  const X = (x) => Math.max(-2000, Math.min(2000, W / 2 - 60 + (x - cx) * s)).toFixed(1), Y = (yy) => Math.max(-2000, Math.min(2000, H / 2 + 15 - (yy - cy) * s)).toFixed(1);
  const line = (p, col, w, dash = "") => `<path d="${p.map(([x, yy], i) => `${i ? "L" : "M"}${X(x)},${Y(yy)}`).join("")}" fill="none" stroke="${col}" stroke-width="${w}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
  let body = `<text x="10" y="18" font-size="13" font-weight="bold">Two target turns between ownship turns (seed 1, σ = 1°)</text>`;
  const own = [], tgt = [];
  for (let i = 0; i < b.n; i += 6) { own.push([b.ox[i], b.oy[i]]); tgt.push([b.tx[i], b.ty[i]]); }
  body += line(own, "#1f77b4", 2.5) + line(tgt, "#d62728", 2.5);
  let ly = 40;
  for (const n of names) {
    const ev = res[n].ev;
    body += line(ev.ex.map((x, k) => [x, ev.ey[k]]), COL[n], 1.6, "6 3");
    for (const f of n === "truth" ? [] : res[n].spans) {
      const tc = (f.start_s + f.end_s) / 2 + res[n].t0;
      let k = 0;
      while (k < ev.t.length - 1 && ev.t[k] < tc) k++;
      const px = Number(X(ev.ex[k])), py = Number(Y(ev.ey[k]));
      body += `<path d="M${px},${py - 6}L${px + 6},${py}L${px},${py + 6}L${px - 6},${py}Z" fill="${COL[n]}" stroke="#fff"/>`;
    }
    body += `<line x1="${W - 190}" x2="${W - 160}" y1="${ly}" y2="${ly}" stroke="${COL[n]}" stroke-width="2" stroke-dasharray="6 3"/><text x="${W - 154}" y="${ly + 4}" font-size="11">${LAB[n]}: ${res[n].range_pct_rms.toFixed(1)}%</text>`;
    ly += 18;
  }
  body += `<text x="${W - 190}" y="${ly + 8}" font-size="10">blue ownship, red target; diamonds: knots</text><text x="${W - 190}" y="${ly + 22}" font-size="10">range RMS over the window</text>`;
  save("two-turns-tracks", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="sans-serif" style="background:#fff">${body}</svg>`, { preset: "two-target-turns", seed: 1, splitters: names, sigma_deg: 1 });
}
console.error("done");
