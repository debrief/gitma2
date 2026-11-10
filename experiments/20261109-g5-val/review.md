# Gate 5 validation stop: agent review panel

Five independent, read-only reviewers looked at the stop: evaluation statistics, estimation and
numerics, TMA domain, reproducibility and process, and red team. Each was briefed on:
- the committed record (`README.md`, `validation.json`, `by-head/`);
- the decision record, the baseline and the code;
- the per-row arrays of the scoring run.

Each returned a verdict with findings tagged [blocker], [major] or [minor], with evidence. Their
scratch scripts are not part of the record. The findings below are condensed, and the numbers are
the reviewers'.

# Round 1

All five returned **approve-with-findings**:
- the stop at validation is correct, and G5-d is void under the registered rule;
- G5-d alone blocks, because G5-b's slope point lies inside its band;
- the carried seed and the control of record are right;
- seed 320 is untouched;
- every artefact reproduces byte for byte.

None raised a blocker. The majors correct the record's Reading and the gate's design. The README
has been rewritten accordingly.

## Statistics: approve-with-findings

**Confirmed independently:**
- coverage 0.938 / 0.938;
- hit − P −0.006;
- slope 1.253 [1.057, 1.466];
- AUC 0.654;
- log gain 0.798;
- the carried seed (s1), which is the median on both scales;
- G5-d −0.081 [−0.126, −0.041], with the encoder-shuffle rule failing at −0.039 [−0.067, −0.015].

**Findings:**
- [major] "P is honest within the band" on flagged rows is false. The classical rule's slice is
  −0.054 [−0.087, −0.018], with its point outside ±0.05. The head's interval also excludes 0.
- [major] The Reading omitted the carried statement's under-confidence at short range: +0.117
  [+0.044, +0.188] at 2–5 km, and +0.22 at 0–2 km (52 rows, ungated).
- [major] The synthetic check (R7) did not represent the real data. The logit sd of P was 0.87
  synthetic against 0.48 real, and there was no within-scenario correlation (about 0.24 real).
  - Resampling hits from the head's real P with the real clusters: a calibrated statement is G5-b
    inconclusive in about 29% of datasets.
  - A −0.08 shortfall on the flagged slice fails in only 5 of 12; a −0.10 shortfall in 10 of 12.
- [minor] Head − encoder shuffle (best) is −0.041 [−0.074, −0.012], so the encoder helps within the
  head. "At least half" should read "about half".
- [minor] The head's margin is all in the range and speed intervals; course is +0.004
  [−0.013, +0.021].
- [minor] Counting unstated rows as P = 0 raises the AUC by about 0.007.
- [minor] The calibration slope is a sound check with appropriate intervals.

## Estimation and numerics: approve-with-findings

**Confirmed:**
- `arc_norm` agrees with dense integration to 9e-10 over κ from 1e-8 to 1e8 and X up to 45°.
- The arc mass equals P to 1e-12.
- The log score is the same function in training and scoring, and it is proper.
- The proxy is causal and reproduces from the data. Its statistics against the truth match the
  noise model (bias mean 0.79 against E|Z| 0.80; χ²/n 0.97).
- The head starts exactly at the classical rule.
- The encoder shuffle permutes exactly the 64 encoder-state columns, and there is no other route
  for the encoder state.
- The points are identical.

**Findings:**
- [major] The course arc is badly fitted.
  - Validation course log scores: temperature −0.904, classical −1.028, head −1.032.
  - X is tied to a, and the log density jumps by about 1.4 nats at X, which gradient fits cannot
    see. Scaling a by 1.5 improves the classical rule on its own stream (−0.966 to −0.861).
  - It is not under-converged: 600 and 2,000 steps give the same result.
- [major] The Platt map caused G5-b's slope result.
  - The unmapped classical P has slope 1.06 [0.94, 1.20] on the scoring rows.
  - The map's b of 0.85 has a tuning interval of [0.67, 1.05].
  - The same 500 tuning scenarios also fitted the proxy, the temperature and the early stopping.
- [minor] The shuffle's best epoch is chosen with the real encoder state (a small leak; the void
  stands either way). The course loss scale could blow up if the mean NLL approached 0. "Every
  probed row" means 200 rows.

## TMA domain: approve-with-findings

- [major] The oracle comparison is unfair, because the oracle's statement is the temperature (AUC
  0.54). "No causal statement can fix that" is not shown.
- [major] The flag catches 42% of unsettled rows, and 55% of flagged rows are settled. The 572
  unflagged unsettled rows state 0.53 and hit 0.22 (129 of them at P ≥ 0.6, hitting 0.49). The row
  and the write-up must say that P assumes no undetected manoeuvre in the last ~5 min.
- [major] The flag also reacts to geometry:
  - its rate falls with the minute (0.27 to 0.18) while the unsettled rate stays near 0.26;
  - at 0–2 km it flags 0.37 of rows against 0.16 unsettled.

  Ownship manoeuvres and target changes during ownship turns (Annex B axes) are not measured.
- [minor]
  - The intervals are honest but wide: range ×/÷1.74 at the median, speed ±7 kt.
  - P's meaning varies with X (0.8° to 45°).
  - Not measured: how quickly P responds to a manoeuvre, flag flicker, joint course and range.
  - P is still compressed.

## Reproducibility and process: approve-with-findings

**Confirmed:**
- **Order.** The bands came at 733de07, the baseline result at 22:26 and the decision at 06dd705,
  before training, the stated files and the scoring.
- **Digests.** The plan and proxy digests are stable throughout.
- **Proxy circularity.** The disclosed argument was verified by refitting the proxy byte for byte.
- **Slope fix.** It changes nothing bound.
- **Reproduction.** The proxy caches, the stated files and `validation.json` reproduce byte for
  byte.
- **Seed 320** is untouched.
- **The SRD row** matches `decision.json`.

**Findings:**
- [major] The stated files and the proxy caches were made in the session, not on CI. They
  reproduce, but their headers do not bind the feature or proxy cache digests.
- [minor]
  - §9's "No Gate 5 result exists" is now stale.
  - The control of record is picked on the first control's scale, while the decision's wording says
    the control of record's.
  - FR-023 was cross-fitted on scoring rows, not fitted on tuning rows.
  - The stated rows keep `schema_version` 0.25.0.
  - `validation.json` says `fail` where the README says void.

## Red team: approve-with-findings

- [major] An encoder-free MLP beats the head. It is 64×64 tanh, trained on the stream on the sds,
  C's code, the proxy design and the minute; its architecture was fixed in advance; two seeds.
  - MLP − classical: −0.16 [−0.23, −0.10].
  - Head − MLP: +0.082 [+0.025, +0.147].
  - One MLP seed passes G5-b outright.
  - A 105-term quadratic rule does not match the head (−0.008 [−0.066, +0.048]).

  So no learning from E-w's state is shown, and the bounded head underfits.
- [major] The flagged slice is honest only on average over a mix: unsettled −0.14, settled +0.04.
  P moves little with the flag.
- [major, design] The per-slice band has little power. About ±0.075 intervals on 200-row slices let
  a slice off by 0.12 pass.
- [minor]
  - **Trivial statements:** an all-constant statement fails G5-a, G5-b and G5-c. Lookup statements
    fail G5-b, caught only by the 2–5 km slice. An AUC of 0.55 is reachable with four cells.
  - **Platt:** the map's b explains the slope exactly (1.25 × 0.85 = 1.06).
  - **The carried classical rule** is dominated by the MLP.

## Outcome of round 1

The stop at validation is upheld unanimously. The README's Reading has been rewritten with each
correction:
- the flagged slice is mildly over-confident;
- the caveat about undetected manoeuvres;
- the flag's geometry response;
- short-range under-confidence;
- the oracle claim withdrawn;
- the Platt map as the cause of the slope result;
- the course arc badly fitted;
- no learning from the encoder state, since an encoder-free MLP beats the head;
- the carried statement is not the best available;
- the weak per-slice check;
- the FR-023 deviation.

Recommended follow-on, for the write-up and spec 011:

1. **Fit the arc without gradients.** Search a, or decouple X from the spread, by grid or
   line search. The temperature's wider arc already scores 0.12 nats better.
2. **Drop or regularise the Platt map.** Either keep P unmapped, which gives slope 1.06, or fit the
   map on more tuning rows with an interval. Use separate tuning scenarios for each fit (the proxy,
   the temperature, early stopping, the map).
3. **Register stronger controls before any result.** Add an encoder-free MLP and an encoder-only
   shuffle of an unbounded head, and take the learning claim against the best of them.
4. **Give the per-slice check power.** Use point bands calibrated by a synthetic check that
   reproduces the real P spread and cluster correlation, and require power of at least 0.8 against
   0.08 shortfalls.
5. **Improve the manoeuvre signal.**
   - Add ownship-manoeuvre and range-band strata (Annex B).
   - Separate geometry from target manoeuvres in the proxy.
   - State the caveat about undetected manoeuvres in the row (a field description) and on any
     display.
6. **Fix the references and provenance.**
   - Give the oracle a statement that uses the manoeuvre times it knows, as a fair ceiling.
   - Run the stated files and the proxy caches on CI, with digests in their headers.
