# Spec 039 development run 2: the time-late control cut at the scored row (spent seed 370; not a result)

300 engagements of seed 370, in distribution, clean (`off`) and under the primary mismatch
condition (`all-central`). CI run 46129792450 at commit 0e3a89f1; plan
`configs/headroom/pic-dev2-in.json`. `cut-ctl` is spec 016's time-late control
(`ctl-d1-q0.01`: wild bearings edited, an effective sd, the evidence search under Annex B's
manoeuvre prior and a broadened one, a declared history, the arc model) run on the bearings up
to each scored row and read at its last moment (`headroom/cut.py`). It reads nothing after the
row (tested) and is told the generator's manoeuvre statistics. About 13 s per estimate.

Paired per engagement, first ÷ second (above 1: the second is better), range, with course and
speed in brackets:

| | clean | primary |
|---|---|---|
| C″-robust ÷ cut-ctl | 1.587 [1.418, 1.783] (1.65; 1.63) | 1.522 [1.352, 1.730] (1.53; 1.33) |
| C″-robust ÷ fine-tuned regressor | 1.624 (1.23; 1.08) | 2.284 (1.83; 1.42) |
| C″-robust ÷ solve told the true times | 1.689 (1.68; 1.56) | 1.996 (2.23; 1.78) |
| cut-ctl ÷ fine-tuned | 1.029 [0.915, 1.156] (0.75; 0.66) | 1.490 [1.342, 1.641] (1.20; 1.06) |
| cut-ctl ÷ solve told the true times | 1.069 [0.950, 1.188] (1.03; 0.96) | 1.305 [1.170, 1.446] (1.46; 1.33) |

Median range error: clean C″-robust 0.112, cut-ctl 0.076, told-truth 0.068, regressor 0.067;
primary 0.241, 0.166, 0.117, 0.106. cut-ctl answers 0.988 of rows. Share of the log gap C″-robust
→ regressor closed: 0.95 [0.75, 1.22] clean, 0.51 [0.39, 0.62] primary.

By thirds of the range bound (tight, middle, loose), cut-ctl ÷ fine-tuned in range: clean 0.74,
1.18, 1.24; primary 1.25, 1.51, 1.46. As the told-truth solve does, the control beats the
regressor where the bearings decide and loses where they do not.

What this says, as development data on one seed:
- A causal classical system told the manoeuvre statistics is level with the regressor in range
  on clean bearings and better in course and speed, and level with the solve told the true
  manoeuvre times. It is about 1.6 times better than the standing C″-robust.
- Under the primary mismatch it keeps its lead over C″-robust (1.5) but the regressor is 1.5
  ahead of it and the told-truth solve 1.3.
- It is a different segmenter and a different motion model (arcs, not chords) and a prior at
  once; this run does not separate those.
