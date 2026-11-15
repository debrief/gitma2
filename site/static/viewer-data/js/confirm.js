// Port of tma2.segment.confirm, tma2.detect.confirm.tau_4dof and tma2.segment.segmenter's
// nominations and intervals_at (spec 021). The layer is a callback: cost(requests) → Promise of
// costs, one per request [k, transitions]; the caller runs the exported physics layer.
import { STEADY, TRANSITION, UNKNOWN, fromCodes, validate } from "./codes.js";

export const OPEN_END = 1 << 30;

export function tau4dof(tau) {
  const p = Math.exp(-tau / 2.0);
  let x = tau + 4.0;
  for (let i = 0; i < 50; i++) {
    const f = Math.exp(-x / 2.0) * (1.0 + x / 2.0) - p;
    const df = (-Math.exp(-x / 2.0) * x) / 4.0;
    x -= f / df;
  }
  return x;
}

export function glrNominations(stat, threshold, p) {
  const out = [];
  const n = stat.length;
  let r = 0;
  while (r < n) {
    if (!(stat[r] > threshold)) {
      r++;
      continue;
    }
    const a0 = r;
    while (r < n && stat[r] > threshold) r++;
    for (let a = a0; a < r; a += p.retest_rows) out.push({ row: a, lo: Math.max(1, a - p.window_rows + 1), hi: a, source: "glr" });
  }
  return out;
}

export function searchNominations(byPrefix, p) {
  const out = [];
  const seen = [];
  const half = Math.floor(p.window_rows / 2);
  for (const [k, trans] of byPrefix) {
    for (const [s, e, isOpen] of trans) {
      if (isOpen || e + p.search_horizon_rows > k) continue;
      if (seen.some((x) => Math.abs(s - x) <= p.candidate_step_rows)) continue;
      seen.push(s);
      out.push({ row: k, lo: Math.max(1, s - half), hi: Math.min(k, s + half), source: "search" });
    }
  }
  return out;
}

// sorted by (row, source, lo), as Python's tuple sort
export function sortNominations(noms) {
  return noms.sort((x, y) => x.row - y.row || (x.source < y.source ? -1 : x.source > y.source ? 1 : 0) || x.lo - y.lo);
}

function inUse(acc, a) {
  const out = [];
  for (const x of acc) {
    if (x.acceptedAt > a) continue;
    const end = x.end !== null && x.closedAt <= a ? x.end : OPEN_END;
    out.push([x.start, end]);
  }
  return out;
}

function free(c, e, acc, gap, lMax) {
  for (const x of acc) {
    const xe = x.end !== null ? x.end : x.start + lMax - 1;
    if (c <= xe + gap && e >= x.start - gap) return false;
  }
  return true;
}

const argmin = (a) => a.reduce((b, v, i) => (v < a[b] ? i : b), 0);
const argmax = (a) => a.reduce((b, v, i) => (v > a[b] ? i : b), 0);

// confirm one scenario of n rows; evidence: Float64Array or null; layer(requests) → costs
export async function confirmOne(n, noms, p, evidence, layer, onDecision = null) {
  const tau = p.tau;
  const tau4 = tau4dof(tau);
  const lengths = [...new Set(p.t_lengths_rows)].sort((a, b) => a - b);
  const lMid = lengths[Math.floor(lengths.length / 2)];
  const lMax = lengths[lengths.length - 1];
  const gap = p.candidate_step_rows;
  const res = { transitions: [], nearMisses: [], solves: 0, decisions: [] };
  const acc = res.transitions;
  const heap = noms.map((x, i) => [x.row, i, x]);
  let seq = noms.length;
  let ce = null;
  if (evidence !== null) {
    ce = new Float64Array(evidence.length + 1);
    for (let i = 0; i < evidence.length; i++) ce[i + 1] = ce[i] + evidence[i];
  }
  const thr = (c, length, a) => {
    const base = c + length - 1 <= a ? tau4 : tau;
    if (ce === null) return base;
    const e = Math.min(c + length - 1, a);
    const shift = 2.0 * (ce[e + 1] - ce[c]);
    return base + Math.max(-tau / 2.0, Math.min(tau / 2.0, shift));
  };
  const costs = async (reqs) => {
    const out = await layer(reqs);
    return out.map((c) => (Number.isFinite(c) ? c : Infinity));
  };
  const polish = async (a, others, c, e, cost) => {
    for (const which of ["start", "end"]) {
      const cands = [];
      for (let dd = -p.polish_rows; dd <= p.polish_rows; dd++) {
        if (dd === 0) continue;
        const [cs, cee] = which === "start" ? [c + dd, e] : [c, e + dd];
        if (cs < 1 || cee > a || !(p.t_min_rows <= cee - cs + 1 && cee - cs + 1 <= lMax)) continue;
        if (!free(cs, cee, acc.filter((x) => x.start !== c), gap, lMax)) continue;
        cands.push([cs, cee]);
      }
      if (!cands.length) continue;
      const cs = await costs(cands.map((x) => [a, [...others, x]]));
      res.solves += cands.length;
      const j = argmin(cs);
      if (cs[j] < cost) {
        [c, e] = cands[j];
        cost = cs[j];
      }
    }
    return [c, e, cost];
  };
  const pop = () => {
    let b = 0;
    for (let i = 1; i < heap.length; i++) if (heap[i][0] < heap[b][0] || (heap[i][0] === heap[b][0] && heap[i][1] < heap[b][1])) b = i;
    return heap.splice(b, 1)[0];
  };
  while (heap.length) {
    const [a, , nom] = pop();
    if (a >= n) continue;
    if (nom.source === "close") {
      const x = acc.find((t) => t.start === nom.lo && t.end === null);
      const others = inUse(acc, a).filter((t) => t[0] !== x.start);
      const restAcc = acc.filter((t) => t !== x);
      let lens = lengths.filter((ln) => x.start + ln - 1 <= a && free(x.start, x.start + ln - 1, restAcc, gap, lMax));
      if (!lens.length) lens = [lengths[0]];
      const cs = await costs(lens.map((ln) => [a, [...others, [x.start, x.start + ln - 1]]]));
      res.solves += lens.length;
      const j = argmin(cs);
      const [c, e] = await polish(a, others, x.start, x.start + lens[j] - 1, cs[j]);
      x.start = c;
      x.end = e;
      x.closedAt = a;
      continue;
    }
    const cur = inUse(acc, a);
    const starts = [];
    for (let c = nom.lo; c <= nom.hi; c += gap) if (c >= 1 && free(c, c + lMid - 1, acc, gap, lMax)) starts.push(c);
    if (!starts.length) continue;
    const cs = await costs([[a, cur], ...starts.map((c) => [a, [...cur, [c, c + lMid - 1]]])]);
    res.solves += 1 + starts.length;
    const base = cs[0];
    const sc = starts.map((c, q) => base - cs[1 + q] - thr(c, lMid, a));
    const q = argmax(sc);
    const c = starts[q];
    const rest = lengths.filter((ln) => ln !== lMid && free(c, c + ln - 1, acc, gap, lMax));
    let bestLen = lMid, bestScore = sc[q], bestCost = cs[1 + q];
    if (rest.length) {
      const cs2 = await costs(rest.map((ln) => [a, [...cur, [c, c + ln - 1]]]));
      res.solves += rest.length;
      rest.forEach((ln, i) => {
        const s = base - cs2[i] - thr(c, ln, a);
        if (s > bestScore) {
          bestLen = ln;
          bestScore = s;
          bestCost = cs2[i];
        }
      });
    }
    let e = c + bestLen - 1;
    const dec = { row: a, start: c, length: bestLen, source: nom.source, drop: base - bestCost, threshold: e <= a ? tau4 : tau, accepted: bestScore > 0.0, score: bestScore };
    res.decisions.push(dec);
    if (onDecision) onDecision(dec);
    if (bestScore <= 0.0) {
      if (bestScore > -p.margin) res.nearMisses.push({ start: c, end: Math.min(e, a), row: a, score: bestScore });
      continue;
    }
    if (e <= a) {
      let cc;
      [cc, e, bestCost] = await polish(a, cur, c, e, bestCost);
      acc.push({ start: cc, end: e, acceptedAt: a, closedAt: a, drop: base - bestCost, score: bestScore, source: nom.source, acceptedStart: cc });
    } else {
      acc.push({ start: c, end: null, acceptedAt: a, closedAt: a, drop: base - bestCost, score: bestScore, source: nom.source, acceptedStart: c });
      seq += 1;
      heap.push([c + lMax - 1, seq, { row: c + lMax - 1, lo: c, hi: c, source: "close" }]);
    }
  }
  return res;
}

function startAt(x, k) {
  const closed = x.end !== null && x.closedAt <= k;
  return closed || x.acceptedStart === null ? x.start : x.acceptedStart;
}

export function intervalsAt(conf, k, p) {
  const codes = new Int8Array(k + 1).fill(STEADY);
  let openAtK = false;
  for (const x of conf.transitions) {
    if (x.acceptedAt > k) continue;
    const closed = x.end !== null && x.closedAt <= k;
    const e = closed ? Math.min(x.end, k) : k;
    if (!closed) openAtK = true;
    const v = x.score >= p.margin ? TRANSITION : UNKNOWN;
    for (let r = startAt(x, k); r <= e; r++) codes[r] = v;
  }
  for (const nm of conf.nearMisses) {
    if (nm.row <= k) for (let r = nm.start; r <= Math.min(nm.end, k); r++) if (codes[r] === STEADY) codes[r] = UNKNOWN;
  }
  for (const iv of fromCodes(codes)) {
    const shortT = iv.kind === TRANSITION && iv.end - iv.start + 1 < p.t_min_rows;
    if (shortT && !(openAtK && iv.end === k)) for (let r = iv.start; r <= iv.end; r++) codes[r] = UNKNOWN;
  }
  for (const iv of fromCodes(codes)) {
    if (iv.kind === STEADY && iv.end - iv.start + 1 < p.l_min_rows) for (let r = iv.start; r <= iv.end; r++) codes[r] = UNKNOWN;
  }
  const ivs = fromCodes(codes);
  if (openAtK && ivs[ivs.length - 1].kind === TRANSITION) ivs[ivs.length - 1].open = true;
  validate(ivs, k, p.l_min_rows, p.t_min_rows);
  return ivs;
}
