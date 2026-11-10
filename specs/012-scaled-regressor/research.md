# Research: spec 012

## R1. What the model reads and returns

- **Decision**: per row, in a canonical frame: sin and cos of the bearing, the ownship's
  displacement since the previous row (east, north), a validity flag, and the stated σ. The
  frame is rotated so that the first valid bearing points north, and lengths are in units of
  10 km, speeds in 10 m/s. Output at each prefix end: log range, and the target's velocity (two
  components) in the same frame, each with a log standard deviation.
- **Rationale**: the problem is invariant to rotation; fixing the frame removes a symmetry the
  model would otherwise have to learn, which is one candidate for gitma's precision floor (note
  01: its networks had to approximate products of geometry and time). Log range is what the
  scorer's relative range error measures. Position follows from range and the last bearing.
- **Alternatives**: raw north-up inputs with rotation augmentation (learns the symmetry from
  data; kept as nothing, to save budget); absolute ownship positions (not translation
  invariant).

## R2. Architecture

- **Decision**: a causal transformer. A front-end folds 3 consecutive rows (30 s) into one
  token, right-aligned so that a prefix's last row ends a token; 8 layers, width 256, 8 heads,
  feed-forward 1,024, pre-norm, learned position embeddings; 6.39 million parameters, twelve
  times gitma's largest model. Every token is a training target (the state at its last row), so
  one scenario gives up to 240 supervised prefixes in one pass.
- **Rationale**: attention can relate any two bearings directly, which is the triangulation the
  estimate needs; folding rows keeps the sequence at 240 tokens so the T4 budget buys millions
  of scenarios. Causality by an attention mask, tested by truncating prefixes.
- **Alternatives**: LSTM (gitma's family, the result in question); one token per row (9 times
  the attention cost, cutting the data budget below 10⁶); a larger model (the pilot may show
  the budget cannot train it).

## R3. Loss, schedule and the data budget

- **Loss**: Gaussian negative log-likelihood on (log range, velocity) with predicted standard
  deviations, in the β-weighted form (β = 0.5) so that rows the model calls uncertain are not
  ignored. Rows before the ownship zig are trained too: the truth there is undetermined from
  the bearings, and the loss lets the model say so with a large standard deviation.
- **Schedule**: AdamW, cosine decay with warm-up, mixed precision, batch 256 scenarios;
  checkpoint every 15 minutes and at the time limit.
- **Data budget**: the generator makes about 20,000 scenarios a second on one CPU core, so the
  GPU is the limit. Note 03 measured a 4-layer, width-128 transformer on 360 tokens at about
  1,300 scenarios a second on a T4. Scaling by depth, width and length puts the planned model
  somewhere near 100–300 a second: 10 hours is then 4 to 11 million scenarios. This is an
  estimate, not a measurement. **The pilot's first job is to measure it.** Rule, fixed now: at
  250 a second or more the plan stands; between 80 and 250 the budget per seed is what 10 hours
  buys and the record says so; below 80 the model is reduced once (to 6 layers, width 192)
  before the three seeds.
- **Tenth-of-the-data control**: the same model and number of updates on a stream that repeats
  its first tenth; if it scores the same, data were not the limit at this size.

## R4. Running on Modal

- **Decision**: `gputrain.yml` (branches `gputrain/**`) checks the ledger, then runs
  `modal run scripts/modal_train.py` and waits. The Modal function has a hard timeout of at most
  5 hours, so the Actions job (6-hour limit) can wait for it and commit the results itself; a
  10-hour seed is two chained segments that resume from a checkpoint on a Modal volume.
- **Rationale**: waiting keeps every credential in one place. A detached run (note 10 §9) would
  need the Modal function to push to GitHub, and so a second secret held outside GitHub. The
  hard timeout is also what enforces each run's share of the cap.
- **Secrets**: `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`, repository Actions secrets, read only
  by `gputrain.yml`, which runs on pushes to this repository's branches and never on pull
  requests from forks.
- **To verify at implementation** from Modal's current documentation, not from memory: the GPU
  selector, the timeout ceiling, volume commit semantics, and how billed GPU seconds are read
  back for the run record.

## R5. The budget

**Owner, 2026-11-10 (later): $50 in total**, replacing the 50 T4-hour cap this table was written
for. Modal bills the container's CPU and memory on top of the GPU rate, so the hours $50 buys
are not known until the throughput pilot's cost is read from Modal's usage page. The table's
shares stand (pilot 16%, three seeds 60%, controls 16%, reserve 8%); the hours are rescaled in
the decision record, and the workflow's cap (`CAP_HOURS`) is set from the measured cost so that
cap × cost per hour ≤ $50 less storage. A faster GPU is allowed if it buys more scenarios per
dollar (the pilot may compare a T4 with an L4 for a few minutes each).


| Use | T4-hours |
| --- | --- |
| Pilot: throughput, then learning curves | 8 |
| Three seeds of the carried configuration, 10 each | 30 |
| Control: ownship track only | 3 |
| Control: a tenth of the data | 5 |
| Reserve (a failed segment, a resume) | 4 |

- Each run's plan names its limit; the function's timeout enforces it; the run record states
  the GPU seconds used.
- **Ledger**: before starting, the workflow sums the GPU seconds in every run record on the
  `results/gputrain-*` branches and refuses a run whose limit would take the total past the cap.
- The controls are shorter than a seed; the write-up must say that the ownship-only control at
  3 hours is a lower bound on what the prior yields, not a matched-budget comparison.

## R6. Scoring and the readings

- `tma2-rpredict` writes the model's rows at the scorer's prefixes (G5 rows) in the existing
  prediction format, in double, with the covariance fields from the predicted standard
  deviations marked as the model's own.
- The existing scorer (`tma2-g2`, as Gate 2) scores them with `--predictions`, beside C″ (zig
  veto and fixed fade; `tma2-g2predict` kind `veto` with the fade plan), one leg, the oracle,
  the IMM, the EKF, and the known-manoeuvres bound (which is the full-window bound where the
  target has not changed).
- `tma2-rread` computes, from one scoring run's `errors.npz`: efficiency on settled held-course
  rows with a scenario-clustered interval, for the regressor and for batch least squares; the
  same by geometry band (quartiles of the bound's range standard deviation, the scorer's
  observability measure); and the paired differences on rows after a target change, by range
  quartile and in operational units. It prints the reading (FR-021).
- Scoring cost is the classical side's (C at about 16 s per engagement): 5,000 test scenarios
  in shards on CI, as Gate 2.

## R7. Known limits, stated before any result

- One architecture at one size: a floor would show that this model at this budget does not
  reach the bound, which is stronger than gitma's evidence but is not a proof about every
  direct model. A "reaches" result has no such caveat.
- The held-course rows on MAN2 data are the rows before the target's first change; they are a
  subset with shorter histories than gitma's constant-velocity data.
- The thresholds 1.25 and 2.0 are proposals (spec assumptions) until the decision record.
- Authors and reviewers are agents of one model family (note 10 §4).
