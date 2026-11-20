// Port of tma2.segment's codes and intervals, and NumPy helpers whose summation order matters
// (spec 021). An interval is {kind, start, end, open}.
export const STEADY = 0, TRANSITION = 1, UNKNOWN = 2;

export function toCodes(intervals, n) {
  const out = new Int8Array(n).fill(UNKNOWN);
  for (const iv of intervals) for (let r = iv.start; r <= Math.min(iv.end, n - 1); r++) out[r] = iv.kind;
  return out;
}

export function fromCodes(codes) {
  const out = [];
  const n = codes.length;
  let s = 0;
  for (let r = 1; r <= n; r++) {
    if (r === n || codes[r] !== codes[s]) {
      out.push({ kind: codes[s], start: s, end: r - 1, open: false });
      s = r;
    }
  }
  return out;
}

export function validate(ivs, k, lMin, tMin) {
  if (!ivs.length) throw new Error("no intervals");
  let nxt = 0;
  ivs.forEach((iv, i) => {
    if (iv.start !== nxt) throw new Error(`interval ${i} starts at ${iv.start}, expected ${nxt}`);
    if (iv.end < iv.start) throw new Error(`interval ${i} ends before it starts`);
    const len = iv.end - iv.start + 1;
    const last = i === ivs.length - 1;
    if (iv.open && (!last || iv.kind !== TRANSITION)) throw new Error(`interval ${i}: only a last transition may be open`);
    if (iv.kind === STEADY && len < lMin) throw new Error(`interval ${i}: steady leg of ${len} rows < L_min`);
    if (iv.kind === TRANSITION && !iv.open && len < tMin) throw new Error(`interval ${i}: transition < T_min`);
    nxt = iv.end + 1;
  });
  if (nxt !== k + 1) throw new Error(`intervals end at row ${nxt - 1}, prefix is [0, ${k}]`);
}

// NumPy's pairwise summation (numpy/core/src/umath/loops_utils.h, PW_BLOCKSIZE 128), so that
// sums and means used in threshold tests round as NumPy's do.
export function pairwiseSum(a, lo = 0, n = a.length - lo) {
  if (n < 8) {
    let res = 0.0;
    for (let i = 0; i < n; i++) res += a[lo + i];
    return res;
  }
  if (n <= 128) {
    const r = new Float64Array(8);
    for (let j = 0; j < 8; j++) r[j] = a[lo + j];
    let i;
    for (i = 8; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j] += a[lo + i + j];
    let res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; i++) res += a[lo + i];
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return pairwiseSum(a, lo, n2) + pairwiseSum(a, lo + n2, n - n2);
}
export const npMean = (a, lo, hi) => pairwiseSum(a, lo, hi - lo) / (hi - lo);

export function cumsum0(a) {
  // np.concatenate([[0.0], np.cumsum(a)])
  const out = new Float64Array(a.length + 1);
  let s = 0.0;
  for (let i = 0; i < a.length; i++) {
    s += a[i];
    out[i + 1] = s;
  }
  return out;
}

// np.unwrap with the default discontinuity π and period 2π
export function unwrap(p) {
  const n = p.length;
  const out = Float64Array.from(p);
  if (n < 2) return out;
  const corr = new Float64Array(n - 1);
  for (let i = 0; i < n - 1; i++) {
    const dd = p[i + 1] - p[i];
    const twoPi = 2 * Math.PI;
    let m = (dd + Math.PI) % twoPi;
    if (m < 0) m += twoPi; // np.mod: the divisor's sign
    let ddmod = m - Math.PI;
    if (ddmod === -Math.PI && dd > 0) ddmod = Math.PI;
    let c = ddmod - dd;
    if (Math.abs(dd) < Math.PI) c = 0;
    corr[i] = c;
  }
  let s = 0.0;
  for (let i = 0; i < n - 1; i++) {
    s += corr[i];
    out[i + 1] = p[i + 1] + s;
  }
  return out;
}

export function argmax(a, lo, hi) {
  let best = lo;
  for (let i = lo + 1; i <= hi; i++) if (a[i] > a[best]) best = i;
  return best;
}

// The same pairwise sum carried out in float32 (NumPy's mean of a float32 array)
export function pairwiseSumF32(a, lo = 0, n = a.length - lo) {
  const f = Math.fround;
  if (n < 8) {
    let res = f(0);
    for (let i = 0; i < n; i++) res = f(res + a[lo + i]);
    return res;
  }
  if (n <= 128) {
    const r = new Float32Array(8);
    for (let j = 0; j < 8; j++) r[j] = a[lo + j];
    let i;
    for (i = 8; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j] = f(r[j] + a[lo + i + j]);
    let res = f(f(f(r[0] + r[1]) + f(r[2] + r[3])) + f(f(r[4] + r[5]) + f(r[6] + r[7])));
    for (; i < n; i++) res = f(res + a[lo + i]);
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return f(pairwiseSumF32(a, lo, n2) + pairwiseSumF32(a, lo + n2, n - n2));
}
export const npMeanF32 = (a, lo, hi) => Math.fround(pairwiseSumF32(a, lo, hi - lo) / (hi - lo));
