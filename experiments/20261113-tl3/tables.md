## Systems (median period range error)

| System | Annex B (364) | Shifted (262) | Held course (348) | Correlated (88) | Outliers (88) | Whole (60) |
| --- | --- | --- | --- | --- | --- | --- |
| One leg | 0.400 | 0.368 | 0.018 | 0.380 | 0.387 | 0.446 |
| C″ read as a track | 0.083 | 0.150 | 0.018 | 0.354 | 0.202 | 0.108 |
| C″ refitted | 0.066 | 0.129 | 0.016 | 0.214 | 0.165 | 0.065 |
| Search, flat prior | 0.049 | 0.111 | 0.016 | 0.216 | 0.097 | 0.037 |
| Search, spec 014's evidence | 0.041 | 0.095 | 0.038 | 0.150 | 0.087 | 0.034 |
| Search, repaired evidence | 0.039 | 0.095 | 0.030 | 0.165 | 0.087 | 0.036 |
| Search, repaired, mixed prior | 0.041 | 0.097 | 0.016 | 0.166 | 0.087 | 0.036 |
| True history, best evidence | 0.028 | 0.042 | 0.016 | 0.098 | 0.046 | 0.021 |
| True history, times held | 0.025 | 0.041 | 0.017 | 0.089 | 0.036 | 0.016 |

## Annex B: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 2.10 [1.82, 2.44] | 2.11 [1.72, 2.48] | 0.31 | 0.44 / 0.12 |
| c2 ÷ c2-refit | 1.28 [1.14, 1.43] | 1.26 [1.09, 1.50] | 0.40 | 0.27 / 0.14 |
| c2-refit ÷ search3 | 1.65 [1.45, 1.87] | 1.67 [1.35, 1.93] | 0.39 | 0.29 / 0.07 |
| search3-flat ÷ search3 | 1.22 [1.10, 1.34] | 1.25 [1.04, 1.39] | 0.37 | 0.19 / 0.10 |
| search2 ÷ search3 | 1.07 [0.98, 1.16] | 1.05 [0.92, 1.15] | 0.20 | 0.10 / 0.06 |
| search3 ÷ search3-mix | 0.98 [0.96, 1.01] | 0.97 [0.91, 1.02] | 0.03 | 0.01 / 0.02 |
| search3 ÷ history-best | 1.43 [1.30, 1.59] | 1.39 [1.24, 1.68] | 0.38 | 0.26 / 0.07 |
| search3 ÷ history-fixed | 1.70 [1.51, 1.92] | 1.55 [1.35, 1.86] | 0.36 | 0.41 / 0.11 |
| search3 ÷ one-leg | 0.05 [0.04, 0.07] | 0.10 [0.08, 0.13] | 0.89 | 0.02 / 0.78 |
| c2 ÷ one-leg | 0.11 [0.09, 0.14] | 0.21 [0.17, 0.26] | 0.77 | 0.04 / 0.64 |
| search3-mix ÷ one-leg | 0.05 [0.04, 0.07] | 0.10 [0.08, 0.13] | 0.90 | 0.01 / 0.76 |

## Annex B: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 364 | 0.64 [0.59, 0.69] | 131 | 0.44 [0.36, 0.53] | 0.13 [0.08, 0.20] | 0.43 [0.35, 0.51] |
| all | 400 | 0.65 [0.60, 0.70] | 139 | 0.45 [0.37, 0.54] | 0.12 [0.08, 0.19] | 0.42 [0.35, 0.51] |
| scored without cut | 301 | 0.62 [0.56, 0.67] | 115 | 0.46 [0.37, 0.55] | 0.14 [0.09, 0.21] | 0.40 [0.32, 0.49] |

## Annex B: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.10 [1.05, 1.17] inconclusive | 1.35 [1.24, 1.48] material | 1.41 [1.29, 1.54] | 1.42 [1.32, 1.55] |
| threshold 1 tol 120 | 1.08 [1.03, 1.14] inconclusive | 1.30 [1.20, 1.42] material | 1.35 [1.24, 1.47] | 1.36 [1.27, 1.48] |
| threshold 1 tol 240 | 1.05 [1.01, 1.11] inconclusive | 1.24 [1.16, 1.34] material | 1.27 [1.18, 1.38] | 1.29 [1.21, 1.38] |
| threshold 3 tol 60 | 1.07 [1.03, 1.13] inconclusive | 1.20 [1.12, 1.29] material | 1.41 [1.29, 1.54] | 1.24 [1.17, 1.33] |
| threshold 3 tol 120 | 1.06 [1.01, 1.11] inconclusive | 1.17 [1.10, 1.25] inconclusive | 1.35 [1.24, 1.47] | 1.21 [1.14, 1.29] |
| registered | 1.06 [1.01, 1.11] inconclusive | 1.17 [1.10, 1.25] inconclusive | 1.35 [1.24, 1.47] | 1.21 [1.14, 1.29] |
| registered without flagged | 1.05 [1.01, 1.11] inconclusive | 1.13 [1.06, 1.20] inconclusive | 1.25 [1.15, 1.37] | 1.16 [1.10, 1.24] |
| threshold 3 tol 240 | 1.04 [1.00, 1.08] not material | 1.15 [1.08, 1.22] inconclusive | 1.27 [1.18, 1.38] | 1.17 [1.11, 1.24] |
| threshold 5 tol 60 | 1.06 [1.02, 1.11] inconclusive | 1.14 [1.07, 1.21] inconclusive | 1.41 [1.29, 1.54] | 1.16 [1.10, 1.24] |
| threshold 5 tol 120 | 1.04 [1.01, 1.09] not material | 1.10 [1.05, 1.17] inconclusive | 1.35 [1.24, 1.47] | 1.13 [1.07, 1.20] |
| threshold 5 tol 240 | 1.03 [1.00, 1.07] not material | 1.08 [1.03, 1.14] inconclusive | 1.27 [1.18, 1.38] | 1.10 [1.05, 1.16] |

Ratio of medians at the registered setting: perfect search 1.04 [1.00, 1.12]; perfect evidence as well 1.08 [1.03, 1.25].

## Annex B: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | 0.33 [0.20, 0.45] (364 periods) |
| without fallbacks | 0.34 [0.20, 0.47] (361 periods) |
| medians at most 1 | 0.37 [0.23, 0.50] (351 periods) |
| search right | 0.34 [0.20, 0.49] (233 periods) |
| search wrong | 0.27 [-0.13, 0.57] (131 periods) |
| flat prior search | 0.74 [0.61, 0.86] (364 periods) |
| ratio of log medians | 0.31 |

Refit fall-backs: 5 of 400; refits with a period median of 1 or more: 7.

## Annex B: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 716 | 412 | 0.58 | 352 | 0.88 | 58 | 0.78 / 0.36 |
| c2-refit | 716 | 255 | 0.36 | 191 | 0.48 | 23 | 0.47 / 0.29 |
| search3-flat | 716 | 193 | 0.27 | 86 | 0.21 | 19 | 0.39 / 0.22 |
| search2 | 716 | 140 | 0.20 | 135 | 0.34 | 18 | 0.30 / 0.14 |
| search3 | 716 | 155 | 0.22 | 89 | 0.22 | 18 | 0.30 / 0.17 |
| search3-mix | 716 | 166 | 0.23 | 74 | 0.18 | 18 | 0.31 / 0.19 |

## Annex B: periods with no true manoeuvre (10): share with one declared

| System | All | 0-30 min | 30-45 min |
| --- | --- | --- | --- |
| c2 | 0.10 [0.02, 0.40] | 0.11 (9) | 0.00 (1) |
| c2-refit | 0.10 [0.02, 0.40] | 0.11 (9) | 0.00 (1) |
| search3-flat | 0.00 [0.00, 0.28] | 0.00 (9) | 0.00 (1) |
| search2 | 0.30 [0.11, 0.60] | 0.33 (9) | 0.00 (1) |
| search3 | 0.10 [0.02, 0.40] | 0.11 (9) | 0.00 (1) |
| search3-mix | 0.00 [0.00, 0.28] | 0.00 (9) | 0.00 (1) |

## Annex B: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.238 (122) | 0.077 (117) | 0.000 (79) |
| c2-refit | 0.238 (122) | 0.077 (117) | 0.000 (79) |
| search3-flat | 0.164 (122) | 0.085 (117) | 0.000 (79) |
| search2 | 0.041 (122) | 0.000 (117) | 0.000 (79) |
| search3 | 0.131 (122) | 0.009 (117) | 0.000 (79) |
| search3-mix | 0.197 (122) | 0.085 (117) | 0.000 (79) |

Candidates (repaired evidence, 400 periods): first right 0.652; true history in the first three 0.770; calibration gap -0.038; kinds differ among right 0.12.

Candidates (spec 014's evidence, 400 periods): first right 0.598; true history in the first three 0.760; calibration gap -0.071; kinds differ among right 0.15.

References held to the true times: 0.133; true-history fits with a consistent cost: 1.000; periods with a cut manoeuvre: 72 of 400.

## Shifted: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 1.69 [1.46, 1.95] | 1.57 [1.29, 1.99] | 0.34 | 0.35 / 0.10 |
| c2 ÷ c2-refit | 1.23 [1.10, 1.38] | 1.16 [0.98, 1.34] | 0.38 | 0.18 / 0.11 |
| c2-refit ÷ search3 | 1.38 [1.20, 1.56] | 1.35 [1.14, 1.73] | 0.38 | 0.28 / 0.10 |
| search3-flat ÷ search3 | 1.10 [0.98, 1.22] | 1.16 [0.97, 1.36] | 0.45 | 0.16 / 0.13 |
| search2 ÷ search3 | 0.95 [0.89, 1.02] | 1.00 [0.86, 1.15] | 0.30 | 0.07 / 0.08 |
| search3 ÷ search3-mix | 1.00 [0.98, 1.02] | 0.99 [0.89, 1.02] | 0.03 | 0.02 / 0.01 |
| search3 ÷ history-best | 2.05 [1.78, 2.38] | 2.26 [1.79, 2.76] | 0.26 | 0.45 / 0.08 |
| search3 ÷ history-fixed | 2.12 [1.80, 2.49] | 2.31 [1.84, 2.86] | 0.24 | 0.46 / 0.13 |
| search3 ÷ one-leg | 0.13 [0.10, 0.18] | 0.26 [0.19, 0.33] | 0.85 | 0.05 / 0.69 |
| c2 ÷ one-leg | 0.23 [0.18, 0.30] | 0.41 [0.33, 0.53] | 0.74 | 0.06 / 0.55 |
| search3-mix ÷ one-leg | 0.13 [0.10, 0.18] | 0.26 [0.20, 0.35] | 0.84 | 0.04 / 0.68 |

## Shifted: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 262 | 0.23 [0.18, 0.28] | 203 | 0.16 [0.11, 0.21] | 0.07 [0.05, 0.12] | 0.77 [0.71, 0.82] |
| all | 300 | 0.23 [0.19, 0.28] | 230 | 0.17 [0.13, 0.22] | 0.07 [0.04, 0.10] | 0.77 [0.71, 0.82] |
| scored without cut | 226 | 0.21 [0.16, 0.27] | 178 | 0.18 [0.13, 0.24] | 0.08 [0.05, 0.13] | 0.74 [0.67, 0.80] |

## Shifted: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.17 [1.09, 1.26] inconclusive | 1.95 [1.70, 2.25] material | 2.05 [1.79, 2.38] | 2.20 [1.95, 2.48] |
| threshold 1 tol 120 | 1.16 [1.08, 1.26] inconclusive | 1.94 [1.68, 2.23] material | 2.02 [1.76, 2.33] | 2.16 [1.92, 2.44] |
| threshold 1 tol 240 | 1.16 [1.08, 1.25] inconclusive | 1.86 [1.62, 2.14] material | 1.94 [1.69, 2.25] | 2.07 [1.84, 2.34] |
| threshold 3 tol 60 | 1.14 [1.07, 1.23] inconclusive | 1.71 [1.49, 1.96] material | 2.05 [1.79, 2.38] | 1.92 [1.71, 2.15] |
| threshold 3 tol 120 | 1.14 [1.07, 1.23] inconclusive | 1.71 [1.50, 1.96] material | 2.02 [1.76, 2.33] | 1.91 [1.69, 2.14] |
| registered | 1.14 [1.07, 1.23] inconclusive | 1.71 [1.50, 1.96] material | 2.02 [1.76, 2.33] | 1.91 [1.69, 2.14] |
| registered without flagged | 1.20 [1.09, 1.32] inconclusive | 1.55 [1.36, 1.77] material | 1.80 [1.56, 2.08] | 1.68 [1.49, 1.91] |
| threshold 3 tol 240 | 1.13 [1.06, 1.22] inconclusive | 1.68 [1.47, 1.92] material | 1.94 [1.69, 2.25] | 1.87 [1.67, 2.09] |
| threshold 5 tol 60 | 1.10 [1.04, 1.18] inconclusive | 1.56 [1.37, 1.79] material | 2.05 [1.79, 2.38] | 1.74 [1.56, 1.95] |
| threshold 5 tol 120 | 1.10 [1.04, 1.18] inconclusive | 1.56 [1.36, 1.78] material | 2.02 [1.76, 2.33] | 1.73 [1.55, 1.94] |
| threshold 5 tol 240 | 1.10 [1.04, 1.18] inconclusive | 1.53 [1.35, 1.75] material | 1.94 [1.69, 2.25] | 1.70 [1.52, 1.91] |

Ratio of medians at the registered setting: perfect search 1.20 [1.04, 1.33]; perfect evidence as well 2.00 [1.52, 2.42].

## Shifted: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | 0.39 [0.20, 0.60] (262 periods) |
| without fallbacks | 0.39 [0.20, 0.58] (257 periods) |
| medians at most 1 | 0.39 [0.21, 0.58] (259 periods) |
| search right | 0.26 [-0.08, 0.51] (59 periods) |
| search wrong | 0.50 [0.24, 0.78] (203 periods) |
| flat prior search | 0.82 [0.65, 1.04] (262 periods) |
| ratio of log medians | 0.33 |

Refit fall-backs: 11 of 300; refits with a period median of 1 or more: 2.

## Shifted: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 921 | 637 | 0.69 | 287 | 0.96 | 64 | 0.86 / 0.51 |
| c2-refit | 921 | 527 | 0.57 | 176 | 0.59 | 24 | 0.66 / 0.49 |
| search3-flat | 921 | 470 | 0.51 | 156 | 0.52 | 23 | 0.60 / 0.44 |
| search2 | 921 | 373 | 0.40 | 136 | 0.45 | 23 | 0.51 / 0.34 |
| search3 | 921 | 410 | 0.45 | 128 | 0.43 | 23 | 0.55 / 0.38 |
| search3-mix | 921 | 415 | 0.45 | 116 | 0.39 | 23 | 0.56 / 0.39 |

## Shifted: periods with no true manoeuvre (2): share with one declared

| System | All | 0-30 min |
| --- | --- | --- |
| c2 | 0.00 [0.00, 0.66] | 0.00 (2) |
| c2-refit | 0.00 [0.00, 0.66] | 0.00 (2) |
| search3-flat | 0.50 [0.09, 0.91] | 0.50 (2) |
| search2 | 0.50 [0.09, 0.91] | 0.50 (2) |
| search3 | 0.50 [0.09, 0.91] | 0.50 (2) |
| search3-mix | 0.50 [0.09, 0.91] | 0.50 (2) |

## Shifted: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.348 (23) | 0.182 (77) | 0.032 (156) |
| c2-refit | 0.348 (23) | 0.182 (77) | 0.032 (156) |
| search3-flat | 0.261 (23) | 0.143 (77) | 0.019 (156) |
| search2 | 0.043 (23) | 0.039 (77) | 0.000 (156) |
| search3 | 0.217 (23) | 0.065 (77) | 0.000 (156) |
| search3-mix | 0.348 (23) | 0.156 (77) | 0.032 (156) |

Candidates (repaired evidence, 300 periods): first right 0.233; true history in the first three 0.400; calibration gap 0.356; kinds differ among right 0.38.

Candidates (spec 014's evidence, 300 periods): first right 0.287; true history in the first three 0.413; calibration gap 0.261; kinds differ among right 0.49.

References held to the true times: 0.300; true-history fits with a consistent cost: 1.000; periods with a cut manoeuvre: 42 of 300.

## Held course: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 0.56 [0.50, 0.63] | 0.58 [0.46, 0.70] | 0.67 | 0.05 / 0.36 |
| c2 ÷ c2-refit | 1.05 [1.00, 1.11] | 1.07 [0.96, 1.19] | 0.43 | 0.07 / 0.05 |
| c2-refit ÷ search3 | 0.53 [0.47, 0.59] | 0.54 [0.45, 0.64] | 0.56 | 0.01 / 0.34 |
| search3-flat ÷ search3 | 0.52 [0.47, 0.58] | 0.53 [0.45, 0.64] | 0.50 | 0.02 / 0.34 |
| search2 ÷ search3 | 1.22 [1.12, 1.34] | 1.26 [1.09, 1.47] | 0.24 | 0.18 / 0.08 |
| search3 ÷ search3-mix | 1.91 [1.73, 2.13] | 1.87 [1.57, 2.27] | 0.07 | 0.34 / 0.01 |
| search3 ÷ history-best | 1.90 [1.72, 2.12] | 1.87 [1.56, 2.24] | 0.16 | 0.34 / 0.01 |
| search3 ÷ history-fixed | 1.89 [1.71, 2.11] | 1.83 [1.54, 2.21] | 0.21 | 0.34 / 0.02 |
| search3 ÷ one-leg | 1.80 [1.60, 2.02] | 1.71 [1.43, 2.13] | 0.33 | 0.36 / 0.05 |
| c2 ÷ one-leg | 1.00 [0.98, 1.03] | 0.99 [0.95, 1.02] | 0.00 | 0.01 / 0.00 |
| search3-mix ÷ one-leg | 0.94 [0.89, 0.99] | 0.91 [0.83, 1.03] | 0.58 | 0.05 / 0.07 |

## Held course: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 348 | 0.42 [0.37, 0.47] | 201 | 0.43 [0.37, 0.50] | 0.00 [0.00, 0.02] | 0.57 [0.50, 0.63] |
| all | 400 | 0.47 [0.42, 0.52] | 213 | 0.46 [0.39, 0.53] | 0.00 [0.00, 0.02] | 0.54 [0.47, 0.61] |
| scored without cut | 348 | 0.42 [0.37, 0.47] | 201 | 0.43 [0.37, 0.50] | 0.00 [0.00, 0.02] | 0.57 [0.50, 0.63] |

## Held course: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.00 [1.00, 1.00] not material | 1.77 [1.61, 1.96] material | 1.90 [1.72, 2.12] | 1.81 [1.65, 2.01] |
| threshold 1 tol 120 | 1.00 [1.00, 1.00] not material | 1.77 [1.61, 1.96] material | 1.90 [1.72, 2.12] | 1.81 [1.65, 2.01] |
| threshold 1 tol 240 | 1.00 [1.00, 1.00] not material | 1.77 [1.61, 1.96] material | 1.90 [1.72, 2.12] | 1.81 [1.65, 2.01] |
| threshold 3 tol 60 | 1.00 [1.00, 1.00] not material | 1.53 [1.40, 1.68] material | 1.90 [1.72, 2.12] | 1.55 [1.42, 1.70] |
| threshold 3 tol 120 | 1.00 [1.00, 1.00] not material | 1.53 [1.40, 1.68] material | 1.90 [1.72, 2.12] | 1.55 [1.42, 1.70] |
| registered | 1.00 [1.00, 1.00] not material | 1.53 [1.40, 1.68] material | 1.90 [1.72, 2.12] | 1.55 [1.42, 1.70] |
| registered without flagged | 1.00 [1.00, 1.00] not material | 1.53 [1.40, 1.68] material | 1.90 [1.72, 2.12] | 1.55 [1.42, 1.70] |
| threshold 3 tol 240 | 1.00 [1.00, 1.00] not material | 1.53 [1.40, 1.68] material | 1.90 [1.72, 2.12] | 1.55 [1.42, 1.70] |
| threshold 5 tol 60 | 1.00 [1.00, 1.00] not material | 1.41 [1.30, 1.53] material | 1.90 [1.72, 2.12] | 1.41 [1.30, 1.54] |
| threshold 5 tol 120 | 1.00 [1.00, 1.00] not material | 1.41 [1.30, 1.53] material | 1.90 [1.72, 2.12] | 1.41 [1.30, 1.54] |
| threshold 5 tol 240 | 1.00 [1.00, 1.00] not material | 1.41 [1.30, 1.53] material | 1.90 [1.72, 2.12] | 1.41 [1.30, 1.54] |

Ratio of medians at the registered setting: perfect search 1.00 [1.00, 1.00]; perfect evidence as well 1.59 [1.34, 1.85].

## Held course: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | -0.09 [-0.20, -0.00] (348 periods) |
| without fallbacks | -0.09 [-0.20, -0.00] (348 periods) |
| medians at most 1 | -0.09 [-0.21, -0.00] (347 periods) |
| search right | 0.94 [0.69, 1.00] (147 periods) |
| search wrong | -0.03 [-0.09, 0.03] (201 periods) |
| flat prior search | -0.11 [-0.23, -0.02] (348 periods) |
| ratio of log medians | -0.13 |

Refit fall-backs: 3 of 400; refits with a period median of 1 or more: 0.

## Held course: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 2 | 2 | 1.00 | 11 | 0.03 | – | 1.00 / 0.00 |
| c2-refit | 2 | 1 | 0.50 | 10 | 0.03 | 112 | 1.00 / 0.50 |
| search3-flat | 2 | 0 | 0.00 | 2 | 0.01 | 49 | 0.50 / 0.00 |
| search2 | 2 | 0 | 0.00 | 391 | 0.98 | 58 | 0.50 / 0.00 |
| search3 | 2 | 0 | 0.00 | 249 | 0.62 | 55 | 0.50 / 0.00 |
| search3-mix | 2 | 0 | 0.00 | 2 | 0.01 | 55 | 0.50 / 0.00 |

## Held course: periods with no true manoeuvre (398): share with one declared

| System | All | 0-30 min | 30-45 min | 45-60 min | 60-90 min | 90-1000 min |
| --- | --- | --- | --- | --- | --- | --- |
| c2 | 0.02 [0.01, 0.03] | 0.03 (86) | 0.01 (99) | 0.00 (88) | 0.01 (94) | 0.03 (31) |
| c2-refit | 0.02 [0.01, 0.03] | 0.03 (86) | 0.01 (99) | 0.00 (88) | 0.01 (94) | 0.03 (31) |
| search3-flat | 0.01 [0.00, 0.02] | 0.02 (86) | 0.00 (99) | 0.00 (88) | 0.00 (94) | 0.00 (31) |
| search2 | 0.80 [0.76, 0.84] | 0.50 (86) | 0.78 (99) | 0.91 (88) | 0.95 (94) | 1.00 (31) |
| search3 | 0.53 [0.48, 0.58] | 0.09 (86) | 0.32 (99) | 0.68 (88) | 0.86 (94) | 1.00 (31) |
| search3-mix | 0.00 [0.00, 0.01] | 0.01 (86) | 0.00 (99) | 0.00 (88) | 0.00 (94) | 0.00 (31) |

## Held course: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.000 (2) | – (0) | – (0) |
| c2-refit | 0.000 (2) | – (0) | – (0) |
| search3-flat | 0.000 (2) | – (0) | – (0) |
| search2 | 0.000 (2) | – (0) | – (0) |
| search3 | 0.000 (2) | – (0) | – (0) |
| search3-mix | 0.000 (2) | – (0) | – (0) |

Candidates (repaired evidence, 400 periods): first right 0.468; true history in the first three 0.713; calibration gap -0.025; kinds differ among right 0.00.

Candidates (spec 014's evidence, 400 periods): first right 0.198; true history in the first three 0.515; calibration gap 0.203; kinds differ among right 0.00.

References held to the true times: 0.000; true-history fits with a consistent cost: 1.000; periods with a cut manoeuvre: 0 of 400.

## Correlated: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 2.03 [1.58, 2.57] | 2.15 [1.56, 2.76] | 0.25 | 0.49 / 0.07 |
| c2 ÷ c2-refit | 1.57 [1.25, 1.98] | 1.65 [1.20, 2.75] | 0.27 | 0.39 / 0.11 |
| c2-refit ÷ search3 | 1.29 [1.02, 1.60] | 1.30 [0.83, 1.74] | 0.39 | 0.26 / 0.15 |
| search3-flat ÷ search3 | 1.19 [1.01, 1.41] | 1.31 [0.92, 1.52] | 0.44 | 0.23 / 0.14 |
| search2 ÷ search3 | 0.98 [0.87, 1.12] | 0.91 [0.70, 1.04] | 0.35 | 0.10 / 0.09 |
| search3 ÷ search3-mix | 1.02 [0.99, 1.09] | 0.99 [0.86, 1.04] | 0.01 | 0.01 / 0.00 |
| search3 ÷ history-best | 1.64 [1.35, 1.99] | 1.68 [1.37, 2.31] | 0.32 | 0.39 / 0.06 |
| search3 ÷ history-fixed | 1.67 [1.31, 2.12] | 1.86 [1.50, 2.58] | 0.33 | 0.45 / 0.14 |
| search3 ÷ one-leg | 0.15 [0.09, 0.25] | 0.43 [0.31, 0.63] | 0.78 | 0.05 / 0.59 |
| c2 ÷ one-leg | 0.30 [0.18, 0.50] | 0.93 [0.64, 1.29] | 0.59 | 0.14 / 0.47 |
| search3-mix ÷ one-leg | 0.15 [0.09, 0.24] | 0.44 [0.31, 0.65] | 0.77 | 0.03 / 0.59 |

## Correlated: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 88 | 0.23 [0.15, 0.33] | 68 | 0.16 [0.09, 0.27] | 0.03 [0.01, 0.10] | 0.81 [0.70, 0.88] |
| all | 100 | 0.23 [0.16, 0.32] | 77 | 0.14 [0.08, 0.24] | 0.03 [0.01, 0.09] | 0.83 [0.73, 0.90] |
| scored without cut | 74 | 0.22 [0.14, 0.32] | 58 | 0.19 [0.11, 0.31] | 0.03 [0.01, 0.12] | 0.78 [0.65, 0.86] |

## Correlated: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.05 [1.00, 1.13] inconclusive | 1.56 [1.29, 1.89] material | 1.63 [1.34, 1.99] | 1.77 [1.51, 2.09] |
| threshold 1 tol 120 | 1.05 [1.00, 1.13] inconclusive | 1.55 [1.28, 1.87] material | 1.61 [1.33, 1.96] | 1.75 [1.49, 2.06] |
| threshold 1 tol 240 | 1.05 [1.00, 1.13] inconclusive | 1.50 [1.24, 1.81] material | 1.56 [1.29, 1.90] | 1.67 [1.43, 1.97] |
| threshold 3 tol 60 | 1.05 [1.00, 1.13] inconclusive | 1.45 [1.21, 1.74] material | 1.63 [1.34, 1.99] | 1.64 [1.42, 1.93] |
| threshold 3 tol 120 | 1.05 [1.00, 1.13] inconclusive | 1.44 [1.20, 1.74] material | 1.61 [1.33, 1.96] | 1.64 [1.41, 1.92] |
| registered | 1.05 [1.00, 1.13] inconclusive | 1.44 [1.20, 1.74] material | 1.61 [1.33, 1.96] | 1.64 [1.41, 1.92] |
| registered without flagged | 1.07 [1.00, 1.18] inconclusive | 1.40 [1.12, 1.79] material | 1.62 [1.25, 2.11] | 1.60 [1.33, 1.98] |
| threshold 3 tol 240 | 1.05 [1.00, 1.13] inconclusive | 1.40 [1.16, 1.69] material | 1.56 [1.29, 1.90] | 1.56 [1.34, 1.84] |
| threshold 5 tol 60 | 1.02 [1.00, 1.06] not material | 1.41 [1.20, 1.66] material | 1.63 [1.34, 1.99] | 1.53 [1.34, 1.77] |
| threshold 5 tol 120 | 1.02 [1.00, 1.05] not material | 1.41 [1.20, 1.65] material | 1.61 [1.33, 1.96] | 1.53 [1.34, 1.77] |
| threshold 5 tol 240 | 1.02 [1.00, 1.05] not material | 1.37 [1.18, 1.62] material | 1.56 [1.29, 1.90] | 1.48 [1.30, 1.71] |

Ratio of medians at the registered setting: perfect search 1.02 [1.00, 1.23]; perfect evidence as well 1.51 [1.19, 2.20].

## Correlated: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | 0.64 [0.35, 0.96] (88 periods) |
| without fallbacks | 0.73 [0.44, 1.06] (81 periods) |
| medians at most 1 | 0.73 [0.45, 1.04] (86 periods) |
| search right | -0.21 [-11.35, 8.28] (20 periods) |
| search wrong | 0.76 [0.49, 1.11] (68 periods) |
| flat prior search | 0.76 [0.52, 0.98] (88 periods) |
| ratio of log medians | 0.66 |

Refit fall-backs: 10 of 100; refits with a period median of 1 or more: 2.

## Correlated: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 188 | 108 | 0.57 | 265 | 2.65 | 58 | 0.78 / 0.38 |
| c2-refit | 188 | 77 | 0.41 | 232 | 2.32 | 46 | 0.63 / 0.27 |
| search3-flat | 188 | 86 | 0.46 | 172 | 1.72 | 38 | 0.64 / 0.29 |
| search2 | 188 | 72 | 0.38 | 156 | 1.56 | 36 | 0.56 / 0.22 |
| search3 | 188 | 71 | 0.38 | 129 | 1.29 | 39 | 0.58 / 0.23 |
| search3-mix | 188 | 71 | 0.38 | 126 | 1.26 | 39 | 0.58 / 0.23 |

## Correlated: periods with no true manoeuvre (3): share with one declared

| System | All | 0-30 min |
| --- | --- | --- |
| c2 | 1.00 [0.44, 1.00] | 1.00 (3) |
| c2-refit | 1.00 [0.44, 1.00] | 1.00 (3) |
| search3-flat | 1.00 [0.44, 1.00] | 1.00 (3) |
| search2 | 1.00 [0.44, 1.00] | 1.00 (3) |
| search3 | 1.00 [0.44, 1.00] | 1.00 (3) |
| search3-mix | 0.33 [0.06, 0.79] | 0.33 (3) |

## Correlated: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| c2-refit | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3-flat | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search2 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3-mix | 0.000 (28) | 0.000 (32) | 0.045 (22) |

Candidates (repaired evidence, 100 periods): first right 0.230; true history in the first three 0.380; calibration gap 0.332; kinds differ among right 0.22.

Candidates (spec 014's evidence, 100 periods): first right 0.170; true history in the first three 0.310; calibration gap 0.344; kinds differ among right 0.21.

References held to the true times: 0.280; true-history fits with a consistent cost: 1.000; periods with a cut manoeuvre: 15 of 100.

## Outliers: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 2.63 [1.97, 3.53] | 2.31 [1.62, 3.01] | 0.20 | 0.50 / 0.06 |
| c2 ÷ c2-refit | 1.32 [1.07, 1.62] | 1.23 [0.90, 1.69] | 0.31 | 0.24 / 0.08 |
| c2-refit ÷ search3 | 1.99 [1.53, 2.60] | 1.88 [1.31, 2.48] | 0.27 | 0.40 / 0.08 |
| search3-flat ÷ search3 | 1.08 [0.83, 1.42] | 1.11 [0.87, 1.36] | 0.51 | 0.19 / 0.22 |
| search2 ÷ search3 | 0.93 [0.79, 1.07] | 1.00 [0.86, 1.16] | 0.32 | 0.11 / 0.10 |
| search3 ÷ search3-mix | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.00 | 0.00 / 0.00 |
| search3 ÷ history-best | 1.77 [1.47, 2.14] | 1.90 [1.47, 2.69] | 0.26 | 0.35 / 0.05 |
| search3 ÷ history-fixed | 2.32 [1.73, 3.02] | 2.46 [1.86, 3.67] | 0.19 | 0.53 / 0.06 |
| search3 ÷ one-leg | 0.08 [0.05, 0.14] | 0.23 [0.16, 0.29] | 0.91 | 0.01 / 0.73 |
| c2 ÷ one-leg | 0.22 [0.13, 0.38] | 0.52 [0.35, 0.70] | 0.73 | 0.12 / 0.52 |
| search3-mix ÷ one-leg | 0.08 [0.05, 0.14] | 0.23 [0.16, 0.29] | 0.91 | 0.01 / 0.73 |

## Outliers: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 88 | 0.40 [0.30, 0.50] | 53 | 0.34 [0.23, 0.47] | 0.17 [0.09, 0.29] | 0.49 [0.36, 0.62] |
| all | 100 | 0.41 [0.32, 0.51] | 59 | 0.36 [0.25, 0.48] | 0.17 [0.09, 0.28] | 0.47 [0.35, 0.60] |
| scored without cut | 74 | 0.35 [0.25, 0.46] | 48 | 0.35 [0.23, 0.50] | 0.19 [0.10, 0.32] | 0.46 [0.33, 0.60] |

## Outliers: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.11 [1.04, 1.20] inconclusive | 1.68 [1.42, 2.03] material | 1.72 [1.45, 2.08] | 1.78 [1.53, 2.10] |
| threshold 1 tol 120 | 1.10 [1.03, 1.19] inconclusive | 1.64 [1.39, 1.95] material | 1.68 [1.41, 2.01] | 1.72 [1.48, 2.02] |
| threshold 1 tol 240 | 1.10 [1.03, 1.19] inconclusive | 1.55 [1.32, 1.84] material | 1.57 [1.33, 1.85] | 1.62 [1.41, 1.89] |
| threshold 3 tol 60 | 1.10 [1.03, 1.19] inconclusive | 1.55 [1.33, 1.81] material | 1.72 [1.45, 2.08] | 1.57 [1.37, 1.85] |
| threshold 3 tol 120 | 1.09 [1.03, 1.18] inconclusive | 1.50 [1.30, 1.75] material | 1.68 [1.41, 2.01] | 1.52 [1.32, 1.78] |
| registered | 1.09 [1.03, 1.18] inconclusive | 1.50 [1.30, 1.75] material | 1.68 [1.41, 2.01] | 1.52 [1.32, 1.78] |
| registered without flagged | 1.11 [1.03, 1.22] inconclusive | 1.32 [1.16, 1.54] material | 1.45 [1.22, 1.72] | 1.34 [1.18, 1.56] |
| threshold 3 tol 240 | 1.08 [1.02, 1.17] inconclusive | 1.45 [1.26, 1.68] material | 1.57 [1.33, 1.85] | 1.47 [1.28, 1.69] |
| threshold 5 tol 60 | 1.06 [1.01, 1.13] inconclusive | 1.40 [1.22, 1.62] material | 1.72 [1.45, 2.08] | 1.42 [1.24, 1.65] |
| threshold 5 tol 120 | 1.06 [1.01, 1.13] inconclusive | 1.37 [1.20, 1.58] material | 1.68 [1.41, 2.01] | 1.38 [1.22, 1.60] |
| threshold 5 tol 240 | 1.05 [1.00, 1.13] inconclusive | 1.32 [1.16, 1.50] material | 1.57 [1.33, 1.85] | 1.33 [1.18, 1.52] |

Ratio of medians at the registered setting: perfect search 1.05 [1.01, 1.31]; perfect evidence as well 1.49 [1.19, 2.09].

## Outliers: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | 0.29 [0.08, 0.48] (88 periods) |
| without fallbacks | 0.39 [0.12, 0.64] (70 periods) |
| medians at most 1 | 0.27 [0.07, 0.46] (87 periods) |
| search right | 0.33 [0.13, 0.55] (35 periods) |
| search wrong | 0.20 [-0.33, 0.62] (53 periods) |
| flat prior search | 0.92 [0.68, 1.22] (88 periods) |
| ratio of log medians | 0.25 |

Refit fall-backs: 20 of 100; refits with a period median of 1 or more: 0.

## Outliers: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 188 | 106 | 0.56 | 255 | 2.55 | 59 | 0.78 / 0.37 |
| c2-refit | 188 | 78 | 0.41 | 226 | 2.26 | 40 | 0.62 / 0.26 |
| search3-flat | 188 | 66 | 0.35 | 108 | 1.08 | 32 | 0.53 / 0.26 |
| search2 | 188 | 51 | 0.27 | 82 | 0.82 | 28 | 0.44 / 0.15 |
| search3 | 188 | 53 | 0.28 | 67 | 0.67 | 30 | 0.44 / 0.19 |
| search3-mix | 188 | 53 | 0.28 | 66 | 0.66 | 30 | 0.44 / 0.19 |

## Outliers: periods with no true manoeuvre (3): share with one declared

| System | All | 0-30 min |
| --- | --- | --- |
| c2 | 0.33 [0.06, 0.79] | 0.33 (3) |
| c2-refit | 0.33 [0.06, 0.79] | 0.33 (3) |
| search3-flat | 0.33 [0.06, 0.79] | 0.33 (3) |
| search2 | 0.33 [0.06, 0.79] | 0.33 (3) |
| search3 | 0.33 [0.06, 0.79] | 0.33 (3) |
| search3-mix | 0.33 [0.06, 0.79] | 0.33 (3) |

## Outliers: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| c2-refit | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3-flat | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search2 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3 | 0.000 (28) | 0.000 (32) | 0.000 (22) |
| search3-mix | 0.000 (28) | 0.000 (32) | 0.000 (22) |

Candidates (repaired evidence, 100 periods): first right 0.410; true history in the first three 0.580; calibration gap 0.155; kinds differ among right 0.19.

Candidates (spec 014's evidence, 100 periods): first right 0.370; true history in the first three 0.580; calibration gap 0.129; kinds differ among right 0.27.

References held to the true times: 0.210; true-history fits with a consistent cost: 0.020; periods with a cut manoeuvre: 15 of 100.

## Whole: paired comparisons

| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |
| --- | --- | --- | --- | --- |
| c2 ÷ search3 | 3.44 [2.48, 4.79] | 3.04 [1.87, 4.78] | 0.20 | 0.55 / 0.02 |
| c2 ÷ c2-refit | 1.50 [1.14, 2.03] | 1.68 [0.83, 2.44] | 0.33 | 0.32 / 0.13 |
| c2-refit ÷ search3 | 2.30 [1.72, 3.14] | 1.81 [1.35, 3.85] | 0.23 | 0.40 / 0.02 |
| search3-flat ÷ search3 | 1.18 [0.94, 1.47] | 1.04 [0.82, 1.59] | 0.50 | 0.18 / 0.10 |
| search2 ÷ search3 | 1.05 [0.88, 1.24] | 0.95 [0.80, 1.33] | 0.17 | 0.12 / 0.07 |
| search3 ÷ search3-mix | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.00 | 0.00 / 0.00 |
| search3 ÷ history-best | 1.57 [1.22, 2.05] | 1.71 [1.10, 2.28] | 0.38 | 0.35 / 0.07 |
| search3 ÷ history-fixed | 1.87 [1.34, 2.54] | 2.21 [1.14, 2.82] | 0.28 | 0.48 / 0.13 |
| search3 ÷ one-leg | 0.04 [0.02, 0.07] | 0.08 [0.05, 0.12] | 0.97 | 0.03 / 0.90 |
| c2 ÷ one-leg | 0.13 [0.07, 0.23] | 0.24 [0.14, 0.37] | 0.82 | 0.05 / 0.73 |
| search3-mix ÷ one-leg | 0.04 [0.02, 0.07] | 0.08 [0.05, 0.12] | 0.97 | 0.03 / 0.90 |

## Whole: classes of wrong-history periods

| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |
| --- | --- | --- | --- | --- | --- | --- |
| scored | 60 | 0.48 [0.36, 0.61] | 31 | 0.32 [0.19, 0.50] | 0.26 [0.14, 0.43] | 0.42 [0.26, 0.59] |
| all | 60 | 0.48 [0.36, 0.61] | 31 | 0.32 [0.19, 0.50] | 0.26 [0.14, 0.43] | 0.42 [0.26, 0.59] |
| scored without cut | 55 | 0.49 [0.36, 0.62] | 28 | 0.36 [0.21, 0.54] | 0.25 [0.13, 0.43] | 0.39 [0.24, 0.58] |

## Whole: attainable headroom (search ÷ composite, paired)

| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |
| --- | --- | --- | --- | --- |
| threshold 1 tol 60 | 1.27 [1.11, 1.51] material | 1.35 [1.09, 1.70] inconclusive | 1.45 [1.15, 1.83] | 1.53 [1.31, 1.85] |
| threshold 1 tol 120 | 1.27 [1.11, 1.51] material | 1.38 [1.14, 1.69] material | 1.48 [1.20, 1.85] | 1.50 [1.28, 1.81] |
| threshold 1 tol 240 | 1.25 [1.10, 1.48] inconclusive | 1.30 [1.08, 1.60] inconclusive | 1.39 [1.14, 1.72] | 1.41 [1.21, 1.69] |
| threshold 3 tol 60 | 1.18 [1.05, 1.37] inconclusive | 1.19 [0.98, 1.47] inconclusive | 1.45 [1.15, 1.83] | 1.35 [1.17, 1.59] |
| threshold 3 tol 120 | 1.18 [1.05, 1.37] inconclusive | 1.22 [1.03, 1.48] inconclusive | 1.48 [1.20, 1.85] | 1.32 [1.15, 1.56] |
| registered | 1.18 [1.05, 1.37] inconclusive | 1.22 [1.03, 1.48] inconclusive | 1.48 [1.20, 1.85] | 1.32 [1.15, 1.56] |
| registered without flagged | 1.22 [1.06, 1.45] inconclusive | 1.19 [0.99, 1.46] inconclusive | 1.44 [1.14, 1.85] | 1.27 [1.10, 1.53] |
| threshold 3 tol 240 | 1.16 [1.04, 1.34] inconclusive | 1.16 [0.99, 1.39] inconclusive | 1.39 [1.14, 1.72] | 1.26 [1.11, 1.47] |
| threshold 5 tol 60 | 1.16 [1.04, 1.34] inconclusive | 1.19 [1.00, 1.43] inconclusive | 1.45 [1.15, 1.83] | 1.28 [1.11, 1.51] |
| threshold 5 tol 120 | 1.16 [1.04, 1.34] inconclusive | 1.21 [1.06, 1.43] inconclusive | 1.48 [1.20, 1.85] | 1.25 [1.10, 1.46] |
| threshold 5 tol 240 | 1.14 [1.02, 1.31] inconclusive | 1.20 [1.04, 1.41] inconclusive | 1.39 [1.14, 1.72] | 1.23 [1.08, 1.44] |

Ratio of medians at the registered setting: perfect search 1.30 [1.01, 1.75]; perfect evidence as well 1.40 [1.00, 1.75].

## Whole: the refit's share of the search's gain

| Estimand | Share |
| --- | --- |
| registered | 0.33 [0.11, 0.51] (60 periods) |
| without fallbacks | 0.34 [0.12, 0.54] (56 periods) |
| medians at most 1 | 0.33 [0.11, 0.51] (60 periods) |
| search right | 0.30 [0.02, 0.59] (29 periods) |
| search wrong | 0.36 [-0.02, 0.64] (31 periods) |
| flat prior search | 0.87 [0.70, 1.05] (60 periods) |
| ratio of log medians | 0.46 |

Refit fall-backs: 4 of 60; refits with a period median of 1 or more: 0.

## Whole: manoeuvre counts (120 s match; cut manoeuvres excluded)

| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2 | 199 | 113 | 0.57 | 97 | 1.62 | 59 | 0.78 / 0.37 |
| c2-refit | 199 | 79 | 0.40 | 63 | 1.05 | 25 | 0.54 / 0.30 |
| search3-flat | 199 | 48 | 0.24 | 35 | 0.58 | 18 | 0.33 / 0.16 |
| search2 | 199 | 35 | 0.18 | 35 | 0.58 | 16 | 0.28 / 0.14 |
| search3 | 199 | 40 | 0.20 | 29 | 0.48 | 16 | 0.29 / 0.15 |
| search3-mix | 199 | 40 | 0.20 | 29 | 0.48 | 16 | 0.29 / 0.15 |

## Whole: periods with no true manoeuvre (1): share with one declared

| System | All | 30-45 min |
| --- | --- | --- |
| c2 | 0.00 [0.00, 0.79] | 0.00 (1) |
| c2-refit | 0.00 [0.00, 0.79] | 0.00 (1) |
| search3-flat | 0.00 [0.00, 0.79] | 0.00 (1) |
| search2 | 1.00 [0.21, 1.00] | 1.00 (1) |
| search3 | 0.00 [0.00, 0.79] | 0.00 (1) |
| search3-mix | 0.00 [0.00, 0.79] | 0.00 (1) |

## Whole: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)

| System | 1 | 2 | 3 or more |
| --- | --- | --- | --- |
| c2 | 0.000 (2) | 0.000 (8) | 0.000 (44) |
| c2-refit | 0.000 (2) | 0.000 (8) | 0.000 (44) |
| search3-flat | 0.000 (2) | 0.000 (8) | 0.000 (44) |
| search2 | 0.000 (2) | 0.000 (8) | 0.000 (44) |
| search3 | 0.000 (2) | 0.000 (8) | 0.000 (44) |
| search3-mix | 0.000 (2) | 0.000 (8) | 0.000 (44) |

Candidates (repaired evidence, 60 periods): first right 0.483; true history in the first three 0.633; calibration gap 0.193; kinds differ among right 0.15.

Candidates (spec 014's evidence, 60 periods): first right 0.467; true history in the first three 0.600; calibration gap 0.117; kinds differ among right 0.12.

References held to the true times: 0.167; true-history fits with a consistent cost: 0.983; periods with a cut manoeuvre: 5 of 60.

## Soundness

Reference efficiency on tight rows 1.00 (band 0.8 to 1.3); consistent fits 1.000 (at least 0.9); references held 0.133 (at most 0.25): pass.
