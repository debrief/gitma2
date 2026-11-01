// Bootstrap conformance fixture: gitma's own bootstrap functions on fixed inputs with ties,
// +Infinity, NaN and shuffled cluster ids (P0 panel, statistics finding 5).
// Usage: node scripts/bootstrap_fixture.mjs <gitma checkout> > tests/fixtures/gitma/bootstrap/cases.json
import path from "node:path";
import { pathToFileURL } from "node:url";

const gitma = process.argv[2];
if (!gitma) throw new Error("usage: bootstrap_fixture.mjs <gitma checkout>");
const b = await import(pathToFileURL(path.join(gitma, "packages/eval/dist/bootstrap.js")).href);

const n = 300;
const enc = (v) => (Number.isNaN(v) ? "NaN" : v === Infinity ? "Infinity" : v);
const a = new Float64Array(n);
const c = new Float64Array(n);
const cluster = new Int32Array(n);
const ga = new Uint8Array(n);
const gb = new Uint8Array(n);
for (let i = 0; i < n; i++) {
  // Values rounded to 0.1 (ties), a few non-finite rows.
  a[i] = Math.round(10 * Math.abs(Math.sin(i * 1.7)) * (1 + (i % 7))) / 10;
  c[i] = Math.round(10 * Math.abs(Math.cos(i * 0.9)) * (1 + (i % 5))) / 10;
  if (i % 37 === 3) a[i] = Infinity;
  if (i % 53 === 11) a[i] = NaN;
  if (i % 41 === 7) c[i] = Infinity;
  // Clusters of uneven size, ids out of order.
  cluster[i] = (i * 31) % 97;
  ga[i] = a[i] > 4 ? 1 : 0;
  gb[i] = c[i] > 4 ? 1 : 0;
}
const zeroish = new Float64Array(n);
for (let i = 0; i < n; i++) zeroish[i] = i % 2 === 0 ? 0.5 : 0;
const plain = (r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, enc(v)]));
const cases = {
  inputs: {
    a: Array.from(a, enc),
    b: Array.from(c, enc),
    cluster: Array.from(cluster),
    gross_a: Array.from(ga),
    gross_b: Array.from(gb),
    zeroish: Array.from(zeroish),
  },
  median: plain(b.bootstrapMedian(a, 500)),
  median_ratio: plain(b.bootstrapMedianRatio(a, c, 500)),
  clustered_q50: plain(b.bootstrapClusteredQuantileRatio(a, c, cluster, 0.5, 0.975, 500)),
  clustered_q90: plain(b.bootstrapClusteredQuantileRatio(a, c, cluster, 0.9, 0.95, 500)),
  clustered_rate_difference: plain(b.bootstrapClusteredRateDifference(ga, gb, cluster, 0.975, 500)),
  // A denominator whose median is 0 in most resamples: JavaScript division gives ∞ or NaN.
  zero_median: plain(b.bootstrapClusteredQuantileRatio(a, zeroish, cluster, 0.5, 0.95, 200)),
};
process.stdout.write(JSON.stringify(cases, null, 1) + "\n");
