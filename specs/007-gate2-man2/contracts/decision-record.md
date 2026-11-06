# Decision record: Gate2Decision

Committed in `experiments/<date>-g2-decision/` before any E training. Its SHA-256 is bound in
every gate manifest.

## Required content

- **Seeds:**
  - validation 314 (tuning 0–499, scoring 500–1499);
  - training stream 318 (count, commit, digests);
  - test 319 (count; generated after this record; digests in an amendment).
- **C:**
  - parameters, parameter digest and code digest;
  - the open-transition hand-over (from `experiments/20261106-c3-val/`);
  - the knot cap (12).
- **E:** configurations, the training plan path and its SHA-256, the components (E = E-w + E-s;
  E-w reported).
- **Criteria** (the SRD §5 Gate 2 row as amended, owner 2026-11-06):
  - G2-a: E / IMM, median range and course over all G5 rows, wholly below 1;
  - G2-b: settled rows' range, course and speed, E / one leg, wholly below 1.1;
  - G2-c: E's gap recovered (median range), wholly above 0.5;
  - G2-d: E − C, gap recovered, wholly above zero; void by the shuffled rule;
  - 97.5% scenario-clustered paired bootstrap, 2,000 resamples, `inverted_cdf`;
  - pass, fail and inconclusive as constitution IV.
- **Carried-seed rule:** the median of three seeds by validation gap recovered.
- **Shuffled rule:** the shuffled control minus C on validation must not lie wholly above zero.
- **Validation rule:** every gated point meets its limit on validation, or the test split is not
  generated.
- **Re-score:** inconclusive counts as not passed. The constitution's re-score is not taken (no
  minimum effect size).
- **Follow-on:** proposed in the write-up with a recommended default (SRD §5).
- **Forecast:** as research R7, refined with validation numbers.
