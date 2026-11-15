// Port of tma2.segment.ownship (segmenter O) and segment.evidence's online ownship codes
// (spec 021).
import { STEADY, TRANSITION, UNKNOWN, fromCodes, toCodes, npMean, npMeanF32, cumsum0, unwrap, argmax, pairwiseSum } from "./codes.js";

const KT = 1852.0 / 3600.0;
const WINDOW = 6, NET_FRACTION = 0.9, TRIM_ROWS = 3;
const radians = (d) => (d * Math.PI) / 180;

function ma(x, w) {
  const n = x.length;
  const cs = cumsum0(x);
  const before = new Float64Array(n).fill(NaN), after = new Float64Array(n).fill(NaN);
  for (let r = w - 1; r < n; r++) before[r] = (cs[r + 1] - cs[r + 1 - w]) / w;
  for (let r = 0; r < n - w; r++) after[r] = (cs[r + 1 + w] - cs[r + 1]) / w;
  return [before, after];
}

function runs(mask) {
  const out = [];
  let r = 0;
  const n = mask.length;
  while (r < n) {
    if (mask[r]) {
      const a = r;
      while (r < n && mask[r]) r++;
      out.push([a, r - 1]);
    } else r++;
  }
  return out;
}

export function changes(course, speed, p, window = WINDOW, netFraction = NET_FRACTION) {
  const n = course.length;
  const u = unwrap(course);
  const dC = radians(p.course_change_deg), bandC = radians(p.course_tol_deg);
  const [bc, ac] = ma(u, window);
  const [bs, as] = ma(speed, window);
  const flagC = new Uint8Array(n), flagS = new Uint8Array(n);
  for (let r = 0; r < n; r++) {
    flagC[r] = Math.abs(ac[r] - bc[r]) > dC ? 1 : 0; // NaN compares false, as NumPy
    flagS[r] = Math.abs(as[r] - bs[r]) > p.speed_change_kt * KT ? 1 : 0;
  }
  const rate = new Float64Array(n);
  for (let r = 1; r < n - 1; r++) rate[r] = (u[r + 1] - u[r - 1]) / 2.0;
  const out = [];
  for (const [f0, f1] of runs(flagC)) {
    const diff = new Float64Array(f1 - f0 + 1);
    for (let i = f0; i <= f1; i++) diff[i - f0] = Math.abs(ac[i] - bc[i]);
    const peak = f0 + argmax(diff, 0, diff.length - 1);
    const sgn = ac[peak] - bc[peak] > 0 ? 1.0 : -1.0;
    const loS = Math.max(1, f0 - window), hiS = Math.min(n - 2, f1 + window);
    const rs = new Float64Array(hiS - loS + 1);
    for (let i = loS; i <= hiS; i++) rs[i - loS] = rate[i] * sgn;
    const mid = loS + argmax(rs, 0, rs.length - 1);
    const lo = Math.max(0, f0 - window + 1);
    const mBefore = lo > 0 ? npMean(u, Math.max(0, lo - window), lo) : u[0];
    let a = mid;
    while (a > 0 && rate[a] * sgn > 0 && Math.abs(u[a] - mBefore) > bandC) a--;
    a += a < mid ? 1 : 0;
    const hi = f1 + window;
    const isOpen = hi + window > n;
    const mAfter = !isOpen ? npMean(u, hi, hi + window) : u[n - 1];
    let b = mid;
    while (b < n - 1 && rate[b] * sgn > 0 && Math.abs(u[b] - mAfter) > bandC) b++;
    b -= b > mid ? 1 : 0;
    if (isOpen) b = n - 1;
    const r0 = Math.max(a - 1, 0), r1 = Math.min(b + 1, n - 1);
    const net = u[r1] - u[r0];
    const ad = new Float64Array(r1 - r0);
    for (let i = r0; i < r1; i++) ad[i - r0] = Math.abs(u[i + 1] - u[i]);
    const total = pairwiseSum(ad);
    if (Math.abs(mAfter - mBefore) < dC || (total > 0 && Math.abs(net) < netFraction * total)) continue;
    out.push([a, b, isOpen]);
  }
  for (const [f0, f1] of runs(flagS)) {
    const a = Math.max(0, Math.floor((f0 + f1) / 2) - Math.floor(window / 2));
    const b = Math.min(n - 1, a + window - 1);
    const isOpen = f1 + 2 * window > n;
    out.push([a, isOpen ? n - 1 : b, isOpen]);
  }
  // Python sorts tuples (a, b, open) with False < True
  out.sort((x, y) => x[0] - y[0] || x[1] - y[1] || Number(x[2]) - Number(y[2]));
  const merged = [];
  for (const [a, b, o] of out) {
    if (merged.length && a <= merged[merged.length - 1][1] + 1) {
      const m = merged[merged.length - 1];
      merged[merged.length - 1] = [m[0], Math.max(m[1], b), m[2] || o];
    } else merged.push([a, b, o]);
  }
  return merged;
}

export function segmentOwnship(course, speed, k, p, trimRows = TRIM_ROWS) {
  const c = course.subarray(0, k + 1), s = speed.subarray(0, k + 1);
  const n = k + 1;
  const codes = new Int8Array(n).fill(STEADY);
  let openLast = false;
  for (let [a, b, o] of changes(c, s, p)) {
    const short = p.t_min_rows - (b - a + 1);
    if (short > 0 && !o) {
      a -= Math.floor(short / 2);
      b += short - Math.floor(short / 2);
    }
    a = Math.max(a, 0);
    b = Math.min(b, n - 1);
    for (let r = a; r <= b; r++) codes[r] = TRANSITION;
    openLast = openLast || (o && b === n - 1);
  }
  for (const iv of fromCodes(codes)) {
    if (iv.kind !== STEADY) continue;
    const a = iv.start, b = iv.end;
    if (a > 0 && codes[a - 1] === TRANSITION) for (let r = a; r < Math.min(a + trimRows, b + 1); r++) codes[r] = TRANSITION;
    if (b < n - 1 && codes[b + 1] === TRANSITION) for (let r = Math.max(b - trimRows + 1, a); r <= b; r++) codes[r] = TRANSITION;
  }
  const u = unwrap(c);
  const bandC = radians(p.course_tol_deg), bandS = p.speed_tol_kt * KT;
  for (const iv of fromCodes(codes)) {
    if (iv.kind !== STEADY) continue;
    // speed is the pack's float32 column: NumPy takes its mean and differences in float32
    const mu = npMean(u, iv.start, iv.end + 1), ms = npMeanF32(s, iv.start, iv.end + 1);
    let du = 0, ds = 0;
    for (let r = iv.start; r <= iv.end; r++) {
      du = Math.max(du, Math.abs(u[r] - mu));
      ds = Math.max(ds, Math.abs(Math.fround(s[r] - ms)));
    }
    const bad = iv.end - iv.start + 1 < p.l_min_rows || du > bandC || ds > bandS;
    if (bad) for (let r = iv.start; r <= iv.end; r++) codes[r] = UNKNOWN;
  }
  const ivs = fromCodes(codes);
  if (openLast && ivs[ivs.length - 1].kind === TRANSITION) ivs[ivs.length - 1].open = true;
  return ivs;
}

// segment.evidence.online_ownship_codes: O on each prefix [0, r]; row r's label
export function onlineOwnshipCodes(course, speed, n, p) {
  const out = new Int8Array(n).fill(UNKNOWN);
  for (let r = 0; r < n; r++) out[r] = toCodes(segmentOwnship(course, speed, r, p), r + 1)[r];
  return out;
}
