# Spec 017: the shifted-prior gap on tuning seed 342 (2026-11-14)

CI run 43604804906 (`timelate/tl-f-tune`, commit 30a5dab, draft plan
`configs/timelate/tl-f-draft.json`). **Tuning data: nothing here is a registered result.**
Every table is in `tables.md`, generated from `summary.json` by
`scripts/research/tl5_tables.py`; the figures below are copied from it. Per-row errors:
results branch `results/timelate-tl-f-tune-43604804906`.

## What it shows

**A third of the shifted targets' manoeuvres can barely be seen in the bearings.** The
detectability of a manoeuvre is the χ² its omission adds to the fit of the true history.
Shifted: median 49.9, with 0.24 [0.21, 0.29] under 10, 0.33 [0.29, 0.37] under 20 and 0.47
[0.42, 0.52] under 40. Annex B: 0.12, 0.18 and 0.23. Shifted 2 (larger, slower turns):
0.04, 0.07 and 0.10.

**The control finds what can be seen and misses what cannot.** Share of shifted manoeuvres
the control misses, by detectability: 0.97 under 5, 0.86 from 5 to 10, 0.65 from 10 to 20,
0.48 from 20 to 40, 0.31 from 40 to 100, 0.12 above 100. Its half-way point is between 20
and 40, where the evidence's price for a manoeuvre (about 22 in χ²) says it should be.

**Split at that point, most of the gap is identifiability.** On the shifted split the
control is 2.02 [1.55, 2.55] times the reference told every manoeuvre. A reference told
only the manoeuvres above 20 is itself 1.62 [1.37, 1.95] times the full reference, and the
control is 1.25 [0.96, 1.59] times that, not separated from 1. The attainable share is 0.32
[-0.08, 0.56] at threshold 20. **It depends heavily on the threshold**: 0.66 [0.42, 0.82]
at 10 and -0.11 [-0.64, 0.19] at 40.

**Knowing the true statistics finds more manoeuvres and does not improve the track.** The
search given the shifted targets' own prior misses 0.32 of manoeuvres against the
control's 0.45 (it does better between 10 and 100), invents more (0.50 a period against
0.37), and its track is level with the control's: 1.02 [0.86, 1.22].

**Where targets turn hard, the gap is attainable**: on shifted 2 the attainable share is
0.83 [0.60, 1.05] at threshold 20, but the gap there is small (the control is 0.031
against 0.016).

Beside: the tuned IMM and EKF read as tracks are 5 to 6 times worse than the control on
the shifted split. Under outliers a reference fitted to the edited bearings is at 0.021
against 0.030 for the unedited one: study L's "the control beats the reference" was the
yardstick's fault, as its panel said.

## What it means for registration

- The rule in research R5 (attainable share at threshold 20 against 0.5) **is not
  registered as a decision**. On 137 scored periods its interval is ±0.3; at the test's
  size it would be about ±0.17, and the tuning value (0.32) is one such half-width from
  0.5. And the threshold moves the share from 0.66 to below zero. A rule here would be
  decided by the threshold and the sample, which is what spec 015's panel warned against.
- The study registers **estimands and forecasts** and the logic of the recommendation,
  and reports at all three thresholds.

## Weaknesses

- One tuning seed; 137 scored shifted periods.
- Detectability holds the other manoeuvres' times at the truth, and the references hold
  theirs: both flatter the references, so the attainable part is an upper limit.
- "Under 20" is tied to the evidence's price under Annex B's prior; a system with a
  better-matched prior pays less (the true-prior search does find more between 10 and 40).
- The true-history fit converged in 0.99 of periods on Annex B; references drift when
  free in 0.27 of shifted periods (study L: the same).
