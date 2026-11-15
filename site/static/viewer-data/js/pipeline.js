// The carried model E end to end from bearings (spec 021): least squares → GLR and O → E-s's
// evidence (exported graph) → search → nominations → C's confirmation with the evidence (the
// exported physics layer) → at each scored row, the hand-over and E-w's estimate (exported
// graph). `run(graph, feeds)` runs one exported graph: graph is "es", "layer" or "ew".
import { classicalPerTimestep, lsStates } from "./lsq.js";
import { glrStat } from "./glr.js";
import { onlineOwnshipCodes } from "./ownship.js";
import { innovations, features, CHANNELS } from "./features.js";
import { searchByPrefix } from "./search.js";
import { glrNominations, searchNominations, sortNominations, confirmOne, intervalsAt } from "./confirm.js";
import { segmentationInputs, prefixInputs, codeChannel, layerFeeds, ROWS } from "./handover.js";

export const PARAMS = {
  course_tol_deg: 5.0, speed_tol_kt: 0.5, course_change_deg: 10.0, speed_change_kt: 1.0,
  l_min_rows: 30, t_min_rows: 6, t_lengths_rows: [6, 9, 12, 18, 24, 36], search_penalty: 30.0,
  nominator_far: 0.2, retest_rows: 6, tau: 13.8, margin: 0.0, mode: "gap",
  glr_threshold: 4.665063657744733, glr_window: 30, window_rows: 36, candidate_step_rows: 3,
  search_every_rows: 30, search_step_rows: 6, search_horizon_rows: 18, polish_rows: 3,
};
export const HANDOVER = "knot_at_k";

// a scenario from its pack arrays: own [n][t, x, y, course, speed], obs [n][t, bearing, valid]
export function scenarioOf(doc) {
  const n = doc.own.length;
  const s = { n, zigIndex: doc.zig_index, sigma: doc.sigma, dt: doc.dt_s, t: new Float64Array(n), ox: new Float64Array(n), oy: new Float64Array(n), z: new Float64Array(n), valid: new Uint8Array(n), course: new Float64Array(n), speed: new Float64Array(n) };
  for (let i = 0; i < n; i++) {
    const o = doc.own[i], b = doc.obs[i];
    s.t[i] = o[0]; s.ox[i] = o[1]; s.oy[i] = o[2]; s.course[i] = o[3]; s.speed[i] = o[4];
    s.z[i] = b[1]; s.valid[i] = b[2] !== 0 ? 1 : 0;
  }
  return s;
}

// every 60 s from the first G5 row (zig + 5 min) to the end of the window
export function scoredRows(s) {
  const first = s.zigIndex + Math.round((5 * 60) / s.dt);
  const out = [];
  for (let k = first; k < s.n; k += Math.round(60 / s.dt)) out.push(k);
  return out;
}

function stack(per) {
  const feeds = {};
  const B = per.length;
  for (const name of Object.keys(per[0])) {
    const one = per[0][name];
    const size = one.data.length;
    const data = new Float64Array(size * B);
    per.forEach((f, b) => data.set(f[name].data, b * size));
    feeds[name] = { dtype: one.dtype, shape: [B, ...one.shape.slice(1)], data };
  }
  return feeds;
}

export async function runLive(s, run, onProgress = () => {}, cancelled = () => false) {
  const P = PARAMS;
  const t0 = Date.now();
  const stage = (name, extra = {}) => onProgress({ stage: name, seconds: (Date.now() - t0) / 1000, ...extra });
  stage("least squares");
  const { state, ok } = lsStates(s, classicalPerTimestep(s));
  stage("GLR statistic");
  const g = glrStat(s, state, ok, P.glr_window);
  stage("ownship legs (O)");
  const oc = onlineOwnshipCodes(s.course, s.speed, s.n, P);
  const fe = features(s, oc, innovations(s, state, ok));
  stage("E-s evidence");
  const x = new Float64Array(CHANNELS * ROWS);
  for (let c = 0; c < CHANNELS; c++) x.set(fe[c].subarray(0, s.n), c * ROWS);
  const ev = (await run("es", { features: { dtype: "float64", shape: [1, CHANNELS, ROWS], data: x } })).evidence.subarray(0, s.n);
  const rows = scoredRows(s);
  stage("search");
  const sr = searchByPrefix(s, rows[0], P);
  const noms = sortNominations([...glrNominations(g, P.glr_threshold, P), ...searchNominations(sr.byPrefix, P)]);
  stage("confirmation", { nominations: noms.length, decided: 0 });
  let decided = 0;
  const layer = async (reqs) => {
    if (cancelled()) throw new Error("cancelled");
    const per = reqs.map(([k, trs]) => {
      const inp = segmentationInputs(s, k, trs, "chord", false);
      if (inp === null) throw new Error(`no valid bearing on [0, ${k}]`);
      return layerFeeds(s, k, inp);
    });
    const out = await run("layer", stack(per));
    return Array.from(out.cost, Number);
  };
  const conf = await confirmOne(s.n, noms, P, ev, layer, () => {
    decided += 1;
    stage("confirmation", { nominations: noms.length, decided });
  });
  const result = { rows, decisions: conf.decisions, intervals: [], estimates: [] };
  for (let q = 0; q < rows.length; q++) {
    if (cancelled()) throw new Error("cancelled");
    const k = rows[q];
    const ivs = intervalsAt(conf, k, P);
    result.intervals.push(ivs);
    const inp = prefixInputs(s, k, ivs, P.mode, HANDOVER);
    if (inp === null) {
      result.estimates.push(null);
      continue;
    }
    const out = await run("ew", layerFeeds(s, k, inp, codeChannel(ivs, k, s.n)));
    result.estimates.push({ state: Array.from(out.state, Number), cov: Array.from(out.cov, Number), plausible: out.plausible[0] === 1, cov_ok: out.cov_ok[0] === 1 });
    stage("estimates", { done: q + 1, of: rows.length, row: q, estimate: result.estimates[q], intervals: ivs });
  }
  stage("done");
  return result;
}
