# Nominator ceiling (spec 007 research R1, task T003)

**Question.** Would a learned nominator (form a) be worth building? Its ceiling: C's confirmation
given every true change start as an extra nomination (`tma2-segment --extra-nominations truth`,
a validation-only diagnostic refused on test splits), with C's acceptance rule unchanged.

**Run.** Seed 314 validation scoring ordinals 500–1499 (3,934 σ = 1° G5 rows). The ceiling's
segmentation is `results/segment-c3-val-truthnom-42242668707` (b927746, clean). C's is
`results/segment-c3-val-42228602685`. Both were scored together in gap mode with `knot_at_k` on
CI: `score.yml` run 42250190193 at 7a4509f. Intervals are 97.5% scenario-clustered.

| | Median range | Gap recovered | Open at k: rows, gap | Range > 50% | Both edges ±60 s | ±3 min |
| --- | --- | --- | --- | --- | --- | --- |
| C | 0.1203 | 0.891 [0.871, 0.910] | 210, 0.695 | 11.5% | 10.1% | 43.2% |
| C + true nominations | 0.1118 | 0.907 [0.887, 0.926] | 197, 0.677 | 10.4% | 22.3% | 52.4% |

**Paired difference (ceiling − C):**

| Error | Difference [97.5%] |
| --- | --- |
| Range | **+0.0164 [+0.0071, +0.0277]** |
| Course | +0.0131 [−0.0037, +0.0278] |
| Speed | +0.0184 [+0.0032, +0.0412] |

**Decision (rule fixed in research R1: build form a only if the ceiling gains at least +0.02).**
Do not build form (a). Even perfect nominations gain +0.016 in range. A learned nominator would
recover only part of that, at the cost of extra physics solves per candidate.

Recall is a real but small lever. The ceiling doubles the boundary hits within ±60 s, but the
gain downstream is a sixtieth of the gap. E-s, evidence trained through confirmation's decisions
(form b), stays the learned segmentation, and E-w acts on the open-at-k rows.
