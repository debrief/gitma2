# Spec 012: GPU run records

One folder per run (`run.json`, `plan.json`), copied from the `results/gputrain-*` branches,
which also hold the checkpoints. All on a Tesla T4 through Modal, code 51cc62b, plans as bound in
`../20261111-r-decision/`. The validation figures are the training loop's own (512 MAN2
scenarios of seed 327, folded rows at least 10 min after the zig); they are not scored results.

| Run | Stopped | Updates | Scenarios seen | T4-hours | Median abs. error of ln range | Median velocity error (m/s) |
| --- | --- | --- | --- | --- | --- | --- |
| Seed 1 | complete | 85,000 | 21.76 M | 9.03 | 0.084 | 1.79 |
| Seed 2 | time limit | 77,743 | 19.90 M | 9.67 | 0.083 | 1.82 |
| Seed 3 | time limit | 82,046 | 21.00 M | 9.67 | 0.083 | 1.82 |
| A tenth of the data | time limit | 41,512 of 42,500 | 10.63 M (2.18 M distinct) | 4.83 | 0.090 | 1.86 |
| Ownship only | complete | 25,000 | 6.40 M | 2.61 | 0.406 | 5.73 |

- **Deviation from the decision record**: seeds 2 and 3 reached their time limits at 91% and
  97% of the 85,000 registered updates (the schedule was sized from 635 scenarios a second; with
  the held-course share the containers ran at 570 to 670). At those points the cosine
  schedule's learning rate is about 2% and 0.3% of its peak. The three seeds' validation errors
  agree to 0.001 in ln range; the shortfall is reported, not repaired.
- Seed 2 and the tenth-of-data control started 23 minutes late after Modal's app-create rate
  limit refused them at launch.
- GPU time in total, pilots included: 38.06 T4-hours, about $25 at the measured $0.66 an hour.
