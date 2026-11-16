// Spec 021: the JavaScript port of C's host code, stage by stage, against Python's dump
// (tma2-viewer-dump), under Node. Usage: node port_node.mjs --dump <dir> [--only 1,3] [--out r.json]
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { join } from "node:path";
import { classicalPerTimestep, lsStates } from "../../site/static/viewer-data/js/lsq.js";
import { glrStat } from "../../site/static/viewer-data/js/glr.js";
import { onlineOwnshipCodes } from "../../site/static/viewer-data/js/ownship.js";
import { innovations, features } from "../../site/static/viewer-data/js/features.js";
import { searchByPrefix } from "../../site/static/viewer-data/js/search.js";
import { glrNominations, searchNominations, sortNominations, confirmOne, intervalsAt } from "../../site/static/viewer-data/js/confirm.js";
import { segmentationInputs, layerFeeds, ROWS } from "../../site/static/viewer-data/js/handover.js";
import * as ort from "./node_modules/onnxruntime-web/dist/ort.node.min.mjs";

const args = process.argv.slice(2);
const arg = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
ort.env.wasm.numThreads = 1;
const layerPath = arg("--layer"), esPath = arg("--es");
const layerSess = layerPath ? await ort.InferenceSession.create(readFileSync(layerPath)) : null;
const esSess = esPath ? await ort.InferenceSession.create(readFileSync(esPath)) : null;
const tensor = (v) => v.dtype === "int64" ? new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape) : new ort.Tensor("float64", Float64Array.from(v.data), v.shape);

// one batch of confirmation requests through the layer graph (chord, no speed prior)
function layerFor(s) {
  return async (reqs) => {
    const B = reqs.length;
    const feeds = {};
    const per = reqs.map(([k, trs]) => {
      const inp = segmentationInputs(s, k, trs, "chord", false);
      if (inp === null) throw new Error(`no valid bearing on [0, ${k}]`);
      return layerFeeds(s, k, inp);
    });
    for (const name of Object.keys(per[0])) {
      const one = per[0][name];
      const size = one.data.length;
      const data = new Float64Array(size * B);
      per.forEach((f, b) => data.set(f[name].data, b * size));
      feeds[name] = tensor({ dtype: one.dtype, shape: [B, ...one.shape.slice(1)], data });
    }
    const out = await layerSess.run(feeds);
    return Array.from(out.cost.data, Number);
  };
}

async function evidenceOf(fe, n) {
  const x = new Float64Array(10 * ROWS);
  for (let c = 0; c < 10; c++) x.set(fe[c].subarray(0, n), c * ROWS);
  const out = await esSess.run({ features: new ort.Tensor("float64", x, [1, 10, ROWS]) });
  return Float64Array.from(out.evidence.data, Number).subarray(0, n);
}

const sameIvs = (a, b) => JSON.stringify(a.map((iv) => [iv.kind, iv.start, iv.end, iv.open])) === JSON.stringify(b);
function cmpConf(conf, want, rows) {
  const dec = conf.decisions.map((d) => [d.row, d.start, d.length, d.source, d.accepted]);
  const wdec = want.decisions.map((d) => [d[0], d[1], d[2], d[3], d[6]]);
  let first = -1;
  for (let i = 0; i < Math.max(dec.length, wdec.length); i++) if (JSON.stringify(dec[i]) !== JSON.stringify(wdec[i])) { first = i; break; }
  let dropW = 0;
  for (let i = 0; i < Math.min(dec.length, wdec.length) && (first < 0 || i < first); i++) dropW = Math.max(dropW, Math.abs(conf.decisions[i].drop - want.decisions[i][4]));
  let same = 0;
  for (const k of rows) if (sameIvs(intervalsAt(conf, k, P), want.intervals[String(k)])) same++;
  const minMargin = Math.min(...conf.decisions.map((d) => Math.abs(d.score)));
  return { decisions: dec.length, py_decisions: wdec.length, first_decision_differs: first, max_drop_abs_diff_before: dropW, rows_same: same, rows: rows.length, min_abs_score: minMargin, solves: conf.solves };
}

const P = JSON.parse(readFileSync(new URL("../../configs/segment/gs-plan.json", import.meta.url))).segmenter.parameters;

const dir = arg("--dump");
const only = arg("--only") ? arg("--only").split(",").map(Number) : null;
const outPath = arg("--out", null);

export function scenarioFrom(doc) {
  const n = doc.n;
  const s = { n, zigIndex: doc.zig_index, sigma: doc.sigma, t: new Float64Array(n), ox: new Float64Array(n), oy: new Float64Array(n), z: new Float64Array(n), valid: new Uint8Array(n), course: new Float64Array(n), speed: new Float64Array(n) };
  for (let i = 0; i < n; i++) {
    const o = doc.own[i], b = doc.obs[i];
    s.t[i] = o[0]; s.ox[i] = o[1]; s.oy[i] = o[2]; s.course[i] = o[3]; s.speed[i] = o[4];
    s.z[i] = b[1]; s.valid[i] = b[2] !== 0 ? 1 : 0;
  }
  return s;
}

const rel = (a, b) => Math.abs(a - b) / Math.max(Math.abs(b), 1);
function cmpArr(got, want) {
  let worst = 0, at = -1;
  for (let i = 0; i < want.length; i++) {
    const d = rel(got[i], want[i]);
    if (!(d <= worst)) { worst = d; at = i; }
  }
  return { worst, at };
}

const files = readdirSync(dir).filter((f) => f.startsWith("scenario-")).sort((a, b) => parseInt(a.slice(9)) - parseInt(b.slice(9)));
const report = [];
for (const f of files) {
  const doc = JSON.parse(gunzipSync(readFileSync(join(dir, f))).toString());
  if (only && !only.includes(doc.ordinal)) continue;
  const s = scenarioFrom(doc);
  const r = { ordinal: doc.ordinal, n: doc.n, stages: {} };
  let t0 = performance.now();
  const rows = classicalPerTimestep(s);
  const { state, ok } = lsStates(s, rows);
  r.stages.ls = { ms: performance.now() - t0 };
  let okDiff = 0, worst = 0;
  for (let i = 0; i < s.n; i++) {
    if (!!ok[i] !== doc.ls_ok[i]) okDiff++;
    if (ok[i] && doc.ls_ok[i]) for (let j = 0; j < 4; j++) worst = Math.max(worst, rel(state[i][j], doc.ls_state[i][j]));
  }
  Object.assign(r.stages.ls, { ok_differs: okDiff, max_rel: worst, usable_rows: doc.ls_ok.filter(Boolean).length });
  t0 = performance.now();
  const g = glrStat(s, state, ok, 30);
  r.stages.glr = { ms: performance.now() - t0, ...cmpArr(g, doc.glr) };
  // rows where the browser's statistic and Python's lie on different sides of the alarm
  // threshold: a nomination can change there (spec 021 review, finding 2)
  r.stages.glr.crossings = [];
  for (let i = 0; i < s.n; i++) {
    if ((g[i] > P.glr_threshold) !== (doc.glr[i] > P.glr_threshold)) r.stages.glr.crossings.push([i, g[i], doc.glr[i]]);
  }
  let absW = 0;
  for (let i = 0; i < s.n; i++) absW = Math.max(absW, Math.abs(g[i] - doc.glr[i]));
  r.stages.glr.max_abs = absW;
  // the GLR on Python's own LS states isolates the statistic from the fit
  const pyState = doc.ls_state.map((x) => Float64Array.from(x)), pyOk = Uint8Array.from(doc.ls_ok.map(Number));
  r.stages.glr_on_py_ls = cmpArr(glrStat(s, pyState, pyOk, 30), doc.glr);
  t0 = performance.now();
  const oc = onlineOwnshipCodes(s.course, s.speed, s.n, P);
  r.stages.ownship = { ms: performance.now() - t0, differs: doc.own_codes.filter((c, i) => c !== oc[i]).length };
  const inn = innovations(s, state, ok);
  r.stages.innovations = cmpArr(inn, doc.innovations);
  const fe = features(s, oc, inn);
  let fw = 0;
  for (let c = 0; c < fe.length; c++) fw = Math.max(fw, cmpArr(fe[c], doc.features[c]).worst);
  r.stages.features = { worst: fw };
  t0 = performance.now();
  const sr = searchByPrefix(s, doc.search.anchor, P);
  r.stages.search = { ms: performance.now() - t0, grid_same: JSON.stringify(sr.grid) === JSON.stringify(doc.search.grid) };
  let cw = 0, inf = 0;
  for (let i = 0; i < sr.grid.length; i++)
    for (let j = 0; j < sr.grid.length; j++) {
      const a = sr.cost[i][j], b = doc.search.cost_table[i][j];
      if (b === null || !Number.isFinite(a)) { if ((b === null) !== !Number.isFinite(a)) inf++; continue; }
      cw = Math.max(cw, rel(a, b));
    }
  Object.assign(r.stages.search, { cost_max_rel: cw, finite_differs: inf, by_prefix_same: JSON.stringify(sr.byPrefix) === JSON.stringify(doc.search.by_prefix) });
  const noms = sortNominations([...glrNominations(g, P.glr_threshold, P), ...searchNominations(sr.byPrefix, P)]);
  r.stages.nominations = { same: JSON.stringify(noms.map((x) => [x.row, x.lo, x.hi, x.source])) === JSON.stringify(doc.nominations), n: noms.length, py: doc.nominations.length };
  if (layerSess) {
    const ev = await evidenceOf(fe, s.n);
    r.stages.evidence = cmpArr(ev, doc.evidence);
    let evAbs = 0;
    for (let i = 0; i < s.n; i++) evAbs = Math.max(evAbs, Math.abs(ev[i] - doc.evidence[i]));
    r.stages.evidence.max_abs = evAbs;
    for (const [name, e] of [["c", null], ["e", ev]]) {
      t0 = performance.now();
      const conf = await confirmOne(s.n, noms.map((x) => ({ ...x })), P, e, layerFor(s));
      r.stages[name] = { ms: performance.now() - t0, ...cmpConf(conf, doc[name], doc.rows) };
    }
  }
  report.push(r);
  console.log(JSON.stringify(r));
}
if (outPath) writeFileSync(outPath, JSON.stringify(report, null, 1));
