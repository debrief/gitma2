# Spec 014, tuning seed 333: controls, classes, held-course periods (2026-11-12)

**Tuning data: nothing here is a registered result.** CI run 43280542307 (`timelate/tl-c-tune`,
commit 50acc2e, clean tree), plan `configs/timelate/tl-c-draft.json`, run
`configs/timelate/runs/tl-c-tune.json`: 150 Annex B periods, 60 under the shifted prior, 100
in which the target holds course. Files: `summary.json`, `score.txt`, `*.periods.json`,
`*.errors.npz` (per-row errors of every system). Median period range error unless said.

## Systems

| System | Annex B (134 scored) | Shifted (51) | Held course (86) |
| --- | --- | --- | --- |
| One leg | 0.447 | 0.371 | 0.023 |
| C″ read as a track | 0.098 | 0.178 | 0.024 |
| C″ refitted (arc model, prior, no search) | 0.069 | 0.184 | 0.021 |
| Search, flat prior | 0.063 | 0.115 | 0.020 |
| Search, Gate T's prior | 0.059 | 0.088 | 0.044 |
| Search, corrected prior (`search2`) | 0.057 | 0.090 | 0.045 |
| True history, with the prior | 0.034 | 0.042 | 0.020 |
| True history, times held | 0.025 | 0.047 | 0.022 |

Soundness (as the validation stop will read it): the reference with times held is at 1.06 of
the bound on tightly bounded rows; every true-history fit has a cost the noise explains.

## What the tuning seed says

1. **The corrected prior changes nothing measurable** (FR-002). Gate T's search ÷ corrected:
   0.98 [0.91, 1.05] paired; manoeuvres missed 19% and 18%; the same false count. The three
   errors the panel recorded were real and immaterial. `search2` is used from here on.
2. **Most of the search's gain over C″ is not the search.** C″'s own transitions refitted
   with the arc model and prior obtain 0.79 [0.49, 1.26] of the log gain on Annex B data
   (0.62 [0.33, 0.95] where the search's history is right). Refit ÷ search: 1.12 [0.90, 1.40]
   paired. The interval is wide: this is what the test seed must narrow.
3. **The manoeuvre statistics add nothing measurable to the track on Annex B data.** The
   flat-prior search is at 1.01 [0.84, 1.23] of the informed search, paired. It finds fewer
   manoeuvres (26% missed against 18%) and the track is no worse.
4. **On a target that holds course the informed search is harmful.** It declares a manoeuvre
   in 81% of held-course periods [72%, 87%]; C″ in 3%, the flat-prior search in 1%. Its
   track error is twice the one-leg fit's (1.63 [1.30, 2.07] paired). The cause is the prior
   itself: Annex B makes a 20 to 60 minute period with no manoeuvre improbable (5 of 134
   Annex B periods), so the evidence prefers to add one. This is the prior working as
   written, and it is the wrong behaviour for the commonest real case.
5. **Under the shifted prior the refit gives nothing** (C″ ÷ refit 1.06 [0.78, 1.44]) and the
   search still gains (C″ ÷ search 1.70 [1.21, 2.39] paired; 60 periods). So where the
   search's assumptions are wrong, searching matters more, not less. Small sample.
6. **Classes of wrong-history periods** (Annex B; 60 wrong of 150): ambiguous 47% [35, 59],
   evidence failure 43% [32, 56], search failure 10% [5, 20]. The search itself is rarely the
   fault. The shares move with the threshold (ambiguous 0.08, 0.19, 0.27 of all periods at 1,
   3, 5) while search failure does not (0.04 to 0.06).
7. **Attainable headroom** (geometric mean per-period ratio, search ÷ composite): a perfect
   search under the same evidence 1.12 [1.03, 1.25], inconclusive against 1.10; a perfect
   evidence as well 1.31 [1.14, 1.53], material. The statistic is not degenerate (the paired
   median ratio is exactly 1, as research R4 expected). Against Gate T's upper limit, 1.75
   paired on this seed, about half is ambiguity that no identifier can win.
8. **Counts** (120 s match, Annex B): C″ misses 49% of true manoeuvres with 100 false; the
   refit 31% and 53; the search 18% and 52. Timing error of matches: C″ 52 s, the others
   17 to 19 s.
9. **Run time** on the runner: the search 21 s a period, the layer 14 s, the refit 7 s. Run
   time does not limit split sizes.

## Cautions

- One tuning seed. C″ ÷ search is 1.72 here against 2.27 on Gate T's test seed: the seeds differ
  by that much, so every share above carries at least that uncertainty.
- The composites use the true history's structure where a period is classed a failure: still
  an oracle of identification, only now without the ambiguous periods.
- "Evidence failure" includes periods where the true history is improbable under the prior and
  the bearings do not insist on it; a better evidence could not win all of them either.
- The held-course split is outside Annex B's statistics by construction. Finding 4 says the
  informed search must not be used as it stands where targets may hold course; it does not say
  the prior is wrong about Annex B data.
