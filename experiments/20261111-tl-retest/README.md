# Spec 013: the full-period re-test on the arc cost (tuning seed 329; never a gate result)

`src/tma2/timelate/retest.py`: from a set of manoeuvre spans it refines every manoeuvre's times
in a joint fit of the arc model, adds a manoeuvre where the whole-period fit saves more than a
threshold, and removes one that saves less. Run from C″'s transitions (`retest-c2`) and from
no manoeuvres at all (`retest-none`), threshold 20 in cost (chosen before the run, not tuned).
Same 60 cut periods as `../20261111-tl-arc/` (57 with determined rows). Script as run:
`scripts/research/tl_retest.py` (four shards), pooled by `tl_arc_pool.py` (`pooled.txt`);
every structure found, with its cost and the log of changes, is in `structures.json`.

## Result: the re-test fits the bearings as well as the truth and is four times worse

| System | Median period range error | Periods over 10% | Efficiency: range, course, speed |
| --- | --- | --- | --- |
| Arc solve, true times (reference) | 0.035 | 0.19 | 1.39, 1.22, 1.38 |
| C″ to the period's end, chord | 0.113 | 0.54 | 3.84, 4.97, 3.86 |
| Re-test from C″'s transitions | 0.141 | 0.56 | 3.80, 5.34, 4.58 |
| Re-test from nothing | 0.110 | 0.56 | 4.45, 6.23, 4.90 |

Ratios [95% interval over periods]: C″ ÷ re-test from C″ 0.80 [0.59, 1.63]; C″ ÷ re-test from
nothing 1.03 [0.52, 1.75]; re-test ÷ reference 4.1 [2.0, 5.5] and 3.2 [2.0, 6.0]. **The
re-test does not improve on C″ read as a track.**

Why, measured:

- **Cost.** The re-test's final cost minus the cost of the arc fit told the true times has
  median 0.0 standard deviations of a chi-square; it is lower in half the periods. The
  bearings do not prefer the true structure to the one the re-test found.
- **Manoeuvres found** (a true manoeuvre counts as found when a span lies within 2 minutes;
  108 true manoeuvres): C″ 62 found, 23 false; re-test from C″ 70 and 16; from nothing 72
  and 15. Recall rises from 0.57 to 0.67; a third are still missed.
- **Where every manoeuvre was found and none was false** (24 or 25 periods): median range
  error 0.037 (from nothing) and 0.059 (from C″) against 0.019 for the reference on the same
  periods. Knowing the times to the row is worth a factor of two to three by itself.
- **Elsewhere** (32 or 33 periods): 0.19 to 0.20 against 0.04, at a cost only 5 to 6 above
  the true-times fit, on about a thousand bearings. A missed manoeuvre costs almost nothing in fit
  and a factor of five in range.

## Reading

The reference is not something a likelihood test on the bearings can reach. A structure with
a manoeuvre missing, or mistimed by a minute, explains the bearings as well as the truth and
puts the target somewhere else. What separates them is not in the period's bearings; it can
only come from what is known beforehand about how targets manoeuvre (Annex B: legs of 10 to
40 minutes, turns of 30° to 120°, turn rates, speeds). The causal segmenter, the re-test and
any other test of fit with a preference for fewer manoeuvres share this limit.

This also explains spec 012's validation result, where the learned regressor matched the
true-manoeuvre chord solve and beat C″: trained on ten million engagements, it carries the
manoeuvre statistics; C″ does not.

So the headroom above C″ is real (a factor of three to four to the reference) but most of
the reference's advantage is knowledge of the manoeuvre times, which no system has. How much
is reachable is the open question, and the answer needs an estimator that uses the manoeuvre
statistics: a classical one (a posterior over manoeuvre structures under Annex B's
distributions, by sampling) as the control, and a learned one against it.

## Limits

- One threshold (20), not tuned; a lower one finds more manoeuvres and more false ones. The
  cost comparison says the trade cannot be won on fit alone, but the curve was not run.
- 57 periods, one tuning seed; no ratio here separates the re-test from C″ in either direction.
- The search is greedy (three candidates per addition, score test at 30 s spacing); a better
  optimiser would lower the cost further, which is not the problem.
- "Found within 2 minutes" is a loose match; the error is sensitive to timing well inside it.
- Undetermined rows (bound on relative range above 0.5) are excluded throughout.
