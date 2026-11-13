# Spec 015, development on a spent seed: what each repair changes (2026-11-13)

**Development data: seed 335 was spec 014's test seed and is spent. Nothing here is a
registered result.** CI run 43383667575 (`timelate/tl-d-dev`, commit 1895362, clean tree):
the first 200 Annex B periods (185 scored) and the first 200 held-course periods of seed 335,
with spec 014's search (`search2`) beside the repaired one (`search3`). Every table is in
`tables.md`, generated from `summary.json` by `scripts/research/tl3_tables.py`; the figures
below are read from it.

## The evidence repair

| | Spec 014's evidence | Repaired |
| --- | --- | --- |
| Held course: periods with a manoeuvre declared | 0.76 [0.69, 0.81] | 0.50 [0.43, 0.57] |
| ... under 30 minutes (38 periods) | 0.42 | 0.08 |
| ... 30 to 45 minutes (60) | 0.68 | 0.22 |
| ... 45 to 60 minutes (48) | 0.88 | 0.69 |
| ... 60 to 90 minutes (42) | 0.95 | 0.93 |
| ... over 90 minutes (12) | 1.00 | 1.00 |
| Held course: track error | 0.038 | 0.032 |
| Annex B: track error | 0.038 | 0.036 |
| Annex B: old ÷ repaired, paired | – | 1.03 [0.93, 1.14] |
| Annex B: false manoeuvres a period | 0.36 | 0.23 |
| Annex B: true manoeuvres missed | 0.19 | 0.22 |
| Annex B: first candidate right (edge-aware) | 0.605 | 0.650 |
| Annex B: targets with one manoeuvre declared quiet (57) | 0.035 | 0.088 |

- **The repair removes the false manoeuvres on short periods and leaves them on long ones.**
  Under 30 minutes the rate falls from 0.42 to 0.08; over an hour it stays above 0.9. That
  separates the two causes the panel named: the short-period ones were the evidence's
  defect, the long-period ones are the prior saying a target does not hold course for an hour.
- On Annex B data the track is no worse (1.03 [0.93, 1.14]), the search declares a third
  fewer false manoeuvres and misses slightly more true ones.
- The mixed prior still removes the held-course problem entirely (0 of 200) and still pays
  for it: it calls a target with one manoeuvre quiet in 0.23 of periods, where the repaired
  search does in 0.09. C″ does in 0.32 and the flat-prior search in 0.25, which spec 014
  did not report.

## The edge rule

38 of 200 Annex B periods have a manoeuvre the period cuts. With the one rule the first
candidate is right in 0.64 of scored periods (0.62 on periods with none cut). The wrong
histories divide 0.49 / 0.12 / 0.39 (ambiguous / search failure / evidence failure), and
nearly the same without the cut periods (0.51 / 0.12 / 0.37): the classes no longer depend
on the period's edges.

## The reference

15% of true-history fits drifted beyond the match tolerance and were held to the true
times (30 of 200). Every true-history fit has a cost the noise explains. The headroom with
a perfect evidence is 1.17 [1.08, 1.27] with them and 1.11 [1.04, 1.19] without: the held
fits are better than the drifted ones were, so the headroom is larger than spec 014's
composite showed on these periods, and still inconclusive against 1.10.

**Changed before registration**: the soundness stop's limit on held references is set at
25%. It was drafted at 15% before this run existed; 15% is what the data give.

## The refit control

The fall-back fired in 26 of 200 Annex B periods, far more than the four runaways it was
built for. Cause: the rule compared the refit's bearing cost with C″'s own track, and the
chord track has four free unknowns a manoeuvre, so it fits the bearings more closely than a
sound arc refit. **Changed before registration** (research R4): a refit whose cost the noise
explains is kept whatever C″'s track costs. The refit's share of the gain on these periods:
0.47 [0.32, 0.61] with the fall-backs, 0.54 [0.39, 0.69] without those periods. What it is
with the changed rule is not measured here; the registered runs use the changed rule.

## Cautions

- These periods were seen by spec 014's panel and by this spec's design. They show the
  repairs do what they were built to do; they are not evidence for the decided quantities.
- The fall-back rule and the stop's limit were both changed after this run and before
  registration. The first is untested on any run.
