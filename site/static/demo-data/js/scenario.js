// Spec 035: a DemoScenario's bearings (FR-010, FR-011) and the solver problem for its window
// (FR-021, FR-024). Noise is zero-mean Gaussian from a seeded xoshiro128** stream (Box-Muller,
// one draw pair per two bearings, in time order over the whole scenario), so a seed gives the
// same bearings whatever the window.
import { buildPath, stateAt, manoeuvres, DEG } from "./track.js";

export const SCHEMA_VERSION = "0.40.0";

// Owner, 2026-11-22: bearings are lost while ownship turns and for two minutes after each turn
// is complete. A scenario's turn_loss_s is that tail in seconds (null: bearings kept through
// turns); a scenario without the field takes the default.
export const TURN_LOSS_S = 120;
export const turnLossOf = (sc) => (sc.turn_loss_s === undefined ? TURN_LOSS_S : sc.turn_loss_s);

// [t0, t1] intervals (s) in which no bearing is received: each ownship course change from its
// start to its end plus the scenario's tail
export function lossIntervals(sc, ownPath) {
  const tail = turnLossOf(sc);
  if (tail === null || !(tail >= 0)) return [];
  return manoeuvres(ownPath).filter((m) => m.course).map((m) => [m.t0, m.t1 + tail]);
}
const TWO_PI = 2 * Math.PI;
export const wrap2pi = (a) => {
  const w = a % TWO_PI;
  return w < 0 ? w + TWO_PI : w;
};
export const wrapPi = (a) => Math.atan2(Math.sin(a), Math.cos(a));

// xoshiro128** seeded by splitmix32 (32-bit integer arithmetic only, so every engine agrees)
export function rng(seed) {
  let z = seed >>> 0;
  const sm = () => {
    z = (z + 0x9e3779b9) >>> 0;
    let x = z;
    x = Math.imul(x ^ (x >>> 16), 0x85ebca6b) >>> 0;
    x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35) >>> 0;
    return (x ^ (x >>> 16)) >>> 0;
  };
  const s = [sm(), sm(), sm(), sm()];
  const rotl = (x, k) => ((x << k) | (x >>> (32 - k))) >>> 0;
  const next = () => {
    const r = Math.imul(rotl(Math.imul(s[1], 5) >>> 0, 7), 9) >>> 0;
    const t = (s[1] << 9) >>> 0;
    s[2] = (s[2] ^ s[0]) >>> 0;
    s[3] = (s[3] ^ s[1]) >>> 0;
    s[1] = (s[1] ^ s[2]) >>> 0;
    s[0] = (s[0] ^ s[3]) >>> 0;
    s[2] = (s[2] ^ t) >>> 0;
    s[3] = rotl(s[3], 11);
    return r;
  };
  // uniform in (0, 1)
  const uniform = () => (next() + 0.5) / 4294967296;
  let spare = null;
  const gauss = () => {
    if (spare !== null) {
      const g = spare;
      spare = null;
      return g;
    }
    const u1 = uniform(), u2 = uniform();
    const m = Math.sqrt(-2 * Math.log(u1));
    spare = m * Math.sin(TWO_PI * u2);
    return m * Math.cos(TWO_PI * u2);
  };
  return { next, uniform, gauss };
}

export function period(sc, paths = null) {
  const p = paths || { own: buildPath(sc.ownship), tgt: buildPath(sc.target) };
  return Math.min(p.own.end, p.tgt.end);
}

// The whole scenario's truth and bearings: arrays over t = 0, dt, ... up to the period.
// `valid[i]` is 0 where the bearing is lost (an ownship turn and its tail); the noise is drawn
// for every row all the same, so the kept bearings do not change with the loss setting.
export function bearings(sc) {
  const own = buildPath(sc.ownship), tgt = buildPath(sc.target);
  const T = Math.min(own.end, tgt.end);
  const dt = sc.interval_s;
  const n = Math.floor(T / dt + 1e-9) + 1;
  const g = rng(sc.seed);
  const sig = sc.sigma_deg * DEG;
  const out = {
    n, dt, period: T, paths: { own, tgt },
    t: new Float64Array(n), z: new Float64Array(n), truth: new Float64Array(n),
    ox: new Float64Array(n), oy: new Float64Array(n), ovx: new Float64Array(n), ovy: new Float64Array(n),
    tx: new Float64Array(n), ty: new Float64Array(n), tvx: new Float64Array(n), tvy: new Float64Array(n),
    valid: new Uint8Array(n).fill(1), lost: lossIntervals(sc, own),
  };
  for (let i = 0; i < n; i++) {
    const t = i * dt;
    const o = stateAt(own, t), q = stateAt(tgt, t);
    out.t[i] = t;
    out.ox[i] = o.x; out.oy[i] = o.y; out.ovx[i] = o.vx; out.ovy[i] = o.vy;
    out.tx[i] = q.x; out.ty[i] = q.y; out.tvx[i] = q.vx; out.tvy[i] = q.vy;
    const b = wrap2pi(Math.atan2(q.x - o.x, q.y - o.y));
    out.truth[i] = b;
    out.z[i] = wrap2pi(b + sig * g.gauss());
    for (const [a, e] of out.lost) if (t >= a - 1e-9 && t <= e + 1e-9) out.valid[i] = 0;
  }
  return out;
}

// indices of the bearing rows inside the window [start, end]; lost bearings keep their row (the
// solvers' grids are regular) and are flagged invalid in the problem
export function windowRows(sc, b) {
  const a = Math.max(0, sc.window.start_s), e = Math.min(sc.window.end_s, b.period);
  const rows = [];
  for (let i = 0; i < b.n; i++) if (b.t[i] >= a - 1e-9 && b.t[i] <= e + 1e-9) rows.push(i);
  return rows;
}

// The TmaProblem for the window: times from the window's first bearing, positions relative to
// ownship there (the solution adds the origin back), and the truth's manoeuvre spans in the
// window for a solver that accepts knots (the oracle).
export function problemOf(sc, b, rows) {
  const i0 = rows[0];
  const origin = [b.ox[i0], b.oy[i0]];
  const t0 = b.t[i0];
  const n = rows.length;
  const p = {
    t_s: new Array(n), bearing_rad: new Array(n), own_x_m: new Array(n), own_y_m: new Array(n),
    own_course_rad: new Array(n), own_speed_mps: new Array(n),
    sigma_rad: sc.sigma_deg * DEG, knots: [], bearing_valid: new Array(n),
  };
  rows.forEach((i, k) => {
    p.t_s[k] = b.t[i] - t0;
    p.bearing_rad[k] = b.z[i];
    p.own_x_m[k] = b.ox[i] - origin[0];
    p.own_y_m[k] = b.oy[i] - origin[1];
    p.own_course_rad[k] = wrap2pi(Math.atan2(b.ovx[i], b.ovy[i]));
    p.own_speed_mps[k] = Math.hypot(b.ovx[i], b.ovy[i]);
    p.bearing_valid[k] = b.valid[i];
  });
  const tEnd = b.t[rows[n - 1]];
  for (const m of manoeuvres(b.paths.tgt)) {
    if (m.t1 < t0 || m.t0 > tEnd) continue;
    p.knots.push({ start_s: Math.max(m.t0, t0) - t0, end_s: Math.min(m.t1, tEnd) - t0, course: m.course, speed: m.speed });
  }
  // ownship turns in the window (the learned model's zig)
  p.own_turns = manoeuvres(b.paths.own)
    .filter((m) => m.course && m.t1 >= t0 && m.t0 <= tEnd)
    .map((m) => ({ start_s: Math.max(m.t0, t0) - t0, end_s: Math.min(m.t1, tEnd) - t0 }));
  return { problem: p, origin, t0 };
}

// FR-036: truth has a target manoeuvre inside the window
export function targetManoeuvresIn(sc, b) {
  const a = sc.window.start_s, e = Math.min(sc.window.end_s, b.period);
  return manoeuvres(b.paths.tgt).filter((m) => m.t1 >= a && m.t0 <= e);
}

export function ownTurnsIn(sc, b) {
  const a = sc.window.start_s, e = Math.min(sc.window.end_s, b.period);
  return manoeuvres(b.paths.own).filter((m) => m.course && m.t1 >= a && m.t0 <= e);
}

// the number of bearings received (not lost) among `rows`
export function validCount(b, rows) {
  let n = 0;
  for (const i of rows) n += b.valid[i];
  return n;
}
