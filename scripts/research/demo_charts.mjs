// Spec 035: the slides post's figures, from the demonstrator's own code (the page's presets,
// bearings, solvers and metrics) and ONNX Runtime Web's Node build of the same graphs.
//   (cd conformance/onnx && npm ci); node scripts/research/demo_charts.mjs <out dir>
// Writes SVGs with .json sidecars naming this script and the commit.
import { writeFileSync, mkdirSync } from "node:fs";
import { execSync } from "node:child_process";
import { createRequire } from "node:module";
import { PRESETS, clone } from "../../site/static/demo-data/js/presets.js";
import { bearings, windowRows, problemOf, targetManoeuvresIn } from "../../site/static/demo-data/js/scenario.js";
import { SOLVERS } from "../../site/static/demo-data/js/solvers.js";
import { evaluate, observability } from "../../site/static/demo-data/js/metrics.js";
import * as T from "../../site/static/demo-data/js/track.js";

const out = process.argv[2] || "site/static/img/2026-11-21-demonstrator";
mkdirSync(out, { recursive: true });
const root = new URL("../../", import.meta.url).pathname;
const req = createRequire(root + "conformance/onnx/package.json");
const ort = await import(req.resolve("onnxruntime-web").replace(/ort\.[^/]*$/, "ort.node.min.mjs"));
ort.env.wasm.numThreads = 1;
const GRAPHS = { "tl-layer": "site/static/demo-data/tl-layer.onnx", "tlm-s1": "site/static/demo-data/tlm-s1.onnx" };
const sessions = {};
async function run(name, feeds) {
  sessions[name] ??= await ort.InferenceSession.create(root + GRAPHS[name]);
  const f = {};
  for (const [k, v] of Object.entries(feeds)) f[k] = v.dtype === "float32" ? new ort.Tensor("float32", Float32Array.from(v.data), v.shape) : v.dtype === "bool" ? new ort.Tensor("bool", Uint8Array.from(v.data), v.shape) : v.dtype === "int64" ? new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape) : new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
  const o = {};
  for (const [k, t] of Object.entries(await sessions[name].run(f))) o[k] = Float64Array.from(t.data, Number);
  return o;
}
const commit = execSync("git rev-parse HEAD", { cwd: root }).toString().trim();
const preset = (id) => clone(PRESETS.find((p) => p.id === id).scenario);
async function solve(sc, name) {
  const b = bearings(sc), rows = windowRows(sc, b);
  const { problem, origin, t0 } = problemOf(sc, b, rows);
  const kn = targetManoeuvresIn(sc, b);
  const sol = await SOLVERS.find((s) => s.info.name === name).solve(problem, { run });
  return { b, rows, ev: evaluate(sc, b, rows, origin, t0, sol, kn), obs: observability(sc, b, rows, kn), kn };
}
const NM = T.NM;
const C = { own: "#1f77b4", tgt: "#d62728", ls: "#2ca02c", cv: "#7f7f7f", or: "#9467bd", brg: "#bcbd22", tlm: "#ff7f0e" };

function save(name, svg, meta) {
  writeFileSync(`${out}/${name}.svg`, svg);
  writeFileSync(`${out}/${name}.json`, JSON.stringify({ script: "scripts/research/demo_charts.mjs", commit, ...meta }, null, 2) + "\n");
}

function trackPlot(sc, b, ests, title) {
  const W = 520, H = 420;
  const pts = [...T.waypoints(sc.ownship), ...T.waypoints(sc.target)].map(([x, y]) => [x * NM, y * NM]);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) * 1.15;
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2, cy = (Math.max(...ys) + Math.min(...ys)) / 2;
  const s = (H - 40) / span;
  const X = (x) => (W / 2 + (x - cx) * s).toFixed(1), Y = (y) => (H / 2 + 10 - (y - cy) * s).toFixed(1);
  const clip = (v) => Math.max(-2000, Math.min(2000, v));
  const line = (p, col, w, dash = "") => `<path d="${p.map(([x, y], i) => `${i ? "L" : "M"}${clip(X(x))},${clip(Y(y))}`).join("")}" fill="none" stroke="${col}" stroke-width="${w}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
  let body = "";
  for (let i = 0; i < b.n; i += Math.ceil(b.n / 40)) {
    const r = Math.hypot(b.tx[i] - b.ox[i], b.ty[i] - b.oy[i]) * 1.15;
    body += line([[b.ox[i], b.oy[i]], [b.ox[i] + r * Math.sin(b.z[i]), b.oy[i] + r * Math.cos(b.z[i])]], C.brg, 0.6);
  }
  body += line(T.pathPoints(b.paths.own), C.own, 2.5) + line(T.pathPoints(b.paths.tgt), C.tgt, 2.5);
  let ly = 34;
  for (const e of ests) {
    body += line(e.ev.ex.map((x, k) => [x, e.ev.ey[k]]), e.colour, 2, "6 3");
    body += `<rect x="${W - 190}" y="${ly - 8}" width="14" height="3" fill="${e.colour}"/><text x="${W - 170}" y="${ly}" font-size="11">${e.label}</text>`;
    ly += 16;
  }
  const bar = 5 * NM * s;
  body += `<line x1="${W - 20 - bar}" x2="${W - 20}" y1="${H - 12}" y2="${H - 12}" stroke="#333" stroke-width="2"/><text x="${W - 20}" y="${H - 18}" font-size="10" text-anchor="end">5 NM</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="sans-serif"><rect width="${W}" height="${H}" fill="#fff"/><text x="8" y="16" font-size="13">${title}</text>${body}</svg>\n`;
}

// time down the left, the value across (as the page's lower charts)
function errorPlot(series, t0, t1, title, label, marks = []) {
  const W = 360, H = 420, L = 48, R = 10, Tp = 46, B = 10;
  const vals = series.flatMap((s) => s.pts.map((p) => p[1]));
  const v0 = Math.min(0, ...vals), v1 = Math.max(...vals) * 1.05;
  const X = (v) => (L + ((v - v0) / (v1 - v0)) * (W - L - R)).toFixed(1), Y = (t) => (Tp + ((t - t0) / (t1 - t0)) * (H - Tp - B)).toFixed(1);
  let body = `<rect x="${L}" y="${Tp}" width="${W - L - R}" height="${H - Tp - B}" fill="none" stroke="#ccc"/>`;
  for (const [a, b] of marks) body += `<rect x="${L}" y="${Y(a)}" width="${W - L - R}" height="${Y(b) - Y(a)}" fill="${C.tgt}" fill-opacity="0.12"/>`;
  for (let i = 0; i <= 6; i++) {
    const t = t0 + ((t1 - t0) * i) / 6;
    body += `<text x="${L - 4}" y="${Number(Y(t)) + 3}" font-size="10" text-anchor="end">${Math.round(t / 60)} min</text>`;
  }
  for (const v of [v0, (v0 + v1) / 2, v1]) body += `<text x="${X(v)}" y="${Tp - 4}" font-size="10" text-anchor="middle">${Number(v.toPrecision(3))}</text>`;
  let ly = Tp + 160;
  for (const s of series) {
    body += `<path d="${s.pts.map(([t, v], i) => `${i ? "L" : "M"}${X(v)},${Y(t)}`).join("")}" fill="none" stroke="${s.colour}" stroke-width="1.8"/>`;
    body += `<text x="${W - R - 6}" y="${ly}" font-size="10" text-anchor="end" fill="${s.colour}">${s.label}</text>`;
    ly += 12;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="sans-serif"><rect width="${W}" height="${H}" fill="#fff"/><text x="6" y="14" font-size="12">${title}</text><text x="${L}" y="${Tp - 18}" font-size="10">${label}</text>${body}</svg>\n`;
}

const summary = {};
// 1. good geometry, least squares
{
  const sc = preset("good-geometry");
  const r = await solve(sc, "ls-js");
  const tl = await solve(sc, "tlm-s1");
  save("good-geometry", trackPlot(sc, r.b, [{ ev: r.ev, colour: C.ls, label: "least squares (JS)" }, { ev: tl.ev, colour: C.tlm, label: "learned, whole period (s1)" }], "Good geometry: ownship zig-zag, σ 1°, seed 1"), { preset: "good-geometry", solver: "ls-js", range_pct_rms: r.ev.summary.range_pct.rms, observability: r.obs.level });
  summary.good = { learned_s1: tl.ev.summary.range_pct.rms, range_pct_rms: r.ev.summary.range_pct.rms, crb_m: r.ev.summary.range_m.crb, rms_m: r.ev.summary.range_m.rms, obs: r.obs.level, nrms: r.ev.summary.nrms };
}
// 2. target turn: one leg against the oracle, and one leg on the first target leg only
{
  const sc = preset("target-turn");
  const cv = await solve(sc, "layer-cv");
  const or = await solve(sc, "layer-oracle");
  const leg = await solve({ ...sc, window: { start_s: 0, end_s: 2900 } }, "ls-js");
  const tlm = await solve(sc, "tlm-s1");
  save("target-turn", trackPlot(sc, cv.b, [{ ev: cv.ev, colour: C.cv, label: "one leg (ONNX layer)" }, { ev: or.ev, colour: C.or, label: "told the turn (oracle)" }, { ev: tlm.ev, colour: C.tlm, label: "learned, whole period (s1)" }], "Target turns after an hour: one leg is biased by design"), { preset: "target-turn", solvers: ["layer-cv", "layer-oracle"] });
  const pct = (e) => e.ev.t.map((t, k) => [t, Math.abs(e.ev.rangePct[k])]);
  save("target-turn-errors", errorPlot([{ pts: pct(cv), colour: C.cv, label: "one leg, whole window" }, { pts: pct(or), colour: C.or, label: "told the turn" }, { pts: pct(leg), colour: C.ls, label: "one leg, first target leg only" }, { pts: pct(tlm), colour: C.tlm, label: "learned, whole period (s1)" }], 0, cv.b.period, "|range error| (% of range) against time", "% of range", cv.kn.map((m) => [m.t0, m.t1])), { preset: "target-turn" });
  summary.turn = { cv: cv.ev.summary.range_pct.rms, oracle: or.ev.summary.range_pct.rms, first_leg: leg.ev.summary.range_pct.rms, learned_s1: tlm.ev.summary.range_pct.rms };
}
// 3. no zig
{
  const sc = preset("no-zig");
  const r = await solve(sc, "ls-js");
  const tl = await solve(sc, "tlm-s1");
  save("no-zig", trackPlot(sc, r.b, [{ ev: r.ev, colour: C.ls, label: "least squares (JS)" }, { ev: tl.ev, colour: C.tlm, label: "learned, whole period (s1)" }], "No ownship zig: the bearings fit, the range does not"), { preset: "no-zig", observability: r.obs.level, range_pct_rms: r.ev.summary.range_pct.rms, nrms: r.ev.summary.nrms });
  summary.nozig = { range_pct_rms: r.ev.summary.range_pct.rms, nrms: r.ev.summary.nrms, obs: r.obs.level, learned_s1: tl.ev.summary.range_pct.rms };
}
writeFileSync(`${out}/summary.json`, JSON.stringify({ script: "scripts/research/demo_charts.mjs", commit, ...summary }, null, 2) + "\n");
console.log(JSON.stringify(summary, null, 1));
