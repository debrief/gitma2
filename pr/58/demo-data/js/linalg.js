// Spec 035: small dense linear algebra for the dashboard (information matrices up to about 20
// parameters). Matrices are arrays of Float64Array rows.
export const zeros = (n, m = n) => Array.from({ length: n }, () => new Float64Array(m));

// Inverse of a symmetric positive semi-definite matrix by Jacobi-scaled Gauss-Jordan with
// partial pivoting; null when a scaled pivot falls under `tol` (the information is singular).
export function invSym(A, tol = 1e-12) {
  const n = A.length;
  const d = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    if (!(A[i][i] > 0) || !Number.isFinite(A[i][i])) return null;
    d[i] = 1 / Math.sqrt(A[i][i]);
  }
  const M = zeros(n, 2 * n);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) M[i][j] = A[i][j] * d[i] * d[j];
    M[i][n + i] = 1;
  }
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    if (!(Math.abs(M[p][c]) > tol)) return null;
    [M[c], M[p]] = [M[p], M[c]];
    const piv = M[c][c];
    for (let j = 0; j < 2 * n; j++) M[c][j] /= piv;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const f = M[r][c];
      if (f === 0) continue;
      for (let j = 0; j < 2 * n; j++) M[r][j] -= f * M[c][j];
    }
  }
  const out = zeros(n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) out[i][j] = M[i][n + j] * d[i] * d[j];
  return out;
}

// Eigenvalues of a symmetric matrix (cyclic Jacobi rotations)
export function eigSym(A) {
  const n = A.length;
  const a = A.map((r) => Float64Array.from(r));
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) off += a[i][j] * a[i][j];
    if (off < 1e-30) break;
    for (let p = 0; p < n; p++) {
      for (let q = p + 1; q < n; q++) {
        if (Math.abs(a[p][q]) < 1e-300) continue;
        const th = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1));
        const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) {
          const akp = a[k][p], akq = a[k][q];
          a[k][p] = c * akp - s * akq;
          a[k][q] = s * akp + c * akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = a[p][k], aqk = a[q][k];
          a[p][k] = c * apk - s * aqk;
          a[q][k] = s * apk + c * aqk;
        }
      }
    }
  }
  return Array.from({ length: n }, (_, i) => a[i][i]);
}

// condition number of the Jacobi-scaled matrix (Infinity when singular)
export function scaledCondition(A) {
  const n = A.length;
  const d = A.map((r, i) => (r[i] > 0 ? 1 / Math.sqrt(r[i]) : NaN));
  if (d.some((x) => !Number.isFinite(x))) return Infinity;
  const S = A.map((r, i) => Float64Array.from(r, (v, j) => v * d[i] * d[j]));
  const ev = eigSym(S);
  const mx = Math.max(...ev), mn = Math.min(...ev);
  return mn > mx * 1e-16 ? mx / mn : Infinity;
}

// B = G A Gᵀ for G (k × n) and A (n × n)
export function sandwich(G, A) {
  const k = G.length, n = A.length;
  const GA = zeros(k, n);
  for (let i = 0; i < k; i++) for (let j = 0; j < n; j++) {
    let s = 0;
    for (let l = 0; l < n; l++) s += G[i][l] * A[l][j];
    GA[i][j] = s;
  }
  const out = zeros(k);
  for (let i = 0; i < k; i++) for (let j = 0; j < k; j++) {
    let s = 0;
    for (let l = 0; l < n; l++) s += GA[i][l] * G[j][l];
    out[i][j] = s;
  }
  return out;
}
