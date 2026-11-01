# Gate 1 validation report

Decision record: `experiments/20261101-g1-decision/decision.json`. Validation split: seed 302, σ = 1° gate rows (zig + 5 min for range and course, zig + 10 min for speed).

| Estimator | Range (median, ratio to LS) | Course (°) | Speed (m/s) | Gross | Efficiency range / course / speed |
| --- | --- | --- | --- | --- | --- |
| g1-physics-s1 | 3.66% (1.001 [0.997, 1.004]) | 1.40 (0.997 [0.992, 1.000]) | 0.313 (1.000 [0.999, 1.001]) | 1.01% | 1.026 / 0.986 / 0.956 |
| g1-physics-s2 (carried) | 3.67% (1.001 [0.997, 1.004]) | 1.40 (0.997 [0.992, 1.000]) | 0.313 (1.000 [1.000, 1.000]) | 1.01% | 1.026 / 0.985 / 0.956 |
| g1-physics-s3 | 3.67% (1.001 [0.997, 1.004]) | 1.40 (0.997 [0.992, 1.000]) | 0.313 (1.000 [1.000, 1.000]) | 1.01% | 1.026 / 0.985 / 0.956 |
| g1-direct | 25.41% (6.937 [6.611, 7.369]) | 16.76 (11.962 [11.286, 12.874]) | 3.075 (9.816 [8.946, 10.709]) | 21.69% | 5.905 / 9.065 / 7.551 |
| g1-shuffled | 3.71% (1.012 [1.005, 1.023]) | 1.42 (1.010 [1.005, 1.029]) | 0.319 (1.020 [1.004, 1.037]) | 1.46% | 1.033 / 0.989 / 0.964 |
| g1-timelate | 1.97% (0.539 [0.516, 0.566]) | 0.68 (0.484 [0.460, 0.515]) | 0.238 (0.759 [0.713, 0.816]) | 0.32% | 0.553 / 0.446 / 0.725 |
| least_squares | 3.66% | 1.40 | 0.313 | 1.11% | 1.027 / 0.988 / 0.957 |
| naive | 40.61% | 89.72 | 4.267 | 38.28% | 8.171 / 42.516 / 8.900 |
| ekf | 4.00% | 1.52 | 0.354 | 1.96% | 1.126 / 1.057 / 1.076 |
| imm | 4.00% | 1.52 | 0.358 | 2.06% | 1.123 / 1.050 / 1.073 |

Carried by rule (median seed by median range error): **g1-physics-s2** (order g1-physics-s1, g1-physics-s2, g1-physics-s3).

Validation rule:

- carried-range-below-1.1: met
- carried-course-below-1.1: met
- carried-speed-below-1.1: met
- shuffled-no-better-than-least-squares: met
- timelate-at-least-as-good: met

**Proceed to the test split (seed 303).**
