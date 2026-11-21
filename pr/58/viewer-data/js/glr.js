// Port of tma2.detect.controls.glr_stat (spec 021): the GLR statistic over a sliding window of
// bearings against each row's least-squares state, for a velocity change at an unknown time.
import { TWO_PI } from "./lsq.js";

const wrap = (x) => x - TWO_PI * Math.floor(x / TWO_PI + 0.5);

// Orthonormal basis of the column space of a (m × c, column arrays): unit columns, modified
// Gram–Schmidt twice, remainders below 1e-6 dropped.
function basis(cols, m) {
  const q = [];
  for (const col of cols) {
    let v = Float64Array.from(col.subarray(0, m));
    let nv = 0;
    for (let i = 0; i < m; i++) nv += v[i] * v[i];
    nv = Math.sqrt(nv);
    if (!(nv > 0)) continue;
    for (let i = 0; i < m; i++) v[i] = v[i] / nv;
    for (let pass = 0; pass < 2; pass++) {
      for (const qi of q) {
        let dot = 0;
        for (let i = 0; i < m; i++) dot += qi[i] * v[i];
        const w = new Float64Array(m);
        for (let i = 0; i < m; i++) w[i] = v[i] - dot * qi[i];
        v = w;
      }
    }
    let nr = 0;
    for (let i = 0; i < m; i++) nr += v[i] * v[i];
    nr = Math.sqrt(nr);
    if (nr > 1e-6) {
      const u = new Float64Array(m);
      for (let i = 0; i < m; i++) u[i] = v[i] / nr;
      q.push(u);
    }
  }
  return q;
}

function projectOut(u, v, m) {
  const out = Float64Array.from(v.subarray(0, m));
  for (const uj of u) {
    let dot = 0;
    for (let i = 0; i < m; i++) dot += uj[i] * v[i];
    for (let i = 0; i < m; i++) out[i] -= dot * uj[i];
  }
  return out;
}

export function glrStat(s, state, ok, window) {
  const n = s.n;
  const out = new Float64Array(n);
  const r = new Float64Array(window), gx = new Float64Array(window), gy = new Float64Array(window), tt = new Float64Array(window);
  const sigma = s.sigma;
  for (let k = 0; k < n; k++) {
    if (!ok[k]) continue;
    const a = Math.max(0, k - window + 1);
    let m = 0;
    for (let i = a; i <= k; i++) {
      if (s.valid[i] === 0) continue;
      const tau = s.t[i] - s.t[k];
      const dx = state[k][0] + state[k][2] * tau - s.ox[i];
      const dy = state[k][1] + state[k][3] * tau - s.oy[i];
      const rho2 = dx * dx + dy * dy;
      if (!(rho2 > 0)) continue;
      r[m] = wrap(s.z[i] - Math.atan2(dx, dy)) / sigma;
      gx[m] = dy / (rho2 * sigma);
      gy[m] = -dx / (rho2 * sigma);
      tt[m] = s.t[i];
      m += 1;
    }
    if (m < 4) continue;
    const cols = [new Float64Array(m), new Float64Array(m), new Float64Array(m), new Float64Array(m)];
    for (let i = 0; i < m; i++) {
      const h = tt[i] - s.t[k];
      cols[0][i] = gx[i];
      cols[1][i] = gy[i];
      cols[2][i] = h * gx[i];
      cols[3][i] = h * gy[i];
    }
    const ub = basis(cols, m);
    const rr = projectOut(ub, r, m);
    let best = 0.0;
    const j0 = new Float64Array(m), j1 = new Float64Array(m);
    for (let c = 0; c < m - 2; c++) {
      const tTau = tt[c];
      for (let i = 0; i < m; i++) {
        let h = tt[i] - tTau;
        h = h > 0 ? h : 0.0;
        j0[i] = h * gx[i];
        j1[i] = h * gy[i];
      }
      const p0 = projectOut(ub, j0, m), p1 = projectOut(ub, j1, m);
      let a11 = 0, a12 = 0, a22 = 0, b1 = 0, b2 = 0;
      for (let i = 0; i < m; i++) {
        a11 += p0[i] * p0[i];
        a12 += p0[i] * p1[i];
        a22 += p1[i] * p1[i];
        b1 += p0[i] * rr[i];
        b2 += p1[i] * rr[i];
      }
      const det = a11 * a22 - a12 * a12;
      if (!(det > 1e-12 * Math.max(a11 * a22, 1e-300))) continue;
      const lam = (a22 * b1 * b1 - 2.0 * a12 * b1 * b2 + a11 * b2 * b2) / det;
      if (lam > best) best = lam;
    }
    out[k] = best;
  }
  return out;
}
