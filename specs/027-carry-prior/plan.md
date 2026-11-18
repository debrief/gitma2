# Plan: spec 027

## Code (new modules only; `ctl`, `ctl-carry`, the simulator and spec 026's bound files untouched)

- **`src/tma2/long/carried.py`**: the carried prior and the search under it.
  - `CarriedPrior`: a mean (x, y, course, speed at the window's first row, window frame) and
    a precision.
  - `joint_fit_c` and `log_evidence_c` mirror `timelate.retest.joint_fit` and `log_evidence`:
    - the fit appends the carried residuals;
    - the evidence adds the carried Gaussian's log density;
    - the Laplace Hessian holds the carried residuals' Jacobian.
  - The search (`evidence_search_c`, `elimination_path_c`) mirrors `timelate.search` and
    `hedge.elimination_path` on those two functions.
  - With no carried prior, everything equals the originals exactly (unit test).
  - The base prior's broad state factor stays beside the carried Gaussian. It is nearly flat
    against it.
- **The carried estimate** (`hand_on`): the previous window's declared history is refitted,
  with the prior that window itself received, on its bearings before the hand-over time t_o
  (the next window's first row).
  - Manoeuvres starting at or after t_o are dropped.
  - The state at t_o, (x, y, course, speed), gets a covariance H⁻¹ propagated through a
    numerical Jacobian. H is the Laplace Hessian, with spec 015's stand-in precisions for open
    directions.
  - The estimate moves to the next window's frame.
- **Widening** (`widen`): cov × `scale`.
  - Course variance grows by `ρ_c·τ·E[Δc²]` and speed variance by `ρ_s·τ·E[Δv²]`, where
    τ = (t_o − last valid bearing before t_o) + `tail_s`.
  - ρ_c and ρ_s are Annex B's rates of manoeuvres with a course change and with a speed
    change: the kind weights over the mean leg.
  - Position variance grows by (v²·Δvar_c + Δvar_s)·g²/3, where g is the gap before t_o.
- **Guard**: D = (bearing cost + carried residuals²) at ctl-prior's declared fit, minus the
  bearing cost of the same history refitted without the carried prior.
  - Rejected if D exceeds the χ²(4) quantile at level α. The quantiles are tabulated, since
    there is no scipy here.
  - On rejection the window is declared as the same window's `ctl-carry` answer.
- **`src/tma2/long/carry2.py`**: the runner.
  - `solve_window2` is `carry.solve_window` (copied; a unit test asserts its `ctl` and
    `ctl-carry` equal the original on a short window) plus `ctl-prior`.
  - `ctl-prior` searches from C″'s answer and from its own chain's carried start, under
    `v3` and `broad`, each with the carried prior. It then pools, declares at margin 1 with
    quiet probability 0.01, and applies the guard.
  - `run_chain2` keeps two chains: `ctl-carry` hands on its own answers, and `ctl-prior` hands
    on its guarded answers and their carried prior.
  - Recorded per window: the carried mean, covariance before and after widening, τ, the gap,
    D, the fall-back flag, and `ctl-prior-noguard` (the guarded chain's raw answer).
  - Where there is nothing to carry (the first window, or the previous answer unusable),
    `ctl-prior` is `ctl`.
- **`src/tma2/long/study27.py`**: scoring.
  - Window classes (FR-005), from the engagement's own record:
    - contact 2;
    - a contact gap intersecting [t_o − 30 min, t_o + 30 min];
    - at most one ownship turn in the window.
  - Per window: median range error per system, plus course and speed medians.
  - The registered rule over windows, with chains' first windows excluded and a bootstrap
    over engagements (2,000 resamples, seed 27).
  - Reported beside (FR-007), coverage of the carried 95% region (FR-008), and spec 026's
    soundness checks.
- **CLI and CI**:
  - `tma2-long carry2 --index --config --contact` and `tma2-long study27 --raw --config`;
  - `long.yml` unchanged, since it already passes `--config` and `--contact`;
  - run files `configs/long/runs/cp-*.json`;
  - study configs `configs/long/cp-{tuning,val,test}.json`, at spec 026's sizes and seeds
    354/355/356;
  - `configs/long/carry2.json`, the declared `scale`, `tail_s` and `alpha`.

## Settings

- The tuning run uses scale 2, tail_s 600 and α 0.001.
- Tuning records each raw covariance and τ, so the coverage is computed offline for
  scale ∈ {1, 1.5, 2, 3, 4} and tail_s ∈ {0, 600, 1200}.
- The decision record binds the pair whose contact-1 coverage of the 95% region is nearest
  0.95, ties broken toward the larger scale.
- α is fixed at 0.001 unless tuning's fall-back rate at that level exceeds 20%; then the
  next tabulated level is taken.
- The coverage soundness band for validation is [0.80, 0.99] unless the tuning value lies
  within 0.03 of an edge. In that case the band is widened symmetrically and recorded.

## Joint solve (FR-012, reported only)

- 12 consecutive window pairs of the tuning seed's contact 1 (12-hour engagements).
- Each pair is solved by `ctl` on the union period, by the existing `run4` pieces through
  a `jointpair` CLI part, one job per pair.
- The union periods are 3.5 h, about 40 minutes each by spec 023's scaling.
- The reading is median range error on the second window's rows against `ctl-prior`. Twelve
  pairs is within the spec's "up to 40" and keeps the cost under 10 runner-hours.

## Order

1. Code and unit tests.
2. Tuning run (seed 354) on CI; choose the settings; check the split's size.
3. Decision record (`experiments/20261118-cp-decision/`): plan, configs, run files and code
   by digest, plus forecasts.
4. Validation (seed 355): soundness and coverage.
5. Test (seed 356), scored once.
6. Panel, then write-up, slides and AGENTS.md.

## Constitution

- Pre-registered decision record and fresh seeds.
- References beside: C″ and the true-history fit, on the same windows.
- Nothing trained.
- The panel reviews the test record.
