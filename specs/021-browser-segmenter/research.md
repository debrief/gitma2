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

Measured, before any comparison was gated: cost drops agree to 1.6e-12 in absolute value, so the
band would be about 2e-11. No decision on the 30 check scenarios fell inside it, or differed at
all (`experiments/20261116-port/`). The band therefore excuses nothing in this record.

The job gates on two things: 95% of rows identical (SC-001) and identical nominations.

## R3 The GLR statistic is discontinuous

The statistic's basis drops a column whose Gram–Schmidt remainder is below 1e-6. A
least-squares state that differs by under a metre (an LM iteration path) can move the statistic
at a row from 0.89 to 0.53 (ordinal 0, row 139).

Ported alone, on Python's own states, the statistic agrees to 5e-12. Fed the browser's states it
differs at a few rows. Those differences are far below the alarm threshold (4.67), and the
nominations are identical on all 30 scenarios. The check therefore reads nominations, not raw
statistic values.

## R4 Search cost tables

Some cost-table entries differ by up to 3%: fits capped at 20 Levenberg–Marquardt iterations
follow different paths from last-bit differences. The search's transitions on every prefix are
identical on all 30 scenarios. These entries do not decide anything there, but they would on a
scenario where two segmentations nearly tie.

## R5 Float32 arithmetic in O

The pack stores ownship course and speed as float32. NumPy takes the speed leg's mean and its
differences in float32, using pairwise summation. The port reproduces both (`codes.js`,
`pairwiseSumF32`). O's codes are identical on all 30 scenarios.

## R6 Padding

Python's reference runs each scenario alone, padded to the graphs' 720 rows. Gate 2 ran C in
chunks of 16 padded to the chunk's longest scenario. The page compares the live estimate with the
shipped Gate 2 estimate as well, and reports the rows that differ.
