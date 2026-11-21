// Spec 035 FR-030..036: the dashboard's numbers. Time-late (owner, 2026-11-21): the error is
// read across the whole window, not at one reference time: each quantity's error against the
// truth at every time the solver answers, summarised by its RMS and its worst value, beside
// the Cramér-Rao bound at the same times (manoeuvre times known) so a lucky or unlucky noise
// draw is visible.
import { stateAt, DEG, KT, NM } from "./track.js";
import { wrapPi, wrap2pi } from "./scenario.js";
import { invSym, scaledCondition, sandwich } from "./linalg.js";

const rms = (a) => (a.length ? Math.sqrt(a.reduce((s, x) => s + x * x, 0) / a.length) : NaN);
const maxAbs = (a) => (a.length ? a.reduce((m, x) => Math.max(m, Math.abs(x)), 0) : NaN);

// Observability thresholds on the bound's relative range sd at the window end (FR-035), at the
// scenario's noise floored at OBS_SIGMA_DEG so that a noise-free run still shows its geometry.
export const OBS_SIGMA_DEG = 0.5;
export const OBS_GREEN = 0.05;
export const OBS_AMBER = 0.25;

// Cramér-Rao bound for the target's track over the window rows, the manoeuvre times known:
// parameters are position and velocity at the window start plus one velocity increment at the
// middle of each target manoeuvre in the window; information from the window's bearings at the
// truth. Returns per-row sds of range (m), bearing (rad), course (rad) and speed (m/s), and the
// condition number of the scaled information.
export function crb(b, rows, knotsAbs, sigma) {
  const t0 = b.t[rows[0]];
  const kt = knotsAbs.map((m) => (m.t0 + m.t1) / 2 - t0);
  const P = 4 + 2 * kt.length;
  const I = Array.from({ length: P }, () => new Float64Array(P));
  const row = new Float64Array(P);
  const w = 1 / (sigma * sigma);
  for (const i of rows) {
    const tau = b.t[i] - t0;
    const dx = b.tx[i] - b.ox[i], dy = b.ty[i] - b.oy[i];
    const r2 = dx * dx + dy * dy;
    const gx = dy / r2, gy = -dx / r2;
    row[0] = gx; row[1] = gy; row[2] = gx * tau; row[3] = gy * tau;
    kt.forEach((tk, j) => {
      const a = Math.max(tau - tk, 0);
      row[4 + 2 * j] = gx * a;
      row[5 + 2 * j] = gy * a;
    });
    for (let p = 0; p < P; p++) for (let q = 0; q < P; q++) I[p][q] += w * row[p] * row[q];
  }
  const cond = scaledCondition(I);
  const C = invSym(I, 1e-13);
  const out = { cond, singular: C === null, range: [], bearing: [], course: [], speed: [] };
  for (const i of rows) {
    if (C === null) {
      for (const k of ["range", "bearing", "course", "speed"]) out[k].push(Infinity);
      continue;
    }
    const tau = b.t[i] - t0;
    const Gp = [new Float64Array(P), new Float64Array(P)], Gv = [new Float64Array(P), new Float64Array(P)];
    Gp[0][0] = 1; Gp[1][1] = 1; Gp[0][2] = tau; Gp[1][3] = tau;
    Gv[0][2] = 1; Gv[1][3] = 1;
    kt.forEach((tk, j) => {
      const a = Math.max(tau - tk, 0);
      Gp[0][4 + 2 * j] = a; Gp[1][5 + 2 * j] = a;
      if (tau >= tk) { Gv[0][4 + 2 * j] = 1; Gv[1][5 + 2 * j] = 1; }
    });
    const Sp = sandwich(Gp, C), Sv = sandwich(Gv, C);
    const dx = b.tx[i] - b.ox[i], dy = b.ty[i] - b.oy[i];
    const r = Math.hypot(dx, dy);
    const u = [dx / r, dy / r], n = [u[1], -u[0]];
    const q = (S, a) => Math.sqrt(Math.max(a[0] * a[0] * S[0][0] + 2 * a[0] * a[1] * S[0][1] + a[1] * a[1] * S[1][1], 0));
    out.range.push(q(Sp, u));
    out.bearing.push(q(Sp, n) / r);
    const sp = Math.hypot(b.tvx[i], b.tvy[i]);
    const h = sp > 0 ? [b.tvx[i] / sp, b.tvy[i] / sp] : [1, 0];
    out.speed.push(q(Sv, h));
    out.course.push(sp > 0 ? q(Sv, [h[1], -h[0]]) / sp : Infinity);
  }
  return out;
}

// Errors of a solution (problem frame) against the truth, at the times it answers.
export function evaluate(sc, b, rows, origin, t0, sol, knotsAbs) {
  const out = { t: [], range: [], rangePct: [], bearing: [], course: [], speed: [], position: [], predicted: [], measured: [], residual: [], ex: [], ey: [] };
  if (!sol || sol.status === "failed" || !sol.t_s) return null;
  const sigma = sc.sigma_deg * DEG;
  for (let k = 0; k < sol.t_s.length; k++) {
    const t = sol.t_s[k] + t0;
    const o = stateAt(b.paths.own, t), q = stateAt(b.paths.tgt, t);
    const ex = sol.x_m[k] + origin[0], ey = sol.y_m[k] + origin[1];
    const rT = Math.hypot(q.x - o.x, q.y - o.y), rE = Math.hypot(ex - o.x, ey - o.y);
    const bT = Math.atan2(q.x - o.x, q.y - o.y), bE = Math.atan2(ex - o.x, ey - o.y);
    const cT = Math.atan2(q.vx, q.vy), cE = Math.atan2(sol.vx_mps[k], sol.vy_mps[k]);
    out.t.push(t);
    out.ex.push(ex);
    out.ey.push(ey);
    out.range.push(rE - rT);
    out.rangePct.push((100 * (rE - rT)) / rT);
    out.bearing.push(wrapPi(bE - bT));
    out.course.push(wrapPi(cE - cT));
    out.speed.push(Math.hypot(sol.vx_mps[k], sol.vy_mps[k]) - Math.hypot(q.vx, q.vy));
    out.position.push(Math.hypot(ex - q.x, ey - q.y));
  }
  // bearing residuals at the solver's times that are bearings of the window
  const byT = new Map(rows.map((i) => [Math.round(b.t[i] * 1000), i]));
  for (let k = 0; k < out.t.length; k++) {
    const i = byT.get(Math.round(out.t[k] * 1000));
    if (i === undefined) continue;
    const pred = wrap2pi(Math.atan2(out.ex[k] - b.ox[i], out.ey[k] - b.oy[i]));
    out.predicted.push([out.t[k], pred]);
    out.residual.push([out.t[k], sigma > 0 ? wrapPi(b.z[i] - pred) / sigma : NaN]);
  }
  const bound = crb(b, rows, knotsAbs, Math.max(sigma, 1e-9));
  const boundAt = (key) => {
    const at = new Map(rows.map((i, k) => [Math.round(b.t[i] * 1000), bound[key][k]]));
    return out.t.map((t) => at.get(Math.round(t * 1000))).filter((x) => x !== undefined);
  };
  const res = out.residual.map((r) => r[1]).filter(Number.isFinite);
  out.summary = {
    range_m: { rms: rms(out.range), max: maxAbs(out.range), crb: rms(boundAt("range")) },
    range_pct: { rms: rms(out.rangePct), max: maxAbs(out.rangePct) },
    bearing_deg: { rms: rms(out.bearing) / DEG, max: maxAbs(out.bearing) / DEG, crb: rms(boundAt("bearing")) / DEG },
    course_deg: { rms: rms(out.course) / DEG, max: maxAbs(out.course) / DEG, crb: rms(boundAt("course")) / DEG },
    speed_kt: { rms: rms(out.speed) / KT, max: maxAbs(out.speed) / KT, crb: rms(boundAt("speed")) / KT },
    position_nm: { rms: rms(out.position) / NM, max: maxAbs(out.position) / NM },
    nrms: res.length ? rms(res) : NaN,
    answered: out.t.length,
  };
  out.bound = bound;
  return out;
}

// FR-035: observability at the window end from the bound (never blocking, decision 8)
export function observability(sc, b, rows, knotsAbs) {
  const sig = Math.max(sc.sigma_deg, OBS_SIGMA_DEG) * DEG;
  const bd = crb(b, rows, knotsAbs, sig);
  const last = rows[rows.length - 1];
  const r = Math.hypot(b.tx[last] - b.ox[last], b.ty[last] - b.oy[last]);
  const rel = bd.singular ? Infinity : bd.range[bd.range.length - 1] / r;
  const level = !(rel < OBS_AMBER) ? "red" : rel < OBS_GREEN ? "green" : "amber";
  return { level, rel, cond: bd.cond, sigma_deg: sig / DEG };
}

// Spec 036: found legs against the truth.
// A true manoeuvre is found when a stated span lies within `tolS` of it (their intervals, each
// widened by tolS, overlap); each stated span matches at most one true manoeuvre, nearest centre
// first. Timing error: centre of the stated span minus centre of the true one.
export function compareLegs(trueSpans, found, tolS = 120) {
  const pairs = [];
  trueSpans.forEach((m, i) => found.forEach((f, j) => {
    if (f.start_s - tolS <= m.end_s && m.start_s - tolS <= f.end_s) {
      pairs.push({ i, j, d: (f.start_s + f.end_s) / 2 - (m.start_s + m.end_s) / 2 });
    }
  }));
  pairs.sort((a, b) => Math.abs(a.d) - Math.abs(b.d));
  const ti = new Set(), fj = new Set(), matched = [];
  for (const q of pairs) {
    if (ti.has(q.i) || fj.has(q.j)) continue;
    ti.add(q.i);
    fj.add(q.j);
    matched.push(q);
  }
  const offs = matched.map((q) => Math.abs(q.d)).sort((a, b) => a - b);
  return {
    truth: trueSpans.length,
    stated: found.length,
    matched: matched.length,
    missed: trueSpans.length - matched.length,
    false_: found.length - matched.length,
    median_offset_s: offs.length ? offs[Math.floor((offs.length - 1) / 2)] : NaN,
    matchedTrue: [...ti],
    matchedFound: [...fj],
  };
}
