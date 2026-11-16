# Research: the carried model end to end in the browser

## R1 The physics layer as a graph, not a hand port

Decision: C's confirmation costs come from `PhysicsLayer()` exported unchanged
(`viewer/layer_export.py`: 100 iterations, 8 knots, one Loop, 1,968 nodes, 274 KB).

Measured: on eight confirmation requests the browser's cost agrees with torch to 6.8e-15, and
Python's onnxruntime to 4.3e-15. The browser takes about 0.1 s a request row, against E-w's
0.27 s.

Alternative, not chosen: a JavaScript port of `physics/reference.py`. It would be a second
implementation of the numerics, needing its own conformance check.

## R2 What the comparison gates

A decision is a threshold on a cost difference. The plan reserved a near-threshold band of ten
times the largest browser–Python difference in a cost drop.

Measured on the 30 check scenarios (`experiments/20261116-port/`):
- On 28 scenarios the cost drops agree to 2e-9.
- On ordinal 23 they agree to 5.4e-9.
- On ordinal 8 one drop differs by 1.3e-4: its 100-iteration layer solve took another path.

So the band is 1.3e-3. The smallest margin of any decision from its threshold is 0.152
(ordinal 31, E). No decision differs, and none falls inside the band.

The CI job (`port_summary.py`) fails unless all of these hold:
- every expected scenario is present;
- nominations and search transitions are identical;
- every confirmation decision is identical;
- at least 95% of rows are identical.

The band concerns confirmation only. Review finding 2 showed that the GLR statistic can cross
its own threshold (R3), and that crossing has no band.

## R3 The GLR statistic is discontinuous, and least squares has more than one minimum

Corrected after review. An earlier draft said every difference lay "far from any threshold";
that was false.

The statistic's basis drops a column whose Gram–Schmidt remainder is below 1e-6. Least-squares
states that differ in the last digits, a metre or less, can move the statistic a long way.

The largest absolute differences:

| Ordinal | Absolute difference |
| --- | --- |
| 1 | 2.93 |
| 7 | 2.07 |
| 22 | 1.44 |
| 15 | 1.02 |
| 11 | 0.83 |

On ordinal 1, row 256, the browser's value is 2.98 and Python's 5.91, on opposite sides of the
alarm threshold of 4.67. Nominations stayed identical only because that row falls between
retests of an episode that began at row 241. The same flip at an episode's start, or on the
retest lattice, would change a nomination. The gate would then fail, which is the intended
behaviour. The check now lists every such crossing; only that one occurs on the 30 scenarios.

Ported alone, on Python's own states, the statistic agrees to 1e-12 on most scenarios and to
7.6e-5 at worst (ordinal 31).

On ordinal 22 the per-row least squares lands in a different minimum at one row (relative
difference 75). That moves E-s's evidence by 0.50 at row 352.

The least-squares comparison is vacuous on ordinals 8 and 16, which have no usable row.

## R4 Search cost tables

Corrected after review. Cost-table entries differ by up to 22%:

| Ordinal | Largest difference |
| --- | --- |
| 30 | 22% |
| 20 | 19% |
| 23 | 9.5% |
| 26 | 8.7% |

These are fits capped at 20 Levenberg–Marquardt iterations that follow different paths from
last-bit differences. The search's transitions on every prefix are identical on all 30
scenarios, so these entries decided nothing there. They would on a scenario where two
segmentations nearly tie.

## R5 Float32 arithmetic in O

The pack stores ownship course and speed as float32. NumPy takes the speed leg's mean and its
differences in float32, using pairwise summation. The port reproduces both (`codes.js`,
`pairwiseSumF32`). O's codes are identical on all 30 scenarios.

## R6 Padding

Python's reference runs each scenario alone, padded to the graphs' 720 rows. Gate 2 ran C in
chunks of 16 padded to the chunk's longest scenario. The page compares the live estimate with the
shipped Gate 2 estimate as well, and reports the rows that differ.
