// Spec 035 (owner, 2026-11-21): spec 016's whole-period learned model, time-late. A port of
// its inputs (tma2.regress.period_data.period_features over regress.frame.features) and of its
// own track (tma2.timelate.learned.direct_track, with smoothed_bearing). The model reads
// 5-second bearings, at most 1,440 rows (two hours), folded six rows to a token; per token it
// states ln(range / 10 km) and the target's velocity / 10 m/s in a frame turned so the first
// bearing points north, and the logit that a target manoeuvre is in progress.
export const MAX_ROWS = 1440;
export const PATCH = 6;
export const N_FEATURES = 9;
export const DT = 5.0;
const DEG = Math.PI / 180;
const L_UNIT = 1.0e4, V_UNIT = 10.0, D_UNIT = 100.0, T_UNIT = 7200.0;
const SMOOTH_ROWS = 7;

// [MAX_ROWS * 9] float32 features and the [MAX_ROWS] row mask; every bearing is valid here
export function periodFeatures(t, ox, oy, z, sigma) {
  const n = t.length;
  const f = new Float32Array(MAX_ROWS * N_FEATURES);
  const mask = new Uint8Array(MAX_ROWS);
  const th = z[0];
  const c = Math.cos(th), s = Math.sin(th);
  const lsig = Math.log(Math.max(sigma, 1e-6) / DEG);
  for (let k = 0; k < n; k++) {
    const tk = k * DT; // the model's clock: rows from 0 at its own spacing
    const dx = k ? ox[k] - ox[k - 1] : 0, dy = k ? oy[k] - oy[k - 1] : 0;
    const dt = k ? tk - (k - 1) * DT : 0;
    const b = z[k] - th;
    const o = k * N_FEATURES;
    f[o] = Math.sin(b);
    f[o + 1] = Math.cos(b);
    f[o + 2] = (dx * c - dy * s) / D_UNIT;
    f[o + 3] = (dy * c + dx * s) / D_UNIT;
    f[o + 4] = 1;
    f[o + 5] = lsig;
    f[o + 6] = dt / 10.0;
    f[o + 7] = tk / T_UNIT;
    f[o + 8] = (n * DT) / T_UNIT;
    mask[k] = 1;
  }
  return { f, mask, th };
}

export function tokenRows(n) {
  const last = [];
  for (let s = 0; s < n; s += PATCH) last.push(Math.min(s + PATCH - 1, n - 1));
  return last;
}

// np.unwrap with the default discontinuity π
function unwrap(z) {
  const out = Float64Array.from(z);
  let corr = 0;
  for (let i = 1; i < z.length; i++) {
    const d = z[i] - z[i - 1];
    let m = ((((d + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;
    if (m === -Math.PI && d > 0) m = Math.PI;
    if (Math.abs(d) >= Math.PI) corr += m - d;
    out[i] = z[i] + corr;
  }
  return out;
}

// learned.smoothed_bearing with every bearing valid: unwrap, then a centred running median of
// seven rows with the ends repeated
export function smoothedBearing(z) {
  const u = unwrap(z);
  const h = SMOOTH_ROWS >> 1, n = u.length;
  const out = new Float64Array(n);
  const win = new Float64Array(SMOOTH_ROWS);
  for (let i = 0; i < n; i++) {
    for (let j = -h; j <= h; j++) win[j + h] = u[Math.min(Math.max(i + j, 0), n - 1)];
    out[i] = Float64Array.from(win).sort()[h];
  }
  return out;
}

// np.interp at integer rows k over knots `xs` (ascending) with values `ys`
function interp(n, xs, ys) {
  const out = new Float64Array(n);
  let j = 0;
  for (let k = 0; k < n; k++) {
    if (k <= xs[0]) { out[k] = ys[0]; continue; }
    if (k >= xs[xs.length - 1]) { out[k] = ys[ys.length - 1]; continue; }
    while (xs[j + 1] < k) j++;
    const w = (k - xs[j]) / (xs[j + 1] - xs[j]);
    out[k] = ys[j] + w * (ys[j + 1] - ys[j]);
  }
  return out;
}

// learned.direct_track: the model's own track at every row (x, y, vx, vy), from its per-token
// means ([T][3]); position is the stated range along the smoothed measured bearing
export function directTrack(mean, ox, oy, z, th) {
  const n = z.length;
  const last = tokenRows(n);
  const col = (c) => last.map((_, j) => mean[j][c]);
  const lnR = interp(n, last, col(0)), vxp = interp(n, last, col(1)), vyp = interp(n, last, col(2));
  if (last.length > 1 && last[0] > 0) {
    const slope = (mean[1][0] - mean[0][0]) / (last[1] - last[0]);
    for (let k = 0; k < last[0]; k++) lnR[k] = mean[0][0] + slope * (k - last[0]);
  }
  const c = Math.cos(th), s = Math.sin(th);
  const zs = smoothedBearing(z);
  const out = [];
  for (let k = 0; k < n; k++) {
    const r = L_UNIT * Math.exp(lnR[k]);
    out.push([ox[k] + r * Math.sin(zs[k]), oy[k] + r * Math.cos(zs[k]), V_UNIT * (vxp[k] * c + vyp[k] * s), V_UNIT * (vyp[k] * c - vxp[k] * s)]);
  }
  return out;
}
