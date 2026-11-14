## Median period range error

| System | Annex B | Shifted | Shifted 2 | Held course | Correlated, mild | Correlated | Outliers | Outliers, harsh | Bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Periods (scored) | 150 (141) | 100 (92) | 100 (97) | 100 (92) | 60 (57) | 80 (75) | 80 (75) | 60 (57) | 80 (75) |
| `broad` | 0.039 | 0.096 | 0.026 | 0.023 | – | – | – | – | – |
| `c2` | 0.083 | 0.152 | 0.061 | 0.014 | 0.342 | 0.308 | 0.235 | 0.450 | 0.089 |
| `corr` | 0.045 | – | – | – | 0.085 | 0.085 | – | – | – |
| `ctl` | 0.039 | 0.092 | 0.028 | 0.024 | 0.101 | 0.090 | 0.042 | 0.039 | 0.073 |
| `edit` | 0.040 | – | – | – | – | – | 0.051 | 0.051 | – |
| `history-best` | 0.035 | 0.048 | 0.027 | 0.016 | 0.058 | 0.055 | 0.041 | 0.089 | 0.037 |
| `history-fixed` | 0.022 | 0.043 | 0.019 | 0.016 | 0.048 | 0.060 | 0.051 | 0.105 | 0.038 |
| `history-map` | 0.033 | 0.055 | 0.027 | 0.016 | 0.065 | 0.081 | 0.048 | 0.091 | 0.039 |
| `mix2` | 0.040 | 0.092 | 0.028 | 0.023 | – | – | – | – | – |
| `one-leg` | 0.386 | 0.344 | 0.355 | 0.014 | 0.490 | 0.483 | 0.486 | 0.527 | 0.467 |
| `search3` | 0.040 | 0.109 | 0.029 | 0.028 | 0.128 | 0.178 | 0.089 | 0.158 | 0.075 |

## The standing search ÷ each system (paired per period; above 1: better)

### Annex B

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 0.96 [0.85, 1.08] | 0.45 |
| `broad-h1` | 0.96 [0.85, 1.09] | 0.50 |
| `c2` | 0.47 [0.39, 0.57] | 0.72 |
| `corr` | 0.89 [0.81, 0.96] | 0.26 |
| `corr-h1` | 0.94 [0.84, 1.06] | 0.50 |
| `ctl` | 0.98 [0.92, 1.05] | 0.20 |
| `ctl-h1` | 1.03 [0.94, 1.13] | 0.52 |
| `edit` | 1.00 [0.99, 1.00] | 0.03 |
| `edit-h1` | 1.06 [0.98, 1.14] | 0.45 |
| `mix2` | 0.99 [0.93, 1.05] | 0.16 |
| `mix2-h1` | 1.03 [0.95, 1.13] | 0.51 |
| `search3-h1` | 1.06 [0.99, 1.15] | 0.43 |

### Shifted

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 0.92 [0.78, 1.08] | 0.52 |
| `broad-h1` | 0.98 [0.84, 1.17] | 0.52 |
| `c2` | 0.62 [0.48, 0.81] | 0.64 |
| `ctl` | 0.99 [0.91, 1.08] | 0.16 |
| `ctl-h1` | 1.03 [0.91, 1.18] | 0.43 |
| `mix2` | 0.99 [0.92, 1.07] | 0.15 |
| `mix2-h1` | 1.06 [0.94, 1.21] | 0.42 |
| `search3-h1` | 1.07 [0.97, 1.22] | 0.42 |

### Shifted 2

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.08 [0.94, 1.24] | 0.44 |
| `broad-h1` | 1.03 [0.89, 1.18] | 0.52 |
| `c2` | 0.58 [0.43, 0.76] | 0.69 |
| `ctl` | 1.05 [0.99, 1.12] | 0.16 |
| `ctl-h1` | 1.02 [0.91, 1.14] | 0.46 |
| `mix2` | 1.05 [0.98, 1.12] | 0.12 |
| `mix2-h1` | 1.02 [0.92, 1.14] | 0.44 |
| `search3-h1` | 1.00 [0.93, 1.06] | 0.45 |

### Held course

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `broad` | 1.16 [0.97, 1.38] | 0.18 |
| `broad-h1` | 1.16 [0.96, 1.39] | 0.40 |
| `c2` | 1.85 [1.45, 2.36] | 0.34 |
| `ctl` | 1.14 [0.92, 1.38] | 0.21 |
| `ctl-h1` | 1.11 [0.93, 1.33] | 0.39 |
| `mix2` | 1.12 [0.94, 1.34] | 0.17 |
| `mix2-h1` | 1.13 [0.94, 1.35] | 0.39 |
| `search3-h1` | 0.98 [0.89, 1.08] | 0.41 |

### Correlated, mild

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.41 [0.31, 0.55] | 0.77 |
| `corr` | 1.52 [1.13, 2.07] | 0.40 |
| `corr-h1` | 1.41 [1.11, 1.80] | 0.37 |
| `ctl` | 1.44 [1.10, 1.89] | 0.44 |
| `ctl-h1` | 1.39 [1.12, 1.75] | 0.39 |
| `search3-h1` | 0.97 [0.86, 1.07] | 0.40 |

### Correlated

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.61 [0.48, 0.77] | 0.73 |
| `corr` | 2.07 [1.57, 2.71] | 0.29 |
| `corr-h1` | 2.04 [1.58, 2.66] | 0.27 |
| `ctl` | 1.79 [1.38, 2.35] | 0.35 |
| `ctl-h1` | 1.82 [1.43, 2.35] | 0.31 |
| `search3-h1` | 1.05 [1.00, 1.12] | 0.48 |

### Outliers

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.34 [0.25, 0.46] | 0.79 |
| `ctl` | 1.69 [1.24, 2.33] | 0.29 |
| `ctl-h1` | 1.73 [1.24, 2.41] | 0.33 |
| `edit` | 1.64 [1.21, 2.27] | 0.29 |
| `edit-h1` | 1.70 [1.22, 2.35] | 0.29 |
| `search3-h1` | 1.00 [0.93, 1.06] | 0.41 |

### Outliers, harsh

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.39 [0.28, 0.53] | 0.75 |
| `ctl` | 3.12 [2.09, 4.54] | 0.19 |
| `ctl-h1` | 2.87 [1.95, 4.18] | 0.23 |
| `edit` | 2.84 [1.93, 4.07] | 0.23 |
| `edit-h1` | 2.63 [1.83, 3.72] | 0.25 |
| `search3-h1` | 1.04 [0.95, 1.12] | 0.32 |

### Bias

| System | Ratio | Share of periods where the search is better |
| --- | --- | --- |
| `c2` | 0.62 [0.48, 0.81] | 0.68 |
| `ctl` | 0.99 [0.90, 1.07] | 0.12 |
| `ctl-h1` | 1.06 [0.93, 1.18] | 0.43 |
| `search3-h1` | 1.06 [1.01, 1.11] | 0.39 |

## Share of the gap from the search to the reference that a control closes

| Split | Control | Share |
| --- | --- | --- |
| Annex B | `broad` | -0.13 [-0.80, 0.24] |
| Annex B | `corr` | -0.40 [-1.14, -0.12] |
| Annex B | `ctl` | -0.06 [-0.38, 0.15] |
| Annex B | `edit` | -0.01 [-0.05, 0.01] |
| Annex B | `mix2` | -0.05 [-0.34, 0.15] |
| Shifted | `broad` | -0.12 [-0.39, 0.10] |
| Shifted | `ctl` | -0.01 [-0.14, 0.10] |
| Shifted | `mix2` | -0.01 [-0.12, 0.10] |
| Shifted 2 | `broad` | 0.41 [-0.48, 1.91] |
| Shifted 2 | `ctl` | 0.26 [-0.10, 1.19] |
| Shifted 2 | `mix2` | 0.26 [-0.10, 1.19] |
| Held course | `broad` | 0.24 [-0.08, 0.44] |
| Held course | `ctl` | 0.21 [-0.18, 0.44] |
| Held course | `mix2` | 0.19 [-0.14, 0.40] |
| Correlated, mild | `corr` | 0.54 [0.20, 0.87] |
| Correlated, mild | `ctl` | 0.46 [0.15, 0.77] |
| Correlated | `corr` | 0.65 [0.44, 0.90] |
| Correlated | `ctl` | 0.52 [0.31, 0.76] |
| Outliers | `ctl` | 1.17 [0.58, 2.75] |
| Outliers | `edit` | 1.11 [0.50, 2.62] |
| Outliers, harsh | `ctl` | 1.63 [1.14, 2.54] |
| Outliers, harsh | `edit` | 1.50 [1.01, 2.37] |
| Bias | `ctl` | -0.03 [-0.27, 0.16] |

## System ÷ the true-history reference, by how the reference is fitted

| Split | System | times free | held where drifted | times held |
| --- | --- | --- | --- | --- |
| Annex B | `search3` | 1.33 [1.14, 1.57] | 1.34 [1.15, 1.59] | 1.76 [1.48, 2.11] |
| Annex B | `ctl` | 1.35 [1.16, 1.60] | 1.37 [1.17, 1.63] | 1.79 [1.49, 2.17] |
| Shifted | `search3` | 1.72 [1.38, 2.16] | 2.08 [1.68, 2.61] | 2.33 [1.86, 3.01] |
| Shifted | `ctl` | 1.73 [1.40, 2.17] | 2.10 [1.69, 2.64] | 2.35 [1.88, 3.00] |
| Shifted 2 | `search3` | 1.20 [1.04, 1.40] | 1.20 [1.04, 1.40] | 1.48 [1.19, 1.86] |
| Shifted 2 | `ctl` | 1.14 [0.98, 1.35] | 1.15 [0.98, 1.36] | 1.41 [1.12, 1.78] |
| Held course | `search3` | 1.87 [1.47, 2.41] | 1.87 [1.47, 2.41] | 1.87 [1.47, 2.41] |
| Held course | `ctl` | 1.64 [1.36, 1.99] | 1.64 [1.36, 1.99] | 1.64 [1.36, 1.99] |
| Correlated, mild | `search3` | 1.88 [1.41, 2.53] | 2.18 [1.62, 2.93] | 2.87 [2.04, 4.01] |
| Correlated, mild | `ctl` | 1.31 [1.00, 1.71] | 1.52 [1.15, 2.00] | 2.00 [1.45, 2.80] |
| Correlated | `search3` | 2.15 [1.67, 2.80] | 3.06 [2.29, 4.07] | 3.52 [2.55, 4.91] |
| Correlated | `ctl` | 1.20 [0.94, 1.56] | 1.71 [1.26, 2.29] | 1.97 [1.43, 2.72] |
| Outliers | `search3` | 1.37 [1.03, 1.81] | 1.57 [1.16, 2.11] | 1.71 [1.21, 2.39] |
| Outliers | `ctl` | 0.81 [0.59, 1.10] | 0.93 [0.69, 1.23] | 1.01 [0.74, 1.33] |
| Outliers, harsh | `search3` | 1.73 [1.30, 2.34] | 2.01 [1.48, 2.72] | 2.50 [1.77, 3.60] |
| Outliers, harsh | `ctl` | 0.55 [0.40, 0.79] | 0.64 [0.46, 0.90] | 0.80 [0.56, 1.15] |
| Bias | `search3` | 1.55 [1.18, 2.05] | 1.64 [1.29, 2.14] | 1.71 [1.28, 2.34] |
| Bias | `ctl` | 1.57 [1.20, 2.08] | 1.66 [1.30, 2.16] | 1.73 [1.28, 2.38] |

## Manoeuvres missed (share) and false (per period), matched within 120 s

| Split | System | Missed | False |
| --- | --- | --- | --- |
| Annex B | `broad` | 0.29 | 0.31 |
| Annex B | `c2` | 0.54 | 0.77 |
| Annex B | `corr` | 0.27 | 0.22 |
| Annex B | `ctl` | 0.27 | 0.29 |
| Annex B | `edit` | 0.25 | 0.25 |
| Annex B | `mix2` | 0.27 | 0.28 |
| Annex B | `search3` | 0.25 | 0.26 |
| Shifted | `broad` | 0.50 | 0.44 |
| Shifted | `c2` | 0.73 | 1.00 |
| Shifted | `ctl` | 0.47 | 0.36 |
| Shifted | `mix2` | 0.47 | 0.36 |
| Shifted | `search3` | 0.47 | 0.31 |
| Shifted 2 | `broad` | 0.15 | 0.15 |
| Shifted 2 | `c2` | 0.45 | 0.71 |
| Shifted 2 | `ctl` | 0.11 | 0.14 |
| Shifted 2 | `mix2` | 0.11 | 0.14 |
| Shifted 2 | `search3` | 0.12 | 0.17 |
| Held course | `broad` | – | 0.50 |
| Held course | `c2` | – | 0.03 |
| Held course | `ctl` | – | 0.53 |
| Held course | `mix2` | – | 0.53 |
| Held course | `search3` | – | 0.61 |
| Correlated, mild | `c2` | 0.60 | 2.52 |
| Correlated, mild | `corr` | 0.37 | 0.37 |
| Correlated, mild | `ctl` | 0.35 | 0.32 |
| Correlated, mild | `search3` | 0.34 | 1.07 |
| Correlated | `c2` | 0.57 | 2.71 |
| Correlated | `corr` | 0.43 | 0.50 |
| Correlated | `ctl` | 0.42 | 0.41 |
| Correlated | `search3` | 0.42 | 1.48 |
| Outliers | `c2` | 0.51 | 2.09 |
| Outliers | `ctl` | 0.27 | 0.31 |
| Outliers | `edit` | 0.25 | 0.30 |
| Outliers | `search3` | 0.26 | 0.57 |
| Outliers, harsh | `c2` | 0.60 | 3.67 |
| Outliers, harsh | `ctl` | 0.28 | 0.33 |
| Outliers, harsh | `edit` | 0.25 | 0.30 |
| Outliers, harsh | `search3` | 0.36 | 1.28 |
| Bias | `c2` | 0.55 | 0.86 |
| Bias | `ctl` | 0.31 | 0.39 |
| Bias | `search3` | 0.29 | 0.40 |

## Declaration: held-course periods given a manoeuvre, and Annex B targets called quiet

| System | Held course: false | One manoeuvre: called quiet | Two or more: called quiet | Annex B median | Held-course median |
| --- | --- | --- | --- | --- | --- |
| `broad` | 0.48 | 0.16 | 0.01 | 0.039 | 0.023 |
| `c2` | 0.01 | 0.21 | 0.02 | 0.083 | 0.014 |
| `ctl` | 0.50 | 0.16 | 0.01 | 0.039 | 0.024 |
| `ctl-d1-q0.01` | 0.07 | 0.18 | 0.02 | 0.040 | 0.016 |
| `mix2` | 0.50 | 0.16 | 0.01 | 0.040 | 0.023 |
| `search3` | 0.52 | 0.12 | 0.01 | 0.040 | 0.028 |
| `search3-d1-q0.01` | 0.11 | 0.18 | 0.02 | 0.040 | 0.017 |

## What the estimates said

| Split | References held | Wild bearings edited a period | Correlated share (median) | Correlation used by `ctl` | Bayes factor for the broad prior (median log) | Share above 0 |
| --- | --- | --- | --- | --- | --- | --- |
| Annex B | 0.11 | 0.0 | 0.02 | 0.05 | -3.2 | 0.35 |
| Shifted | 0.37 | 0.0 | 0.02 | 0.04 | -0.8 | 0.43 |
| Shifted 2 | 0.03 | 0.0 | 0.02 | 0.05 | -2.7 | 0.35 |
| Held course | 0.00 | 0.0 | 0.02 | 0.06 | 5.4 | 0.91 |
| Correlated, mild | 0.18 | 0.0 | 0.52 | 1.00 | -1.5 | 0.35 |
| Correlated | 0.28 | 0.0 | 0.53 | 1.00 | -1.2 | 0.41 |
| Outliers | 0.23 | 8.5 | 0.00 | 0.01 | -2.5 | 0.35 |
| Outliers, harsh | 0.18 | 20.6 | 0.00 | 0.02 | -1.9 | 0.37 |
| Bias | 0.20 | 0.0 | 0.03 | 0.03 | -3.6 | 0.26 |
