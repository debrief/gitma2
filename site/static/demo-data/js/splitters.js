// Spec 036: the demonstrator's leg splitters. A splitter reads the window's bearings and ownship's
// track and states where it thinks the target manoeuvred, as time spans; a TMA solver that accepts
// knots (the ONNX physics layer) then fits constant-velocity legs joined across those spans.
// Each splitter declares a DemoSplitterInfo (schema 0.38.0) and `split(problem, ctx)` →
// {spans: [{start_s, end_s, stat}], rows_dt_s, runtime_ms, message}.
//
// Only the "truth" splitter is shown the problem's true manoeuvre spans; the worker strips them
// for every other splitter.
import { classicalPerTimestep, lsStates } from "../../viewer-data/js/lsq.js";
import { glrStat } from "../../viewer-data/js/glr.js";
import { searchByPrefix } from "../../viewer-data/js/search.js";
import { glrNominations, searchNominations, sortNominations, confirmOne, intervalsAt } from "../../viewer-data/js/confirm.js";
import { segmentationInputs, layerFeeds, ROWS } from "../../viewer-data/js/handover.js";
import { TRANSITION } from "../../viewer-data/js/codes.js";
import { PARAMS as C_PARAMS } from "../../viewer-data/js/pipeline.js";
import { debriefSlicing, multiSlicing, joinedSlicing, DEBRIEF, MULTI, JOINED } from "./arctan.js";
import { SPLITTER_INFO } from "./solver-info.js";

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());
const MIN_SIGMA = 0.1 * (Math.PI / 180);
const breathe = () => new Promise((r) => setTimeout(r, 0));

// The problem's bearings on a grid of about `targetDt` seconds (the splitters' row parameters
// are in rows of 10 s, as C's), at most `maxRows` rows.
export function splitterArrays(p, targetDt = 10, maxRows = ROWS) {
  const n0 = p.t_s.length;
  const dt0 = n0 > 1 ? p.t_s[1] - p.t_s[0] : targetDt;
  let stride = Math.max(1, Math.round(targetDt / dt0));
  stride = Math.max(stride, Math.ceil(n0 / maxRows));
  const idx = [];
  for (let i = 0; i < n0; i += stride) idx.push(i);
  const n = idx.length;
  const s = { n, stride, idx, t: new Float64Array(n), ox: new Float64Array(n), oy: new Float64Array(n), z: new Float64Array(n), valid: new Uint8Array(n).fill(1), course: new Float64Array(n), speed: new Float64Array(n), sigma: Math.max(p.sigma_rad, MIN_SIGMA), zigIndex: 0 };
  idx.forEach((i, k) => {
    s.t[k] = p.t_s[i];
    s.ox[k] = p.own_x_m[i];
    s.oy[k] = p.own_y_m[i];
    s.z[k] = p.bearing_rad[i];
    s.course[k] = p.own_course_rad ? p.own_course_rad[i] : 0;
    s.speed[k] = p.own_speed_mps ? p.own_speed_mps[i] : 0;
  });
  s.dt = n > 1 ? s.t[1] - s.t[0] : targetDt;
  return s;
}

const spansOf = (s, rowSpans) => rowSpans.map((x) => ({ start_s: s.t[Math.max(0, x.lo)], end_s: s.t[Math.min(s.n - 1, x.hi)], stat: x.stat }));
const dtNote = (s) => (Math.abs(s.dt - 10) > 1e-6 ? `bearings every ${s.dt.toFixed(0)} s; its parameters are set in rows of 10 s` : undefined);

// ---------- none: one leg ----------
export const none = {
  info: SPLITTER_INFO.none,
  async split() {
    return { spans: [], runtime_ms: 0 };
  },
};

// ---------- truth: the page tells it the true manoeuvre spans (an oracle) ----------
export const truth = {
  info: SPLITTER_INFO.truth,
  async split(p) {
    return { spans: (p.knots || []).map((m) => ({ start_s: m.start_s, end_s: m.end_s, course: m.course, speed: m.speed })), runtime_ms: 0 };
  },
};

// ---------- arctan slicing, Debrief 2015 ----------
export const arctanDebrief = {
  info: SPLITTER_INFO.arctanDebrief,
  async split(p, ctx = {}) {
    const t0 = now();
    const s = splitterArrays(p);
    const r = await debriefSlicing(s, DEBRIEF, ctx.cancelled || (() => false));
    const notes = [];
    if (!r.legs.some(([a, b]) => b - a + 1 >= DEBRIEF.minLegRows)) notes.push("no steady ownship leg long enough to slice");
    const d = dtNote(s);
    if (d) notes.push(d);
    // spec 036 follow-up: ownship turns as Debrief found them: the gaps between its steady ownship legs
    const own = [];
    for (let i = 0; i + 1 < r.legs.length; i++) own.push({ lo: r.legs[i][1], hi: r.legs[i + 1][0] });
    return { spans: spansOf(s, r.spans), ownship_spans: spansOf(s, own), rows_dt_s: s.dt, fits: r.fits, runtime_ms: now() - t0, message: notes.join("; ") || undefined };
  },
};

// ---------- arctan slicing, multi-leg ----------
export const arctanMulti = {
  info: SPLITTER_INFO.arctanMulti,
  async split(p, ctx = {}) {
    const t0 = now();
    const s = splitterArrays(p);
    const r = await multiSlicing(s, MULTI, ctx.cancelled || (() => false));
    return { spans: spansOf(s, r.spans), rows_dt_s: s.dt, fits: r.fits, runtime_ms: now() - t0, message: dtNote(s) };
  },
};

// ---------- arctan law, joined legs ----------
export const arctanJoined = {
  info: SPLITTER_INFO.arctanJoined,
  async split(p, ctx = {}) {
    const t0 = now();
    const s = splitterArrays(p);
    const r = await joinedSlicing(s, JOINED, ctx.cancelled || (() => false));
    return { spans: spansOf(s, r.spans), rows_dt_s: s.dt, fits: r.fits, runtime_ms: now() - t0, message: dtNote(s) };
  },
};

// ---------- C: spec 005's classical segmenter (spec 021's port), its segmentation at the window's
// last bearing. GLR and search nominate; the physics layer at confirmation's settings confirms
// each nomination on its own prefix. No learned evidence (C, not E).
function stack(per) {
  const feeds = {};
  const B = per.length;
  for (const name of Object.keys(per[0])) {
    const one = per[0][name];
    const size = one.data.length;
    const data = new Float64Array(size * B);
    per.forEach((f, b) => data.set(f[name].data, b * size));
    feeds[name] = { dtype: one.dtype, shape: [B, ...one.shape.slice(1)], data };
  }
  return feeds;
}

export const segmenterC = {
  info: SPLITTER_INFO.c,
  async split(p, ctx) {
    const t0 = now();
    const P = C_PARAMS;
    const s = splitterArrays(p);
    const progress = ctx.progress || (() => {});
    const cancelled = ctx.cancelled || (() => false);
    const check = async () => {
      await breathe();
      if (cancelled()) throw new Error("cancelled");
    };
    if (s.n < 2 * P.l_min_rows + P.t_min_rows) return { spans: [], rows_dt_s: s.dt, runtime_ms: now() - t0, message: "window too short for C (it needs two 5-minute legs and a transition)" };
    progress({ stage: "C: least squares" });
    await check();
    const { state, ok } = lsStates(s, classicalPerTimestep(s));
    progress({ stage: "C: GLR statistic" });
    await check();
    const g = glrStat(s, state, ok, P.glr_window);
    progress({ stage: "C: search" });
    await check();
    const sr = searchByPrefix(s, 0, P);
    const noms = sortNominations([...glrNominations(g, P.glr_threshold, P), ...searchNominations(sr.byPrefix, P)]);
    let decided = 0;
    progress({ stage: "C: confirmation", nominations: noms.length, decided });
    const layer = async (reqs) => {
      await check();
      const per = reqs.map(([k, trs]) => {
        const inp = segmentationInputs(s, k, trs, "chord", false);
        if (inp === null) throw new Error(`no valid bearing on [0, ${k}]`);
        return layerFeeds(s, k, inp);
      });
      const out = await ctx.run("c-layer", stack(per));
      return Array.from(out.cost, Number);
    };
    const conf = await confirmOne(s.n, noms, P, null, layer, () => {
      decided += 1;
      progress({ stage: "C: confirmation", nominations: noms.length, decided });
    });
    const ivs = intervalsAt(conf, s.n - 1, P);
    const rowSpans = ivs.filter((iv) => iv.kind === TRANSITION).map((iv) => ({ lo: iv.start, hi: iv.end, stat: undefined }));
    return { spans: spansOf(s, rowSpans), rows_dt_s: s.dt, nominations: noms.length, runtime_ms: now() - t0, message: dtNote(s) };
  },
};

export const SPLITTERS = [none, truth, arctanDebrief, arctanMulti, arctanJoined, segmenterC];
export const splitterByName = (name) => SPLITTERS.find((x) => x.info.name === name) || none;

export { compareLegs } from "./metrics.js";
