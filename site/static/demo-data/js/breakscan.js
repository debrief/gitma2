// Spec 035 (owner, 2026-11-21): a classical yardstick for where a target manoeuvred. One
// hypothesis beside "one leg": the target holds ONE speed and changes course once, at once, at
// time tb (five unknowns: x0, y0, speed, course, course change). The break time is scanned and
// each candidate fitted to the bearings by damped least squares; the break is declared when the
// fit improves on one leg by more than the BIC's price of its three extra unknowns (course
// change, and the time and the hard choice of having one). Nothing is learned and no prior on
// manoeuvres is used. The physics layer's chord gives a break four free unknowns and a soft
// speed prior, which leaves the time undetermined over half an hour on the target-turn preset;
// holding speed exactly is what pins it.
import { solveBatch } from "../../viewer-data/js/lsq.js";

const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
export const MAX_ROWS = 1440; // thinned to at most this many bearings
export const EDGE_S = 300; // no break within five minutes of either end of the window
export const COARSE_S = 240, FINE_S = 60;
const STARTS = [0, 0.7, -0.7, 1.6, -1.6]; // course changes tried at every candidate time, rad
const SPEED_MAX = 25; // m/s, as the layer's plausibility

// position at t of q = [x0, y0, speed, course, course change] with the break at tb
export function position(q, tb, t) {
  const t1 = Math.min(t, tb), t2 = Math.max(t - tb, 0);
  return [q[0] + q[2] * (Math.sin(q[3]) * t1 + Math.sin(q[3] + q[4]) * t2), q[1] + q[2] * (Math.cos(q[3]) * t1 + Math.cos(q[3] + q[4]) * t2)];
}

function residuals(d, q, tb, out) {
  for (let i = 0; i < d.n; i++) {
    const [x, y] = position(q, tb, d.t[i]);
    out[i] = wrap(d.z[i] - Math.atan2(x - d.ox[i], y - d.oy[i]));
  }
  return out;
}
const sumsq = (r) => { let s = 0; for (let i = 0; i < r.length; i++) s += r[i] * r[i]; return s; };

// Gauss-Jordan with partial pivoting on a 5 by 5 system; null when singular
function solve5(A, b) {
  const M = A.map((row, i) => [...row, b[i]]);
  for (let c = 0; c < 5; c++) {
    let p = c;
    for (let r = c + 1; r < 5; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    if (!(Math.abs(M[c][c]) > 1e-300)) return null;
    for (let r = 0; r < 5; r++) {
      if (r === c) continue;
      const f = M[r][c] / M[c][c];
      for (let k = c; k <= 5; k++) M[r][k] -= f * M[c][k];
    }
  }
  return M.map((row, i) => row[5] / row[i]);
}

const STEP = [1, 1, 1e-4, 1e-6, 1e-6]; // forward-difference steps: m, m, m/s, rad, rad

// damped least squares for the break at tb from q0: {q, cost} (cost in rad squared)
export function fitBreak(d, tb, q0) {
  let q = q0.slice();
  let r = residuals(d, q, tb, new Float64Array(d.n));
  let c = sumsq(r), lam = 1e-3;
  const J = STEP.map(() => new Float64Array(d.n)), rr = new Float64Array(d.n);
  for (let it = 0; it < 40; it++) {
    for (let k = 0; k < 5; k++) {
      const qq = q.slice();
      qq[k] += STEP[k];
      residuals(d, qq, tb, rr);
      for (let i = 0; i < d.n; i++) J[k][i] = (rr[i] - r[i]) / STEP[k];
    }
    const A = Array.from({ length: 5 }, () => new Array(5).fill(0)), g = new Array(5).fill(0);
    for (let a = 0; a < 5; a++) {
      for (let b = a; b < 5; b++) {
        let s = 0;
        for (let i = 0; i < d.n; i++) s += J[a][i] * J[b][i];
        A[a][b] = A[b][a] = s;
      }
      let s = 0;
      for (let i = 0; i < d.n; i++) s += J[a][i] * r[i];
      g[a] = -s;
    }
    let stop = true;
    for (let trial = 0; trial < 8; trial++) {
      const dq = solve5(A.map((row, i) => row.map((v, j) => (i === j ? v * (1 + lam) : v))), g);
      const qn = dq && q.map((v, k) => v + dq[k]);
      if (qn && qn.every(Number.isFinite) && qn[2] > 0.05 && qn[2] < SPEED_MAX) {
        const cn = sumsq(residuals(d, qn, tb, rr));
        if (cn < c) {
          stop = c - cn < 1e-10 * c;
          q = qn;
          r.set(rr);
          c = cn;
          lam = Math.max(lam / 10, 1e-9);
          break;
        }
      }
      lam *= 10;
    }
    if (stop) break;
  }
  return { q, cost: c };
}

// every `stride`-th bearing of a TmaProblem, at most MAX_ROWS
export function thin(p) {
  const stride = Math.max(1, Math.ceil(p.t_s.length / MAX_ROWS));
  const idx = [];
  for (let i = 0; i < p.t_s.length; i += stride) idx.push(i);
  const pick = (a) => Float64Array.from(idx, (i) => a[i]);
  return { n: idx.length, stride, t: pick(p.t_s), ox: pick(p.own_x_m), oy: pick(p.own_y_m), z: pick(p.bearing_rad) };
}

// The scan. Returns {one: {theta, cost}, best: {tb, q, cost} | null, declared, price, drop,
// fits, stride, n}; costs are sums of squared residuals in rad squared over the thinned rows,
// `drop` and `price` are in chi-square units (divided by sigma squared).
export function scanBreak(p, sigma, hooks = {}) {
  const d = thin(p);
  const s = { n: d.n, t: d.t, ox: d.ox, oy: d.oy, z: d.z, valid: new Uint8Array(d.n).fill(1), sigma };
  const one = solveBatch(s, d.n);
  if (one === null || !Array.from(one.theta).every(Number.isFinite)) return null;
  const th = one.theta;
  const q1 = [th[0], th[1], Math.hypot(th[2], th[3]), Math.atan2(th[2], th[3]), 0];
  const lo = d.t[0] + EDGE_S, hi = d.t[d.n - 1] - EDGE_S;
  const price = 3 * Math.log(d.n);
  const out = { one: { theta: Array.from(th), cost: one.cost }, best: null, declared: false, price, drop: 0, fits: 0, stride: d.stride, n: d.n };
  if (!(hi > lo) || !(q1[2] > 0.05)) return out;
  const seen = new Map();
  let best = null;
  const tryAt = (tb, warm) => {
    if (seen.has(tb)) return;
    let b = null;
    const starts = STARTS.map((dc) => [q1[0], q1[1], q1[2], q1[3], dc]);
    if (warm) starts.push(warm.slice());
    for (const q0 of starts) {
      const f = fitBreak(d, tb, q0);
      out.fits++;
      if (b === null || f.cost < b.cost) b = f;
    }
    seen.set(tb, b);
    if (best === null || b.cost < best.cost) best = { tb, q: b.q, cost: b.cost };
  };
  const coarse = [];
  for (let tb = lo; tb <= hi + 1e-9; tb += COARSE_S) coarse.push(tb);
  for (let i = 0; i < coarse.length; i++) {
    if (hooks.cancelled && hooks.cancelled()) return null;
    tryAt(coarse[i], null);
    if (hooks.progress) hooks.progress({ stage: "scanning break times", done: i + 1, of: coarse.length });
  }
  if (best) {
    const centre = best.tb;
    for (let tb = Math.max(lo, centre - COARSE_S + FINE_S); tb <= Math.min(hi, centre + COARSE_S - FINE_S) + 1e-9; tb += FINE_S) tryAt(tb, best.q);
  }
  out.best = best;
  if (best) {
    out.drop = (one.cost - best.cost) / (sigma * sigma);
    out.declared = out.drop > price;
  }
  return out;
}
