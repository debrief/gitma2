// Spec 035 FR-024/025: the demonstrator's solver plug-ins. Each declares a DemoSolverInfo and
// `solve(problem, ctx)` → TmaSolution (both LinkML types, schema 0.37.0). `ctx.run(graph, feeds)`
// runs an exported graph (the worker's ONNX Runtime Web); `ctx.progress` and `ctx.cancelled`
// serve the slow learned model. Solutions are in the problem's frame (metres from ownship at
// the window's first bearing, seconds from it).
import { solveBatch, gridStart } from "../../viewer-data/js/lsq.js";
import { segmentationInputs, layerFeeds, ROWS } from "../../viewer-data/js/handover.js";
import { invSym, scaledCondition, sandwich } from "./linalg.js";
import { INFO } from "./solver-info.js";

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

function layerSolver(oracle) {
  const info = oracle ? INFO.layerOracle : INFO.layerCv;
  return {
    info,
    async solve(p, ctx) {
      const t0 = now();
      const stride = Math.max(1, Math.ceil(p.t_s.length / ROWS));
      const s = scenarioArrays(p, stride, MIN_SIGMA);
      if (s.n > ROWS) return failed(info, t0, "too many bearings for the graph");
      if (s.n < 4) return failed(info, t0, "fewer than four bearings in the window");
      const k = s.n - 1;
      let trs = [];
      let courseOnly = null;
      if (oracle) {
        trs = spanRows(s, p.knots || []);
        courseOnly = (p.knots || []).map((m) => !m.speed);
        if (2 * trs.length > 8) return failed(info, t0, "more than four target manoeuvres in the window (the graph has eight knots)");
      }
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
    },
  };
}
export const layerCv = layerSolver(false);
export const layerOracle = layerSolver(true);

// ---------- Gate 2's carried model E, end to end from bearings (spec 021's pipeline) ----------
export const learnedE = {
  info: INFO.learnedE,
  async solve(p, ctx) {
    const t0 = now();
    const { runLive } = await import("../../viewer-data/js/pipeline.js");
    const dt0 = p.t_s.length > 1 ? p.t_s[1] - p.t_s[0] : 10;
    const stride = Math.max(Math.ceil(10 / dt0 - 1e-9), Math.ceil(p.t_s.length / ROWS));
    const s = scenarioArrays(p, stride, MIN_SIGMA);
    // E's row-based settings assume a regular grid: drop the appended last row if off-grid
    if (s.n > 1 && Math.abs(s.t[s.n - 1] - s.t[s.n - 2] - s.dt) > 1e-6) s.n -= 1;
    if (s.n < 40) return failed(this.info, t0, "the window is too short for the learned model (under 40 rows)");
    const turn = (p.own_turns || [])[0];
    s.zigIndex = turn ? Math.min(Math.round(turn.start_s / s.dt), s.n - 1) : 0;
    const res = await runLive(s, ctx.run, ctx.progress || (() => {}), ctx.cancelled || (() => false));
    const out = { solver: this.info.name, solver_version: this.info.version, status: "converged", t_s: [], x_m: [], y_m: [], vx_mps: [], vy_mps: [], stride };
    let last = null;
    res.rows.forEach((k, q) => {
      const e = res.estimates[q];
      if (!e || !e.plausible || !e.state.every(Number.isFinite)) return;
      out.t_s.push(s.t[k]);
      out.x_m.push(e.state[0]);
      out.y_m.push(e.state[1]);
      out.vx_mps.push(e.state[2]);
      out.vy_mps.push(e.state[3]);
      last = e;
    });
    if (!out.t_s.length) return failed(this.info, t0, "no plausible estimate in the window");
    out.cov_end = null; // never shown (Gate 3: overconfident)
    out.condition_number = last && last.cov_ok ? conditionOf(last.cov) : Infinity;
    out.runtime_ms = now() - t0;
    return out;
  },
};

export const SOLVERS = [lsJs, layerCv, layerOracle, learnedE];
export const solverByName = (name) => SOLVERS.find((s) => s.info.name === name) || lsJs;
export { gridStart };
