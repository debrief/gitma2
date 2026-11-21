// Spec 035 FR-024/025: the demonstrator's solver plug-ins. Each declares a DemoSolverInfo and
// `solve(problem, ctx)` → TmaSolution (both LinkML types, schema 0.38.0). `ctx.run(graph, feeds)`
// runs an exported graph (the worker's ONNX Runtime Web); `ctx.progress` and `ctx.cancelled`
// serve the slow learned model. Solutions are in the problem's frame (metres from ownship at
// the window's first bearing, seconds from it).
import { solveBatch, gridStart } from "../../viewer-data/js/lsq.js";
import { segmentationInputs, layerFeeds, ROWS } from "../../viewer-data/js/handover.js";
import { invSym, scaledCondition, sandwich } from "./linalg.js";
import { INFO } from "./solver-info.js";
import * as TLM from "./tlm.js";

const DEG = Math.PI / 180;
const MIN_SIGMA = 0.1 * DEG; // the physics layer's and C's floor: a noise-free run still divides by sigma

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

// the problem as spec 021's scenario arrays, every `stride`-th bearing
function scenarioArrays(p, stride = 1, sigmaFloor = 0) {
  const idx = [];
  for (let i = 0; i < p.t_s.length; i += stride) idx.push(i);
  if (idx[idx.length - 1] !== p.t_s.length - 1 && stride > 1) idx.push(p.t_s.length - 1);
  const n = idx.length;
  const s = { n, t: new Float64Array(n), ox: new Float64Array(n), oy: new Float64Array(n), z: new Float64Array(n), valid: new Uint8Array(n).fill(1), course: new Float64Array(n), speed: new Float64Array(n), sigma: Math.max(p.sigma_rad, sigmaFloor), zigIndex: 0, idx };
  idx.forEach((i, k) => {
    s.t[k] = p.t_s[i];
    s.ox[k] = p.own_x_m[i];
    s.oy[k] = p.own_y_m[i];
    s.z[k] = p.bearing_rad[i];
    s.course[k] = p.own_course_rad ? p.own_course_rad[i] : 0;
    s.speed[k] = p.own_speed_mps ? p.own_speed_mps[i] : 0;
  });
  s.dt = n > 1 ? s.t[1] - s.t[0] : 10;
  return s;
}

const endG = (T) => [Float64Array.of(1, 0, T, 0), Float64Array.of(0, 1, 0, T), Float64Array.of(0, 0, 1, 0), Float64Array.of(0, 0, 0, 1)];
const flat = (M) => M.flatMap((r) => Array.from(r));

// information of a constant-velocity state (x0, y0, vx, vy) at t = 0 from the bearings
function cvInformation(p, th, sigma) {
  const I = Array.from({ length: 4 }, () => new Float64Array(4));
  const w = 1 / (sigma * sigma);
  for (let i = 0; i < p.t_s.length; i++) {
    const t = p.t_s[i];
    const dx = th[0] + th[2] * t - p.own_x_m[i], dy = th[1] + th[3] * t - p.own_y_m[i];
    const r2 = dx * dx + dy * dy;
    const g = [dy / r2, -dx / r2, (t * dy) / r2, (-t * dx) / r2];
    for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) I[a][b] += w * g[a] * g[b];
  }
  return I;
}

// condition number of the information of the end state, from its covariance
function conditionOf(cov) {
  if (!cov || !cov.every(Number.isFinite)) return Infinity;
  const C = [0, 1, 2, 3].map((i) => Float64Array.from(cov.slice(4 * i, 4 * i + 4)));
  const I = invSym(C, 1e-14);
  return I ? scaledCondition(I) : Infinity;
}

function failed(info, t0, message) {
  return { solver: info.name, solver_version: info.version, status: "failed", message, runtime_ms: now() - t0 };
}

// ---------- batch least squares, JavaScript (spec 021's port of the Python reference) ----------
export const lsJs = {
  info: INFO.lsJs,
  async solve(p) {
    const t0 = now();
    const s = scenarioArrays(p);
    if (s.n < 4) return failed(this.info, t0, "fewer than four bearings in the window");
    const r = solveBatch(s, s.n);
    if (r === null || !Array.from(r.theta).every(Number.isFinite)) return failed(this.info, t0, "no solution");
    const th = r.theta;
    const out = { solver: this.info.name, solver_version: this.info.version, status: r.converged ? "converged" : "not_converged", iterations: r.iterations, cost: r.cost, t_s: [], x_m: [], y_m: [], vx_mps: [], vy_mps: [] };
    for (const t of p.t_s) {
      out.t_s.push(t);
      out.x_m.push(th[0] + th[2] * t);
      out.y_m.push(th[1] + th[3] * t);
      out.vx_mps.push(th[2]);
      out.vy_mps.push(th[3]);
    }
    const ci = invSym(cvInformation(p, th, Math.max(p.sigma_rad, MIN_SIGMA)));
    out.cov_end = ci ? flat(sandwich(endG(p.t_s[p.t_s.length - 1]), ci)) : null;
    out.condition_number = conditionOf(out.cov_end);
    out.runtime_ms = now() - t0;
    return out;
  },
};

// ---------- the physics layer (ONNX), time-late ----------
// rows of the thinned arrays for the problem's manoeuvre spans
function spanRows(s, knots) {
  const row = (t) => {
    let k = 0;
    while (k < s.n - 1 && s.t[k] < t - 1e-9) k++;
    return k;
  };
  return knots.map((m) => [row(m.start_s), Math.max(row(m.end_s), row(m.start_s))]);
}

// constant-velocity legs joined at `knots` ([{start_s, end_s, speed}], at most four: the graph
// has eight knots) fitted to the problem's bearings by the exported physics layer. `courseOnly`
// per knot puts the speed-continuity prior on its end (the truth's kind is told to the oracle;
// a read-out of a model's spans leaves both free). Thinned to ROWS bearings.
async function solveLegs(info, p, ctx, t0, knots, courseOnly) {
  const stride = Math.max(1, Math.ceil(p.t_s.length / ROWS));
  const s = scenarioArrays(p, stride, MIN_SIGMA);
  if (s.n > ROWS) return failed(info, t0, "too many bearings for the graph");
  if (s.n < 4) return failed(info, t0, "fewer than four bearings in the window");
  const k = s.n - 1;
  const trs = spanRows(s, knots);
  if (2 * trs.length > 8) return failed(info, t0, "more than four target manoeuvres in the window (the graph has eight knots)");
  const inp = segmentationInputs(s, k, trs, "chord", true, courseOnly);
  if (inp === null) return failed(info, t0, "no start found");
  const feeds = layerFeeds(s, k, inp);
  feeds.k_state = { dtype: "int64", shape: [1], data: Float64Array.of(k) };
  const o = await ctx.run("tl-layer", feeds);
  const th = Array.from(o.theta, Number);
  if (!th.every(Number.isFinite)) return failed(info, t0, "non-finite solution");
  const M = (th.length - 4) / 2;
  const kn = [];
  for (let j = 0; j < M; j++) {
    const c = o.knot_weights[j];
    if (c > 0) kn.push({ c, t: s.t[Math.round(o.knots[j])], d: [th[4 + 2 * j], th[5 + 2 * j]] });
  }
  const out = { solver: info.name, solver_version: info.version, status: o.plausible[0] === 1 ? "converged" : "not_converged", message: o.plausible[0] === 1 ? undefined : "implausible state (speed over 25 m/s or range over 100 km)", cost: o.cost[0] * s.sigma * s.sigma, t_s: [], x_m: [], y_m: [], vx_mps: [], vy_mps: [], stride };
  for (const t of p.t_s) {
    let x = th[0] + th[2] * t, y = th[1] + th[3] * t, vx = th[2], vy = th[3];
    for (const q of kn) {
      const a = Math.max(t - q.t, 0);
      x += q.c * a * q.d[0];
      y += q.c * a * q.d[1];
      if (t >= q.t) {
        vx += q.c * q.d[0];
        vy += q.c * q.d[1];
      }
    }
    out.t_s.push(t);
    out.x_m.push(x);
    out.y_m.push(y);
    out.vx_mps.push(vx);
    out.vy_mps.push(vy);
  }
  out.cov_end = o.cov_ok[0] === 1 ? Array.from(o.cov, Number) : null;
  out.condition_number = conditionOf(out.cov_end);
  out.runtime_ms = now() - t0;
  return out;
}

function layerSolver(oracle) {
  const info = oracle ? INFO.layerOracle : INFO.layerCv;
  return {
    info,
    async solve(p, ctx) {
      const t0 = now();
      const knots = oracle ? p.knots || [] : [];
      return solveLegs(info, p, ctx, t0, knots, knots.map((m) => !m.speed));
    },
  };
}
export const layerCv = layerSolver(false);
export const layerOracle = layerSolver(true);

// ---------- spec 016's whole-period learned model (ONNX), time-late ----------
// the network on the problem: its per-token means, manoeuvre probabilities and declared spans
// (spans_from_logit at spec 016's settings), or {fail} with the reason
async function runNetwork(info, p, ctx, seed, t0) {
  const n = p.t_s.length;
  const dt = n > 1 ? p.t_s[1] - p.t_s[0] : 0;
  if (Math.abs(dt - TLM.DT) > 1e-6) return { fail: failed(info, t0, "the learned model reads 5-second bearings: set the interval to 5 s") };
  if (n > TLM.MAX_ROWS) return { fail: failed(info, t0, "the learned model reads at most two hours (1,440 bearings): narrow the window") };
  if (n < 2 * TLM.PATCH) return { fail: failed(info, t0, "fewer than twelve bearings in the window") };
  const { f, mask, th } = TLM.periodFeatures(p.t_s, p.own_x_m, p.own_y_m, p.bearing_rad, Math.max(p.sigma_rad, 1e-6));
  if (ctx.progress) ctx.progress({ stage: "running the network" });
  const o = await ctx.run(`tlm-s${seed}`, {
    features: { dtype: "float32", shape: [1, TLM.MAX_ROWS, TLM.N_FEATURES], data: f },
    mask: { dtype: "bool", shape: [1, TLM.MAX_ROWS], data: mask },
  });
  const last = TLM.tokenRows(n);
  const T = last.length;
  const mean = [];
  for (let j = 0; j < T; j++) mean.push([o.mean[3 * j], o.mean[3 * j + 1], o.mean[3 * j + 2]]);
  if (!mean.flat().every(Number.isFinite)) return { fail: failed(info, t0, "non-finite output") };
  const prob = Array.from({ length: T }, (_, j) => 1 / (1 + Math.exp(-o.logit[j])));
  const threshold = p.manoeuvre_threshold ?? 0.5; // spec 016's 0.5 unless the page's slider says otherwise
  const spans = TLM.spansFromLogit(prob, n, threshold, 60.0, Infinity); // every run: the page counts them
  return { n, th, mean, prob, spans, threshold, manoeuvre_t_s: last.map((k) => p.t_s[k]) };
}

function withSpans(out, r) {
  out.manoeuvre_t_s = r.manoeuvre_t_s;
  out.manoeuvre_prob = r.prob;
  out.manoeuvre_start_s = r.spans.map((x) => x[0]);
  out.manoeuvre_end_s = r.spans.map((x) => x[1]);
  return out;
}

function tlmSolver(seed) {
  const info = INFO[`tlm${seed}`];
  return {
    info,
    async solve(p, ctx) {
      const t0 = now();
      const r = await runNetwork(info, p, ctx, seed, t0);
      if (r.fail) return r.fail;
      const tr = TLM.directTrack(r.mean, p.own_x_m, p.own_y_m, p.bearing_rad, r.th);
      const out = { solver: info.name, solver_version: info.version, status: "converged", t_s: [], x_m: [], y_m: [], vx_mps: [], vy_mps: [] };
      for (let k = 0; k < r.n; k++) {
        out.t_s.push(p.t_s[k]);
        out.x_m.push(tr[k][0]);
        out.y_m.push(tr[k][1]);
        out.vx_mps.push(tr[k][2]);
        out.vy_mps.push(tr[k][3]);
      }
      withSpans(out, r);
      out.cov_end = null; // the model states a variance per output, not a joint covariance
      out.condition_number = undefined;
      out.runtime_ms = now() - t0;
      return out;
    },
  };
}

// Spec 016's `learned-arc` read-out in the browser (owner, 2026-11-21: "predict steady legs"):
// the model's declared spans (probability over the scenario's threshold, 0.5 unless the owner
// moves the slider), at most the four with the most probability (the graph's eight knots), and constant-velocity legs (chords) fitted to the bearings at those spans by the
// physics layer, both knots free since the model does not state a manoeuvre's kind. Spec 016
// fitted the arc model with Annex B's prior at the same spans; the legs here are the chord
// model of Gates 1-2, so this is that read-out's shape, not its figures.
const LEGS_MAX = 4;
const LEGS_TAIL_S = 60.0;
function tlmLegsSolver(seed) {
  const info = INFO[`tlm${seed}Legs`];
  return {
    info,
    async solve(p, ctx) {
      const t0 = now();
      const r = await runNetwork(info, p, ctx, seed, t0);
      if (r.fail) return r.fail;
      // a span whose end knot would have fewer than LEGS_TAIL_S of bearings after it leaves the
      // knot's two parameters undetermined (the head does declare the window's last rows): drop it
      const last = p.t_s[p.t_s.length - 1];
      const spans = TLM.spansFromLogit(r.prob, r.n, r.threshold, 60.0, Infinity).filter(([, b]) => last - b >= LEGS_TAIL_S).slice(0, LEGS_MAX);
      if (ctx.progress) ctx.progress({ stage: `fitting ${spans.length + 1} legs` });
      const knots = spans.map(([a, b]) => ({ start_s: a, end_s: b, speed: true }));
      const out = await solveLegs(info, p, ctx, t0, knots, knots.map(() => false));
      if (out.status === "failed") return out;
      withSpans(out, { ...r, spans });
      out.runtime_ms = now() - t0;
      return out;
    },
  };
}
export const tlm1 = tlmSolver(1), tlm2 = tlmSolver(2), tlm3 = tlmSolver(3);
export const tlm1Legs = tlmLegsSolver(1), tlm2Legs = tlmLegsSolver(2), tlm3Legs = tlmLegsSolver(3);

// Gate 2's real-time E is no longer offered (owner, 2026-11-21: "not interested in a track of
// real-time estimates"); spec 021's pipeline stays on the viewer page.

export const SOLVERS = [lsJs, layerCv, layerOracle, tlm1, tlm2, tlm3, tlm1Legs, tlm2Legs, tlm3Legs];
export const solverByName = (name) => SOLVERS.find((s) => s.info.name === name) || lsJs;
export { gridStart };
