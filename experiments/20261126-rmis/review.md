# Panel review, round 1: spec 037 test record (2026-11-26)

Three independent reviewers read the decision record, the code and this record, and recomputed
from the per-row errors on the results branches. **Three approve with findings.** Every
registered number reproduces; the order of registration holds. The findings narrow what the
readings support. The reviewers' working scripts, as run, are in `panel/` (they read copies of
`errors.npz` fetched to a scratch folder).

## Seats and verdicts

| Seat | Verdict |
|---|---|
| A. Reproduction and registration | approve with findings |
| B. Statistics and estimands | approve with findings |
| C. Claims, design and domain | approve with findings |

## Verified

- `rmis_readings.py` on a scratch copy with fetched errors gives `readings.json` and
  `readings.md` byte for byte (A). An independent numpy recomputation with its own bootstrap
  matches all 27 point values of M1 to M4, Y1 and Y2 to three decimals (A); M1, M2 and M4
  reproduce again in seat B's code.
- Protocol, decision README and digests have one commit, d386257, never edited; every training
  segment records that commit. Addenda 1 and 2 precede the validation launch; addendum 3, the
  test plan and the interval fit are in the commit the test ran from. One test run exists (A).
- The eight bound configuration files are unchanged. Only `mread.py` moved (89 insertions, no
  deletions), declared in addendum 1 (A).
- The test plan's checkpoint digests equal the run records'. No path lets the training mix draw
  a held-out kind (A).
- M1 and M2 are typical gains, not tails: median per-engagement ratio 1.92 and 2.23; trimmed 5%
  at both ends 1.97 and 2.30; at row level 1.98 and 2.23; with the engagement's mean error
  instead of its median 2.06 and 2.39 (B).

## Findings that narrow the record

1. **"Held out" is a weak form, and the family was chosen after looking** (A major, C major).
   The spec's default held-out family (Student-t noise, a level step) hurt nobody on tuning data
   and was replaced, three minutes before registration, by a sinusoid and bursts, after the
   unchanged regressor was seen to be hurt by them and the pilot model to recover. In statistics
   the new kinds sit inside what training covered: a sinusoid of amplitude one sd has an rms of
   0.71 sd, inside the trained correlated share, in a band a trained correlation time of about
   48 s already reaches; three bursts of 120 s are about 5% of bearings at five sd, the trained
   outlier marginal, and a common offset is a short bias. Only the line spectrum and the
   clustering are new. The fine-tuned model is no worse there (0.114) than on the trained
   primary condition (0.112). M2 is biased towards the regressor and reads "kinds not in the
   training mix, chosen because they hurt the unchanged model", not "unseen errors".
2. **The gain sits where C″'s segmentation has failed** (B major, C major). A classical robust
   solve told the true manoeuvre times equals the regressor in range on every condition (0.89
   clean, 1.03 primary, 0.96 held out) and beats it in course (0.74 to 0.79) and speed (0.68 to
   0.84). The factor of two is C″-robust (0.233) against that solve (0.116): the segmentation
   gap of specs 010 and 011. Splitting engagements by C″-robust's error on two rows and scoring
   the other two: in C″'s best quartile under mismatch the regressor is 1.15 to 1.43 better in
   range with 15% to 19% of engagements twice as bad, and not separated in course or speed; in
   its worst half 2.7 to 3.3. On clean data in C″'s best quartile the regressor is **worse** in
   course (0.75 to 0.83) and speed (0.62 to 0.73, a third of engagements twice as bad). A lead
   of 1.49 exists on clean data already; the part specific to mismatch is about 1.3 and 1.5. No
   prior-informed or mismatch-hardened classical segmenter was registered as a control.
3. **Prior or bearings is still open; the static-prior comparator was a straw control** (C
   major, B major). Its ln-range sd of 0.649 at weight 1 could not move a solve whose error is
   10% to 25%, so its null was foreseeable and rules out only a constant. In the third of rows
   with the loosest bound under the primary condition the regressor's efficiency is 0.61 / 0.78
   / 0.69 in range, course and speed: below 1, which is prior, not information from the
   bearings. The gain grows with range (1.11 near, 1.91 far on clean data), the signature of a
   prior. On clean data in the third with the tightest bound it is worse than C″ in course
   (5.24 against 3.68) and speed (5.5 against 4.93). Spec 012's ownship-only regressor would
   give the pure prior and was not scored here.
4. **M4's "no cost" clause is not resolved by this bootstrap** (A major, B major). The lower
   limit is 0.9496 with a Monte Carlo sd of 0.0005 at 2,000 resamples; 17% to 22% of bootstrap
   seeds return "no cost". The cost itself is real (upper limit 0.985), about 3%, a tail (median
   per-engagement ratio 0.989) and concentrated under 22 km (near third 0.954 [0.925, 0.986],
   far third 0.995 [0.958, 1.034]); by seed 0.974, 0.971, 0.957.
5. **M5 is honest on average, not conditionally, and not ready for display** (B major, C
   major). Course covers 0.78 to 0.79 on unsettled rows and 0.97 to 0.98 on settled ones. The
   narrowest fifth of speed intervals covers 0.92 to 0.94 and the widest 0.985 or more. The
   nearest 5% of true ranges cover 0.885 [0.838, 0.929] in range under the primary condition.
   Rows with no stated course are the hard ones (median error 29°, 13% over 90°); counted with
   a 90° arc, all-row course coverage is 0.91 to 0.92; a quarter to nearly half of stated arcs
   exceed 60°. By condition the course head is not separated from the constant-width control on
   the held-out condition (0.986 [0.930, 1.047]). A variance head trained on the generating
   distribution is calibrated there by construction, so this is not the advance over Gates 3
   and 4 that it looks; the control (thirds of estimated range) is the weak kind Gate 4's panel
   warned about. The interval score's bootstrap is sound in its units.
6. **The hybrid is the regressor's range with a classical velocity refit** (C major, B minor).
   A weight of 0.25 on a roughly calibrated sd claims sixteen times the regressor's real
   information, and the prior is made from the same bearings as the likelihood, so the data are
   counted twice; the prior carries nearly all of the range precision. "Reports from the
   physics layer" holds in letter only, and the layer's covariance must not be shown. Its course
   and speed gains over the regressor are a minority effect (median ratio 1.04 to 1.06 on clean
   data, 1.00 in course under the primary condition; 16% to 18% of engagements twice as good).
   It is worse than the regressor in the far third on clean data (0.955 [0.918, 0.995]) and
   inherits the regressor's losses where C″ was right. "No harm" is a pooled statement. Its
   weight was chosen on one training seed on a grid changed after a pilot look.

## Corrections to the record's text (all taken in)

- Four scored rows an engagement (3,936 rows over 1,000 engagements: 942 with four, 52 with
  three, 6 with two), not five.
- "Three seeds agree to the second decimal" was false: M2 by seed is 2.34, 2.27, 2.24 and M4
  0.974, 0.971, 0.957.
- The count of hybrid rows that used their prior was in no committed file; `hybrid-ties.json`
  now holds it (none fell back on either condition).
- Four CPU families ran the scoring jobs, not two.
- `rmis_readings.py` was committed with the record, not before the launch as addendum 3
  promised; Y1 and Y2 use the same pooling, which addendum 3 names only for M3 and M4.
- Validation seed 370 was the training monitor's seed (512 scenarios, logged only; no
  checkpoint was selected on it).
- The scoring code (`hybrid.py`, `hpredict.py`, `rmis_fit.py`, `headroom.yml`) is bound by the
  test's commit only.
- A resumed run sees the same scenarios but reseeds its patch offsets at each segment, so its
  weights are not an uninterrupted run's.
- The fine-tune record's money paragraph had lost its dollar amounts to the shell (repaired).
- Missing from "promised and not run": the default held-out family on the test, the hybrid
  started from the regressor, validation early stopping, rows every system answers with counts.

## What may be said, and what may not

May say:

- On this simulator, a regressor fine-tuned on the simulator's bearing-error family halves the
  range error of the frozen classical real-time system under those errors and structured
  relatives of them, at a cost of about 3% on clean data.
- A classical robust solve told the manoeuvre times matches it in range and beats it in course
  and speed, so the gap is the segmentation.
- Its stated intervals cover about 95% on average on this simulator at a bearing sd of 1°.

Must not say:

- "The regressor is robust to unseen bearing errors", or "it beats classical TMA".
- "The gain comes from reading the bearings, not from the prior."
- "The hybrid is a physics-layer estimate with a usable uncertainty", or "the intervals are
  calibrated for an operator".

## The panel's order for what follows (the owner's choice)

1. **Recommended: a prior-informed classical control and a decomposition of the gain, on CPU,
   nothing trained.** C with a raised threshold and with wild-bearing editing and an effective
   sd in front of it; spec 012's ownship-only regressor as the pure prior; the readings owed
   (time since the last change, first bearing an outlier); the existing weights on a shifted
   manoeuvre prior and held-out geometry.
2. A conditional coverage study on spent seeds (range band, time since manoeuvre, observability,
   ownship turn, other bearing sds, a richer classical width rule, median NEES beside each).
3. Only after 1: carry the hybrid provisionally as a real-time candidate with C″ and C″-robust
   standing, described as "regressor range, layer velocity", with no covariance shown.
4. An ONNX export for the demonstrator, labelled a simulator-prior model. No further GPU
   spending; real or differently simulated data is what would change the conclusion.
