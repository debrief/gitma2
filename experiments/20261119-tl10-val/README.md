# Spec 030 validation (seed 362): soundness

CI run 44589038104 (`timelate/tl-o-val` at 09d03dc), plan `configs/timelate/tl-o.json`
(`74166535…`, registered in `experiments/20261119-tl10-decision/`), code `90a19712…`, clean tree,
seed 362, Annex B 110 engagements. Tables: `tables.md` (`scripts/research/tl10_tables.py`).

**Soundness passes**: span reference with times held, per-engagement geometric mean 0.915
[0.709, 1.149] over 56 engagements, inside [0.6, 1.6]; the joint solve answered every period.
The study proceeds to the test (seed 363).

Reported only (not decided on validation; later periods):

| | range |
|---|---|
| alone ÷ k4 | 1.512 [1.231, 1.825] (median 1.10) |
| alone ÷ k4, own turn | 1.201 [0.981, 1.502] |
| alone ÷ k4, no own turn | 1.785 [1.342, 2.452] |
| k4 ÷ joint | 1.671 [1.281, 2.229] |
| alone ÷ uninflated carried prior | 1.254 [1.003, 1.563] |
| k4 coverage (95%, 4 dof) | 0.975 (median d² 0.51) |
