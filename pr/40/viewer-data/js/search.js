// Port of tma2.segment.search (spec 021): the cost table of constant-velocity legs on a grid,
// the dynamic programme over legs and transitions, and search_by_prefix.
import { levenbergMarquardt, gridStart } from "./lsq.js";

const RESTART = 4, MAX_ITER = 20, JUMP_PER_ROW = 9.0, JUMP_BASE = 30.0, MIN_VALID = 6;
export const TRANS_COST = 1.0;
export const MIN_SIGMA_RAD = 0.0001;

function lm(seg, start, m) {
  const r = levenbergMarquardt(seg, start, m, MAX_ITER);
  return [r.theta, r.cost];
}

function slice(s, a, b, tb) {
  const m = b - a + 1;
  const tt = new Float64Array(m);
  for (let r = 0; r < m; r++) tt[r] = s.t[a + r] - tb;
  return { t: tt, ox: s.ox.subarray(a, b + 1), oy: s.oy.subarray(a, b + 1), z: s.z.subarray(a, b + 1), valid: s.valid.subarray(a, b + 1) };
}

// cost[i][j] (Float64Array rows), inf where absent
export function segmentCosts(s, sigma, grid, lMin) {
  const g = grid.length;
  const cost = Array.from({ length: g }, () => new Float64Array(g).fill(Infinity));
  const theta = Array.from({ length: g }, () => new Array(g).fill(null));
  const s2 = sigma * sigma;
  for (let i = 0; i < g; i++) {
    const a = grid[i];
    let have = false;
    let prev = new Float64Array(4);
    let tprev = 0.0, cprev = 0.0, nvprev = 0, steps = 0;
    for (let j = i + 1; j < g; j++) {
      const b = grid[j];
      if (b - a + 1 < lMin) continue;
      const m = b - a + 1;
      let nv = 0;
      for (let r = a; r <= b; r++) nv += s.valid[r];
      if (nv < MIN_VALID) continue;
      const seg = slice(s, a, b, s.t[b]);
      let th = null;
      let c = Infinity;
      if (have) {
        const st = Float64Array.from(prev);
        st[0] += prev[2] * (s.t[b] - tprev);
        st[1] += prev[3] * (s.t[b] - tprev);
        [th, c] = lm(seg, st, m);
      }
      const jump = have && c > cprev + s2 * (JUMP_PER_ROW * (nv - nvprev) + JUMP_BASE);
      if (!have || steps % RESTART === 0 || jump || !Number.isFinite(c)) {
        const [found, st] = gridStart(seg, m);
        if (found) {
          const [th2, c2] = lm(seg, st, m);
          if (c2 < c) {
            th = th2;
            c = c2;
          }
        }
      }
      steps += 1;
      if (Number.isFinite(c)) {
        cost[i][j] = c / s2;
        theta[i][j] = th;
        prev = th;
        tprev = s.t[b];
        cprev = c;
        nvprev = nv;
        have = true;
      }
    }
    for (let j = g - 1; j > i + 1; j--) {
      if (!(Number.isFinite(cost[i][j]) && Number.isFinite(cost[i][j - 1]))) continue;
      if (cost[i][j - 1] <= cost[i][j]) continue;
      const b = grid[j - 1];
      const m = b - a + 1;
      const seg = slice(s, a, b, s.t[b]);
      const st = Float64Array.from(theta[i][j]);
      st[0] -= st[2] * (s.t[grid[j]] - s.t[b]);
      st[1] -= st[3] * (s.t[grid[j]] - s.t[b]);
      const [th, c] = lm(seg, st, m);
      if (Number.isFinite(c) && c / s2 < cost[i][j - 1]) {
        cost[i][j - 1] = c / s2;
        theta[i][j - 1] = th;
      }
    }
  }
  return cost;
}

export function search(cost, grid, valid, evidence, penalty, tMin, tMax, transCost) {
  const g = grid.length;
  const last = grid[g - 1];
  const f = new Float64Array(g).fill(Infinity);
  const backI = new Int32Array(g).fill(-1), backP = new Int32Array(g).fill(-1);
  const cv = new Float64Array(last + 2), ce = new Float64Array(last + 2);
  for (let r = 0; r <= last; r++) {
    cv[r + 1] = cv[r] + valid[r];
    ce[r + 1] = ce[r] + evidence[r];
  }
  for (let j = 1; j < g; j++) {
    if (Number.isFinite(cost[0][j])) {
      const v0 = cost[0][j] - 2.0 * (ce[grid[j] + 1] - ce[0]);
      if (v0 < f[j]) {
        f[j] = v0;
        backI[j] = 0;
        backP[j] = -1;
      }
    }
    for (let i = 1; i < j; i++) {
      if (!Number.isFinite(cost[i][j])) continue;
      const leg = cost[i][j] - 2.0 * (ce[grid[j] + 1] - ce[grid[i]]);
      for (let p = 0; p < i; p++) {
        const gap = grid[i] - grid[p] - 1;
        if (gap < tMin) break;
        if (gap > tMax || !Number.isFinite(f[p])) continue;
        const nt = cv[grid[i]] - cv[grid[p] + 1];
        const et = ce[grid[i]] - ce[grid[p] + 1];
        const v = f[p] + transCost * nt + 2.0 * et + leg + penalty;
        if (v < f[j]) {
          f[j] = v;
          backI[j] = i;
          backP[j] = p;
        }
      }
    }
  }
  let best = f[g - 1];
  let endP = -1;
  for (let p = 0; p < g - 1; p++) {
    const gap = last - grid[p];
    if (gap < tMin || gap > tMax || !Number.isFinite(f[p])) continue;
    const nt = cv[last + 1] - cv[grid[p] + 1];
    const et = ce[last + 1] - ce[grid[p] + 1];
    const v = f[p] + transCost * nt + 2.0 * et + penalty;
    if (v < best) {
      best = v;
      endP = p;
    }
  }
  const out = [];
  let j = endP >= 0 ? endP : g - 1;
  while (j >= 0 && backI[j] >= 0) {
    out.push(grid[j]);
    out.push(grid[backI[j]]);
    j = backP[j];
  }
  const res = out.reverse();
  if (endP >= 0) res.push(grid[endP] + 1);
  return [best, res];
}

export function anchoredGrid(kMax, anchor, step) {
  const first = anchor % step;
  const rows = [];
  for (let r = first; r <= kMax; r += step) rows.push(r);
  if (!rows.length || rows[0] !== 0) rows.unshift(0);
  return rows;
}

export function legsAndTransitions(seg, k) {
  const legs = [];
  for (let q = 0; q + 1 < seg.length; q += 2) legs.push([seg[q], seg[q + 1]]);
  const trans = [];
  for (let q = 0; q + 1 < legs.length; q++) trans.push([legs[q][1] + 1, legs[q + 1][0] - 1, false]);
  if (seg.length % 2 === 1) trans.push([seg[seg.length - 1], k, true]);
  return [legs, trans];
}

export function costTable(s, grid, lMin) {
  return segmentCosts(s, Math.max(s.sigma, MIN_SIGMA_RAD), grid, lMin);
}

// segmenter.search_by_prefix: the search's transitions on every search_every_rows prefix
export function searchByPrefix(s, anchor, p, evidence = null, kMax = null, table = null) {
  kMax = kMax === null ? s.n - 1 : kMax;
  const grid = anchoredGrid(kMax, anchor, p.search_step_rows);
  const cost = table === null ? costTable(s, grid, p.l_min_rows) : table;
  const onGrid = new Set(grid);
  const tMax = Math.max(...p.t_lengths_rows);
  const first = anchor % p.search_every_rows;
  const ev = evidence === null ? new Float64Array(s.n) : evidence;
  const out = [];
  for (let k = first; k <= kMax; k += p.search_every_rows) {
    if (k < 2 * p.l_min_rows + p.t_min_rows || !onGrid.has(k)) continue;
    // prefix_grid: grid points ≤ k; the table's leading block
    const pg = grid.filter((x) => x <= k);
    const [, seg] = search(cost, pg, s.valid, ev, p.search_penalty, p.t_min_rows, tMax, TRANS_COST);
    const [, trans] = legsAndTransitions(seg, k);
    out.push([k, trans]);
  }
  return { grid, cost, byPrefix: out };
}
