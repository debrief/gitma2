// Spec 036: arctan slicing, the leg splitter of Debrief's 2015 zig detector, and a multi-leg
// variant (Annex B's background table; research note 07 §1).
//
// While target and ownship both hold course and speed, the relative position is linear in time,
// so the bearings follow the arctan law
//   b(t) = atan2(sin b0 + a t, cos b0 + c t)
// with three parameters (b0, a, c): range is a free scale and a, c are the relative velocity
// divided by the range at t = 0. A target manoeuvre breaks the law. Debrief's detector fits it to
// a steady ownship leg, tries every split of that leg with a fixed buffer of bearings dropped
// around the split, and accepts the best split if the slices' score is under the whole leg's
// score times ZigRatio. One split per ownship leg.
//
// The multi-leg variant answers the 2017 note and Annex B's shortfalls: it subtracts ownship's
// known motion (a constant-velocity target fit, valid through ownship's turns, so windows are not
// cut at them), splits recursively, and accepts a split when the drop in cost, in units of the
// bearing variance, exceeds a threshold tied to the noise rather than a ratio.
import { levenbergMarquardt, gridStart, angleDiff } from "../../viewer-data/js/lsq.js";

const MIN_SIGMA = 0.1 * (Math.PI / 180);

// ---------- the three-parameter arctan law ----------
function arctanCost(t, z, b0, a, c) {
  let sum = 0;
  const sb = Math.sin(b0), cb = Math.cos(b0);
  for (let i = 0; i < t.length; i++) {
    const r = angleDiff(z[i], Math.atan2(sb + a * t[i], cb + c * t[i]));
    sum += r * r;
  }
  return sum;
}

function solve3(A, g) {
  // Gaussian elimination with partial pivoting on a 3 × 3 system
  const M = A.map((row, i) => [...row, g[i]]);
  for (let k = 0; k < 3; k++) {
    let p = k;
    for (let i = k + 1; i < 3; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
    if (!(Math.abs(M[p][k]) > 1e-300)) return null;
    [M[k], M[p]] = [M[p], M[k]];
    for (let i = k + 1; i < 3; i++) {
      const f = M[i][k] / M[k][k];
      for (let j = k; j < 4; j++) M[i][j] -= f * M[k][j];
    }
  }
  const x = [0, 0, 0];
  for (let i = 2; i >= 0; i--) {
    let s = M[i][3];
    for (let j = i + 1; j < 3; j++) s -= M[i][j] * x[j];
    x[i] = s / M[i][i];
  }
  return x.every(Number.isFinite) ? x : null;
}

// Levenberg–Marquardt on (b0, a, c); t relative to the slice's first bearing
function lm3(t, z, start, maxIt = 60) {
  let [b0, a, c] = start;
  let cost = arctanCost(t, z, b0, a, c);
  let lam = 1e-3;
  for (let it = 0; it < maxIt; it++) {
    const J = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    const g = [0, 0, 0];
    const sb = Math.sin(b0), cb = Math.cos(b0);
    for (let i = 0; i < t.length; i++) {
      const X = sb + a * t[i], Y = cb + c * t[i];
      const r2 = X * X + Y * Y;
      if (!(r2 > 0)) continue;
      const res = angleDiff(z[i], Math.atan2(X, Y));
      const dX = Y / r2, dY = -X / r2;
      const row = [dX * cb - dY * sb, dX * t[i], dY * t[i]];
      for (let p = 0; p < 3; p++) {
        g[p] += row[p] * res;
        for (let q = 0; q < 3; q++) J[p][q] += row[p] * row[q];
      }
    }
    let accepted = false;
    while (lam < 1e12) {
      const D = J.map((row, p) => row.map((v, q) => (p === q ? v * (1 + lam) + 1e-30 : v)));
      const step = solve3(D, g);
      if (step) {
        const nb = b0 + step[0], na = a + step[1], nc = c + step[2];
        const nCost = arctanCost(t, z, nb, na, nc);
        if (nCost < cost) {
          const done = cost - nCost < 1e-12 * Math.max(cost, 1e-30);
          b0 = nb; a = na; c = nc; cost = nCost;
          lam = Math.max(lam / 10, 1e-12);
          accepted = true;
          if (done) return { theta: [b0, a, c], cost };
          break;
        }
      }
      lam *= 10;
    }
    if (!accepted) break;
  }
  return { theta: [b0, a, c], cost };
}

// the arctan law's best fit to bearings z at times t (any origin): a start that matches the
// first bearing and the mean bearing rate, and one with no relative motion
export function fitArctan(t, z) {
  const n = t.length;
  if (n < 4) return { cost: Infinity, theta: null };
  const tt = t.map((x) => x - t[0]);
  const span = tt[n - 1] || 1;
  const rate = angleDiff(z[n - 1], z[0]) / span;
  let best = null;
  for (const scale of [1, 0.3, 3]) {
    const b0 = z[0];
    const r = rate * scale;
    for (const start of [[b0, r * Math.cos(b0), -r * Math.sin(b0)], [b0, 0, 0]]) {
      const f = lm3(tt, z, start);
      if (!best || f.cost < best.cost) best = f;
    }
  }
  return best;
}

// ---------- slices of a scenario's arrays ----------
// s: the splitter's arrays {n, t, ox, oy, z, valid, course, speed, sigma}; rows [a, b] inclusive,
// leaving out [skipA, skipB] when given
function rowsOf(a, b, skipA = -1, skipB = -2) {
  const out = [];
  for (let r = a; r <= b; r++) if (r < skipA || r > skipB) out.push(r);
  return out;
}
function sliceScenario(s, rows) {
  const n = rows.length;
  const o = { n, t: new Float64Array(n), ox: new Float64Array(n), oy: new Float64Array(n), z: new Float64Array(n), valid: new Uint8Array(n), sigma: s.sigma };
  rows.forEach((r, k) => {
    o.t[k] = s.t[r]; o.ox[k] = s.ox[r]; o.oy[k] = s.oy[r]; o.z[k] = s.z[r]; o.valid[k] = s.valid ? s.valid[r] : 1;
  });
  return o;
}

// the ownship-subtracted constant-velocity fit (gitma's LM from its grid start, warm start too)
function fitCv(s, rows, warm = null) {
  const sub = sliceScenario(s, rows);
  if (sub.n < 4) return { cost: Infinity, theta: null };
  let best = null;
  const [found, g] = gridStart(sub, sub.n);
  if (found) best = levenbergMarquardt(sub, g, sub.n);
  if (warm) {
    const w = levenbergMarquardt(sub, warm, sub.n);
    if (!best || w.cost < best.cost) best = w;
  }
  if (!best || !Number.isFinite(best.cost)) return { cost: Infinity, theta: null };
  return { cost: best.cost, theta: best.theta };
}

const best2 = (x, y) => (y && y.cost < x.cost ? y : x);

// warm start only
function fitCvWarm(s, rows, warm) {
  const sub = sliceScenario(s, rows);
  if (sub.n < 4) return { cost: Infinity, theta: null };
  const w = levenbergMarquardt(sub, warm, sub.n);
  return Number.isFinite(w.cost) ? { cost: w.cost, theta: w.theta } : { cost: Infinity, theta: null };
}

// ---------- ownship's steady legs (ownship's motion is known exactly) ----------
export function ownshipLegs(s, tolDeg = 0.5, tolMps = 0.05) {
  const legs = [];
  let start = 0;
  const steadyAt = (r) => r > 0 && Math.abs(angleDiff(s.course[r], s.course[r - 1])) * (180 / Math.PI) < tolDeg && Math.abs(s.speed[r] - s.speed[r - 1]) < tolMps;
  let inLeg = true;
  for (let r = 1; r < s.n; r++) {
    const st = steadyAt(r);
    if (inLeg && !st) {
      legs.push([start, r - 1]);
      inLeg = false;
    } else if (!inLeg && st) {
      start = r;
      inLeg = true;
    }
  }
  if (inLeg) legs.push([start, s.n - 1]);
  return legs;
}

// ---------- Debrief 2015: one split per steady ownship leg, ZigRatio ----------
export const DEBRIEF = { zigRatio: 0.6, bufferRows: 12, minSliceRows: 18, stepRows: 3, minLegRows: 2 * 18 + 12 };

export async function debriefSlicing(s, P = DEBRIEF, cancelled = () => false) {
  const found = [];
  const legs = ownshipLegs(s).filter(([a, b]) => b - a + 1 >= P.minLegRows);
  const breathe = () => new Promise((r) => setTimeout(r, 0));
  let fits = 0;
  for (const [a, b] of legs) {
    const tt = Array.from(s.t.subarray(a, b + 1)), zz = Array.from(s.z.subarray(a, b + 1));
    const whole = fitArctan(tt, zz);
    fits++;
    const wholeScore = whole.cost / (b - a + 1); // per bearing: the slices drop the buffer
    let best = null;
    const half = Math.floor(P.bufferRows / 2);
    for (let c = a + P.minSliceRows + half; c <= b - P.minSliceRows - half; c += P.stepRows) {
      const L = fitArctan(tt.slice(0, c - half - a), zz.slice(0, c - half - a));
      const R = fitArctan(tt.slice(c + half - a + 1), zz.slice(c + half - a + 1));
      fits += 2;
      const m = (c - half - a) + (b - c - half);
      const score = (L.cost + R.cost) / m;
      if (!best || score < best.score) best = { c, score, lo: c - half, hi: c + half };
      if (fits % 40 === 0) {
        await breathe();
        if (cancelled()) throw new Error("cancelled");
      }
    }
    if (best && best.score < wholeScore * P.zigRatio) found.push({ lo: best.lo, hi: best.hi, stat: wholeScore / best.score });
  }
  return { spans: found, fits, legs };
}

// ---------- multi-leg: recursive, ownship subtracted, threshold tied to the noise ----------
// tau: the cost drop / σ² a split must exceed. A split adds four parameters (a new leg) and its
// place is searched, so the threshold sits well above χ²(4)'s 99.9% point (18.5); the default was
// set on the presets' held-course windows at σ = 1° (spec 036 research R2).
export const MULTI = { tau: 40, bufferRows: 12, minSliceRows: 24, stepRows: 3, maxDepth: 5, refine: 8, refinePasses: 3 };

export async function multiSlicing(s, P = MULTI, cancelled = () => false) {
  const sigma = Math.max(s.sigma, MIN_SIGMA);
  const half = Math.floor(P.bufferRows / 2);
  const out = [];
  let fits = 0;
  const breathe = () => new Promise((r) => setTimeout(r, 0));
  // the best single split of segment [a, b]: its cost drop / σ² and row
  async function bestSplit(a, b) {
    if (b - a + 1 < 2 * P.minSliceRows + P.bufferRows) return null;
    const whole = fitCv(s, rowsOf(a, b));
    fits++;
    if (!whole.theta) return null;
    // a coarse pass warm-started from the whole fit, then the best few candidates refitted from
    // gitma's grid start as well (a warm start can sit in the old leg's minimum)
    // left slices forward and right slices backward, each warm-started from its neighbour
    // candidate's fit (a continuation), the first of each from gitma's grid start
    const cs = [];
    for (let c = a + P.minSliceRows + half; c <= b - P.minSliceRows - half; c += P.stepRows) cs.push(c);
    const Lc = new Array(cs.length), Rc = new Array(cs.length), Oc = new Array(cs.length);
    let prev = null;
    for (let i = 0; i < cs.length; i++) {
      const f = prev ? best2(fitCvWarm(s, rowsOf(a, cs[i] - half - 1), prev), i % 8 === 0 ? fitCv(s, rowsOf(a, cs[i] - half - 1)) : null) : fitCv(s, rowsOf(a, cs[i] - half - 1));
      Lc[i] = f.cost;
      if (f.theta) prev = f.theta;
      fits++;
      if (fits % 60 === 0) {
        await breathe();
        if (cancelled()) throw new Error("cancelled");
      }
    }
    prev = null;
    for (let i = cs.length - 1; i >= 0; i--) {
      const f = prev ? best2(fitCvWarm(s, rowsOf(cs[i] + half + 1, b), prev), i % 8 === 0 ? fitCv(s, rowsOf(cs[i] + half + 1, b)) : null) : fitCv(s, rowsOf(cs[i] + half + 1, b));
      Rc[i] = f.cost;
      if (f.theta) prev = f.theta;
      fits++;
      if (fits % 60 === 0) {
        await breathe();
        if (cancelled()) throw new Error("cancelled");
      }
    }
    for (let i = 0; i < cs.length; i++) {
      Oc[i] = fitCvWarm(s, rowsOf(a, b, cs[i] - half, cs[i] + half), whole.theta).cost;
      fits++;
    }
    const cands = cs.map((c, i) => ({ c, drop: (Oc[i] - Lc[i] - Rc[i]) / (sigma * sigma) }));
    cands.sort((x, y) => (Number.isFinite(y.drop) ? y.drop : -Infinity) - (Number.isFinite(x.drop) ? x.drop : -Infinity));
    let best = null;
    for (const q of cands.slice(0, P.refine)) {
      const c = q.c;
      const one = fitCv(s, rowsOf(a, b, c - half, c + half), whole.theta);
      const L = fitCv(s, rowsOf(a, c - half - 1), whole.theta);
      const R = fitCv(s, rowsOf(c + half + 1, b), whole.theta);
      fits += 3;
      const drop = (one.cost - L.cost - R.cost) / (sigma * sigma);
      if (Number.isFinite(drop) && (!best || drop > best.drop)) best = { c, drop };
    }
    return best;
  }
  async function split(a, b, depth) {
    if (depth > P.maxDepth) return;
    const best = await bestSplit(a, b);
    if (!best || !(best.drop > P.tau)) return;
    out.push({ lo: best.c - half, hi: best.c + half, stat: best.drop });
    await split(a, best.c - half - 1, depth + 1);
    await split(best.c + half + 1, b, depth + 1);
  }
  await split(0, s.n - 1, 0);
  out.sort((x, y) => x.lo - y.lo);
  // joint refinement (the 2017 note: splits interact): re-place each split on the segment between
  // its neighbours with them held, and drop it if it no longer clears tau; repeat until stable
  for (let pass = 0; pass < P.refinePasses; pass++) {
    let changed = false;
    for (let i = 0; i < out.length; i++) {
      const a = i === 0 ? 0 : out[i - 1].hi + 1;
      const b = i === out.length - 1 ? s.n - 1 : out[i + 1].lo - 1;
      const r = await bestSplit(a, b);
      if (!r || !(r.drop > P.tau)) {
        out.splice(i, 1);
        i--;
        changed = true;
        continue;
      }
      if (r.c - half !== out[i].lo) changed = true;
      out[i] = { lo: r.c - half, hi: r.c + half, stat: r.drop };
    }
    if (!changed) break;
  }
  return { spans: out, fits };
}

// ---------- joined legs: the arctan law with ownship subtracted, legs joined at knots ----------
// Position is continuous; at knot j (time tj) the velocity changes by d_j. Parameters
// (x0, y0, vx, vy, d1x, d1y, …) at the window's times. The knots are instants: a turn of a
// minute or two is short against the legs.
function knotCost(s, th, knots) {
  let c = 0;
  for (let i = 0; i < s.n; i++) {
    if (s.valid[i] !== 1) continue;
    const t = s.t[i];
    let x = th[0] + th[2] * t - s.ox[i], y = th[1] + th[3] * t - s.oy[i];
    for (let j = 0; j < knots.length; j++) {
      const h = t - knots[j];
      if (h > 0) {
        x += th[4 + 2 * j] * h;
        y += th[5 + 2 * j] * h;
      }
    }
    const r = angleDiff(s.z[i], Math.atan2(x, y));
    c += r * r;
  }
  return c;
}

function solveN(A, g) {
  const m = g.length;
  const M = A.map((row, i) => [...row, g[i]]);
  for (let k = 0; k < m; k++) {
    let p = k;
    for (let i = k + 1; i < m; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
    if (!(Math.abs(M[p][k]) > 1e-300)) return null;
    [M[k], M[p]] = [M[p], M[k]];
    for (let i = k + 1; i < m; i++) {
      const f = M[i][k] / M[k][k];
      if (f !== 0) for (let j = k; j <= m; j++) M[i][j] -= f * M[k][j];
    }
  }
  const x = new Array(m).fill(0);
  for (let i = m - 1; i >= 0; i--) {
    let v = M[i][m];
    for (let j = i + 1; j < m; j++) v -= M[i][j] * x[j];
    x[i] = v / M[i][i];
  }
  return x.every(Number.isFinite) ? x : null;
}

// Levenberg–Marquardt with Jacobi scaling; returns {theta, cost}
export function fitKnots(s, knots, start, maxIt = 40) {
  const m = 4 + 2 * knots.length;
  let th = Array.from(start);
  while (th.length < m) th.push(0);
  let cost = knotCost(s, th, knots);
  let lam = 1e-3;
  for (let it = 0; it < maxIt; it++) {
    const A = Array.from({ length: m }, () => new Array(m).fill(0));
    const g = new Array(m).fill(0);
    const row = new Array(m);
    for (let i = 0; i < s.n; i++) {
      if (s.valid[i] !== 1) continue;
      const t = s.t[i];
      let x = th[0] + th[2] * t - s.ox[i], y = th[1] + th[3] * t - s.oy[i];
      const hs = knots.map((k) => Math.max(t - k, 0));
      for (let j = 0; j < knots.length; j++) {
        x += th[4 + 2 * j] * hs[j];
        y += th[5 + 2 * j] * hs[j];
      }
      const r2 = x * x + y * y;
      if (!(r2 > 0)) continue;
      const res = angleDiff(s.z[i], Math.atan2(x, y));
      const gx = y / r2, gy = -x / r2;
      row[0] = gx; row[1] = gy; row[2] = gx * t; row[3] = gy * t;
      for (let j = 0; j < knots.length; j++) {
        row[4 + 2 * j] = gx * hs[j];
        row[5 + 2 * j] = gy * hs[j];
      }
      for (let p = 0; p < m; p++) {
        if (row[p] === 0) continue;
        g[p] += row[p] * res;
        for (let q = p; q < m; q++) A[p][q] += row[p] * row[q];
      }
    }
    for (let p = 0; p < m; p++) for (let q = 0; q < p; q++) A[p][q] = A[q][p];
    let accepted = false;
    while (lam < 1e12) {
      const D = A.map((r, p) => r.map((v, q) => (p === q ? v * (1 + lam) + 1e-300 : v)));
      const step = solveN(D, g);
      if (step) {
        const nt = th.map((v, p) => v + step[p]);
        const nc = knotCost(s, nt, knots);
        if (nc < cost) {
          const done = cost - nc < 1e-10 * Math.max(cost, 1e-30);
          th = nt;
          cost = nc;
          lam = Math.max(lam / 10, 1e-12);
          accepted = true;
          if (done) return { theta: th, cost };
          break;
        }
      }
      lam *= 10;
    }
    if (!accepted) break;
  }
  return { theta: th, cost };
}

// tau: the cost drop / σ² a new knot must bring (two parameters, its time searched over the
// window: well above χ²(2)'s 99.9% point, 13.8); set on the presets' held-course windows at
// σ = 1° and 2° (spec 036 research R2).
export const JOINED = { tau: 25, minLegRows: 24, stepRows: 3, maxKnots: 4, passes: 3 };

export async function joinedSlicing(s, P = JOINED, cancelled = () => false) {
  const sigma = Math.max(s.sigma, MIN_SIGMA);
  const s2 = sigma * sigma;
  const breathe = () => new Promise((r) => setTimeout(r, 0));
  let fits = 0;
  const [found, g] = gridStart(s, s.n);
  if (!found) return { spans: [], fits };
  const base = levenbergMarquardt(s, g, s.n);
  let model = { knots: [], theta: Array.from(base.theta), cost: base.cost };
  const allowed = (r, knotRows) => r >= P.minLegRows && r <= s.n - 1 - P.minLegRows && knotRows.every((k) => Math.abs(k - r) >= P.minLegRows);
  // the best knot to add to `m` (others held in place, all parameters refitted)
  async function bestAdd(m, knotRows) {
    let best = null;
    for (let r = 0; r < s.n; r += P.stepRows) {
      if (!allowed(r, knotRows)) continue;
      const order = [...knotRows, r].sort((a, b) => a - b);
      const at = order.indexOf(r);
      const start = m.theta.slice(0, 4);
      for (let j = 0, q = 0; j < order.length; j++) {
        if (j === at) start.push(0, 0);
        else {
          start.push(m.theta[4 + 2 * q], m.theta[5 + 2 * q]);
          q++;
        }
      }
      const f = fitKnots(s, order.map((k) => s.t[k]), start, 25);
      fits++;
      const drop = (m.cost - f.cost) / s2;
      if (Number.isFinite(drop) && (!best || drop > best.drop)) best = { r, drop, fit: f, order };
      if (fits % 20 === 0) {
        await breathe();
        if (cancelled()) throw new Error("cancelled");
      }
    }
    return best;
  }
  let rows = [];
  // forward: add knots one at a time while each clears tau
  while (rows.length < P.maxKnots) {
    const b = await bestAdd(model, rows);
    if (!b || !(b.drop > P.tau)) break;
    rows = b.order;
    model = { knots: rows, theta: b.fit.theta, cost: b.fit.cost };
  }
  // joint re-placement: take each knot out, put the best one back among the others; drop it if
  // even the best no longer clears tau
  const drops = new Map();
  for (let pass = 0; pass < P.passes && rows.length; pass++) {
    let changed = false;
    for (let i = 0; i < rows.length; i++) {
      const others = rows.filter((_, j) => j !== i);
      const start = model.theta.slice(0, 4);
      for (let j = 0; j < rows.length; j++) if (j !== i) start.push(model.theta[4 + 2 * j], model.theta[5 + 2 * j]);
      const without = fitKnots(s, others.map((k) => s.t[k]), start);
      fits++;
      const m0 = { theta: without.theta, cost: without.cost };
      const b = await bestAdd(m0, others);
      if (!b || !(b.drop > P.tau)) {
        rows = others;
        model = { knots: rows, theta: without.theta, cost: without.cost };
        changed = true;
        i--;
        continue;
      }
      if (b.r !== rows[i]) changed = true;
      rows = b.order;
      model = { knots: rows, theta: b.fit.theta, cost: b.fit.cost };
      drops.set(b.r, b.drop);
      i = rows.indexOf(b.r);
    }
    if (!changed) break;
  }
  // each kept knot's strength: the cost its removal adds (others held, all refitted)
  for (let i = 0; i < rows.length; i++) {
    const start = model.theta.slice(0, 4);
    for (let j = 0; j < rows.length; j++) if (j !== i) start.push(model.theta[4 + 2 * j], model.theta[5 + 2 * j]);
    const without = fitKnots(s, rows.filter((_, j) => j !== i).map((k) => s.t[k]), start);
    fits++;
    drops.set(rows[i], (without.cost - model.cost) / s2);
  }
  const half = 3; // a knot is an instant; shown as a one-minute span centred on it
  return { spans: rows.map((r) => ({ lo: Math.max(0, r - half), hi: Math.min(s.n - 1, r + half), stat: drops.get(r) })), fits, theta: model.theta, knots: rows };
}
