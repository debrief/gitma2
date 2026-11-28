// Spec 035 FR-041: preset scenarios (generic and unclassified, NFR-5). Distances in NM from an
// arbitrary origin, two-hour engagements, bearings every 5 s at 1 degree.
import { SCHEMA_VERSION, TURN_LOSS_S } from "./scenario.js";
import { LEGACY_SOLVERS } from "./solver-info.js";

const leg = (course_deg, speed_kt, minutes, turn_rate_dps = 1) => ({ course_deg, speed_kt, duration_s: minutes * 60, turn_rate_dps });
const zigzag = () => ({ start_x_nm: 0, start_y_nm: 0, legs: [leg(0, 8, 30), leg(60, 8, 30), leg(330, 8, 30), leg(60, 8, 30)] });
const base = (name, ownship, target, extra = {}) => ({
  schema_version: SCHEMA_VERSION, name, ownship, target,
  sigma_deg: 1, interval_s: 5, turn_loss_s: TURN_LOSS_S, seed: 1, window: { start_s: 0, end_s: 7140 }, solver: "ls-js", show_ellipses: false, ...extra,
});

export const PRESETS = [
  {
    id: "good-geometry",
    title: "Good geometry: ownship zig-zag",
    note: "Ownship turns every 30 minutes; the target holds course. A single-leg fit should be close.",
    scenario: base("Good geometry", zigzag(), { start_x_nm: -1, start_y_nm: 9, legs: [leg(100, 6, 120)] }),
  },
  {
    id: "no-zig",
    title: "No ownship zig (unobservable)",
    note: "Both hold course: the bearings cannot fix range. The indicator goes red; the solution is still shown.",
    scenario: base("No ownship zig", { start_x_nm: 0, start_y_nm: 0, legs: [leg(0, 8, 120)] }, { start_x_nm: -1, start_y_nm: 9, legs: [leg(100, 6, 120)] }),
  },
  {
    id: "target-turn",
    title: "Target turns mid-window",
    note: "The target turns after an hour. A one-leg solver is biased by design; narrow the window to one target leg, or pick the solver told the manoeuvre times.",
    scenario: base("Target turn", zigzag(), { start_x_nm: -1, start_y_nm: 9, legs: [leg(100, 6, 60, 0.5), leg(140, 6, 60)] }),
  },
  {
    id: "two-target-turns",
    golden: false, // not in spec 035's golden problem set (conformance/onnx/demo_problems.mjs)
    title: "Target turns twice between ownship turns",
    note: "Spec 036: the target turns at 45 and 75 minutes, inside ownship's legs. Compare the leg splitters with the physics layer.",
    scenario: base("Two target turns", zigzag(), { start_x_nm: -1, start_y_nm: 9, legs: [leg(100, 6, 45, 0.5), leg(150, 6, 30, 0.5), leg(90, 7, 45)] }, { solver: "layer", splitter: "arctan-joined" }),
  },
  {
    id: "endfire",
    title: "Near-endfire geometry",
    note: "The target is nearly dead ahead and on a similar course: small zigs barely change the bearing rate.",
    scenario: base("Near endfire", { start_x_nm: 0, start_y_nm: 0, legs: [leg(0, 8, 40), leg(6, 8, 40), leg(354, 8, 40)] }, { start_x_nm: 0.4, start_y_nm: 9, legs: [leg(2, 6, 120)] }),
  },
  {
    id: "short-window",
    title: "Short window across a zig",
    note: "Only 15 minutes of bearings around the first ownship turn.",
    scenario: base("Short window across zig", zigzag(), { start_x_nm: -1, start_y_nm: 9, legs: [leg(100, 6, 120)] }, { window: { start_s: 1500, end_s: 2400 } }),
  },
];

export const DEFAULT_SCENARIO = PRESETS[0].scenario;
export const clone = (x) => JSON.parse(JSON.stringify(x));

// Spec 036: spec 035's scenarios name "layer-cv" or "layer-oracle"; today the layer takes its legs
// from a leg splitter. A scenario without a splitter has none (one leg).
export function normaliseScenario(sc) {
  const out = { ...sc };
  if (LEGACY_SOLVERS[out.solver]) {
    const [solver, splitter] = LEGACY_SOLVERS[out.solver];
    out.solver = solver;
    out.splitter = splitter;
  }
  if (!out.splitter) out.splitter = "none";
  // owner, 2026-11-22: bearings are lost in ownship's turns and two minutes after; a scenario
  // saved before then takes the default
  if (out.turn_loss_s === undefined) out.turn_loss_s = TURN_LOSS_S;
  return out;
}
