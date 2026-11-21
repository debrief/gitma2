// Spec 035: the demonstrator's solver problems for the golden least-squares vectors. Every
// preset at sigma 1 and 0, the target-turn preset narrowed to its first leg, written as JSON
// for demo_golden.py (Python's tma2.references.lsq.solve_batch on the same arrays).
//   node demo_problems.mjs > demo/problems.json
import { PRESETS } from "../../site/static/demo-data/js/presets.js";
import { bearings, windowRows, problemOf } from "../../site/static/demo-data/js/scenario.js";

export function goldenCases() {
  const out = [];
  for (const p of PRESETS) {
    for (const sigma of [1, 0]) out.push({ id: `${p.id}-s${sigma}`, sc: { ...p.scenario, sigma_deg: sigma } });
  }
  const tt = PRESETS.find((p) => p.id === "target-turn").scenario;
  out.push({ id: "target-turn-first-leg", sc: { ...tt, window: { start_s: 0, end_s: 3500 } } });
  return out.map(({ id, sc }) => {
    const b = bearings(sc);
    const { problem } = problemOf(sc, b, windowRows(sc, b));
    return { id, t: problem.t_s, ox: problem.own_x_m, oy: problem.own_y_m, z: problem.bearing_rad, sigma: problem.sigma_rad };
  });
}

if (import.meta.url === `file://${process.argv[1]}`) process.stdout.write(JSON.stringify({ cases: goldenCases() }) + "\n");
