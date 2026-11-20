// Port of tma2.segment.evidence's features and innovations (spec 021): E-s's ten input
// channels, from bearings, ownship navigation, O's online codes and the per-row least-squares
// innovations.
import { STEADY, TRANSITION, UNKNOWN } from "./codes.js";

export const CHANNELS = 10;

// Python's % on floats takes the divisor's sign
const pmod = (a, m) => {
  const r = a % m;
  return r < 0 ? r + m : r;
};

export function innovations(s, state, ok) {
  const n = s.n;
  const out = new Float64Array(n);
  const sg = Math.max(s.sigma, 1e-4);
  for (let r = 1; r < n; r++) {
    if (!(ok[r - 1] && s.valid[r])) continue;
    const dt = s.t[r] - s.t[r - 1];
    const x = state[r - 1][0] + state[r - 1][2] * dt - s.ox[r];
    const y = state[r - 1][1] + state[r - 1][3] * dt - s.oy[r];
    const res = pmod(s.z[r] - Math.atan2(x, y) + Math.PI, 2 * Math.PI) - Math.PI;
    out[r] = Math.max(-10.0, Math.min(10.0, res / sg));
  }
  return out;
}

// [CHANNELS][n]
export function features(s, ownCodes, innov) {
  const n = s.n;
  const f = Array.from({ length: CHANNELS }, () => new Float64Array(n));
  for (let r = 0; r < n; r++) {
    const v = s.valid[r] ? 1.0 : 0.0;
    f[0][r] = Math.sin(s.z[r]) * v;
    f[1][r] = Math.cos(s.z[r]) * v;
    f[2][r] = v;
    f[3][r] = (s.ox[r] - s.ox[0]) / 1e4;
    f[4][r] = (s.oy[r] - s.oy[0]) / 1e4;
    f[5][r] = (s.t[r] - s.t[0]) / 3600.0;
    f[6][r] = ownCodes[r] === STEADY ? 1 : 0;
    f[7][r] = ownCodes[r] === TRANSITION ? 1 : 0;
    f[8][r] = ownCodes[r] === UNKNOWN ? 1 : 0;
    f[9][r] = innov[r];
  }
  return f;
}
