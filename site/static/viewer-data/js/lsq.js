// Port of tma2.references.lsq and the per-timestep driver of tma2.references.classical
// (spec 021). Same arithmetic order as the Python (itself a port of gitma's lsq.ts). Arrays
// are plain Float64Array / Uint8Array; a scenario is {t, ox, oy, z, valid, zigIndex, sigma, n}.
export const MAX_ITERATIONS = 50;
export const GRID_EVERY = 6;
const LAMBDA0 = 1e-3;
const LAMBDA_MAX = 1e12;
const GRID_SPEEDS = [2.0, 5.0, 9.0];
export const TWO_PI = 2.0 * Math.PI;
const PLAUSIBLE_MAX_SPEED_MPS = 25.0;
const PLAUSIBLE_MAX_RANGE_M = 100000.0;

export const f32 = (x) => Math.fround(x) + 0;

// np.fmod semantics: JS % keeps the dividend's sign, as fmod.
export function wrap2pi(a) {
  const w = a % TWO_PI;
  const r = w < 0 ? w + TWO_PI : w;
  return r >= TWO_PI ? 0.0 : r;
}
export const bearingOf = (dx, dy) => wrap2pi(Math.atan2(dx, dy));
export function f32Angle(a) {
  const v = f32(wrap2pi(a));
  return v >= TWO_PI ? 0.0 : v;
}
export const angleDiff = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));

export function cost(s, th, upto) {
  let c = 0.0;
  const [x0, y0, vx, vy] = th;
  for (let i = 0; i < upto; i++) {
    if (s.valid[i] !== 1) continue;
    const ti = s.t[i];
    const h = bearingOf(x0 + vx * ti - s.ox[i], y0 + vy * ti - s.oy[i]);
    const r = angleDiff(s.z[i], h);
    c += r * r;
  }
  return c;
}

function normalEquations(s, th, upto) {
  const jtj = [new Float64Array(4), new Float64Array(4), new Float64Array(4), new Float64Array(4)];
  const jtr = new Float64Array(4);
  const [x0, y0, vx, vy] = th;
  const g = new Float64Array(4);
  for (let i = 0; i < upto; i++) {
    if (s.valid[i] !== 1) continue;
    const ti = s.t[i];
    const dx = x0 + vx * ti - s.ox[i];
    const dy = y0 + vy * ti - s.oy[i];
    const rho2 = dx * dx + dy * dy;
    g[0] = dy / rho2;
    g[1] = -dx / rho2;
    g[2] = ti * g[0];
    g[3] = ti * g[1];
    const r = angleDiff(s.z[i], bearingOf(dx, dy));
    for (let a = 0; a < 4; a++) {
      const ga = g[a];
      jtr[a] = jtr[a] + ga * r;
      for (let b = 0; b < 4; b++) jtj[a][b] = jtj[a][b] + ga * g[b];
    }
  }
  return [jtj, jtr];
}

function solve4(a, b) {
  const m = a.map((row) => Float64Array.from(row));
  const x = Float64Array.from(b);
  for (let c = 0; c < 4; c++) {
    let p = c;
    for (let r = c + 1; r < 4; r++) if (Math.abs(m[r][c]) > Math.abs(m[p][c])) p = r;
    const pivot = m[p][c];
    if (!Number.isFinite(pivot) || Math.abs(pivot) < 1e-300) return [false, x];
    if (p !== c) {
      for (let k = 0; k < 4; k++) {
        const tmp = m[c][k];
        m[c][k] = m[p][k];
        m[p][k] = tmp;
      }
      const tb = x[c];
      x[c] = x[p];
      x[p] = tb;
    }
    for (let r = c + 1; r < 4; r++) {
      const f = m[r][c] / pivot;
      for (let k = c; k < 4; k++) m[r][k] = m[r][k] - f * m[c][k];
      x[r] = x[r] - f * x[c];
    }
  }
  for (let r = 3; r >= 0; r--) {
    let s = x[r];
    for (let k = r + 1; k < 4; k++) s -= m[r][k] * x[k];
    x[r] = s / m[r][r];
  }
  for (let k = 0; k < 4; k++) if (!Number.isFinite(x[k])) return [false, x];
  return [true, x];
}

export function levenbergMarquardt(s, start, upto, maxIterations = MAX_ITERATIONS) {
  let th = Float64Array.from(start);
  let c = cost(s, th, upto);
  let lam = LAMBDA0;
  for (let it = 1; it <= maxIterations; it++) {
    const [jtj, jtr] = normalEquations(s, th, upto);
    let accepted = false;
    while (lam <= LAMBDA_MAX) {
      const damped = jtj.map((row) => Float64Array.from(row));
      for (let k = 0; k < 4; k++) damped[k][k] = jtj[k][k] * (1.0 + lam);
      const [ok, step] = solve4(damped, jtr);
      if (ok) {
        const nxt = new Float64Array(4);
        for (let k = 0; k < 4; k++) nxt[k] = th[k] + step[k];
        const cn = cost(s, nxt, upto);
        if (cn <= c) {
          const done = c - cn <= 1e-12 * c || cn < 1e-24;
          th = nxt;
          c = cn;
          lam = Math.max(lam / 10.0, 1e-12);
          accepted = true;
          if (done) return { theta: th, converged: true, iterations: it, cost: c };
          break;
        }
      }
      lam *= 10.0;
    }
    if (!accepted) return { theta: th, converged: true, iterations: it, cost: c };
  }
  return { theta: th, converged: false, iterations: maxIterations, cost: c };
}

function firstValid(valid, upto) {
  for (let i = 0; i < upto; i++) if (valid[i] === 1) return i;
  return -1;
}

export function gridStart(s, upto) {
  let best = new Float64Array(4);
  const i0 = firstValid(s.valid, upto);
  if (i0 < 0) return [false, best];
  const t0 = s.t[i0];
  const b0 = s.z[i0];
  let bestCost = Infinity;
  const th = new Float64Array(4);
  let found = false;
  for (let ri = 0; ri < 12; ri++) {
    const r = 1000.0 * Math.pow(40.0, ri / 11.0);
    const px = s.ox[i0] + r * Math.sin(b0);
    const py = s.oy[i0] + r * Math.cos(b0);
    for (let ci = 0; ci < 8; ci++) {
      const course = (ci * TWO_PI) / 8.0;
      for (let si = 0; si < 3; si++) {
        const speed = GRID_SPEEDS[si];
        const vx = speed * Math.sin(course);
        const vy = speed * Math.cos(course);
        th[0] = px - vx * t0;
        th[1] = py - vy * t0;
        th[2] = vx;
        th[3] = vy;
        const c = cost(s, th, upto);
        if (c < bestCost) {
          bestCost = c;
          best = Float64Array.from(th);
          found = true;
        }
      }
    }
  }
  return [found, best];
}

export function solveBatch(s, upto, maxIterations = MAX_ITERATIONS) {
  const [found, start] = gridStart(s, upto);
  if (!found) return null;
  return levenbergMarquardt(s, start, upto, maxIterations);
}

function plausible(s, sol, i) {
  const [x0, y0, vx, vy] = sol.theta;
  const t = s.t[i];
  const rng = Math.hypot(x0 + vx * t - s.ox[i], y0 + vy * t - s.oy[i]);
  return Math.hypot(vx, vy) <= PLAUSIBLE_MAX_SPEED_MPS && rng <= PLAUSIBLE_MAX_RANGE_M;
}

function better(s, a, b, i) {
  const pa = plausible(s, a, i), pb = plausible(s, b, i);
  if (pa !== pb) return pa;
  return a.cost < b.cost;
}

function rowAt(s, sol, i) {
  const [x0, y0, vx, vy] = sol.theta;
  const t = s.t[i];
  const x = x0 + vx * t;
  const y = y0 + vy * t;
  return {
    timestamp_s: f32(t),
    range_m: f32(Math.hypot(x - s.ox[i], y - s.oy[i])),
    course_rad: f32Angle(bearingOf(vx, vy)),
    speed_mps: f32(Math.hypot(vx, vy)),
    x_m: f32(x),
    y_m: f32(y),
    converged: sol.converged,
  };
}

const emptyRow = (s, i) => ({ timestamp_s: f32(s.t[i]), range_m: 0, course_rad: 0, speed_mps: 0, x_m: 0, y_m: 0, converged: false });

// classical_predict(d, "per_timestep")["rows"]
export function classicalPerTimestep(s, maxIterations = MAX_ITERATIONS, gridEvery = GRID_EVERY) {
  const rows = [];
  const emit = (sol, i) => {
    if (sol === null) {
      rows.push(emptyRow(s, i));
      return;
    }
    const row = rowAt(s, sol, i);
    if (!plausible(s, sol, i)) row.converged = false;
    rows.push(row);
  };
  let prev = null;
  const first = s.zigIndex + 1;
  for (let i = first; i < s.n; i++) {
    const warm = prev === null ? null : levenbergMarquardt(s, prev.theta, i + 1, maxIterations);
    let sol = warm;
    const needGrid =
      warm === null || !warm.converged || !plausible(s, warm, i) || (gridEvery > 0 && (i - first) % gridEvery === 0);
    if (needGrid) {
      const fresh = solveBatch(s, i + 1, maxIterations);
      if (fresh !== null && (sol === null || better(s, fresh, sol, i))) sol = fresh;
    }
    emit(sol, i);
    prev = sol !== null && plausible(s, sol, i) ? sol : null;
  }
  return rows;
}

// eval.errors.plausible_row
export function plausibleRow(r) {
  const v = [r.range_m, r.course_rad, r.speed_mps, r.x_m, r.y_m];
  if (!v.every(Number.isFinite)) return false;
  return r.range_m > 0 && r.range_m <= PLAUSIBLE_MAX_RANGE_M && r.speed_mps <= PLAUSIBLE_MAX_SPEED_MPS;
}

// detect.controls.ls_states: per-row (x, y, vx, vy) and a usable flag
export function lsStates(s, rows) {
  const n = s.n;
  const state = Array.from({ length: n }, () => new Float64Array(4));
  const ok = new Uint8Array(n);
  const dt = n > 1 ? s.t[1] - s.t[0] : 10.0;
  for (const r of rows) {
    const k = Math.floor(r.timestamp_s / dt + 0.5);
    if (!(k >= 0 && k < n) || !plausibleRow(r)) continue;
    const c = r.course_rad, sp = r.speed_mps;
    state[k][0] = r.x_m;
    state[k][1] = r.y_m;
    state[k][2] = sp * Math.sin(c);
    state[k][3] = sp * Math.cos(c);
    ok[k] = 1;
  }
  return { state, ok };
}
