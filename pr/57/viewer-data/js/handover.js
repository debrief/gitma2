// Port of tma2.physics.segmentation.trivial_inputs, tma2.segment.inputs.segmentation_inputs and
// tma2.gate2.inputs (prefix inputs, code channel) (spec 021): the physics layer's inputs for a
// segmentation of the prefix [0, k], and their padding into the exported graphs' feeds.
import { gridStart } from "./lsq.js";
import { STEADY, TRANSITION, UNKNOWN, toCodes } from "./codes.js";

export const MASKED_LOG_WEIGHT = -60.0;
export const ROWS = 720;

export function trivialInputs(s, k) {
  const [found, th0] = gridStart(s, k + 1);
  if (!found) return null;
  const n = s.n;
  return { changepoint: new Float64Array(n), speed_weight: new Float64Array(n), log_weight: new Float64Array(n), theta0: Float64Array.from(th0), speed_skip: null };
}

// transitions: [[a, b], ...] inclusive rows
export function segmentationInputs(s, k, transitions, mode, speedPrior = true, courseOnly = null, openLast = false, openHandover = null) {
  const base = trivialInputs(s, k);
  if (base === null) return null;
  const n = s.n;
  const cp = new Float64Array(n), sw = new Float64Array(n), sk = new Float64Array(n), lw = new Float64Array(n);
  const handover = openHandover || "knot_at_k";
  if (!["knot_at_k", "start_masked", "start_chord"].includes(handover)) throw new Error(`unknown hand-over ${handover}`);
  transitions.forEach(([a, b], i) => {
    if (openLast && i === transitions.length - 1 && b === k && handover !== "knot_at_k") {
      if (0 < a && a <= k) cp[a] = 1.0;
      if (handover === "start_masked") for (let r = a; r <= k; r++) lw[r] = MASKED_LOG_WEIGHT;
      return;
    }
    for (const r of [a, b]) if (0 < r && r <= k) cp[r] = 1.0;
    if (mode === "gap") for (let r = a; r < Math.min(b, k + 1); r++) lw[r] = MASKED_LOG_WEIGHT;
    const co = courseOnly === null ? true : !!courseOnly[i];
    if (speedPrior && co && 0 < a && a <= k && b <= k) {
      sw[b] = 1.0;
      sk[b] = 1.0;
    }
  });
  return { changepoint: cp, speed_weight: sw, log_weight: lw, theta0: base.theta0, speed_skip: sk };
}

// gate2.inputs.prefix_inputs: C's hand-over of its segmentation of [0, k]
export function prefixInputs(s, k, intervals, mode, openHandover) {
  const trs = intervals.filter((iv) => iv.kind === TRANSITION).map((iv) => [iv.start, iv.end]);
  const last = intervals.length ? intervals[intervals.length - 1] : null;
  const openLast = last !== null && last.kind === TRANSITION && !!last.open;
  return segmentationInputs(s, k, trs, mode, true, null, openLast, openHandover);
}

const CODE_VALUE = { [STEADY]: 0.0, [TRANSITION]: 1.0, [UNKNOWN]: 0.5 };
export function codeChannel(intervals, k, n) {
  const out = new Float64Array(n);
  const codes = toCodes(intervals, k + 1);
  for (let r = 0; r <= k; r++) out[r] = CODE_VALUE[codes[r]];
  return out;
}

// One request's feeds for a physics-layer graph (cli.oracle.inputs_for, padded to ROWS).
export function layerFeeds(s, k, inp, code = null) {
  const pad = (a) => {
    const out = new Float64Array(ROWS);
    out.set(a.subarray ? a.subarray(0, Math.min(a.length, ROWS)) : a);
    return out;
  };
  const own = new Float64Array(ROWS * 2);
  for (let r = 0; r < s.n; r++) {
    own[2 * r] = s.ox[r];
    own[2 * r + 1] = s.oy[r];
  }
  const valid = new Float64Array(ROWS);
  for (let r = 0; r < s.n; r++) valid[r] = s.valid[r] ? 1 : 0;
  const f = {
    bearing: { dtype: "float64", shape: [1, ROWS], data: pad(s.z) },
    valid: { dtype: "float64", shape: [1, ROWS], data: valid },
    own: { dtype: "float64", shape: [1, ROWS, 2], data: own },
    t: { dtype: "float64", shape: [1, ROWS], data: pad(s.t) },
    sigma: { dtype: "float64", shape: [1], data: Float64Array.of(s.sigma) },
    k: { dtype: "int64", shape: [1], data: Float64Array.of(k) },
    theta0: { dtype: "float64", shape: [1, 4], data: Float64Array.from(inp.theta0) },
    changepoint: { dtype: "float64", shape: [1, ROWS], data: pad(inp.changepoint) },
    speed_weight: { dtype: "float64", shape: [1, ROWS], data: pad(inp.speed_weight) },
    log_weight: { dtype: "float64", shape: [1, ROWS], data: pad(inp.log_weight) },
    speed_skip: { dtype: "float64", shape: [1, ROWS], data: inp.speed_skip ? pad(inp.speed_skip) : new Float64Array(ROWS) },
  };
  if (code !== null) f.code = { dtype: "float64", shape: [1, ROWS], data: pad(code) };
  return f;
}
