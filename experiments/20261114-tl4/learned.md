## L-c and L-d: the registered verdicts

| Split | Verdict | Seed | Declared control ÷ learned | Side | Hedged track ÷ learned | Side |
| --- | --- | --- | --- | --- | --- | --- |
| Shifted | not shown | `learned-s1-arc` | 0.82 [0.73, 0.91] | loses | 0.76 [0.67, 0.85] | loses |
| Shifted | not shown | `learned-s2-arc` | 0.80 [0.71, 0.90] | loses | 0.74 [0.66, 0.83] | loses |
| Shifted | not shown | `learned-s3-arc` | 0.82 [0.73, 0.91] | loses | 0.75 [0.67, 0.85] | loses |
| Shifted 2 | not shown | `learned-s1-arc` | 0.87 [0.79, 0.96] | loses | 0.91 [0.83, 1.01] | not separated |
| Shifted 2 | not shown | `learned-s2-arc` | 0.87 [0.79, 0.95] | loses | 0.90 [0.82, 0.99] | loses |
| Shifted 2 | not shown | `learned-s3-arc` | 0.94 [0.85, 1.05] | not separated | 0.99 [0.89, 1.09] | not separated |
| Correlated | not shown | `learned-s1-arc` | 0.83 [0.74, 0.92] | loses | 0.82 [0.73, 0.92] | loses |
| Correlated | not shown | `learned-s2-arc` | 0.83 [0.74, 0.92] | loses | 0.82 [0.73, 0.92] | loses |
| Correlated | not shown | `learned-s3-arc` | 0.84 [0.75, 0.94] | loses | 0.83 [0.74, 0.93] | loses |
| Outliers | not shown | `learned-s1-arc` | 0.78 [0.70, 0.89] | loses | 0.80 [0.71, 0.91] | loses |
| Outliers | not shown | `learned-s2-arc` | 0.77 [0.68, 0.88] | loses | 0.79 [0.70, 0.90] | loses |
| Outliers | not shown | `learned-s3-arc` | 0.81 [0.71, 0.91] | loses | 0.83 [0.73, 0.93] | loses |
| Bias | not shown | `learned-s1-arc` | 0.98 [0.88, 1.09] | not separated | 0.98 [0.88, 1.09] | not separated |
| Bias | not shown | `learned-s2-arc` | 1.00 [0.90, 1.09] | not separated | 0.99 [0.90, 1.09] | not separated |
| Bias | not shown | `learned-s3-arc` | 0.97 [0.86, 1.07] | not separated | 0.97 [0.87, 1.07] | not separated |
| Annex B | harm | `learned-s1-arc` | 0.82 [0.74, 0.90] | loses | 0.84 [0.76, 0.93] | loses |
| Annex B | harm | `learned-s2-arc` | 0.81 [0.73, 0.89] | loses | 0.83 [0.75, 0.93] | loses |
| Annex B | harm | `learned-s3-arc` | 0.82 [0.75, 0.91] | loses | 0.85 [0.77, 0.94] | loses |
| Held course | no harm shown | `learned-s1-arc` | 1.06 [1.01, 1.11] | wins | 1.51 [1.36, 1.67] | wins |
| Held course | no harm shown | `learned-s2-arc` | 1.06 [1.01, 1.11] | wins | 1.51 [1.36, 1.67] | wins |
| Held course | no harm shown | `learned-s3-arc` | 1.06 [1.01, 1.11] | wins | 1.51 [1.36, 1.67] | wins |

Learning shown on 0 mismatch split(s); harm: yes. What follows: the classical controls stand as the time-late system; the learned track stops.

## Each system ÷ each learned track (paired per period; above 1: the learned track is better)

### Annex B

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 1.59 [1.39, 1.86] | 0.35 | 0.19 |
| `c2` | `learned-s1-arc` | 1.83 [1.60, 2.09] | 0.31 | 0.11 |
| `c2` | `learned-s2` | 1.62 [1.40, 1.89] | 0.36 | 0.19 |
| `c2` | `learned-s2-arc` | 1.81 [1.59, 2.08] | 0.31 | 0.10 |
| `c2` | `learned-s3` | 1.73 [1.51, 1.99] | 0.33 | 0.18 |
| `c2` | `learned-s3-arc` | 1.85 [1.61, 2.11] | 0.31 | 0.09 |
| `ctl-d1-q0.01` | `learned-s1` | 0.71 [0.63, 0.80] | 0.59 | 0.37 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.82 [0.74, 0.90] | 0.61 | 0.20 |
| `ctl-d1-q0.01` | `learned-s2` | 0.72 [0.64, 0.82] | 0.58 | 0.37 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.81 [0.73, 0.89] | 0.60 | 0.20 |
| `ctl-d1-q0.01` | `learned-s3` | 0.77 [0.69, 0.87] | 0.54 | 0.33 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.82 [0.75, 0.91] | 0.59 | 0.19 |
| `ctl-h1` | `learned-s1` | 0.73 [0.66, 0.82] | 0.58 | 0.34 |
| `ctl-h1` | `learned-s1-arc` | 0.84 [0.76, 0.93] | 0.61 | 0.22 |
| `ctl-h1` | `learned-s2` | 0.75 [0.66, 0.84] | 0.56 | 0.35 |
| `ctl-h1` | `learned-s2-arc` | 0.83 [0.75, 0.93] | 0.60 | 0.21 |
| `ctl-h1` | `learned-s3` | 0.79 [0.71, 0.88] | 0.55 | 0.30 |
| `ctl-h1` | `learned-s3-arc` | 0.85 [0.77, 0.94] | 0.59 | 0.22 |
| `search3` | `learned-s1` | 0.78 [0.68, 0.89] | 0.57 | 0.35 |
| `search3` | `learned-s1-arc` | 0.89 [0.80, 0.99] | 0.57 | 0.18 |
| `search3` | `learned-s2` | 0.79 [0.69, 0.91] | 0.56 | 0.34 |
| `search3` | `learned-s2-arc` | 0.89 [0.80, 0.99] | 0.55 | 0.18 |
| `search3` | `learned-s3` | 0.84 [0.74, 0.96] | 0.53 | 0.32 |
| `search3` | `learned-s3-arc` | 0.90 [0.81, 1.01] | 0.56 | 0.18 |

### Shifted

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 1.70 [1.52, 1.91] | 0.29 | 0.09 |
| `c2` | `learned-s1-arc` | 1.38 [1.22, 1.56] | 0.41 | 0.16 |
| `c2` | `learned-s2` | 1.72 [1.52, 1.94] | 0.30 | 0.10 |
| `c2` | `learned-s2-arc` | 1.35 [1.20, 1.52] | 0.41 | 0.17 |
| `c2` | `learned-s3` | 1.71 [1.53, 1.93] | 0.28 | 0.10 |
| `c2` | `learned-s3-arc` | 1.38 [1.22, 1.55] | 0.40 | 0.15 |
| `ctl-d1-q0.01` | `learned-s1` | 1.01 [0.90, 1.13] | 0.45 | 0.20 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.82 [0.73, 0.91] | 0.54 | 0.27 |
| `ctl-d1-q0.01` | `learned-s2` | 1.02 [0.90, 1.15] | 0.45 | 0.20 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.80 [0.71, 0.90] | 0.54 | 0.27 |
| `ctl-d1-q0.01` | `learned-s3` | 1.02 [0.90, 1.15] | 0.44 | 0.19 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.82 [0.73, 0.91] | 0.54 | 0.25 |
| `ctl-h1` | `learned-s1` | 0.93 [0.84, 1.04] | 0.49 | 0.22 |
| `ctl-h1` | `learned-s1-arc` | 0.76 [0.67, 0.85] | 0.61 | 0.29 |
| `ctl-h1` | `learned-s2` | 0.94 [0.84, 1.06] | 0.49 | 0.22 |
| `ctl-h1` | `learned-s2-arc` | 0.74 [0.66, 0.83] | 0.59 | 0.31 |
| `ctl-h1` | `learned-s3` | 0.94 [0.84, 1.06] | 0.48 | 0.22 |
| `ctl-h1` | `learned-s3-arc` | 0.75 [0.67, 0.85] | 0.61 | 0.29 |
| `search3` | `learned-s1` | 1.04 [0.93, 1.16] | 0.43 | 0.20 |
| `search3` | `learned-s1-arc` | 0.84 [0.75, 0.94] | 0.55 | 0.26 |
| `search3` | `learned-s2` | 1.04 [0.92, 1.18] | 0.43 | 0.19 |
| `search3` | `learned-s2-arc` | 0.82 [0.73, 0.93] | 0.55 | 0.26 |
| `search3` | `learned-s3` | 1.04 [0.93, 1.18] | 0.43 | 0.19 |
| `search3` | `learned-s3-arc` | 0.84 [0.75, 0.94] | 0.55 | 0.25 |

### Shifted 2

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 1.46 [1.27, 1.68] | 0.39 | 0.18 |
| `c2` | `learned-s1-arc` | 2.12 [1.83, 2.45] | 0.27 | 0.10 |
| `c2` | `learned-s2` | 1.48 [1.29, 1.70] | 0.37 | 0.17 |
| `c2` | `learned-s2-arc` | 2.10 [1.82, 2.43] | 0.28 | 0.10 |
| `c2` | `learned-s3` | 1.51 [1.31, 1.74] | 0.37 | 0.19 |
| `c2` | `learned-s3-arc` | 2.29 [1.98, 2.65] | 0.26 | 0.09 |
| `ctl-d1-q0.01` | `learned-s1` | 0.60 [0.53, 0.68] | 0.67 | 0.40 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.87 [0.79, 0.96] | 0.52 | 0.15 |
| `ctl-d1-q0.01` | `learned-s2` | 0.61 [0.54, 0.69] | 0.67 | 0.38 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.87 [0.79, 0.95] | 0.50 | 0.14 |
| `ctl-d1-q0.01` | `learned-s3` | 0.62 [0.55, 0.70] | 0.65 | 0.37 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.94 [0.85, 1.05] | 0.50 | 0.14 |
| `ctl-h1` | `learned-s1` | 0.63 [0.56, 0.70] | 0.65 | 0.37 |
| `ctl-h1` | `learned-s1-arc` | 0.91 [0.83, 1.01] | 0.53 | 0.17 |
| `ctl-h1` | `learned-s2` | 0.64 [0.57, 0.71] | 0.66 | 0.34 |
| `ctl-h1` | `learned-s2-arc` | 0.90 [0.82, 0.99] | 0.52 | 0.16 |
| `ctl-h1` | `learned-s3` | 0.65 [0.57, 0.73] | 0.63 | 0.34 |
| `ctl-h1` | `learned-s3-arc` | 0.99 [0.89, 1.09] | 0.53 | 0.15 |
| `search3` | `learned-s1` | 0.65 [0.58, 0.73] | 0.66 | 0.37 |
| `search3` | `learned-s1-arc` | 0.94 [0.86, 1.03] | 0.48 | 0.12 |
| `search3` | `learned-s2` | 0.66 [0.58, 0.74] | 0.65 | 0.36 |
| `search3` | `learned-s2-arc` | 0.94 [0.85, 1.02] | 0.48 | 0.12 |
| `search3` | `learned-s3` | 0.67 [0.59, 0.76] | 0.63 | 0.34 |
| `search3` | `learned-s3-arc` | 1.02 [0.93, 1.13] | 0.47 | 0.11 |

### Held course

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 0.62 [0.54, 0.72] | 0.66 | 0.40 |
| `c2` | `learned-s1-arc` | 1.06 [0.99, 1.14] | 0.48 | 0.05 |
| `c2` | `learned-s2` | 0.63 [0.55, 0.73] | 0.70 | 0.35 |
| `c2` | `learned-s2-arc` | 1.07 [0.99, 1.14] | 0.48 | 0.05 |
| `c2` | `learned-s3` | 0.64 [0.56, 0.74] | 0.67 | 0.36 |
| `c2` | `learned-s3-arc` | 1.07 [1.00, 1.14] | 0.48 | 0.05 |
| `ctl-d1-q0.01` | `learned-s1` | 0.62 [0.54, 0.71] | 0.67 | 0.40 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 1.06 [1.01, 1.11] | 0.48 | 0.01 |
| `ctl-d1-q0.01` | `learned-s2` | 0.63 [0.54, 0.72] | 0.69 | 0.36 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 1.06 [1.01, 1.11] | 0.46 | 0.01 |
| `ctl-d1-q0.01` | `learned-s3` | 0.64 [0.55, 0.74] | 0.65 | 0.35 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 1.06 [1.01, 1.11] | 0.46 | 0.01 |
| `ctl-h1` | `learned-s1` | 0.88 [0.77, 1.02] | 0.50 | 0.21 |
| `ctl-h1` | `learned-s1-arc` | 1.51 [1.36, 1.67] | 0.35 | 0.08 |
| `ctl-h1` | `learned-s2` | 0.89 [0.77, 1.03] | 0.52 | 0.25 |
| `ctl-h1` | `learned-s2-arc` | 1.51 [1.36, 1.67] | 0.35 | 0.08 |
| `ctl-h1` | `learned-s3` | 0.91 [0.78, 1.04] | 0.50 | 0.22 |
| `ctl-h1` | `learned-s3-arc` | 1.51 [1.36, 1.67] | 0.35 | 0.08 |
| `search3` | `learned-s1` | 1.05 [0.89, 1.23] | 0.48 | 0.24 |
| `search3` | `learned-s1-arc` | 1.79 [1.57, 2.05] | 0.29 | 0.05 |
| `search3` | `learned-s2` | 1.06 [0.90, 1.25] | 0.51 | 0.27 |
| `search3` | `learned-s2-arc` | 1.79 [1.57, 2.05] | 0.29 | 0.05 |
| `search3` | `learned-s3` | 1.08 [0.90, 1.28] | 0.45 | 0.24 |
| `search3` | `learned-s3-arc` | 1.80 [1.57, 2.06] | 0.28 | 0.05 |

### Correlated, mild

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 3.28 [2.75, 3.86] | 0.13 | 0.07 |
| `c2` | `learned-s1-arc` | 3.17 [2.58, 3.89] | 0.22 | 0.08 |
| `c2` | `learned-s2` | 3.22 [2.70, 3.82] | 0.13 | 0.06 |
| `c2` | `learned-s2-arc` | 2.92 [2.40, 3.57] | 0.22 | 0.09 |
| `c2` | `learned-s3` | 3.34 [2.78, 3.98] | 0.12 | 0.07 |
| `c2` | `learned-s3-arc` | 3.25 [2.62, 4.04] | 0.23 | 0.10 |
| `ctl-d1-q0.01` | `learned-s1` | 0.86 [0.74, 1.00] | 0.53 | 0.28 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.84 [0.72, 0.96] | 0.59 | 0.22 |
| `ctl-d1-q0.01` | `learned-s2` | 0.85 [0.71, 1.00] | 0.53 | 0.29 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.77 [0.65, 0.89] | 0.59 | 0.23 |
| `ctl-d1-q0.01` | `learned-s3` | 0.88 [0.75, 1.03] | 0.54 | 0.28 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.86 [0.73, 1.00] | 0.59 | 0.19 |
| `ctl-h1` | `learned-s1` | 0.87 [0.75, 1.00] | 0.55 | 0.24 |
| `ctl-h1` | `learned-s1-arc` | 0.84 [0.72, 0.97] | 0.58 | 0.23 |
| `ctl-h1` | `learned-s2` | 0.85 [0.73, 0.98] | 0.54 | 0.28 |
| `ctl-h1` | `learned-s2-arc` | 0.77 [0.66, 0.90] | 0.61 | 0.24 |
| `ctl-h1` | `learned-s3` | 0.89 [0.77, 1.02] | 0.55 | 0.25 |
| `ctl-h1` | `learned-s3-arc` | 0.86 [0.73, 1.00] | 0.57 | 0.20 |
| `search3` | `learned-s1` | 1.10 [0.95, 1.28] | 0.46 | 0.17 |
| `search3` | `learned-s1-arc` | 1.07 [0.90, 1.27] | 0.48 | 0.19 |
| `search3` | `learned-s2` | 1.08 [0.92, 1.26] | 0.49 | 0.18 |
| `search3` | `learned-s2-arc` | 0.98 [0.83, 1.17] | 0.49 | 0.22 |
| `search3` | `learned-s3` | 1.13 [0.97, 1.31] | 0.43 | 0.20 |
| `search3` | `learned-s3-arc` | 1.10 [0.92, 1.30] | 0.46 | 0.19 |

### Correlated

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 2.70 [2.35, 3.09] | 0.18 | 0.05 |
| `c2` | `learned-s1-arc` | 2.24 [1.92, 2.60] | 0.27 | 0.11 |
| `c2` | `learned-s2` | 2.64 [2.31, 3.02] | 0.18 | 0.05 |
| `c2` | `learned-s2-arc` | 2.25 [1.92, 2.60] | 0.25 | 0.11 |
| `c2` | `learned-s3` | 2.68 [2.33, 3.06] | 0.20 | 0.06 |
| `c2` | `learned-s3-arc` | 2.28 [1.94, 2.62] | 0.27 | 0.11 |
| `ctl-d1-q0.01` | `learned-s1` | 0.99 [0.88, 1.13] | 0.49 | 0.22 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.83 [0.74, 0.92] | 0.56 | 0.23 |
| `ctl-d1-q0.01` | `learned-s2` | 0.97 [0.85, 1.10] | 0.48 | 0.24 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.83 [0.74, 0.92] | 0.56 | 0.22 |
| `ctl-d1-q0.01` | `learned-s3` | 0.99 [0.86, 1.12] | 0.51 | 0.22 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.84 [0.75, 0.94] | 0.55 | 0.22 |
| `ctl-h1` | `learned-s1` | 0.98 [0.88, 1.10] | 0.50 | 0.22 |
| `ctl-h1` | `learned-s1-arc` | 0.82 [0.73, 0.92] | 0.60 | 0.26 |
| `ctl-h1` | `learned-s2` | 0.96 [0.86, 1.07] | 0.50 | 0.23 |
| `ctl-h1` | `learned-s2-arc` | 0.82 [0.73, 0.92] | 0.60 | 0.24 |
| `ctl-h1` | `learned-s3` | 0.97 [0.87, 1.09] | 0.52 | 0.23 |
| `ctl-h1` | `learned-s3-arc` | 0.83 [0.74, 0.93] | 0.61 | 0.25 |
| `search3` | `learned-s1` | 1.32 [1.17, 1.50] | 0.35 | 0.17 |
| `search3` | `learned-s1-arc` | 1.10 [0.95, 1.27] | 0.45 | 0.21 |
| `search3` | `learned-s2` | 1.29 [1.14, 1.47] | 0.36 | 0.17 |
| `search3` | `learned-s2-arc` | 1.10 [0.95, 1.26] | 0.45 | 0.20 |
| `search3` | `learned-s3` | 1.31 [1.15, 1.49] | 0.35 | 0.19 |
| `search3` | `learned-s3-arc` | 1.12 [0.97, 1.28] | 0.44 | 0.21 |

### Outliers

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 3.27 [2.78, 3.85] | 0.19 | 0.07 |
| `c2` | `learned-s1-arc` | 4.08 [3.44, 4.88] | 0.18 | 0.06 |
| `c2` | `learned-s2` | 3.37 [2.85, 3.99] | 0.19 | 0.07 |
| `c2` | `learned-s2-arc` | 4.03 [3.37, 4.82] | 0.21 | 0.08 |
| `c2` | `learned-s3` | 3.46 [2.96, 4.12] | 0.19 | 0.08 |
| `c2` | `learned-s3-arc` | 4.21 [3.46, 5.08] | 0.18 | 0.08 |
| `ctl-d1-q0.01` | `learned-s1` | 0.63 [0.54, 0.73] | 0.62 | 0.40 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.78 [0.70, 0.89] | 0.58 | 0.23 |
| `ctl-d1-q0.01` | `learned-s2` | 0.65 [0.55, 0.76] | 0.61 | 0.38 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.77 [0.68, 0.88] | 0.59 | 0.22 |
| `ctl-d1-q0.01` | `learned-s3` | 0.67 [0.57, 0.77] | 0.59 | 0.41 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.81 [0.71, 0.91] | 0.57 | 0.21 |
| `ctl-h1` | `learned-s1` | 0.64 [0.56, 0.74] | 0.60 | 0.39 |
| `ctl-h1` | `learned-s1-arc` | 0.80 [0.71, 0.91] | 0.60 | 0.25 |
| `ctl-h1` | `learned-s2` | 0.66 [0.57, 0.76] | 0.61 | 0.38 |
| `ctl-h1` | `learned-s2-arc` | 0.79 [0.70, 0.90] | 0.60 | 0.25 |
| `ctl-h1` | `learned-s3` | 0.68 [0.59, 0.78] | 0.62 | 0.38 |
| `ctl-h1` | `learned-s3-arc` | 0.83 [0.73, 0.93] | 0.60 | 0.24 |
| `search3` | `learned-s1` | 1.05 [0.92, 1.21] | 0.45 | 0.25 |
| `search3` | `learned-s1-arc` | 1.32 [1.14, 1.52] | 0.41 | 0.17 |
| `search3` | `learned-s2` | 1.09 [0.95, 1.25] | 0.43 | 0.24 |
| `search3` | `learned-s2-arc` | 1.30 [1.12, 1.49] | 0.42 | 0.18 |
| `search3` | `learned-s3` | 1.12 [0.98, 1.28] | 0.44 | 0.22 |
| `search3` | `learned-s3-arc` | 1.36 [1.18, 1.58] | 0.42 | 0.17 |

### Outliers, harsh

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 5.00 [4.18, 5.96] | 0.10 | 0.03 |
| `c2` | `learned-s1-arc` | 6.58 [5.22, 8.17] | 0.10 | 0.04 |
| `c2` | `learned-s2` | 5.01 [4.22, 5.96] | 0.09 | 0.03 |
| `c2` | `learned-s2-arc` | 6.44 [5.16, 7.96] | 0.10 | 0.05 |
| `c2` | `learned-s3` | 5.15 [4.30, 6.10] | 0.09 | 0.03 |
| `c2` | `learned-s3-arc` | 6.35 [5.07, 7.89] | 0.10 | 0.05 |
| `ctl-d1-q0.01` | `learned-s1` | 0.67 [0.55, 0.81] | 0.58 | 0.38 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.88 [0.75, 1.02] | 0.52 | 0.23 |
| `ctl-d1-q0.01` | `learned-s2` | 0.67 [0.56, 0.80] | 0.60 | 0.38 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.86 [0.74, 0.99] | 0.52 | 0.20 |
| `ctl-d1-q0.01` | `learned-s3` | 0.69 [0.57, 0.83] | 0.59 | 0.36 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.85 [0.73, 0.98] | 0.58 | 0.21 |
| `ctl-h1` | `learned-s1` | 0.67 [0.56, 0.80] | 0.63 | 0.40 |
| `ctl-h1` | `learned-s1-arc` | 0.88 [0.75, 1.03] | 0.58 | 0.25 |
| `ctl-h1` | `learned-s2` | 0.67 [0.57, 0.79] | 0.65 | 0.39 |
| `ctl-h1` | `learned-s2-arc` | 0.86 [0.74, 1.00] | 0.59 | 0.23 |
| `ctl-h1` | `learned-s3` | 0.69 [0.58, 0.82] | 0.60 | 0.35 |
| `ctl-h1` | `learned-s3-arc` | 0.85 [0.73, 0.98] | 0.61 | 0.23 |
| `search3` | `learned-s1` | 1.63 [1.38, 1.94] | 0.32 | 0.13 |
| `search3` | `learned-s1-arc` | 2.14 [1.76, 2.61] | 0.30 | 0.10 |
| `search3` | `learned-s2` | 1.63 [1.39, 1.91] | 0.31 | 0.13 |
| `search3` | `learned-s2-arc` | 2.10 [1.72, 2.56] | 0.30 | 0.10 |
| `search3` | `learned-s3` | 1.68 [1.43, 1.96] | 0.30 | 0.11 |
| `search3` | `learned-s3-arc` | 2.07 [1.72, 2.49] | 0.28 | 0.10 |

### Bias

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 1.74 [1.50, 2.02] | 0.33 | 0.12 |
| `c2` | `learned-s1-arc` | 1.86 [1.62, 2.15] | 0.32 | 0.10 |
| `c2` | `learned-s2` | 1.69 [1.46, 1.96] | 0.33 | 0.14 |
| `c2` | `learned-s2-arc` | 1.88 [1.65, 2.16] | 0.31 | 0.07 |
| `c2` | `learned-s3` | 1.87 [1.63, 2.16] | 0.29 | 0.11 |
| `c2` | `learned-s3-arc` | 1.84 [1.60, 2.12] | 0.31 | 0.08 |
| `ctl-d1-q0.01` | `learned-s1` | 0.92 [0.81, 1.05] | 0.52 | 0.23 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.98 [0.88, 1.09] | 0.49 | 0.15 |
| `ctl-d1-q0.01` | `learned-s2` | 0.89 [0.78, 1.03] | 0.50 | 0.25 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 1.00 [0.90, 1.09] | 0.47 | 0.14 |
| `ctl-d1-q0.01` | `learned-s3` | 0.99 [0.87, 1.13] | 0.46 | 0.23 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.97 [0.86, 1.07] | 0.50 | 0.15 |
| `ctl-h1` | `learned-s1` | 0.92 [0.81, 1.03] | 0.54 | 0.21 |
| `ctl-h1` | `learned-s1-arc` | 0.98 [0.88, 1.09] | 0.54 | 0.15 |
| `ctl-h1` | `learned-s2` | 0.89 [0.78, 1.01] | 0.53 | 0.23 |
| `ctl-h1` | `learned-s2-arc` | 0.99 [0.90, 1.09] | 0.54 | 0.14 |
| `ctl-h1` | `learned-s3` | 0.99 [0.87, 1.11] | 0.47 | 0.22 |
| `ctl-h1` | `learned-s3-arc` | 0.97 [0.87, 1.07] | 0.54 | 0.15 |
| `search3` | `learned-s1` | 0.92 [0.81, 1.05] | 0.51 | 0.23 |
| `search3` | `learned-s1-arc` | 0.99 [0.89, 1.09] | 0.48 | 0.15 |
| `search3` | `learned-s2` | 0.89 [0.78, 1.02] | 0.50 | 0.25 |
| `search3` | `learned-s2-arc` | 1.00 [0.90, 1.10] | 0.47 | 0.14 |
| `search3` | `learned-s3` | 0.99 [0.87, 1.13] | 0.45 | 0.22 |
| `search3` | `learned-s3-arc` | 0.97 [0.87, 1.08] | 0.49 | 0.15 |

### Whole

| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |
| --- | --- | --- | --- | --- |
| `c2` | `learned-s1` | 1.52 [1.11, 2.12] | 0.35 | 0.15 |
| `c2` | `learned-s1-arc` | 2.00 [1.53, 2.68] | 0.30 | 0.13 |
| `c2` | `learned-s2` | 1.42 [1.05, 1.96] | 0.43 | 0.18 |
| `c2` | `learned-s2-arc` | 1.81 [1.40, 2.45] | 0.35 | 0.13 |
| `c2` | `learned-s3` | 1.65 [1.21, 2.28] | 0.37 | 0.13 |
| `c2` | `learned-s3-arc` | 1.81 [1.34, 2.44] | 0.32 | 0.13 |
| `ctl-d1-q0.01` | `learned-s1` | 0.62 [0.46, 0.84] | 0.55 | 0.33 |
| `ctl-d1-q0.01` | `learned-s1-arc` | 0.82 [0.63, 1.07] | 0.50 | 0.25 |
| `ctl-d1-q0.01` | `learned-s2` | 0.58 [0.41, 0.81] | 0.58 | 0.40 |
| `ctl-d1-q0.01` | `learned-s2-arc` | 0.74 [0.58, 0.96] | 0.55 | 0.30 |
| `ctl-d1-q0.01` | `learned-s3` | 0.68 [0.50, 0.93] | 0.58 | 0.37 |
| `ctl-d1-q0.01` | `learned-s3-arc` | 0.74 [0.58, 0.95] | 0.53 | 0.27 |
| `ctl-h1` | `learned-s1` | 0.63 [0.48, 0.84] | 0.55 | 0.32 |
| `ctl-h1` | `learned-s1-arc` | 0.83 [0.65, 1.06] | 0.57 | 0.28 |
| `ctl-h1` | `learned-s2` | 0.59 [0.42, 0.81] | 0.62 | 0.35 |
| `ctl-h1` | `learned-s2-arc` | 0.76 [0.60, 0.95] | 0.63 | 0.32 |
| `ctl-h1` | `learned-s3` | 0.69 [0.51, 0.92] | 0.58 | 0.35 |
| `ctl-h1` | `learned-s3-arc` | 0.75 [0.59, 0.95] | 0.60 | 0.27 |
| `search3` | `learned-s1` | 0.66 [0.48, 0.90] | 0.53 | 0.33 |
| `search3` | `learned-s1-arc` | 0.87 [0.65, 1.17] | 0.47 | 0.27 |
| `search3` | `learned-s2` | 0.62 [0.44, 0.86] | 0.57 | 0.40 |
| `search3` | `learned-s2-arc` | 0.79 [0.60, 1.04] | 0.52 | 0.33 |
| `search3` | `learned-s3` | 0.72 [0.52, 0.99] | 0.58 | 0.35 |
| `search3` | `learned-s3-arc` | 0.79 [0.61, 1.01] | 0.50 | 0.30 |

## Efficiency against the bound (range, course, speed) and rows without a state

| Split | System | Range | Course | Speed | Periods without a track |
| --- | --- | --- | --- | --- | --- |
| Annex B | `c2` | 3.26 | 4.30 | 3.48 | 0 |
| Annex B | `ctl-d1-q0.01` | 1.66 | 1.98 | 1.57 | 0 |
| Annex B | `ctl-h1` | 1.66 | 1.99 | 1.60 | 0 |
| Annex B | `learned-s1` | 2.06 | 2.81 | 2.31 | 0 |
| Annex B | `learned-s1-arc` | 1.94 | 2.21 | 1.78 | 0 |
| Annex B | `learned-s2` | 2.13 | 2.99 | 2.26 | 0 |
| Annex B | `learned-s2-arc` | 1.92 | 2.26 | 1.76 | 0 |
| Annex B | `learned-s3` | 1.89 | 2.94 | 2.17 | 0 |
| Annex B | `learned-s3-arc` | 1.93 | 2.34 | 1.80 | 0 |
| Annex B | `search3` | 1.71 | 1.99 | 1.62 | 0 |
| Shifted | `c2` | 3.41 | 3.96 | 3.25 | 0 |
| Shifted | `ctl-d1-q0.01` | 2.13 | 2.34 | 2.08 | 0 |
| Shifted | `ctl-h1` | 2.06 | 2.34 | 2.02 | 0 |
| Shifted | `learned-s1` | 2.03 | 2.78 | 2.09 | 0 |
| Shifted | `learned-s1-arc` | 2.69 | 3.13 | 2.47 | 0 |
| Shifted | `learned-s2` | 2.00 | 2.75 | 2.06 | 0 |
| Shifted | `learned-s2-arc` | 2.66 | 3.25 | 2.34 | 0 |
| Shifted | `learned-s3` | 1.94 | 2.76 | 2.09 | 0 |
| Shifted | `learned-s3-arc` | 2.64 | 3.19 | 2.49 | 0 |
| Shifted | `search3` | 2.13 | 2.12 | 1.93 | 0 |
| Shifted 2 | `c2` | 3.56 | 4.33 | 3.56 | 0 |
| Shifted 2 | `ctl-d1-q0.01` | 1.45 | 1.80 | 1.50 | 0 |
| Shifted 2 | `ctl-h1` | 1.59 | 1.98 | 1.71 | 0 |
| Shifted 2 | `learned-s1` | 2.36 | 3.57 | 2.82 | 0 |
| Shifted 2 | `learned-s1-arc` | 1.74 | 1.98 | 1.68 | 0 |
| Shifted 2 | `learned-s2` | 2.34 | 3.64 | 2.70 | 0 |
| Shifted 2 | `learned-s2-arc` | 1.80 | 2.01 | 1.75 | 0 |
| Shifted 2 | `learned-s3` | 2.25 | 3.52 | 2.66 | 0 |
| Shifted 2 | `learned-s3-arc` | 1.66 | 1.93 | 1.68 | 0 |
| Shifted 2 | `search3` | 1.59 | 1.89 | 1.60 | 0 |
| Held course | `c2` | 0.97 | 1.00 | 0.89 | 0 |
| Held course | `ctl-d1-q0.01` | 0.95 | 1.01 | 0.84 | 0 |
| Held course | `ctl-h1` | 1.46 | 1.64 | 1.73 | 0 |
| Held course | `learned-s1` | 1.45 | 1.85 | 1.50 | 0 |
| Held course | `learned-s1-arc` | 0.91 | 0.96 | 0.79 | 0 |
| Held course | `learned-s2` | 1.34 | 1.87 | 1.49 | 0 |
| Held course | `learned-s2-arc` | 0.91 | 0.96 | 0.79 | 0 |
| Held course | `learned-s3` | 1.28 | 1.83 | 1.45 | 0 |
| Held course | `learned-s3-arc` | 0.91 | 0.94 | 0.79 | 0 |
| Held course | `search3` | 1.79 | 2.19 | 2.36 | 0 |
| Correlated, mild | `c2` | 13.07 | 17.27 | 9.79 | 0 |
| Correlated, mild | `ctl-d1-q0.01` | 3.25 | 3.94 | 2.85 | 0 |
| Correlated, mild | `ctl-h1` | 3.26 | 3.98 | 3.29 | 0 |
| Correlated, mild | `learned-s1` | 4.11 | 5.21 | 4.02 | 0 |
| Correlated, mild | `learned-s1-arc` | 3.95 | 4.97 | 3.84 | 0 |
| Correlated, mild | `learned-s2` | 4.22 | 5.30 | 3.97 | 0 |
| Correlated, mild | `learned-s2-arc` | 4.45 | 5.48 | 4.20 | 0 |
| Correlated, mild | `learned-s3` | 4.17 | 5.29 | 4.08 | 0 |
| Correlated, mild | `learned-s3-arc` | 3.90 | 4.92 | 3.79 | 0 |
| Correlated, mild | `search3` | 4.45 | 6.07 | 3.91 | 0 |
| Correlated | `c2` | 11.57 | 17.87 | 9.00 | 0 |
| Correlated | `ctl-d1-q0.01` | 4.26 | 5.57 | 3.87 | 0 |
| Correlated | `ctl-h1` | 4.22 | 5.32 | 3.85 | 0 |
| Correlated | `learned-s1` | 4.20 | 6.07 | 4.41 | 0 |
| Correlated | `learned-s1-arc` | 5.12 | 6.36 | 4.62 | 0 |
| Correlated | `learned-s2` | 4.35 | 6.29 | 4.32 | 0 |
| Correlated | `learned-s2-arc` | 5.22 | 6.30 | 5.05 | 0 |
| Correlated | `learned-s3` | 4.34 | 6.18 | 4.51 | 0 |
| Correlated | `learned-s3-arc` | 5.08 | 6.10 | 5.05 | 0 |
| Correlated | `search3` | 5.62 | 8.63 | 5.05 | 0 |
| Outliers | `c2` | 10.28 | 12.90 | 7.44 | 0 |
| Outliers | `ctl-d1-q0.01` | 1.70 | 1.99 | 1.49 | 0 |
| Outliers | `ctl-h1` | 1.75 | 2.14 | 1.59 | 0 |
| Outliers | `learned-s1` | 2.49 | 3.16 | 2.81 | 0 |
| Outliers | `learned-s1-arc` | 2.08 | 2.58 | 1.93 | 0 |
| Outliers | `learned-s2` | 2.52 | 3.47 | 2.54 | 0 |
| Outliers | `learned-s2-arc` | 2.11 | 2.62 | 2.09 | 0 |
| Outliers | `learned-s3` | 2.35 | 3.35 | 2.91 | 0 |
| Outliers | `learned-s3-arc` | 2.09 | 2.52 | 1.98 | 0 |
| Outliers | `search3` | 3.03 | 3.59 | 3.16 | 0 |
| Outliers, harsh | `c2` | 15.21 | 22.83 | 10.10 | 0 |
| Outliers, harsh | `ctl-d1-q0.01` | 2.03 | 2.16 | 1.67 | 0 |
| Outliers, harsh | `ctl-h1` | 2.03 | 2.29 | 1.73 | 0 |
| Outliers, harsh | `learned-s1` | 2.91 | 3.70 | 3.17 | 0 |
| Outliers, harsh | `learned-s1-arc` | 2.08 | 2.74 | 1.61 | 0 |
| Outliers, harsh | `learned-s2` | 2.72 | 3.87 | 2.84 | 0 |
| Outliers, harsh | `learned-s2-arc` | 2.08 | 2.72 | 1.80 | 0 |
| Outliers, harsh | `learned-s3` | 2.86 | 4.02 | 3.03 | 0 |
| Outliers, harsh | `learned-s3-arc` | 2.18 | 2.78 | 1.81 | 0 |
| Outliers, harsh | `search3` | 5.11 | 6.64 | 4.10 | 0 |
| Bias | `c2` | 5.03 | 6.24 | 4.79 | 0 |
| Bias | `ctl-d1-q0.01` | 2.69 | 3.56 | 2.65 | 0 |
| Bias | `ctl-h1` | 2.72 | 3.57 | 2.78 | 0 |
| Bias | `learned-s1` | 2.78 | 3.96 | 2.93 | 0 |
| Bias | `learned-s1-arc` | 2.71 | 4.01 | 3.01 | 0 |
| Bias | `learned-s2` | 2.65 | 4.13 | 2.92 | 0 |
| Bias | `learned-s2-arc` | 2.79 | 4.03 | 2.94 | 0 |
| Bias | `learned-s3` | 2.48 | 4.01 | 2.84 | 0 |
| Bias | `learned-s3-arc` | 2.85 | 3.80 | 3.09 | 0 |
| Bias | `search3` | 2.68 | 3.56 | 2.67 | 0 |
| Whole | `c2` | 5.94 | 7.54 | 5.46 | 0 |
| Whole | `ctl-d1-q0.01` | 2.16 | 2.26 | 1.88 | 0 |
| Whole | `ctl-h1` | 2.25 | 2.32 | 1.92 | 0 |
| Whole | `learned-s1` | 3.12 | 5.00 | 3.73 | 0 |
| Whole | `learned-s1-arc` | 2.73 | 3.21 | 2.45 | 0 |
| Whole | `learned-s2` | 3.30 | 5.50 | 3.53 | 0 |
| Whole | `learned-s2-arc` | 2.74 | 3.21 | 2.43 | 0 |
| Whole | `learned-s3` | 3.26 | 4.83 | 3.65 | 0 |
| Whole | `learned-s3-arc` | 2.46 | 2.98 | 2.12 | 0 |
| Whole | `search3` | 2.16 | 2.29 | 1.88 | 0 |
