## Median period range error

| System | Annex B | Shifted | Shifted 2 | Held course | Correlated, mild | Correlated | Outliers | Outliers, harsh | Bias | Whole |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Periods (scored) | 400 (374) | 400 (365) | 400 (375) | 300 (263) | 200 (186) | 300 (278) | 300 (278) | 200 (186) | 300 (278) | 60 (60) |
| `broad` | 0.042 | 0.093 | 0.030 | 0.022 | – | – | – | – | – | – |
| `c2` | 0.085 | 0.141 | 0.068 | 0.016 | 0.324 | 0.272 | 0.248 | 0.468 | 0.117 | 0.073 |
| `corr` | 0.041 | – | – | – | 0.088 | 0.098 | – | – | – | – |
| `ctl` | 0.039 | 0.086 | 0.028 | 0.024 | 0.084 | 0.102 | 0.041 | 0.051 | 0.060 | 0.039 |
| `edit` | 0.041 | – | – | – | – | – | 0.041 | 0.048 | – | – |
| `history-best` | 0.029 | 0.044 | 0.024 | 0.015 | 0.064 | 0.076 | 0.046 | 0.070 | 0.049 | 0.021 |
| `history-fixed` | 0.022 | 0.042 | 0.019 | 0.015 | 0.058 | 0.072 | 0.036 | 0.060 | 0.040 | 0.018 |
| `history-map` | 0.029 | 0.047 | 0.025 | 0.015 | 0.072 | 0.086 | 0.049 | 0.079 | 0.051 | 0.025 |
| `learned-s1` | 0.050 | 0.084 | 0.043 | 0.025 | 0.093 | 0.106 | 0.062 | 0.071 | 0.065 | 0.043 |
| `learned-s1-arc` | 0.047 | 0.112 | 0.033 | 0.015 | 0.110 | 0.133 | 0.060 | 0.056 | 0.064 | 0.044 |
| `learned-s2` | 0.051 | 0.081 | 0.043 | 0.025 | 0.092 | 0.099 | 0.059 | 0.074 | 0.063 | 0.045 |
| `learned-s2-arc` | 0.049 | 0.117 | 0.033 | 0.015 | 0.111 | 0.129 | 0.057 | 0.058 | 0.059 | 0.046 |
| `learned-s3` | 0.049 | 0.080 | 0.044 | 0.025 | 0.093 | 0.106 | 0.059 | 0.068 | 0.063 | 0.042 |
| `learned-s3-arc` | 0.046 | 0.110 | 0.032 | 0.015 | 0.113 | 0.125 | 0.055 | 0.059 | 0.065 | 0.048 |
| `mix2` | 0.039 | 0.086 | 0.028 | 0.023 | – | – | – | – | – | – |
| `one-leg` | 0.413 | 0.340 | 0.386 | 0.016 | 0.426 | 0.429 | 0.409 | 0.415 | 0.429 | 0.459 |
| `search3` | 0.041 | 0.094 | 0.029 | 0.031 | 0.115 | 0.136 | 0.077 | 0.125 | 0.059 | 0.037 |

## The standing search ÷ each system (paired per period; above 1: better)

### Annex B

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.02 [0.94, 1.12] | 0.46 |
| `broad-h1` | 1.00 [0.92, 1.10] | 0.48 |
| `c2` | 0.49 [0.43, 0.56] | 0.72 |
| `corr` | 0.97 [0.92, 1.03] | 0.21 |
| `corr-h1` | 0.97 [0.91, 1.04] | 0.43 |
| `ctl` | 1.08 [1.02, 1.16] | 0.13 |
| `ctl-h1` | 1.06 [0.99, 1.14] | 0.44 |
| `edit` | 0.99 [0.97, 1.01] | 0.04 |
| `edit-h1` | 0.99 [0.95, 1.04] | 0.43 |
| `learned-s1` | 0.78 [0.68, 0.89] | 0.57 |
| `learned-s1-arc` | 0.89 [0.80, 0.99] | 0.57 |
| `learned-s2` | 0.79 [0.69, 0.91] | 0.56 |
| `learned-s2-arc` | 0.89 [0.80, 0.99] | 0.55 |
| `learned-s3` | 0.84 [0.74, 0.96] | 0.53 |
| `learned-s3-arc` | 0.90 [0.81, 1.01] | 0.56 |
| `mix2` | 1.08 [1.02, 1.15] | 0.09 |
| `mix2-h1` | 1.06 [0.98, 1.14] | 0.43 |
| `search3-h1` | 1.00 [0.96, 1.04] | 0.41 |

### Shifted

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.03 [0.95, 1.12] | 0.47 |
| `broad-h1` | 1.09 [1.00, 1.19] | 0.39 |
| `c2` | 0.61 [0.54, 0.69] | 0.64 |
| `ctl` | 1.05 [0.99, 1.12] | 0.20 |
| `ctl-h1` | 1.11 [1.04, 1.19] | 0.36 |
| `learned-s1` | 1.04 [0.93, 1.16] | 0.43 |
| `learned-s1-arc` | 0.84 [0.75, 0.94] | 0.55 |
| `learned-s2` | 1.04 [0.92, 1.18] | 0.43 |
| `learned-s2-arc` | 0.82 [0.73, 0.93] | 0.55 |
| `learned-s3` | 1.04 [0.93, 1.18] | 0.43 |
| `learned-s3-arc` | 0.84 [0.75, 0.94] | 0.55 |
| `mix2` | 1.06 [1.00, 1.13] | 0.15 |
| `mix2-h1` | 1.12 [1.05, 1.20] | 0.35 |
| `search3-h1` | 1.07 [1.04, 1.11] | 0.35 |

### Shifted 2

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.03 [0.96, 1.10] | 0.44 |
| `broad-h1` | 1.04 [0.97, 1.13] | 0.47 |
| `c2` | 0.44 [0.39, 0.51] | 0.73 |
| `ctl` | 1.07 [1.02, 1.13] | 0.17 |
| `ctl-h1` | 1.03 [0.98, 1.09] | 0.44 |
| `learned-s1` | 0.65 [0.58, 0.73] | 0.66 |
| `learned-s1-arc` | 0.94 [0.86, 1.03] | 0.48 |
| `learned-s2` | 0.66 [0.58, 0.74] | 0.65 |
| `learned-s2-arc` | 0.94 [0.85, 1.02] | 0.48 |
| `learned-s3` | 0.67 [0.59, 0.76] | 0.63 |
| `learned-s3-arc` | 1.02 [0.93, 1.13] | 0.47 |
| `mix2` | 1.07 [1.02, 1.13] | 0.12 |
| `mix2-h1` | 1.05 [0.99, 1.11] | 0.42 |
| `search3-h1` | 1.00 [0.96, 1.04] | 0.43 |

### Held course

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.27 [1.15, 1.42] | 0.17 |
| `broad-h1` | 1.25 [1.12, 1.40] | 0.38 |
| `c2` | 1.68 [1.45, 1.96] | 0.35 |
| `ctl` | 1.24 [1.12, 1.37] | 0.17 |
| `ctl-h1` | 1.19 [1.07, 1.32] | 0.40 |
| `learned-s1` | 1.05 [0.89, 1.23] | 0.48 |
| `learned-s1-arc` | 1.79 [1.57, 2.05] | 0.29 |
| `learned-s2` | 1.06 [0.90, 1.25] | 0.51 |
| `learned-s2-arc` | 1.79 [1.57, 2.05] | 0.29 |
| `learned-s3` | 1.08 [0.90, 1.28] | 0.45 |
| `learned-s3-arc` | 1.80 [1.57, 2.06] | 0.28 |
| `mix2` | 1.21 [1.10, 1.34] | 0.15 |
| `mix2-h1` | 1.20 [1.08, 1.33] | 0.37 |
| `search3-h1` | 0.96 [0.89, 1.04] | 0.40 |

### Correlated, mild

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.34 [0.28, 0.40] | 0.78 |
| `corr` | 1.17 [0.99, 1.39] | 0.40 |
| `corr-h1` | 1.20 [1.02, 1.40] | 0.38 |
| `ctl` | 1.27 [1.10, 1.48] | 0.34 |
| `ctl-h1` | 1.27 [1.11, 1.47] | 0.36 |
| `learned-s1` | 1.10 [0.95, 1.28] | 0.46 |
| `learned-s1-arc` | 1.07 [0.90, 1.27] | 0.48 |
| `learned-s2` | 1.08 [0.92, 1.26] | 0.49 |
| `learned-s2-arc` | 0.98 [0.83, 1.17] | 0.49 |
| `learned-s3` | 1.13 [0.97, 1.31] | 0.43 |
| `learned-s3-arc` | 1.10 [0.92, 1.30] | 0.46 |
| `search3-h1` | 1.00 [0.95, 1.06] | 0.41 |

### Correlated

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.49 [0.43, 0.56] | 0.74 |
| `corr` | 1.34 [1.16, 1.53] | 0.35 |
| `corr-h1` | 1.38 [1.21, 1.58] | 0.37 |
| `ctl` | 1.33 [1.16, 1.51] | 0.37 |
| `ctl-h1` | 1.35 [1.18, 1.54] | 0.36 |
| `learned-s1` | 1.32 [1.17, 1.50] | 0.35 |
| `learned-s1-arc` | 1.10 [0.95, 1.27] | 0.45 |
| `learned-s2` | 1.29 [1.14, 1.47] | 0.36 |
| `learned-s2-arc` | 1.10 [0.95, 1.26] | 0.45 |
| `learned-s3` | 1.31 [1.15, 1.49] | 0.35 |
| `learned-s3-arc` | 1.12 [0.97, 1.28] | 0.44 |
| `search3-h1` | 1.00 [0.96, 1.05] | 0.41 |

### Outliers

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.32 [0.27, 0.39] | 0.79 |
| `ctl` | 1.68 [1.47, 1.95] | 0.34 |
| `ctl-h1` | 1.64 [1.44, 1.88] | 0.31 |
| `edit` | 1.62 [1.42, 1.86] | 0.35 |
| `edit-h1` | 1.61 [1.41, 1.85] | 0.33 |
| `learned-s1` | 1.05 [0.92, 1.21] | 0.45 |
| `learned-s1-arc` | 1.32 [1.14, 1.52] | 0.41 |
| `learned-s2` | 1.09 [0.95, 1.25] | 0.43 |
| `learned-s2-arc` | 1.30 [1.12, 1.49] | 0.42 |
| `learned-s3` | 1.12 [0.98, 1.28] | 0.44 |
| `learned-s3-arc` | 1.36 [1.18, 1.58] | 0.42 |
| `search3-h1` | 1.03 [0.98, 1.07] | 0.39 |

### Outliers, harsh

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.33 [0.27, 0.40] | 0.80 |
| `ctl` | 2.50 [2.07, 3.06] | 0.22 |
| `ctl-h1` | 2.43 [2.04, 2.92] | 0.22 |
| `edit` | 2.50 [2.09, 3.05] | 0.21 |
| `edit-h1` | 2.44 [2.06, 2.94] | 0.20 |
| `learned-s1` | 1.63 [1.38, 1.94] | 0.32 |
| `learned-s1-arc` | 2.14 [1.76, 2.61] | 0.30 |
| `learned-s2` | 1.63 [1.39, 1.91] | 0.31 |
| `learned-s2-arc` | 2.10 [1.72, 2.56] | 0.30 |
| `learned-s3` | 1.68 [1.43, 1.96] | 0.30 |
| `learned-s3-arc` | 2.07 [1.72, 2.49] | 0.28 |
| `search3-h1` | 1.04 [1.00, 1.09] | 0.37 |

### Bias

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.53 [0.46, 0.61] | 0.69 |
| `ctl` | 0.97 [0.92, 1.02] | 0.16 |
| `ctl-h1` | 1.00 [0.94, 1.07] | 0.41 |
| `learned-s1` | 0.92 [0.81, 1.05] | 0.51 |
| `learned-s1-arc` | 0.99 [0.89, 1.09] | 0.48 |
| `learned-s2` | 0.89 [0.78, 1.02] | 0.50 |
| `learned-s2-arc` | 1.00 [0.90, 1.10] | 0.47 |
| `learned-s3` | 0.99 [0.87, 1.13] | 0.45 |
| `learned-s3-arc` | 0.97 [0.87, 1.08] | 0.49 |
| `search3-h1` | 1.01 [0.96, 1.06] | 0.37 |

### Whole

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.43 [0.30, 0.62] | 0.72 |
| `ctl` | 1.09 [0.93, 1.26] | 0.08 |
| `ctl-h1` | 1.04 [0.88, 1.22] | 0.45 |
| `learned-s1` | 0.66 [0.48, 0.90] | 0.53 |
| `learned-s1-arc` | 0.87 [0.65, 1.17] | 0.47 |
| `learned-s2` | 0.62 [0.44, 0.86] | 0.57 |
| `learned-s2-arc` | 0.79 [0.60, 1.04] | 0.52 |
| `learned-s3` | 0.72 [0.52, 0.99] | 0.58 |
| `learned-s3-arc` | 0.79 [0.61, 1.01] | 0.50 |
| `search3-h1` | 0.98 [0.92, 1.06] | 0.53 |

## Share of the gap from the search to the reference that a control closes

| Split | Control | Share |
| --- | --- | --- |
| Annex B | `broad` | 0.06 [-0.22, 0.29] |
| Annex B | `corr` | -0.08 [-0.30, 0.09] |
| Annex B | `ctl` | 0.24 [0.06, 0.41] |
| Annex B | `edit` | -0.02 [-0.09, 0.04] |
| Annex B | `learned-s1` | -0.76 [-1.41, -0.30] |
| Annex B | `learned-s1-arc` | -0.34 [-0.82, -0.02] |
| Annex B | `learned-s2` | -0.70 [-1.38, -0.22] |
| Annex B | `learned-s2-arc` | -0.37 [-0.85, -0.02] |
| Annex B | `learned-s3` | -0.52 [-1.09, -0.10] |
| Annex B | `learned-s3-arc` | -0.31 [-0.77, 0.02] |
| Annex B | `mix2` | 0.22 [0.06, 0.39] |
| Shifted | `broad` | 0.05 [-0.09, 0.18] |
| Shifted | `ctl` | 0.08 [-0.01, 0.18] |
| Shifted | `learned-s1` | 0.06 [-0.13, 0.22] |
| Shifted | `learned-s1-arc` | -0.28 [-0.52, -0.09] |
| Shifted | `learned-s2` | 0.07 [-0.14, 0.25] |
| Shifted | `learned-s2-arc` | -0.31 [-0.56, -0.11] |
| Shifted | `learned-s3` | 0.07 [-0.13, 0.24] |
| Shifted | `learned-s3-arc` | -0.28 [-0.51, -0.09] |
| Shifted | `mix2` | 0.09 [0.00, 0.19] |
| Shifted 2 | `broad` | 0.11 [-0.23, 0.43] |
| Shifted 2 | `ctl` | 0.29 [0.09, 0.58] |
| Shifted 2 | `learned-s1` | -1.85 [-3.63, -1.03] |
| Shifted 2 | `learned-s1-arc` | -0.25 [-0.89, 0.11] |
| Shifted 2 | `learned-s2` | -1.79 [-3.61, -0.97] |
| Shifted 2 | `learned-s2-arc` | -0.29 [-0.94, 0.09] |
| Shifted 2 | `learned-s3` | -1.72 [-3.44, -0.92] |
| Shifted 2 | `learned-s3-arc` | 0.09 [-0.43, 0.47] |
| Shifted 2 | `mix2` | 0.28 [0.08, 0.56] |
| Held course | `broad` | 0.39 [0.25, 0.52] |
| Held course | `ctl` | 0.35 [0.20, 0.48] |
| Held course | `learned-s1` | 0.08 [-0.22, 0.30] |
| Held course | `learned-s1-arc` | 0.95 [0.90, 0.99] |
| Held course | `learned-s2` | 0.10 [-0.22, 0.33] |
| Held course | `learned-s2-arc` | 0.95 [0.90, 0.99] |
| Held course | `learned-s3` | 0.12 [-0.19, 0.36] |
| Held course | `learned-s3-arc` | 0.95 [0.90, 0.99] |
| Held course | `mix2` | 0.31 [0.18, 0.44] |
| Correlated, mild | `corr` | 0.30 [-0.03, 0.56] |
| Correlated, mild | `ctl` | 0.46 [0.20, 0.69] |
| Correlated, mild | `learned-s1` | 0.19 [-0.11, 0.43] |
| Correlated, mild | `learned-s1-arc` | 0.13 [-0.23, 0.39] |
| Correlated, mild | `learned-s2` | 0.16 [-0.16, 0.42] |
| Correlated, mild | `learned-s2-arc` | -0.03 [-0.44, 0.26] |
| Correlated, mild | `learned-s3` | 0.23 [-0.07, 0.49] |
| Correlated, mild | `learned-s3-arc` | 0.17 [-0.18, 0.44] |
| Correlated | `corr` | 0.52 [0.30, 0.73] |
| Correlated | `ctl` | 0.51 [0.30, 0.69] |
| Correlated | `learned-s1` | 0.50 [0.30, 0.71] |
| Correlated | `learned-s1-arc` | 0.17 [-0.11, 0.39] |
| Correlated | `learned-s2` | 0.46 [0.25, 0.67] |
| Correlated | `learned-s2-arc` | 0.17 [-0.11, 0.39] |
| Correlated | `learned-s3` | 0.48 [0.27, 0.70] |
| Correlated | `learned-s3-arc` | 0.20 [-0.08, 0.41] |
| Outliers | `ctl` | 1.20 [0.89, 1.61] |
| Outliers | `edit` | 1.11 [0.80, 1.53] |
| Outliers | `learned-s1` | 0.12 [-0.23, 0.42] |
| Outliers | `learned-s1-arc` | 0.63 [0.32, 0.97] |
| Outliers | `learned-s2` | 0.19 [-0.13, 0.49] |
| Outliers | `learned-s2-arc` | 0.60 [0.29, 0.92] |
| Outliers | `learned-s3` | 0.25 [-0.05, 0.53] |
| Outliers | `learned-s3-arc` | 0.70 [0.39, 1.04] |
| Outliers, harsh | `ctl` | 1.55 [1.23, 2.08] |
| Outliers, harsh | `edit` | 1.55 [1.23, 2.08] |
| Outliers, harsh | `learned-s1` | 0.83 [0.59, 1.11] |
| Outliers, harsh | `learned-s1-arc` | 1.29 [0.98, 1.72] |
| Outliers, harsh | `learned-s2` | 0.83 [0.59, 1.14] |
| Outliers, harsh | `learned-s2-arc` | 1.25 [0.96, 1.66] |
| Outliers, harsh | `learned-s3` | 0.87 [0.64, 1.18] |
| Outliers, harsh | `learned-s3-arc` | 1.23 [0.93, 1.66] |
| Bias | `ctl` | -0.11 [-0.48, 0.09] |
| Bias | `learned-s1` | -0.33 [-1.42, 0.16] |
| Bias | `learned-s1-arc` | -0.06 [-0.76, 0.30] |
| Bias | `learned-s2` | -0.44 [-1.58, 0.07] |
| Bias | `learned-s2-arc` | -0.01 [-0.66, 0.32] |
| Bias | `learned-s3` | -0.04 [-0.92, 0.43] |
| Bias | `learned-s3-arc` | -0.11 [-0.98, 0.25] |
| Whole | `ctl` | 0.16 [-0.18, 0.47] |
| Whole | `learned-s1` | -0.80 [-2.43, -0.15] |
| Whole | `learned-s1-arc` | -0.27 [-1.41, 0.25] |
| Whole | `learned-s2` | -0.93 [-2.68, -0.23] |
| Whole | `learned-s2-arc` | -0.46 [-1.60, 0.07] |
| Whole | `learned-s3` | -0.64 [-2.11, -0.03] |
| Whole | `learned-s3-arc` | -0.46 [-1.63, 0.02] |

## System ÷ the true-history reference, by how the reference is fitted

| Split | System | times free | held where drifted | times held |
| --- | --- | --- | --- | --- |
| Annex B | `search3` | 1.37 [1.24, 1.51] | 1.40 [1.27, 1.54] | 2.06 [1.79, 2.37] |
| Annex B | `ctl` | 1.26 [1.15, 1.38] | 1.29 [1.17, 1.41] | 1.90 [1.67, 2.16] |
| Shifted | `search3` | 1.75 [1.57, 1.95] | 1.88 [1.68, 2.10] | 2.19 [1.94, 2.48] |
| Shifted | `ctl` | 1.66 [1.50, 1.85] | 1.79 [1.61, 1.99] | 2.08 [1.86, 2.34] |
| Shifted 2 | `search3` | 1.24 [1.12, 1.38] | 1.26 [1.14, 1.41] | 1.65 [1.47, 1.85] |
| Shifted 2 | `ctl` | 1.16 [1.05, 1.28] | 1.18 [1.07, 1.31] | 1.54 [1.37, 1.72] |
| Held course | `search3` | 1.85 [1.63, 2.12] | 1.85 [1.63, 2.12] | 1.85 [1.63, 2.13] |
| Held course | `ctl` | 1.49 [1.35, 1.67] | 1.49 [1.35, 1.67] | 1.50 [1.35, 1.67] |
| Correlated, mild | `search3` | 1.54 [1.28, 1.83] | 1.69 [1.44, 1.97] | 1.92 [1.59, 2.34] |
| Correlated, mild | `ctl` | 1.21 [1.04, 1.40] | 1.33 [1.16, 1.52] | 1.51 [1.26, 1.78] |
| Correlated | `search3` | 1.58 [1.38, 1.82] | 1.75 [1.52, 2.04] | 2.05 [1.75, 2.40] |
| Correlated | `ctl` | 1.19 [1.06, 1.35] | 1.32 [1.17, 1.50] | 1.54 [1.35, 1.76] |
| Outliers | `search3` | 1.40 [1.26, 1.57] | 1.55 [1.37, 1.76] | 2.01 [1.74, 2.35] |
| Outliers | `ctl` | 0.83 [0.73, 0.96] | 0.92 [0.80, 1.06] | 1.20 [1.02, 1.39] |
| Outliers, harsh | `search3` | 1.66 [1.40, 1.96] | 1.81 [1.51, 2.16] | 2.41 [1.99, 2.89] |
| Outliers, harsh | `ctl` | 0.66 [0.55, 0.78] | 0.72 [0.60, 0.86] | 0.96 [0.79, 1.17] |
| Bias | `search3` | 1.22 [1.08, 1.37] | 1.29 [1.13, 1.44] | 1.54 [1.33, 1.76] |
| Bias | `ctl` | 1.26 [1.12, 1.40] | 1.32 [1.17, 1.47] | 1.58 [1.37, 1.80] |
| Whole | `search3` | 1.46 [1.12, 1.87] | 1.68 [1.27, 2.22] | 2.44 [1.68, 3.57] |
| Whole | `ctl` | 1.34 [1.06, 1.72] | 1.55 [1.19, 2.03] | 2.25 [1.59, 3.19] |

## Manoeuvres missed (share) and false (per period), matched within 120 s

| Split | System | Missed | False |
| --- | --- | --- | --- |
| Annex B | `broad` | 0.28 | 0.24 |
| Annex B | `c2` | 0.57 | 0.76 |
| Annex B | `corr` | 0.29 | 0.26 |
| Annex B | `ctl` | 0.25 | 0.23 |
| Annex B | `edit` | 0.25 | 0.25 |
| Annex B | `learned-s1` | 0.31 | 0.03 |
| Annex B | `learned-s1-arc` | 0.34 | 0.08 |
| Annex B | `learned-s2` | 0.31 | 0.04 |
| Annex B | `learned-s2-arc` | 0.33 | 0.08 |
| Annex B | `learned-s3` | 0.29 | 0.03 |
| Annex B | `learned-s3-arc` | 0.32 | 0.08 |
| Annex B | `mix2` | 0.25 | 0.23 |
| Annex B | `search3` | 0.25 | 0.24 |
| Shifted | `broad` | 0.48 | 0.42 |
| Shifted | `c2` | 0.70 | 0.94 |
| Shifted | `ctl` | 0.48 | 0.42 |
| Shifted | `learned-s1` | 0.58 | 0.09 |
| Shifted | `learned-s1-arc` | 0.62 | 0.20 |
| Shifted | `learned-s2` | 0.58 | 0.10 |
| Shifted | `learned-s2-arc` | 0.62 | 0.22 |
| Shifted | `learned-s3` | 0.59 | 0.09 |
| Shifted | `learned-s3-arc` | 0.62 | 0.19 |
| Shifted | `mix2` | 0.48 | 0.41 |
| Shifted | `search3` | 0.48 | 0.42 |
| Shifted 2 | `broad` | 0.14 | 0.19 |
| Shifted 2 | `c2` | 0.47 | 0.74 |
| Shifted 2 | `ctl` | 0.12 | 0.19 |
| Shifted 2 | `learned-s1` | 0.21 | 0.13 |
| Shifted 2 | `learned-s1-arc` | 0.20 | 0.11 |
| Shifted 2 | `learned-s2` | 0.21 | 0.14 |
| Shifted 2 | `learned-s2-arc` | 0.20 | 0.12 |
| Shifted 2 | `learned-s3` | 0.19 | 0.14 |
| Shifted 2 | `learned-s3-arc` | 0.19 | 0.14 |
| Shifted 2 | `mix2` | 0.12 | 0.18 |
| Shifted 2 | `search3` | 0.12 | 0.19 |
| Held course | `broad` | 0.00 | 0.43 |
| Held course | `c2` | 1.00 | 0.05 |
| Held course | `ctl` | 0.00 | 0.45 |
| Held course | `learned-s1` | 0.00 | 0.01 |
| Held course | `learned-s1-arc` | 0.00 | 0.01 |
| Held course | `learned-s2` | 0.00 | 0.01 |
| Held course | `learned-s2-arc` | 0.00 | 0.01 |
| Held course | `learned-s3` | 0.00 | 0.01 |
| Held course | `learned-s3-arc` | 0.00 | 0.01 |
| Held course | `mix2` | 0.00 | 0.47 |
| Held course | `search3` | 0.00 | 0.58 |
| Correlated, mild | `c2` | 0.61 | 2.44 |
| Correlated, mild | `corr` | 0.38 | 0.32 |
| Correlated, mild | `ctl` | 0.36 | 0.27 |
| Correlated, mild | `learned-s1` | 0.47 | 0.10 |
| Correlated, mild | `learned-s1-arc` | 0.49 | 0.14 |
| Correlated, mild | `learned-s2` | 0.48 | 0.09 |
| Correlated, mild | `learned-s2-arc` | 0.51 | 0.14 |
| Correlated, mild | `learned-s3` | 0.48 | 0.11 |
| Correlated, mild | `learned-s3-arc` | 0.49 | 0.13 |
| Correlated, mild | `search3` | 0.31 | 0.86 |
| Correlated | `c2` | 0.57 | 2.45 |
| Correlated | `corr` | 0.44 | 0.38 |
| Correlated | `ctl` | 0.44 | 0.38 |
| Correlated | `learned-s1` | 0.51 | 0.13 |
| Correlated | `learned-s1-arc` | 0.54 | 0.19 |
| Correlated | `learned-s2` | 0.50 | 0.10 |
| Correlated | `learned-s2-arc` | 0.53 | 0.15 |
| Correlated | `learned-s3` | 0.50 | 0.13 |
| Correlated | `learned-s3-arc` | 0.53 | 0.17 |
| Correlated | `search3` | 0.37 | 1.27 |
| Outliers | `c2` | 0.53 | 2.25 |
| Outliers | `ctl` | 0.21 | 0.22 |
| Outliers | `edit` | 0.22 | 0.24 |
| Outliers | `learned-s1` | 0.34 | 0.06 |
| Outliers | `learned-s1-arc` | 0.34 | 0.07 |
| Outliers | `learned-s2` | 0.33 | 0.08 |
| Outliers | `learned-s2-arc` | 0.35 | 0.10 |
| Outliers | `learned-s3` | 0.32 | 0.08 |
| Outliers | `learned-s3-arc` | 0.33 | 0.10 |
| Outliers | `search3` | 0.28 | 0.56 |
| Outliers, harsh | `c2` | 0.58 | 3.52 |
| Outliers, harsh | `ctl` | 0.26 | 0.32 |
| Outliers, harsh | `edit` | 0.26 | 0.33 |
| Outliers, harsh | `learned-s1` | 0.39 | 0.09 |
| Outliers, harsh | `learned-s1-arc` | 0.41 | 0.12 |
| Outliers, harsh | `learned-s2` | 0.40 | 0.12 |
| Outliers, harsh | `learned-s2-arc` | 0.40 | 0.12 |
| Outliers, harsh | `learned-s3` | 0.40 | 0.12 |
| Outliers, harsh | `learned-s3-arc` | 0.40 | 0.12 |
| Outliers, harsh | `search3` | 0.37 | 1.16 |
| Bias | `c2` | 0.57 | 0.93 |
| Bias | `ctl` | 0.25 | 0.35 |
| Bias | `learned-s1` | 0.31 | 0.09 |
| Bias | `learned-s1-arc` | 0.32 | 0.11 |
| Bias | `learned-s2` | 0.30 | 0.13 |
| Bias | `learned-s2-arc` | 0.31 | 0.15 |
| Bias | `learned-s3` | 0.30 | 0.10 |
| Bias | `learned-s3-arc` | 0.31 | 0.11 |
| Bias | `search3` | 0.26 | 0.37 |
| Whole | `c2` | 0.51 | 1.27 |
| Whole | `ctl` | 0.18 | 0.33 |
| Whole | `learned-s1` | 0.29 | 0.12 |
| Whole | `learned-s1-arc` | 0.31 | 0.17 |
| Whole | `learned-s2` | 0.31 | 0.10 |
| Whole | `learned-s2-arc` | 0.33 | 0.15 |
| Whole | `learned-s3` | 0.28 | 0.13 |
| Whole | `learned-s3-arc` | 0.31 | 0.22 |
| Whole | `search3` | 0.19 | 0.47 |

## Declaration: held-course periods given a manoeuvre, and Annex B targets called quiet

| System | Held course: false | One manoeuvre: called quiet | Two or more: called quiet | Annex B median | Held-course median |
| --- | --- | --- | --- | --- | --- |
| `broad` | 0.41 | 0.12 | 0.01 | 0.042 | 0.022 |
| `c2` | 0.04 | 0.22 | 0.04 | 0.085 | 0.016 |
| `ctl` | 0.41 | 0.11 | 0.00 | 0.039 | 0.024 |
| `ctl-d1-q0.01` | 0.08 | 0.14 | 0.01 | 0.040 | 0.017 |
| `learned-s1` | 0.01 | 0.29 | 0.07 | 0.050 | 0.025 |
| `learned-s1-arc` | 0.01 | 0.29 | 0.07 | 0.047 | 0.015 |
| `learned-s2` | 0.01 | 0.26 | 0.06 | 0.051 | 0.025 |
| `learned-s2-arc` | 0.01 | 0.26 | 0.06 | 0.049 | 0.015 |
| `learned-s3` | 0.01 | 0.26 | 0.06 | 0.049 | 0.025 |
| `learned-s3-arc` | 0.01 | 0.26 | 0.06 | 0.046 | 0.015 |
| `mix2` | 0.43 | 0.11 | 0.00 | 0.039 | 0.023 |
| `search3` | 0.49 | 0.13 | 0.00 | 0.041 | 0.031 |
| `search3-d1-q0.01` | 0.10 | 0.15 | 0.01 | 0.042 | 0.017 |

## What the estimates said

| Split | References held | Wild bearings edited a period | Correlated share (median) | Correlation used by `ctl` | Bayes factor for the broad prior (median log) | Share above 0 |
| --- | --- | --- | --- | --- | --- | --- |
| Annex B | 0.09 | 0.1 | 0.01 | 0.08 | -3.2 | 0.31 |
| Shifted | 0.27 | 0.1 | 0.00 | 0.08 | -1.3 | 0.42 |
| Shifted 2 | 0.06 | 0.1 | 0.00 | 0.07 | -2.4 | 0.40 |
| Held course | 0.00 | 0.1 | 0.02 | 0.06 | 4.9 | 0.91 |
| Correlated, mild | 0.21 | 0.0 | 0.52 | 1.00 | -1.4 | 0.40 |
| Correlated | 0.25 | 0.0 | 0.52 | 1.00 | -1.1 | 0.40 |
| Outliers | 0.19 | 7.5 | 0.00 | 0.07 | -3.1 | 0.32 |
| Outliers, harsh | 0.18 | 18.5 | 0.00 | 0.04 | -3.6 | 0.29 |
| Bias | 0.14 | 0.1 | 0.00 | 0.07 | -2.5 | 0.31 |
| Whole | 0.13 | 0.1 | 0.01 | 0.03 | -3.9 | 0.25 |
