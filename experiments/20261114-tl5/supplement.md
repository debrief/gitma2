## Manoeuvres missed, pooled over detectability bands (matched within 120 s)

| Split | System | Under 20 (manoeuvres) | Above 40 (manoeuvres) |
| --- | --- | --- | --- |
| Annex B | `ctl-d1-q0.01` | 0.81 (80) | 0.08 (402) |
| Annex B | `search3` | 0.75 (80) | 0.08 (402) |
| Annex B | `true` | 0.82 (80) | 0.08 (402) |
| Annex B | `c2` | 0.96 (80) | 0.41 (402) |
| Shifted | `ctl-d1-q0.01` | 0.83 (542) | 0.18 (782) |
| Shifted | `search3` | 0.84 (542) | 0.17 (782) |
| Shifted | `true` | 0.70 (542) | 0.12 (782) |
| Shifted | `c2` | 0.93 (542) | 0.49 (782) |
| Shifted 2 | `ctl-d1-q0.01` | 0.84 (19) | 0.07 (198) |
| Shifted 2 | `search3` | 0.74 (19) | 0.08 (198) |
| Shifted 2 | `true` | 0.84 (19) | 0.06 (198) |
| Shifted 2 | `c2` | 0.95 (19) | 0.36 (198) |
| Outliers | `ctl-d1-q0.01` | 0.76 (33) | 0.08 (197) |
| Outliers | `search3` | 0.82 (33) | 0.18 (197) |
| Outliers | `true` | 0.76 (33) | 0.11 (197) |
| Outliers | `c2` | 0.85 (33) | 0.50 (197) |

## The recommendation's logic (decision record), shifted split

- E4 at threshold 20, control ÷ `ref-d20`: 1.43 [1.28, 1.61]; lower limit above 1.10: **yes**.
- The control misses 0.18 of the 782 manoeuvres above 40; more than a third: **no**.
- Both needed for a proposer study to be recommended: **not recommended**.
