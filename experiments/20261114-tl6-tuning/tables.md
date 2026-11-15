## Median period range error

| System | Annex B | Shifted | Shifted 2 | Held course | Outliers | Correlated |
| --- | --- | --- | --- | --- | --- | --- |
| Periods (scored) | 100 (89) | 150 (132) | 80 (73) | 80 (65) | 60 (51) | 60 (51) |
| `ada` | 0.039 | 0.114 | 0.032 | 0.017 | 0.047 | 0.087 |
| `ada-a0.5` | 0.041 | 0.116 | 0.032 | 0.014 | 0.042 | 0.087 |
| `ada-a0.8` | 0.041 | 0.098 | 0.030 | 0.017 | 0.034 | 0.079 |
| `ada-d1-q0.01` | 0.039 | 0.116 | 0.033 | 0.014 | 0.047 | 0.087 |
| `ada-h1` | 0.041 | 0.098 | 0.030 | 0.019 | 0.034 | 0.078 |
| `c2` | 0.088 | 0.153 | 0.093 | 0.013 | 0.224 | 0.394 |
| `ctl-d1-q0.01` | 0.040 | 0.105 | 0.033 | 0.013 | 0.031 | 0.078 |
| `ctl-h1` | 0.037 | 0.098 | 0.029 | 0.028 | 0.033 | 0.081 |
| `one-leg` | 0.439 | 0.312 | 0.370 | 0.013 | 0.256 | 0.272 |
| `ref-full` | 0.025 | 0.042 | 0.018 | 0.012 | 0.039 | 0.087 |
| `true` | 0.033 | 0.084 | 0.031 | – | 0.031 | 0.085 |

## Paired comparisons (a ÷ b per period; above 1: b is better)

### Annex B

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 89 | 1.01 [0.92, 1.12] | 1.00 | 0.03 | 0.06 |
| `ada-d1-q0.01` | `ada-h1` | course | 89 | 0.90 [0.77, 1.05] | 1.00 | 0.06 | 0.13 |
| `ada-d1-q0.01` | `ada-h1` | speed | 89 | 0.94 [0.82, 1.07] | 1.00 | 0.04 | 0.07 |
| `ada-d1-q0.01` | `ref-full` | range | 89 | 1.74 [1.22, 2.40] | 1.80 | 0.46 | 0.16 |
| `ada-d1-q0.01` | `ref-full` | course | 89 | 1.85 [1.29, 2.53] | 1.84 | 0.44 | 0.12 |
| `ada-d1-q0.01` | `ref-full` | speed | 89 | 1.77 [1.25, 2.48] | 1.74 | 0.44 | 0.16 |
| `ada-d1-q0.01` | `true` | range | 89 | 1.13 [0.95, 1.36] | 1.00 | 0.12 | 0.11 |
| `ada-d1-q0.01` | `true` | course | 89 | 1.22 [0.95, 1.58] | 1.07 | 0.24 | 0.15 |
| `ada-d1-q0.01` | `true` | speed | 89 | 1.10 [0.87, 1.37] | 1.00 | 0.19 | 0.20 |
| `ada-h1` | `ref-full` | range | 89 | 1.72 [1.20, 2.40] | 1.99 | 0.49 | 0.16 |
| `ada-h1` | `ref-full` | course | 89 | 2.06 [1.48, 2.77] | 1.88 | 0.48 | 0.12 |
| `ada-h1` | `ref-full` | speed | 89 | 1.88 [1.30, 2.67] | 2.00 | 0.51 | 0.16 |
| `c2` | `ctl-d1-q0.01` | range | 89 | 2.21 [1.67, 2.97] | 1.86 | 0.48 | 0.08 |
| `c2` | `ctl-d1-q0.01` | course | 89 | 2.65 [1.94, 3.65] | 2.35 | 0.55 | 0.08 |
| `c2` | `ctl-d1-q0.01` | speed | 89 | 2.41 [1.74, 3.36] | 1.88 | 0.48 | 0.16 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 89 | 0.96 [0.81, 1.11] | 1.00 | 0.10 | 0.09 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 89 | 0.90 [0.73, 1.09] | 0.98 | 0.12 | 0.19 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 89 | 0.88 [0.73, 1.05] | 1.00 | 0.12 | 0.18 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 89 | 0.95 [0.81, 1.10] | 1.00 | 0.10 | 0.11 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 89 | 0.88 [0.71, 1.09] | 0.98 | 0.11 | 0.19 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 89 | 0.91 [0.75, 1.09] | 1.00 | 0.13 | 0.19 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 89 | 0.95 [0.80, 1.11] | 1.00 | 0.10 | 0.09 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 89 | 0.93 [0.73, 1.16] | 1.00 | 0.13 | 0.18 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 89 | 0.96 [0.79, 1.14] | 1.00 | 0.16 | 0.13 |
| `ctl-d1-q0.01` | `ada-h1` | range | 89 | 0.95 [0.81, 1.12] | 1.00 | 0.10 | 0.11 |
| `ctl-d1-q0.01` | `ada-h1` | course | 89 | 0.84 [0.69, 1.02] | 0.95 | 0.10 | 0.20 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 89 | 0.90 [0.75, 1.08] | 1.00 | 0.12 | 0.19 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 89 | 0.96 [0.89, 1.05] | 1.00 | 0.02 | 0.08 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 89 | 0.94 [0.84, 1.06] | 1.00 | 0.06 | 0.07 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 89 | 1.03 [0.94, 1.12] | 1.00 | 0.02 | 0.03 |
| `ctl-d1-q0.01` | `ref-full` | range | 89 | 1.64 [1.17, 2.25] | 1.62 | 0.42 | 0.13 |
| `ctl-d1-q0.01` | `ref-full` | course | 89 | 1.72 [1.25, 2.34] | 1.55 | 0.37 | 0.12 |
| `ctl-d1-q0.01` | `ref-full` | speed | 89 | 1.69 [1.20, 2.34] | 1.63 | 0.45 | 0.17 |
| `ctl-d1-q0.01` | `true` | range | 89 | 1.07 [0.98, 1.18] | 1.00 | 0.06 | 0.02 |
| `ctl-d1-q0.01` | `true` | course | 89 | 1.14 [1.02, 1.30] | 1.00 | 0.07 | 0.02 |
| `ctl-d1-q0.01` | `true` | speed | 89 | 1.05 [0.93, 1.20] | 1.00 | 0.07 | 0.06 |
| `ctl-h1` | `ada-h1` | range | 89 | 0.99 [0.87, 1.13] | 0.99 | 0.09 | 0.07 |
| `ctl-h1` | `ada-h1` | course | 89 | 0.89 [0.74, 1.05] | 0.96 | 0.10 | 0.22 |
| `ctl-h1` | `ada-h1` | speed | 89 | 0.88 [0.74, 1.03] | 0.99 | 0.09 | 0.19 |

### Shifted

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 132 | 1.11 [1.03, 1.19] | 1.04 | 0.06 | 0.04 |
| `ada-d1-q0.01` | `ada-h1` | course | 132 | 1.08 [0.98, 1.21] | 1.04 | 0.07 | 0.06 |
| `ada-d1-q0.01` | `ada-h1` | speed | 132 | 1.14 [1.02, 1.27] | 1.07 | 0.12 | 0.05 |
| `ada-d1-q0.01` | `ref-full` | range | 132 | 2.70 [2.18, 3.32] | 2.44 | 0.58 | 0.08 |
| `ada-d1-q0.01` | `ref-full` | course | 132 | 3.10 [2.43, 3.94] | 3.03 | 0.61 | 0.10 |
| `ada-d1-q0.01` | `ref-full` | speed | 132 | 3.03 [2.28, 3.99] | 2.91 | 0.60 | 0.12 |
| `ada-d1-q0.01` | `true` | range | 132 | 1.27 [1.06, 1.51] | 1.16 | 0.24 | 0.13 |
| `ada-d1-q0.01` | `true` | course | 132 | 1.40 [1.14, 1.75] | 1.09 | 0.26 | 0.15 |
| `ada-d1-q0.01` | `true` | speed | 132 | 1.39 [1.13, 1.71] | 1.09 | 0.28 | 0.16 |
| `ada-h1` | `ref-full` | range | 132 | 2.43 [1.98, 3.00] | 2.16 | 0.52 | 0.09 |
| `ada-h1` | `ref-full` | course | 132 | 2.87 [2.22, 3.73] | 2.79 | 0.59 | 0.07 |
| `ada-h1` | `ref-full` | speed | 132 | 2.66 [1.98, 3.57] | 2.29 | 0.55 | 0.14 |
| `c2` | `ctl-d1-q0.01` | range | 132 | 1.56 [1.27, 1.89] | 1.47 | 0.39 | 0.13 |
| `c2` | `ctl-d1-q0.01` | course | 132 | 1.72 [1.39, 2.11] | 1.62 | 0.42 | 0.11 |
| `c2` | `ctl-d1-q0.01` | speed | 132 | 1.39 [1.05, 1.78] | 1.17 | 0.34 | 0.20 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 132 | 1.03 [0.92, 1.16] | 1.00 | 0.12 | 0.10 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 132 | 0.94 [0.82, 1.09] | 1.00 | 0.13 | 0.14 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 132 | 1.03 [0.90, 1.19] | 1.00 | 0.17 | 0.11 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 132 | 1.09 [0.98, 1.23] | 1.04 | 0.13 | 0.08 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 132 | 0.95 [0.82, 1.11] | 1.00 | 0.14 | 0.14 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 132 | 1.14 [0.98, 1.33] | 1.01 | 0.18 | 0.11 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 132 | 0.99 [0.88, 1.11] | 1.00 | 0.11 | 0.11 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 132 | 0.88 [0.77, 1.00] | 1.00 | 0.09 | 0.14 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 132 | 0.99 [0.87, 1.15] | 1.00 | 0.15 | 0.13 |
| `ctl-d1-q0.01` | `ada-h1` | range | 132 | 1.09 [0.98, 1.23] | 1.06 | 0.11 | 0.07 |
| `ctl-d1-q0.01` | `ada-h1` | course | 132 | 0.95 [0.82, 1.12] | 1.01 | 0.13 | 0.14 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 132 | 1.13 [0.97, 1.32] | 1.03 | 0.18 | 0.12 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 132 | 1.05 [0.99, 1.12] | 1.02 | 0.05 | 0.03 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 132 | 1.06 [0.97, 1.16] | 1.00 | 0.06 | 0.05 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 132 | 1.03 [0.92, 1.12] | 1.01 | 0.07 | 0.04 |
| `ctl-d1-q0.01` | `ref-full` | range | 132 | 2.66 [2.19, 3.26] | 2.72 | 0.58 | 0.05 |
| `ctl-d1-q0.01` | `ref-full` | course | 132 | 2.73 [2.14, 3.52] | 2.49 | 0.55 | 0.08 |
| `ctl-d1-q0.01` | `ref-full` | speed | 132 | 3.01 [2.29, 3.95] | 2.57 | 0.60 | 0.10 |
| `ctl-d1-q0.01` | `true` | range | 132 | 1.25 [1.07, 1.49] | 1.06 | 0.23 | 0.15 |
| `ctl-d1-q0.01` | `true` | course | 132 | 1.24 [1.02, 1.51] | 1.07 | 0.21 | 0.13 |
| `ctl-d1-q0.01` | `true` | speed | 132 | 1.38 [1.11, 1.71] | 1.07 | 0.23 | 0.14 |
| `ctl-h1` | `ada-h1` | range | 132 | 1.04 [0.94, 1.15] | 0.97 | 0.11 | 0.05 |
| `ctl-h1` | `ada-h1` | course | 132 | 0.90 [0.76, 1.04] | 0.98 | 0.12 | 0.12 |
| `ctl-h1` | `ada-h1` | speed | 132 | 1.10 [0.95, 1.28] | 1.00 | 0.20 | 0.12 |

### Shifted 2

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 73 | 1.00 [0.94, 1.07] | 1.00 | 0.03 | 0.01 |
| `ada-d1-q0.01` | `ada-h1` | course | 73 | 0.97 [0.87, 1.07] | 1.00 | 0.04 | 0.04 |
| `ada-d1-q0.01` | `ada-h1` | speed | 73 | 1.01 [0.91, 1.12] | 1.00 | 0.07 | 0.04 |
| `ada-d1-q0.01` | `ref-full` | range | 73 | 1.59 [1.15, 2.22] | 1.66 | 0.38 | 0.14 |
| `ada-d1-q0.01` | `ref-full` | course | 73 | 1.43 [0.97, 1.99] | 1.49 | 0.40 | 0.10 |
| `ada-d1-q0.01` | `ref-full` | speed | 73 | 2.07 [1.45, 3.05] | 1.78 | 0.45 | 0.14 |
| `ada-d1-q0.01` | `true` | range | 73 | 0.98 [0.86, 1.14] | 1.00 | 0.05 | 0.08 |
| `ada-d1-q0.01` | `true` | course | 73 | 0.96 [0.84, 1.11] | 1.00 | 0.05 | 0.10 |
| `ada-d1-q0.01` | `true` | speed | 73 | 1.18 [0.89, 1.71] | 1.00 | 0.11 | 0.08 |
| `ada-h1` | `ref-full` | range | 73 | 1.59 [1.14, 2.20] | 1.61 | 0.36 | 0.14 |
| `ada-h1` | `ref-full` | course | 73 | 1.48 [1.00, 2.05] | 1.67 | 0.44 | 0.10 |
| `ada-h1` | `ref-full` | speed | 73 | 2.06 [1.42, 3.05] | 1.78 | 0.47 | 0.12 |
| `c2` | `ctl-d1-q0.01` | range | 73 | 2.37 [1.72, 3.26] | 1.83 | 0.47 | 0.10 |
| `c2` | `ctl-d1-q0.01` | course | 73 | 3.01 [2.12, 4.38] | 2.12 | 0.51 | 0.08 |
| `c2` | `ctl-d1-q0.01` | speed | 73 | 2.67 [1.91, 3.84] | 2.03 | 0.51 | 0.10 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 73 | 1.06 [0.98, 1.16] | 1.00 | 0.03 | 0.00 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 73 | 1.05 [0.95, 1.18] | 1.00 | 0.05 | 0.03 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 73 | 1.05 [0.90, 1.20] | 1.00 | 0.07 | 0.05 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 73 | 1.06 [0.97, 1.17] | 1.00 | 0.04 | 0.01 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 73 | 1.00 [0.91, 1.11] | 1.00 | 0.04 | 0.04 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 73 | 1.02 [0.89, 1.15] | 1.00 | 0.07 | 0.05 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 73 | 1.05 [0.97, 1.15] | 1.00 | 0.04 | 0.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 73 | 1.02 [0.92, 1.14] | 1.00 | 0.05 | 0.04 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 73 | 1.01 [0.87, 1.17] | 1.00 | 0.05 | 0.05 |
| `ctl-d1-q0.01` | `ada-h1` | range | 73 | 1.05 [0.96, 1.16] | 1.00 | 0.04 | 0.03 |
| `ctl-d1-q0.01` | `ada-h1` | course | 73 | 0.99 [0.86, 1.14] | 1.00 | 0.05 | 0.07 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 73 | 1.02 [0.88, 1.17] | 1.00 | 0.11 | 0.07 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 73 | 1.07 [1.00, 1.17] | 1.01 | 0.03 | 0.01 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 73 | 0.99 [0.88, 1.09] | 1.00 | 0.04 | 0.03 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 73 | 1.06 [0.94, 1.22] | 1.00 | 0.04 | 0.05 |
| `ctl-d1-q0.01` | `ref-full` | range | 73 | 1.68 [1.22, 2.32] | 1.82 | 0.42 | 0.14 |
| `ctl-d1-q0.01` | `ref-full` | course | 73 | 1.46 [1.01, 2.07] | 1.49 | 0.40 | 0.11 |
| `ctl-d1-q0.01` | `ref-full` | speed | 73 | 2.09 [1.42, 3.09] | 1.76 | 0.47 | 0.15 |
| `ctl-d1-q0.01` | `true` | range | 73 | 1.03 [0.90, 1.19] | 1.00 | 0.08 | 0.08 |
| `ctl-d1-q0.01` | `true` | course | 73 | 0.99 [0.82, 1.16] | 1.00 | 0.10 | 0.08 |
| `ctl-d1-q0.01` | `true` | speed | 73 | 1.19 [0.88, 1.71] | 1.00 | 0.11 | 0.12 |
| `ctl-h1` | `ada-h1` | range | 73 | 0.98 [0.89, 1.10] | 1.01 | 0.03 | 0.07 |
| `ctl-h1` | `ada-h1` | course | 73 | 1.00 [0.88, 1.13] | 0.99 | 0.07 | 0.07 |
| `ctl-h1` | `ada-h1` | speed | 73 | 0.96 [0.82, 1.11] | 1.02 | 0.08 | 0.08 |

### Held course

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 65 | 0.94 [0.78, 1.12] | 1.00 | 0.09 | 0.11 |
| `ada-d1-q0.01` | `ada-h1` | course | 65 | 0.95 [0.76, 1.18] | 1.00 | 0.11 | 0.14 |
| `ada-d1-q0.01` | `ada-h1` | speed | 65 | 0.84 [0.67, 1.03] | 1.00 | 0.09 | 0.17 |
| `ada-d1-q0.01` | `ref-full` | range | 65 | 1.06 [0.95, 1.26] | 1.00 | 0.03 | 0.02 |
| `ada-d1-q0.01` | `ref-full` | course | 65 | 1.01 [0.95, 1.08] | 1.00 | 0.03 | 0.02 |
| `ada-d1-q0.01` | `ref-full` | speed | 65 | 1.11 [1.00, 1.31] | 1.00 | 0.05 | 0.00 |
| `ada-h1` | `ref-full` | range | 65 | 1.13 [0.91, 1.44] | 1.00 | 0.14 | 0.11 |
| `ada-h1` | `ref-full` | course | 65 | 1.07 [0.86, 1.34] | 1.00 | 0.15 | 0.12 |
| `ada-h1` | `ref-full` | speed | 65 | 1.32 [1.04, 1.75] | 1.01 | 0.20 | 0.09 |
| `c2` | `ctl-d1-q0.01` | range | 65 | 1.03 [0.89, 1.21] | 1.00 | 0.09 | 0.06 |
| `c2` | `ctl-d1-q0.01` | course | 65 | 0.76 [0.58, 0.99] | 0.96 | 0.08 | 0.20 |
| `c2` | `ctl-d1-q0.01` | speed | 65 | 1.07 [0.88, 1.31] | 1.00 | 0.15 | 0.11 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 65 | 0.94 [0.76, 1.11] | 1.00 | 0.08 | 0.05 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 65 | 0.96 [0.86, 1.07] | 1.00 | 0.02 | 0.05 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 65 | 0.86 [0.72, 0.99] | 1.00 | 0.00 | 0.06 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 65 | 0.84 [0.67, 1.01] | 1.00 | 0.09 | 0.12 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 65 | 0.92 [0.74, 1.14] | 1.00 | 0.08 | 0.14 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 65 | 0.72 [0.57, 0.88] | 1.00 | 0.02 | 0.17 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 65 | 0.91 [0.75, 1.04] | 1.00 | 0.03 | 0.05 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 65 | 0.98 [0.89, 1.09] | 1.00 | 0.03 | 0.05 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 65 | 0.88 [0.73, 1.00] | 1.00 | 0.00 | 0.05 |
| `ctl-d1-q0.01` | `ada-h1` | range | 65 | 0.85 [0.67, 1.04] | 1.00 | 0.11 | 0.14 |
| `ctl-d1-q0.01` | `ada-h1` | course | 65 | 0.93 [0.75, 1.16] | 1.00 | 0.09 | 0.15 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 65 | 0.74 [0.57, 0.93] | 0.99 | 0.08 | 0.20 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 65 | 0.64 [0.49, 0.80] | 0.87 | 0.03 | 0.28 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 65 | 0.66 [0.48, 0.88] | 0.92 | 0.06 | 0.26 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 65 | 0.60 [0.43, 0.82] | 0.83 | 0.08 | 0.32 |
| `ctl-d1-q0.01` | `ref-full` | range | 65 | 0.96 [0.85, 1.08] | 1.00 | 0.03 | 0.05 |
| `ctl-d1-q0.01` | `ref-full` | course | 65 | 1.00 [0.90, 1.10] | 1.00 | 0.03 | 0.03 |
| `ctl-d1-q0.01` | `ref-full` | speed | 65 | 0.98 [0.85, 1.11] | 1.00 | 0.02 | 0.03 |
| `ctl-h1` | `ada-h1` | range | 65 | 1.34 [1.12, 1.64] | 1.03 | 0.20 | 0.05 |
| `ctl-h1` | `ada-h1` | course | 65 | 1.41 [1.14, 1.78] | 1.07 | 0.25 | 0.05 |
| `ctl-h1` | `ada-h1` | speed | 65 | 1.23 [0.97, 1.54] | 1.00 | 0.25 | 0.08 |

### Outliers

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 51 | 1.11 [0.92, 1.33] | 1.00 | 0.12 | 0.06 |
| `ada-d1-q0.01` | `ada-h1` | course | 51 | 0.95 [0.70, 1.27] | 1.00 | 0.12 | 0.18 |
| `ada-d1-q0.01` | `ada-h1` | speed | 51 | 0.94 [0.71, 1.20] | 1.00 | 0.12 | 0.14 |
| `ada-d1-q0.01` | `ref-full` | range | 51 | 0.78 [0.50, 1.19] | 0.79 | 0.18 | 0.31 |
| `ada-d1-q0.01` | `ref-full` | course | 51 | 0.98 [0.61, 1.55] | 0.96 | 0.27 | 0.31 |
| `ada-d1-q0.01` | `ref-full` | speed | 51 | 0.84 [0.55, 1.28] | 0.86 | 0.25 | 0.35 |
| `ada-d1-q0.01` | `true` | range | 51 | 0.98 [0.77, 1.26] | 1.00 | 0.12 | 0.16 |
| `ada-d1-q0.01` | `true` | course | 51 | 1.24 [0.83, 1.99] | 1.00 | 0.20 | 0.18 |
| `ada-d1-q0.01` | `true` | speed | 51 | 0.96 [0.71, 1.32] | 0.99 | 0.10 | 0.14 |
| `ada-h1` | `ref-full` | range | 51 | 0.70 [0.46, 1.05] | 0.70 | 0.16 | 0.39 |
| `ada-h1` | `ref-full` | course | 51 | 1.04 [0.70, 1.53] | 0.94 | 0.33 | 0.33 |
| `ada-h1` | `ref-full` | speed | 51 | 0.90 [0.61, 1.33] | 0.90 | 0.25 | 0.33 |
| `c2` | `ctl-d1-q0.01` | range | 51 | 5.57 [3.60, 8.45] | 5.91 | 0.69 | 0.08 |
| `c2` | `ctl-d1-q0.01` | course | 51 | 8.79 [5.34, 15.27] | 6.02 | 0.76 | 0.04 |
| `c2` | `ctl-d1-q0.01` | speed | 51 | 4.12 [2.67, 6.21] | 3.07 | 0.65 | 0.08 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 51 | 0.95 [0.73, 1.23] | 1.00 | 0.12 | 0.16 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 51 | 0.71 [0.46, 1.01] | 1.00 | 0.14 | 0.24 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 51 | 0.82 [0.61, 1.09] | 1.00 | 0.12 | 0.20 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 51 | 1.08 [0.81, 1.43] | 1.00 | 0.16 | 0.18 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 51 | 0.83 [0.56, 1.21] | 1.00 | 0.18 | 0.27 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 51 | 0.94 [0.69, 1.28] | 1.00 | 0.14 | 0.20 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 51 | 0.98 [0.77, 1.25] | 1.00 | 0.14 | 0.16 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 51 | 0.78 [0.49, 1.13] | 1.00 | 0.16 | 0.18 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 51 | 1.01 [0.74, 1.37] | 1.00 | 0.16 | 0.14 |
| `ctl-d1-q0.01` | `ada-h1` | range | 51 | 1.08 [0.81, 1.43] | 1.03 | 0.14 | 0.18 |
| `ctl-d1-q0.01` | `ada-h1` | course | 51 | 0.74 [0.49, 1.09] | 0.97 | 0.16 | 0.33 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 51 | 0.95 [0.69, 1.30] | 0.99 | 0.14 | 0.20 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 51 | 0.94 [0.81, 1.08] | 1.00 | 0.02 | 0.10 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 51 | 0.89 [0.71, 1.11] | 1.00 | 0.04 | 0.16 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 51 | 0.96 [0.73, 1.30] | 1.00 | 0.04 | 0.10 |
| `ctl-d1-q0.01` | `ref-full` | range | 51 | 0.76 [0.48, 1.17] | 0.86 | 0.24 | 0.33 |
| `ctl-d1-q0.01` | `ref-full` | course | 51 | 0.76 [0.45, 1.24] | 0.75 | 0.33 | 0.37 |
| `ctl-d1-q0.01` | `ref-full` | speed | 51 | 0.85 [0.54, 1.33] | 0.89 | 0.27 | 0.33 |
| `ctl-d1-q0.01` | `true` | range | 51 | 0.96 [0.89, 1.02] | 1.00 | 0.00 | 0.04 |
| `ctl-d1-q0.01` | `true` | course | 51 | 0.96 [0.88, 1.04] | 1.00 | 0.04 | 0.02 |
| `ctl-d1-q0.01` | `true` | speed | 51 | 0.97 [0.84, 1.15] | 1.00 | 0.04 | 0.04 |
| `ctl-h1` | `ada-h1` | range | 51 | 1.15 [0.92, 1.45] | 1.14 | 0.16 | 0.10 |
| `ctl-h1` | `ada-h1` | course | 51 | 0.83 [0.63, 1.10] | 0.99 | 0.14 | 0.22 |
| `ctl-h1` | `ada-h1` | speed | 51 | 0.99 [0.74, 1.29] | 1.13 | 0.18 | 0.16 |

### Correlated

| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `ada-h1` | range | 51 | 1.09 [0.94, 1.27] | 1.00 | 0.12 | 0.04 |
| `ada-d1-q0.01` | `ada-h1` | course | 51 | 0.90 [0.73, 1.10] | 1.00 | 0.06 | 0.12 |
| `ada-d1-q0.01` | `ada-h1` | speed | 51 | 1.13 [0.92, 1.41] | 1.00 | 0.16 | 0.10 |
| `ada-d1-q0.01` | `ref-full` | range | 51 | 1.31 [1.05, 1.62] | 1.24 | 0.25 | 0.08 |
| `ada-d1-q0.01` | `ref-full` | course | 51 | 1.73 [1.13, 2.60] | 2.08 | 0.51 | 0.18 |
| `ada-d1-q0.01` | `ref-full` | speed | 51 | 1.48 [1.07, 2.08] | 1.42 | 0.31 | 0.18 |
| `ada-d1-q0.01` | `true` | range | 51 | 1.04 [0.85, 1.28] | 1.00 | 0.14 | 0.12 |
| `ada-d1-q0.01` | `true` | course | 51 | 1.19 [0.90, 1.60] | 1.00 | 0.24 | 0.10 |
| `ada-d1-q0.01` | `true` | speed | 51 | 1.09 [0.85, 1.42] | 1.00 | 0.12 | 0.12 |
| `ada-h1` | `ref-full` | range | 51 | 1.20 [0.96, 1.51] | 1.06 | 0.24 | 0.14 |
| `ada-h1` | `ref-full` | course | 51 | 1.93 [1.37, 2.72] | 1.83 | 0.49 | 0.12 |
| `ada-h1` | `ref-full` | speed | 51 | 1.31 [0.92, 1.95] | 1.02 | 0.31 | 0.25 |
| `c2` | `ctl-d1-q0.01` | range | 51 | 3.60 [2.52, 5.31] | 3.33 | 0.65 | 0.06 |
| `c2` | `ctl-d1-q0.01` | course | 51 | 3.95 [2.54, 6.25] | 3.36 | 0.63 | 0.08 |
| `c2` | `ctl-d1-q0.01` | speed | 51 | 3.46 [2.07, 5.96] | 2.74 | 0.59 | 0.16 |
| `ctl-d1-q0.01` | `ada-a0.5` | range | 51 | 0.97 [0.82, 1.13] | 1.00 | 0.04 | 0.06 |
| `ctl-d1-q0.01` | `ada-a0.5` | course | 51 | 1.02 [0.81, 1.33] | 1.00 | 0.12 | 0.16 |
| `ctl-d1-q0.01` | `ada-a0.5` | speed | 51 | 0.90 [0.67, 1.16] | 1.00 | 0.12 | 0.14 |
| `ctl-d1-q0.01` | `ada-a0.8` | range | 51 | 1.03 [0.86, 1.22] | 1.01 | 0.04 | 0.08 |
| `ctl-d1-q0.01` | `ada-a0.8` | course | 51 | 1.00 [0.80, 1.29] | 1.00 | 0.14 | 0.12 |
| `ctl-d1-q0.01` | `ada-a0.8` | speed | 51 | 0.94 [0.70, 1.23] | 1.00 | 0.18 | 0.18 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | range | 51 | 0.97 [0.80, 1.16] | 1.00 | 0.08 | 0.10 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | course | 51 | 1.05 [0.83, 1.37] | 1.00 | 0.12 | 0.18 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | speed | 51 | 0.86 [0.66, 1.10] | 1.00 | 0.08 | 0.14 |
| `ctl-d1-q0.01` | `ada-h1` | range | 51 | 1.05 [0.87, 1.26] | 1.02 | 0.06 | 0.08 |
| `ctl-d1-q0.01` | `ada-h1` | course | 51 | 0.94 [0.75, 1.20] | 0.95 | 0.14 | 0.14 |
| `ctl-d1-q0.01` | `ada-h1` | speed | 51 | 0.97 [0.71, 1.30] | 0.99 | 0.22 | 0.18 |
| `ctl-d1-q0.01` | `ctl-h1` | range | 51 | 1.01 [0.89, 1.14] | 1.00 | 0.06 | 0.06 |
| `ctl-d1-q0.01` | `ctl-h1` | course | 51 | 0.99 [0.86, 1.12] | 1.00 | 0.06 | 0.02 |
| `ctl-d1-q0.01` | `ctl-h1` | speed | 51 | 1.01 [0.76, 1.35] | 1.00 | 0.16 | 0.14 |
| `ctl-d1-q0.01` | `ref-full` | range | 51 | 1.27 [0.99, 1.63] | 1.24 | 0.25 | 0.10 |
| `ctl-d1-q0.01` | `ref-full` | course | 51 | 1.81 [1.22, 2.73] | 1.43 | 0.45 | 0.12 |
| `ctl-d1-q0.01` | `ref-full` | speed | 51 | 1.28 [0.84, 1.90] | 1.47 | 0.27 | 0.20 |
| `ctl-d1-q0.01` | `true` | range | 51 | 1.01 [0.88, 1.18] | 1.00 | 0.04 | 0.08 |
| `ctl-d1-q0.01` | `true` | course | 51 | 1.24 [1.02, 1.63] | 1.00 | 0.10 | 0.00 |
| `ctl-d1-q0.01` | `true` | speed | 51 | 0.94 [0.79, 1.10] | 1.00 | 0.04 | 0.08 |
| `ctl-h1` | `ada-h1` | range | 51 | 1.04 [0.87, 1.23] | 0.97 | 0.12 | 0.08 |
| `ctl-h1` | `ada-h1` | course | 51 | 0.95 [0.82, 1.11] | 0.97 | 0.08 | 0.08 |
| `ctl-h1` | `ada-h1` | speed | 51 | 0.97 [0.74, 1.21] | 1.01 | 0.16 | 0.10 |

## The adaptive control's share of the true-prior search's gain over the control

| Split | Range | Course | Speed |
| --- | --- | --- | --- |
| Annex B | -0.85 [-13.21, 11.57] | -0.54 [-5.86, 1.77] | -0.94 [-15.24, 15.54] |
| Shifted | -0.06 [-1.00, 0.48] | -0.58 [-3.44, 0.11] | -0.02 [-0.91, 0.39] |
| Shifted 2 | 1.56 [-10.30, 11.10] | -1.52 [-7.95, 9.22] | 0.06 [-2.87, 3.15] |
| Outliers | 0.55 [-18.97, 21.08] | 6.26 [-69.55, 88.82] | -0.57 [-25.59, 20.71] |
| Correlated | -4.40 [-17.38, 17.98] | 0.21 [-3.19, 2.31] | 2.35 [-16.74, 21.62] |

## Members chosen by groups of periods (a ÷ b per period; above 1: b is better)

(a group is a run of consecutive periods of the split taken to share their statistics; it uses the member with the most summed log evidence)

## Each fixed member: control ÷ member (range) and its mean log evidence


## By kind of period (range; a ÷ b)

### Annex B

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `true` | control misses a detectable manoeuvre | 12 | 0.88 [0.47, 1.63] | 0.81 |
| `ada-d1-q0.01` | `true` | control misses none | 77 | 1.17 [0.99, 1.42] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: tight third | 30 | 1.19 [0.96, 1.57] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: middle third | 29 | 0.97 [0.72, 1.27] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: loose third | 30 | 1.24 [0.85, 1.85] | 1.02 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses a detectable manoeuvre | 12 | 0.91 [0.50, 1.82] | 0.87 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 77 | 0.95 [0.81, 1.11] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 30 | 0.84 [0.64, 1.03] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 29 | 0.99 [0.76, 1.35] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 30 | 1.02 [0.74, 1.40] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | control misses a detectable manoeuvre | 12 | 0.87 [0.58, 1.26] | 0.98 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 77 | 0.97 [0.81, 1.15] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 30 | 0.89 [0.68, 1.19] | 0.95 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 29 | 0.91 [0.70, 1.18] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 30 | 1.07 [0.80, 1.43] | 1.04 |
| `ctl-d1-q0.01` | `true` | control misses a detectable manoeuvre | 12 | 0.80 [0.63, 0.98] | 1.00 |
| `ctl-d1-q0.01` | `true` | control misses none | 77 | 1.12 [1.03, 1.24] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: tight third | 30 | 1.00 [0.97, 1.02] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: middle third | 29 | 0.96 [0.84, 1.09] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: loose third | 30 | 1.27 [1.04, 1.64] | 1.00 |

### Shifted

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `true` | control misses a detectable manoeuvre | 40 | 1.81 [1.33, 2.56] | 1.33 |
| `ada-d1-q0.01` | `true` | control misses none | 92 | 1.09 [0.89, 1.33] | 1.08 |
| `ada-d1-q0.01` | `true` | bound: tight third | 44 | 1.50 [1.15, 2.07] | 1.15 |
| `ada-d1-q0.01` | `true` | bound: middle third | 44 | 1.30 [0.98, 1.70] | 1.28 |
| `ada-d1-q0.01` | `true` | bound: loose third | 44 | 1.06 [0.76, 1.48] | 1.01 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses a detectable manoeuvre | 40 | 1.14 [0.98, 1.35] | 1.01 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 92 | 0.92 [0.80, 1.06] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 44 | 0.89 [0.74, 1.10] | 0.99 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 44 | 1.00 [0.84, 1.16] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 44 | 1.08 [0.87, 1.34] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | control misses a detectable manoeuvre | 40 | 1.27 [1.06, 1.54] | 1.13 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 92 | 1.02 [0.89, 1.17] | 1.03 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 44 | 1.01 [0.83, 1.26] | 1.02 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 44 | 1.08 [0.89, 1.31] | 1.07 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 44 | 1.19 [0.97, 1.46] | 1.10 |
| `ctl-d1-q0.01` | `true` | control misses a detectable manoeuvre | 40 | 2.07 [1.50, 2.89] | 1.84 |
| `ctl-d1-q0.01` | `true` | control misses none | 92 | 1.01 [0.85, 1.19] | 1.02 |
| `ctl-d1-q0.01` | `true` | bound: tight third | 44 | 1.33 [1.00, 1.85] | 1.11 |
| `ctl-d1-q0.01` | `true` | bound: middle third | 44 | 1.29 [0.99, 1.71] | 1.08 |
| `ctl-d1-q0.01` | `true` | bound: loose third | 44 | 1.15 [0.86, 1.54] | 1.01 |

### Shifted 2

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `true` | control misses a detectable manoeuvre | 6 | 1.48 [0.99, 2.52] | 1.06 |
| `ada-d1-q0.01` | `true` | control misses none | 67 | 0.95 [0.82, 1.10] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: tight third | 25 | 0.88 [0.69, 1.04] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: middle third | 24 | 1.12 [0.96, 1.36] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: loose third | 24 | 0.97 [0.71, 1.38] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses a detectable manoeuvre | 6 | 1.03 [0.78, 1.36] | 1.02 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 67 | 1.06 [0.98, 1.16] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 25 | 1.09 [0.96, 1.33] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 24 | 1.03 [0.93, 1.14] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 24 | 1.04 [0.91, 1.23] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | control misses a detectable manoeuvre | 6 | 1.06 [0.93, 1.16] | 1.10 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 67 | 1.05 [0.95, 1.18] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 25 | 1.08 [0.94, 1.35] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 24 | 1.00 [0.88, 1.11] | 1.03 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 24 | 1.07 [0.90, 1.31] | 1.01 |
| `ctl-d1-q0.01` | `true` | control misses a detectable manoeuvre | 6 | 1.52 [1.12, 2.17] | 1.46 |
| `ctl-d1-q0.01` | `true` | control misses none | 67 | 1.00 [0.86, 1.16] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: tight third | 25 | 0.96 [0.74, 1.23] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: middle third | 24 | 1.15 [0.98, 1.38] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: loose third | 24 | 1.01 [0.78, 1.42] | 1.00 |

### Held course

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 65 | 0.91 [0.75, 1.04] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 22 | 1.00 [1.00, 1.00] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 21 | 0.89 [0.55, 1.22] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 22 | 0.84 [0.64, 1.00] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 65 | 0.85 [0.67, 1.04] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 22 | 0.78 [0.61, 0.96] | 0.98 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 21 | 0.76 [0.43, 1.24] | 0.99 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 22 | 1.04 [0.74, 1.42] | 1.02 |

### Outliers

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `true` | control misses a detectable manoeuvre | 7 | 0.87 [0.41, 2.17] | 0.85 |
| `ada-d1-q0.01` | `true` | control misses none | 44 | 1.00 [0.77, 1.30] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: tight third | 17 | 0.92 [0.71, 1.16] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: middle third | 17 | 0.94 [0.71, 1.24] | 0.98 |
| `ada-d1-q0.01` | `true` | bound: loose third | 17 | 1.09 [0.59, 2.12] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses a detectable manoeuvre | 7 | 1.04 [0.44, 2.06] | 1.27 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 44 | 0.97 [0.74, 1.25] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 17 | 0.97 [0.78, 1.20] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 17 | 1.04 [0.77, 1.41] | 1.01 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 17 | 0.92 [0.47, 1.73] | 1.00 |
| `ctl-d1-q0.01` | `ada-h1` | control misses a detectable manoeuvre | 7 | 1.54 [0.55, 3.76] | 1.79 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 44 | 1.02 [0.77, 1.36] | 0.99 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 17 | 1.25 [0.86, 2.02] | 1.08 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 17 | 1.07 [0.72, 1.69] | 0.99 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 17 | 0.94 [0.51, 1.68] | 1.10 |
| `ctl-d1-q0.01` | `true` | control misses a detectable manoeuvre | 7 | 0.91 [0.60, 1.24] | 1.00 |
| `ctl-d1-q0.01` | `true` | control misses none | 44 | 0.96 [0.91, 1.01] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: tight third | 17 | 0.89 [0.73, 1.00] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: middle third | 17 | 0.97 [0.88, 1.08] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: loose third | 17 | 1.01 [0.97, 1.08] | 1.00 |

### Correlated

| a | b | Kind of period | Periods | Ratio | Median |
| --- | --- | --- | --- | --- | --- |
| `ada-d1-q0.01` | `true` | control misses a detectable manoeuvre | 22 | 1.12 [0.82, 1.50] | 1.03 |
| `ada-d1-q0.01` | `true` | control misses none | 29 | 0.98 [0.77, 1.30] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: tight third | 17 | 1.11 [0.87, 1.38] | 1.05 |
| `ada-d1-q0.01` | `true` | bound: middle third | 17 | 1.34 [0.90, 2.14] | 1.00 |
| `ada-d1-q0.01` | `true` | bound: loose third | 17 | 0.75 [0.55, 1.03] | 0.96 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses a detectable manoeuvre | 22 | 1.08 [0.80, 1.49] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | control misses none | 29 | 0.89 [0.70, 1.08] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: tight third | 17 | 0.85 [0.72, 0.99] | 0.95 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: middle third | 17 | 0.72 [0.47, 0.99] | 1.00 |
| `ctl-d1-q0.01` | `ada-d1-q0.01` | bound: loose third | 17 | 1.49 [1.16, 1.98] | 1.04 |
| `ctl-d1-q0.01` | `ada-h1` | control misses a detectable manoeuvre | 22 | 1.24 [0.97, 1.72] | 1.21 |
| `ctl-d1-q0.01` | `ada-h1` | control misses none | 29 | 0.93 [0.73, 1.17] | 0.97 |
| `ctl-d1-q0.01` | `ada-h1` | bound: tight third | 17 | 0.85 [0.64, 1.08] | 0.95 |
| `ctl-d1-q0.01` | `ada-h1` | bound: middle third | 17 | 0.96 [0.68, 1.31] | 1.03 |
| `ctl-d1-q0.01` | `ada-h1` | bound: loose third | 17 | 1.44 [1.09, 2.03] | 1.34 |
| `ctl-d1-q0.01` | `true` | control misses a detectable manoeuvre | 22 | 1.20 [0.96, 1.67] | 1.00 |
| `ctl-d1-q0.01` | `true` | control misses none | 29 | 0.88 [0.77, 0.98] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: tight third | 17 | 0.94 [0.83, 1.01] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: middle third | 17 | 0.97 [0.73, 1.28] | 1.00 |
| `ctl-d1-q0.01` | `true` | bound: loose third | 17 | 1.12 [0.88, 1.59] | 1.00 |

## Manoeuvres missed (share) and false (per period), matched within 60, 120 and 240 s

| Split | System | Missed 60 / 120 / 240 | False 60 / 120 / 240 | Periods with a false one 60 / 120 / 240 | One-manoeuvre targets called quiet | Quiet targets given a manoeuvre |
| --- | --- | --- | --- | --- | --- | --- |
| Annex B | `ada-d1-q0.01` | 0.33 / 0.26 / 0.21 | 0.44 / 0.30 / 0.20 | 0.37 / 0.25 / 0.19 | 0.12 (26) | 0.00 (2) |
| Annex B | `c2` | 0.75 / 0.53 / 0.33 | 1.27 / 0.83 / 0.42 | 0.73 / 0.55 / 0.35 | 0.23 (26) | 0.00 (2) |
| Annex B | `ctl-d1-q0.01` | 0.31 / 0.21 / 0.18 | 0.45 / 0.24 / 0.18 | 0.38 / 0.24 / 0.18 | 0.04 (26) | 0.00 (2) |
| Annex B | `true` | 0.32 / 0.23 / 0.21 | 0.43 / 0.26 / 0.22 | 0.35 / 0.26 / 0.22 | 0.04 (26) | 0.00 (2) |
| Shifted | `ada-d1-q0.01` | 0.55 / 0.45 / 0.37 | 0.77 / 0.45 / 0.19 | 0.57 / 0.37 / 0.16 | 0.50 (12) | – |
| Shifted | `c2` | 0.88 / 0.69 / 0.54 | 1.61 / 1.00 / 0.55 | 0.79 / 0.65 / 0.42 | 0.75 (12) | – |
| Shifted | `ctl-d1-q0.01` | 0.56 / 0.47 / 0.39 | 0.73 / 0.44 / 0.19 | 0.56 / 0.39 / 0.17 | 0.50 (12) | – |
| Shifted | `true` | 0.48 / 0.35 / 0.27 | 0.91 / 0.51 / 0.23 | 0.62 / 0.42 / 0.23 | 0.33 (12) | – |
| Shifted 2 | `ada-d1-q0.01` | 0.29 / 0.14 / 0.08 | 0.33 / 0.12 / 0.03 | 0.26 / 0.10 / 0.03 | 0.11 (35) | 0.00 (4) |
| Shifted 2 | `c2` | 0.69 / 0.40 / 0.21 | 1.14 / 0.74 / 0.47 | 0.65 / 0.50 / 0.35 | 0.17 (35) | 0.00 (4) |
| Shifted 2 | `ctl-d1-q0.01` | 0.26 / 0.14 / 0.06 | 0.31 / 0.15 / 0.03 | 0.26 / 0.12 / 0.03 | 0.06 (35) | 0.00 (4) |
| Shifted 2 | `true` | 0.26 / 0.12 / 0.07 | 0.29 / 0.10 / 0.03 | 0.26 / 0.10 / 0.03 | 0.09 (35) | 0.00 (4) |
| Held course | `ada-d1-q0.01` | 0.00 / 0.00 / 0.00 | 0.04 / 0.04 / 0.04 | 0.04 / 0.04 / 0.04 | 0.00 (1) | 0.04 (79) |
| Held course | `c2` | 1.00 / 1.00 / 1.00 | 0.04 / 0.04 / 0.04 | 0.04 / 0.04 / 0.04 | 0.00 (1) | 0.03 (79) |
| Held course | `ctl-d1-q0.01` | 0.00 / 0.00 / 0.00 | 0.09 / 0.09 / 0.09 | 0.07 / 0.07 / 0.07 | 0.00 (1) | 0.08 (79) |
| Outliers | `ada-d1-q0.01` | 0.31 / 0.22 / 0.17 | 0.47 / 0.30 / 0.22 | 0.38 / 0.28 / 0.20 | 0.05 (19) | 0.00 (2) |
| Outliers | `c2` | 0.73 / 0.49 / 0.30 | 2.77 / 2.33 / 1.95 | 0.95 / 0.87 / 0.83 | 0.05 (19) | 1.00 (2) |
| Outliers | `ctl-d1-q0.01` | 0.32 / 0.22 / 0.14 | 0.45 / 0.27 / 0.13 | 0.37 / 0.23 / 0.13 | 0.00 (19) | 0.00 (2) |
| Outliers | `true` | 0.30 / 0.22 / 0.16 | 0.42 / 0.28 / 0.18 | 0.37 / 0.27 / 0.18 | 0.00 (19) | 0.00 (2) |
| Correlated | `ada-d1-q0.01` | 0.57 / 0.50 / 0.42 | 0.47 / 0.33 / 0.20 | 0.40 / 0.32 / 0.18 | 0.26 (19) | 0.00 (2) |
| Correlated | `c2` | 0.83 / 0.69 / 0.45 | 2.97 / 2.72 / 2.27 | 1.00 / 0.98 / 0.87 | 0.00 (19) | 1.00 (2) |
| Correlated | `ctl-d1-q0.01` | 0.58 / 0.45 / 0.41 | 0.62 / 0.38 / 0.30 | 0.48 / 0.35 / 0.27 | 0.16 (19) | 0.00 (2) |
| Correlated | `true` | 0.59 / 0.43 / 0.40 | 0.57 / 0.28 / 0.22 | 0.48 / 0.28 / 0.22 | 0.16 (19) | 0.00 (2) |

## The inferred rate

| Split | Periods | Inferred leg length, median (quartiles), s | Members most often chosen by one period's evidence |
| --- | --- | --- | --- |
| Annex B | 100 | 1625 (1304, 2006) | `rate1200` 0.46, `rate2400` 0.46, `rate600` 0.08 |
| Shifted | 150 | 1366 (1103, 1771) | `rate1200` 0.49, `rate2400` 0.27, `rate600` 0.24 |
| Shifted 2 | 80 | 1885 (1614, 2152) | `rate2400` 0.61, `rate1200` 0.36, `rate600` 0.03 |
| Held course | 80 | 2353 (2213, 2395) | `rate2400` 0.99, `rate600` 0.01 |
| Outliers | 60 | 1615 (1380, 1906) | `rate1200` 0.45, `rate2400` 0.43, `rate600` 0.12 |
| Correlated | 60 | 1863 (1445, 2089) | `rate2400` 0.65, `rate1200` 0.30, `rate600` 0.05 |

## The hedged track's stated spread in range: coverage

(share of rows whose true range is within one and two stated sds of the mixture's mean range; a normal spread gives 0.68 and 0.95)

| Split | True manoeuvres | Periods | Rows | Within 1 sd | Within 2 sd | Median stated sd ÷ range |
| --- | --- | --- | --- | --- | --- | --- |
| Annex B | all | 89 | 9869 | 0.64 | 0.88 | 0.066 |
| Annex B | 1 | 28 | 2003 | 0.70 | 0.93 | 0.073 |
| Annex B | 2+ | 61 | 7866 | 0.62 | 0.86 | 0.065 |
| Shifted | all | 132 | 13522 | 0.48 | 0.73 | 0.084 |
| Shifted | 1 | 9 | 468 | 0.65 | 0.79 | 0.120 |
| Shifted | 2+ | 123 | 13054 | 0.47 | 0.73 | 0.083 |
| Shifted 2 | all | 73 | 7777 | 0.62 | 0.85 | 0.040 |
| Shifted 2 | 0 | 4 | 203 | 0.68 | 0.98 | 0.038 |
| Shifted 2 | 1 | 42 | 3687 | 0.63 | 0.85 | 0.050 |
| Shifted 2 | 2+ | 27 | 3887 | 0.61 | 0.84 | 0.036 |
| Held course | all | 65 | 7217 | 0.71 | 0.99 | 0.033 |
| Held course | 0 | 64 | 7108 | 0.71 | 1.00 | 0.033 |
| Held course | 1 | 1 | 109 | 0.48 | 0.57 | 0.042 |
| Outliers | all | 51 | 5201 | 0.77 | 0.92 | 0.066 |
| Outliers | 1 | 21 | 1389 | 0.77 | 0.97 | 0.064 |
| Outliers | 2+ | 30 | 3812 | 0.76 | 0.90 | 0.067 |
| Correlated | all | 51 | 5201 | 0.67 | 0.92 | 0.140 |
| Correlated | 1 | 21 | 1389 | 0.75 | 0.96 | 0.121 |
| Correlated | 2+ | 30 | 3812 | 0.64 | 0.90 | 0.144 |

## Per-period choice: share of periods in which the declared history is given

| Split | Annex B | Shifted | Shifted 2 | Held course | Outliers | Correlated |
| --- | --- | --- | --- | --- | --- | --- |
| first candidate at least 0.5 | 0.84 | 0.82 | 0.91 | 0.91 | 0.83 | 0.83 |
| first candidate at least 0.8 | 0.57 | 0.39 | 0.71 | 0.61 | 0.53 | 0.33 |

## Efficiency against the bound (range, course, speed) and references held

| Split | References drifting when free | System | Range | Course | Speed |
| --- | --- | --- | --- | --- | --- |
| Annex B | 0.10 | `ctl-d1-q0.01` | 1.59 | 1.99 | 1.55 |
| Annex B | 0.10 | `ada-d1-q0.01` | 1.59 | 2.31 | 1.95 |
| Annex B | 0.10 | `ada-h1` | 1.55 | 2.23 | 2.08 |
| Annex B | 0.10 | `true` | 1.35 | 1.83 | 1.26 |
| Annex B | 0.10 | `ref-full` | 0.99 | 1.18 | 0.98 |
| Annex B | 0.10 | `c2` | 3.27 | 5.09 | 3.79 |
| Shifted | 0.27 | `ctl-d1-q0.01` | 2.42 | 2.53 | 2.27 |
| Shifted | 0.27 | `ada-d1-q0.01` | 2.56 | 2.71 | 2.18 |
| Shifted | 0.27 | `ada-h1` | 2.21 | 2.70 | 2.13 |
| Shifted | 0.27 | `true` | 2.14 | 2.10 | 1.72 |
| Shifted | 0.27 | `ref-full` | 0.99 | 0.95 | 0.84 |
| Shifted | 0.27 | `c2` | 4.13 | 5.13 | 3.43 |
| Shifted 2 | 0.10 | `ctl-d1-q0.01` | 2.12 | 1.99 | 2.10 |
| Shifted 2 | 0.10 | `ada-d1-q0.01` | 1.93 | 1.97 | 2.09 |
| Shifted 2 | 0.10 | `ada-h1` | 1.93 | 1.86 | 2.04 |
| Shifted 2 | 0.10 | `true` | 2.03 | 1.87 | 1.91 |
| Shifted 2 | 0.10 | `ref-full` | 1.18 | 1.34 | 1.15 |
| Shifted 2 | 0.10 | `c2` | 4.53 | 5.03 | 4.69 |
| Held course | 0.00 | `ctl-d1-q0.01` | 0.88 | 1.07 | 0.85 |
| Held course | 0.00 | `ada-d1-q0.01` | 1.06 | 1.07 | 0.94 |
| Held course | 0.00 | `ada-h1` | 1.38 | 1.42 | 1.34 |
| Held course | 0.00 | `true` | – | – | – |
| Held course | 0.00 | `ref-full` | 0.96 | 1.07 | 0.85 |
| Held course | 0.00 | `c2` | 1.08 | 1.18 | 1.14 |
| Outliers | 0.17 | `ctl-d1-q0.01` | 1.32 | 1.94 | 1.54 |
| Outliers | 0.17 | `ada-d1-q0.01` | 1.53 | 2.04 | 1.15 |
| Outliers | 0.17 | `ada-h1` | 1.22 | 1.70 | 1.28 |
| Outliers | 0.17 | `true` | 1.44 | 1.74 | 1.56 |
| Outliers | 0.17 | `ref-full` | 1.64 | 1.80 | 1.59 |
| Outliers | 0.17 | `c2` | 8.76 | 11.00 | 8.16 |
| Correlated | 0.35 | `ctl-d1-q0.01` | 3.65 | 5.38 | 3.15 |
| Correlated | 0.35 | `ada-d1-q0.01` | 4.08 | 5.79 | 3.80 |
| Correlated | 0.35 | `ada-h1` | 3.69 | 5.79 | 3.69 |
| Correlated | 0.35 | `true` | 3.78 | 5.00 | 3.65 |
| Correlated | 0.35 | `ref-full` | 3.08 | 3.19 | 2.68 |
| Correlated | 0.35 | `c2` | 15.08 | 22.67 | 13.87 |

## Seconds per period

| Split | Annex B | Shifted | Shifted 2 | Held course | Outliers | Correlated |
| --- | --- | --- | --- | --- | --- | --- |
| ada/hedge | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ada/path | 0.2 | 0.4 | 0.1 | 0.0 | 0.2 | 0.1 |
| ada/rate1200 | 24.3 | 33.7 | 18.1 | 9.9 | 32.0 | 31.9 |
| ada/rate2400 | 21.8 | 31.9 | 17.3 | 4.5 | 32.6 | 31.8 |
| ada/rate600 | 30.0 | 38.2 | 27.7 | 20.5 | 34.7 | 39.9 |
| ctl/broad | 24.5 | 29.7 | 13.3 | 8.5 | 69.2 | 32.6 |
| ctl/path | 0.2 | 0.4 | 0.1 | 0.0 | 0.1 | 0.1 |
| ctl/v3 | 22.3 | 22.4 | 11.9 | 5.5 | 61.7 | 30.2 |
| detectability | 23.1 | 69.6 | 10.6 | 0.2 | 14.1 | 15.3 |
| edit/broad | 37.6 | 48.5 | 25.7 | 7.8 | 29.9 | – |
| edit/v3 | 24.3 | 38.1 | 29.7 | 10.6 | 28.0 | – |
| plain/broad | 22.7 | 34.0 | 17.2 | 5.9 | – | – |
| plain/v3 | 20.1 | 29.8 | 16.4 | 7.2 | – | – |
| reference | 4.9 | 10.9 | 3.0 | 0.1 | 3.7 | 3.9 |
| true | 20.8 | 41.0 | 16.4 | – | 30.8 | 30.4 |
