// Slice-key conformance fixture: gitma's own sliceKeys on metadata at and around every band edge
// (P0 panel round 1, statistics finding 6).
// Usage: node scripts/slices_fixture.mjs <gitma checkout> > tests/fixtures/gitma/slices/cases.json
import path from "node:path";
import { pathToFileURL } from "node:url";

const gitma = process.argv[2];
if (!gitma) throw new Error("usage: slices_fixture.mjs <gitma checkout>");
const { sliceKeys } = await import(pathToFileURL(path.join(gitma, "packages/eval/dist/slices.js")).href);
const f32 = Math.fround;
const deg = (d) => (d * Math.PI) / 180;
const near = (x) => [x - 1e-4, x, x + 1e-4, f32(x), x - 0.0005, x + 0.0005];
const metas = [];
const base = { mean_range_m: 7000, parameters: { noise_sigma_rad: deg(1), zig_angle_rad: deg(60), dropout_fraction: 0.02 } };
const push = (over, pover) =>
  metas.push({ ...base, ...over, parameters: { ...base.parameters, ...pover } });
for (const km of [0, 2, 5, 10, 20, 30, 45]) for (const v of near(km)) if (v >= 0) push({ mean_range_m: v * 1000 }, {});
for (const d of [30, 50, 70, 90, 120, 150, 180]) for (const v of near(d)) {
  push({}, { zig_angle_rad: f32(deg(v)) });
  push({}, { zig_angle_rad: -deg(v) });
}
for (const s of [0.5, 1, 1.5, 2, 2.005, 0.995]) push({}, { noise_sigma_rad: f32(deg(s)) });
for (const pct of [0, 5, 10]) for (const v of near(pct)) if (v >= 0) push({}, { dropout_fraction: v / 100 });
for (const d of [30, 60, 90, 120]) for (const v of near(d)) push({}, { target_manoeuvre_angle_rad: f32(-deg(v)) });
const plans = [[], [{ kind: "course" }], [{ kind: "course" }, { kind: "course" }], [{ kind: "speed" }], [{ kind: "course" }, { kind: "speed" }], [{ kind: "course" }, { kind: "course" }, { kind: "course" }]];
for (const pl of plans) push({}, { target_manoeuvres: pl.map((x, i) => ({ ...x, start_time_s: 100 * i, change: 0.5, rate: 0.01 })) });
process.stdout.write(JSON.stringify(metas.map((m) => ({ meta: m, keys: sliceKeys(m) })), null, 0) + "\n");
