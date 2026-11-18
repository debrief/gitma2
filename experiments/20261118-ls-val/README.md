# Spec 026: validation (seed 350)

CI run 44257499250 (Intel Xeon 6975P-C; commit e27e183, the decision record's). It ran 10 + 10
realistic engagements of 6 and 12 hours (`configs/long/study-val.json`). The digests are
unchanged from `experiments/20261118-ls-decision/digests.json`. Outputs: `raw/`; `study.json`
is from `tma2-long study`.

**Soundness passes**, so the test on seed 351 follows:
- S1: 120 of 120 windows ran;
- S2: ctl ÷ the true-history fit is 1.50;
- S3: bearings held 0.86.

Reported only (validation decides nothing beyond soundness):
- **E1** (contact 1): 1.096 [0.988, 1.218].
  - Carry better in 39 windows, worse in 25, level in 56; twice better in 9, twice worse in 3.
  - Search CPU: 2.11 h from the carry against 3.97 h from nothing.
- **E1 on contact 2**: 1.007 [0.886, 1.153].
- **E2**: 2.00 [1.33, 2.72]; by band, contact 1 against contact 2:
  - 2–10 km: 1.2% against 2.2%;
  - 10–20 km: 1.5% against 2.4%;
  - 20–40 km: 1.8% against 5.3%.

  This is higher than tuning's 1.26, so the forecast "1.2 to 1.4, interval including 1" now
  looks low.
- **E3**: 1.21 [0.86, 1.87].
  - Share answered by 2-hour bin: 0.86, 0.93, 0.87, 0.71, 0.76, 0.85.
  - Median by bin: 0.19, 0.21, 0.22, 0.29, 0.25, 0.24.
