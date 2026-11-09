# Reflection after Gate 4: is there anything for learning to win?

Status: reflection requested by the owner, 9 November 2026, after Gate 4 stopped at validation.
Nothing here is a new measurement; every figure cites a committed record. It ends in two owner
decisions (§6) and spec 010.

## 1. The record of learned components against their controls

| Gate | Learned component | What the control showed | Record |
| --- | --- | --- | --- |
| 1 | weighting and initialisation heads | the heads died in training; the model is batch least squares | `experiments/20261101-g1-a-g1/` |
| D | steady-leg detector | p_change reads the time since the zig; no alarm raised | `experiments/20261102-gd-a-val/` |
| S | learned segmenter L against classical C | L − C +0.0012 [−0.0031, +0.0049]: inconclusive, recorded as not shown | `experiments/20261105-gs-r2/` |
| 2 | E-s (evidence), E-w (weights) | a zig veto and a fixed fade (C″) give +0.018 of the gap; E − C″ is +0.007 [+0.001, +0.012] | `experiments/20261107-g2/`, `experiments/20261107-g2-veto/` |
| 3 | calibration head | worse than a per-slice temperature | `experiments/20261108-g3-val/` |
| 4 | statement head | 72% of its margin over the temperature is a quadratic rule in E's three sds | `experiments/20261109-g4-val/` |

Every learned part, once controlled, reduced to a simple classical rule. The gains that are real
are classical: C recovers 0.898 of the gap between one leg and the oracle (Gate S), and C″ most of
Gate 2's improvement. The classical side of the programme keeps producing results; the learned
side has been patched after each failure with a narrower follow-on gate.

## 2. Why: the simulator is the estimator's own model

- The generator draws white Gaussian bearing errors with a σ the estimator is told, and a target
  moving in constant-velocity legs. The physics layer solves exactly that model. Where the model
  is the truth, maximum likelihood is close to efficient: P0 measured batch least squares at
  0.95–1.01 of the Cramér–Rao bound on held-course rows. A learned component can at best tie.
- What remained to learn was segmentation, and research note 08 found that most target changes
  leave almost no trace in the bearings. That is a limit of information, not of method.
- The shortcuts the networks found (time since the zig, recency) are what the literature on
  shortcut learning predicts when a cheap cue carries most of the available signal.

## 3. What other fields suggest

- **Hybrid filters** (the KalmanNet family, `02-literature.md` §2) report their gains under
  model mismatch: unknown or wrong noise statistics, wrong dynamics. With a correct model they
  match the Kalman filter and do not beat it.
- **Simulation-based inference** in gravitational-wave and cosmological analysis wins on speed,
  or where the likelihood cannot be written down. Ours can, in four dimensions per leg.
- **Weather and protein-structure models** win on real data containing physics the hand-built
  models lack. We have only simulated data, by the classification rules.
- **Seismic phase picking** is the nearest success for a learned detector, and it had millions
  of labelled real traces with a visible signature. Our manoeuvres mostly have none (note 08).

The common thread: learning pays where the hand-built model is wrong, unknown or intractable.
The SRD deferred realistic bearing error "until Gate 2 is passed". It has passed.

## 4. Criticism of the process

- Pre-registration, standing controls, fresh test seeds and the panel are the project's best
  asset. They are why the null results above can be believed.
- Validation seed 314 has been used to tune the IMM and EKF, C, E, and two calibration gates.
  Fresh test seeds limit the damage, but choices made on 314 are adapted to it.
- The authors and the review panel are agents of one model family; their blind spots are
  correlated. The panel has caught real faults (Gate S round 1's causality bug), which shows it
  works, not that it is independent.
- Gates 3 and 4 refined an uncertainty statement on an estimator whose learned content is about
  0.7% of the gap. The effort was out of proportion to what it could show about learning.
- Effects have been stated as fractions of a gap, never as metres, knots or minutes to a
  solution. A reader cannot tell whether +0.025 matters to an operator.

## 5. Fresh start, or evolve?

Evolve. The generator, references, physics layer, scorer, controls and process are the asset, and
any new question needs all of them. What must change is the question.

A different paradigm would be the only reason to start again, and the obvious one is a large
end-to-end regressor. An earlier draft of this reflection dismissed it on gitma's evidence
("about 3 × the bound"). That overstated the evidence:

- gitma's figure is for small models (128-unit LSTM; at most 540k parameters) trained on 80,000
  scenarios on 4 CPU cores, about 300 CPU-hours in all. Note 01 says its capacity scan "could not
  separate 'capacity is flat' from 'nothing here is trained to convergence'".
- Note 04 proposed the test as option B ("run it as the control: it is cheap on GPU and answers
  'was gitma undertrained?'"). The decision for free CPU runners changed it to a same-budget
  control, which answers a different question. The scaled test has never been run.
- Against it: gitma's speed error was flat across geometry bands where classical error falls,
  the signature of a precision floor; and on straight legs the best outcome is a tie with least
  squares. Where it could win is after manoeuvres, where gitma's networks beat the IMM by 25–40%.
- Cost is small (note 03: about $30 for 50 T4-hours on Modal, mostly inside the free credit).

So the scaled regressor is a cheap, decisive experiment inside this repository, not a fresh start.

## 6. Decisions (owner, 9 November 2026)

1. **Next: a headroom gate under bearing-error mismatch, with no learned model** (spec 010,
   Gate H). Add correlated, biased, unknown-σ and outlier-bearing errors; measure how far the
   standing classical estimator, and a classical robust control, fall short of an oracle that
   knows the error model. If the remaining gap is material, train there with C″ and the robust
   control as standing controls. If not, stop the learning track and publish the null result.
   The Gate 4 follow-on (course-probability fixes) is set aside.
2. **Then: the scaled end-to-end regressor control** (note 04 option B) on Modal within its free
   credit, after the headroom gate and whatever its result. It needs an account and a secret,
   which are the owner's to create.

Practice changes adopted with them: a fresh tuning seed separate from the validation seed for
every choice (seed 314 retired from tuning); every effect also stated in operational units.
