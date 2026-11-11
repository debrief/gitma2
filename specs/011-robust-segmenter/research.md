# Research: spec 011

## R1. Keeping C frozen

- **Decision**: C-r lives in a new module, `segment/robust.py`, which imports C's generator
  (`confirm._confirm_one`), nominators and `intervals_at` unchanged and supplies its own driver
  for the costs. No file in `segment/codeid.SOURCES` is edited; a test asserts both digests.
- **Rationale**: C's `code_sha256` covers `segment/confirm.py`, `segmenter.py` and
  `physics/layer.py` (spec 010 gotcha). The confirmation logic is a coroutine that asks for
  costs, so a different cost can be supplied from outside.
- **Alternatives**: a `robust` flag in `confirm.py` (changes the frozen digest; rejected).

## R2. Where C-r acts: confirmation

- **Decision**: robust costs in the confirmation test; nominators as C's.
- **Rationale** (diagnosis): false transitions rise 3.7 times under outliers and misses do not
  rise; adding the true change starts as nominations leaves the false transitions where they
  were. C accepts a candidate when the drop in the sum of squared residuals exceeds a χ² point:
  one 10 σ bearing contributes about 100 to that sum, against a threshold of 13.8, so any knot
  that partly absorbs it buys a transition. (This arithmetic is the hypothesis; phase 1 measures
  which decisions over-accept before the design is fixed.)
- **Spec change**: FR-010 said "in nomination and confirmation". It now reads: in confirmation,
  and in nomination only if the pilot shows an effect on accuracy or run time.
- **Alternatives considered**:
  - *A causal outlier pre-filter* (flag a bearing far from a robust local line through the
    previous 12–24, then run C unchanged). Tried on 40 engagements of seed 323: 82–88% of
    outliers over 4 σ flagged, with 4–7% of good bearings flagged. Too lossy for a hard
    rejection; why the false flags are so many was not established. Not pursued.
  - *Raising C's threshold*: lowers false transitions and raises misses on every condition; it
    is the trivial control, run in the pilot as a reference line (τ × 1.5, × 2).

## R3. The robust test

- **Fit**: each hypothesis (base, candidate) is solved by iteratively reweighted least squares
  with Huber weights, constant 2.0 (Gate H's frozen value), three reweightings, through the
  weighted layer subclass of spec 010 (`headroom/gls.py`).
- **Statistic**: the drop in Huber cost, Σ 2ρ(r/s), base minus candidate.
- **Scale s**: the stated σ by default. Pilot alternative (FR-014: it reads neither
  hypothesis): 1.4826 × the median absolute second difference of the bearings up to the prefix
  row, ÷ √6. Measured on seed 323 (150 engagements): on clean data it is 1.17 × the stated σ at
  the median (0.96–1.56 at the 5% and 95% points), and why it is above 1 is not established.
- **Threshold**: C's χ² point × E[ψ²]/E[ψ′] for the Huber constant (0.964 at 2.0), the scaling
  of a Huber cost drop under Gaussian errors; applied by dividing the costs, so the 2- and
  4-degree-of-freedom points both scale.
- **Reweightings**: 2 after the plain start (3 solves per request), for run time; not searched.
- **Dropped before the pilot**: a threshold correction for correlation (the diagnosis puts
  correlated error's segmentation part at +0.032 [−0.005, +0.070]; correlated error alone is
  measured at the gate) and weights reused from the base hypothesis (it biases against a real
  change, and the driver sees the base only for some requests).

## R4. Settings rule (FR-013), declared before the pilot

- Settings: Huber constant (2.0, 1.345), scale (stated, estimated), and the reference lines
  τ × 1.5 and × 2 for plain C (`configs/headroom/gr-pilot.json`).
- Pilot: 60 engagements of seed 323, primary condition and off. A setting whose two values
  differ by less than 0.005 in median range error (robust final solve) on both is fixed at its
  cheaper value.
- Choice among the rest, on the 150 engagements: the lowest median range error on the primary
  condition among those whose clean-data error is within 2% of C″-r's; ties to the cheaper.
- The final solve's robust settings are Gate H's and are not searched.

## R5. Gate R

- **Systems**, all with the Gate H robust control in the final solve, 12 knots: C″-r (C's
  segmentation; the baseline), C-r, the true-segmentation reference. Beside them: C″ plain, one
  leg, IMM, EKF.
- **Headline**: share closed = (C″-r − C-r) ÷ (C″-r − reference), median relative range error,
  primary condition, G5 rows, paired scenario-clustered bootstrap, 97.5% as Gate H.
- **R-a** (soundness, clean data): C-r's median range error over C″-r's, minus 1: point at most
  5% and interval not wholly above 2% (the form the owner chose for H-b, adopted here).
- **R-b** (owner, 2026-11-10): adopted as the standing control if the share's interval is
  wholly above zero; **closed** if also (C-r − reference) ÷ reference has its interval wholly
  below 10%; otherwise open headroom, stated with its interval.
- **Validation** stops the gate only on R-a or an unsound pipeline (C-r with unit weights not
  reproducing C), never on a small share.
- **Registered breakdowns** (FR-022): by quartile of true range, per kind, operational units,
  rows every system answers, P90, segmentation counts for C and C-r (`gr_diagnosis.py`).

## R6. Sizes and cost

- C: 16 s per engagement clean, about 75 s under outliers (3-engagement trial). C-r: three
  reweightings per request, but fewer accepted transitions to carry; budget 4 × C clean.
- Test primary 2,000 engagements: about 2,000 × (75 + 64) s ≈ 77 core-hours, 20 shards on
  4-core runners ≈ 1 h each. One run at a time.

## R7. Known limits, stated before any result

- The outlier model (independent, additive, 10 σ) is the family Huber weights were made for;
  Gate H's panel made the same point. Bursty outliers are out of scope and named as such.
- A share closed is relative to this C; the remainder is headroom for any segmenter, learned or
  not, and the true-segmentation reference is not a ceiling for systems that do not segment.
- Seed 323 has now been used for the diagnosis and will be used for the pilot; nothing chosen
  on it is a result.
