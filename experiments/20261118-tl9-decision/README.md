# Spec 026 decision record: carrying state across gaps, against joining through them

Registered 2026-11-18, before seeds 360 (validation) and 361 (test) exist. Nothing is trained;
CPU only. A registered study, not a gate.

## What is bound

- Plan `configs/timelate/tl-m.json`, SHA-256
  `0f1a8caee87f722394c2cd62ce0d1134166af42fedad419e0685932e89af5bed` (never edited after).
- Code: time-late modules digest (`tma2-tlsolve`'s `CARRY_FILES`)
  `cee4a319a08968851775e6b7d0fbe50f404086056aa2ef5f202fd0503ddf5750`, as in the tuning run's
  shard headers. Runner `run9` (spec 025's `run8` unchanged, then the carry), scorer
  `tma2-tlscore` (`study9`).
- Runs: `configs/timelate/runs/tl-m-val.json` (seed 360, Annex B, 110 engagements),
  `configs/timelate/runs/tl-m-test.json` (seed 361; Annex B 70, busier 100, wild bearings 50,
  held course 50 engagements).

## Systems

`ctl` alone and the joint solve (spec 025, unchanged); **carry**: each period in order on its
own bearings, `ctl`'s start from nothing replaced by the previous period's declared state at
its last row run forward at constant velocity through the gap (C″'s start kept). With no
carried state it reproduces `ctl` exactly (`scripts/research/tl9_ctl_equivalence.py`: 0.0 m on
two periods; every run records the first period's agreement).

## Rule (spec FR-003), over periods after an engagement's first, rows as spec 025

- (a) carry ÷ joint: **joining better** if the range interval is wholly above 1; **carry
  better** if wholly below 1; else **not separated**.
- (b) alone ÷ carry: **carrying helps** if the range interval is wholly above 1; **carrying
  harms** if any of range, course, speed is wholly below 1; else **not shown**.

Annex B decides; the other splits are reported by the same rule (wild bearings is Annex B's
engagements; held course shares nearly all its layouts).

What follows:

- Joining better on Annex B: the joint solve stays the standing system for several periods;
  the carry is recorded as cheaper and weaker. If carrying also helps without harm, it is
  recommended where a joint solve is not available (one period at a time); if it harms, not.
- Not separated or carry better: the carry is recommended as the cheaper equal where it is
  not worse, and the owner decides.

## Soundness (validation, seed 360; stops the study if it fails)

The span reference with times held, per engagement (at least 10 rows with span bound below
0.05), geometric mean within **[0.6, 1.6]** (spec 025's panel: the efficient value is about
0.79 under the one-draw model, so the band is centred on it; a gross-fault screen), and the
carry answering at least 0.95 of later periods. Tuning: 0.85 [0.58, 1.19] (20 engagements).

## Sizes and forecasts (from tuning)

At tuning's 43 Annex B later periods, carry ÷ joint is already separated (lower limit 1.51);
70 engagements give about 70 later periods. Alone ÷ carry is near 1 with a median of 1.00, so
"not shown" is the expected outcome; no size here would show an effect of a few percent, and
none is claimed.

Forecasts: joining better on every split (Annex B about 2.2, busier about 1.6, wild bearings
about 3, held course about 4); carrying not shown on Annex B (about 1.0), possibly helps on
busier targets (about 1.1); a harm reading in speed on held course is possible (tuning 0.66
[0.38, 1.01]).

## Known before registration

- Tuning used spent seed 353 (spec 025's test engagements), not a fresh seed.
- Seeds 360 and 361 were chosen clear of PR 47's registrations (350, 351).

## Recorded after the test (panel round 1)

- The soundness band [0.6, 1.6] has a geometric centre of 0.98, not 0.79 as written above.
- Seeds 354 to 359 are unused (skipped to stay clear of PR 47's numbering).
