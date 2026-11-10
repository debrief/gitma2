# Research note 11: the set-aside Gate 4 follow-on ("Gate 5"), archived

**Status.** Archived, not merged. On 2026-11-09 the owner set the Gate 4 follow-on aside in favour
of Gate H (spec 010 on main, `docs/research/10-reflection-headroom.md`). A parallel session that
had not seen that decision implemented the follow-on as "spec 010 / Gate 5" and ran it to a
validation verdict. The owner closed the PR unmerged (debrief/gitma2 PR 26) and asked for this
pointer.

## Where the record is

- **Branch `archive/gate5-honest-course`** (commit 65c959b). It holds:
  - the spec `specs/010-honest-course-statement/`;
  - the code: `calib/statement5.py`, `calib/proxy.py`, `calib/gate5.py`, and the CLIs
    `tma2-g5proxy`, `tma2-g5train`, `tma2-g5predict` and `tma2-g5`;
  - the decision record `experiments/20261109-g5-decision/`;
  - the validation record `experiments/20261109-g5-val/`, with the panel's `review.md`;
  - the write-up `site/blog/2026-11-10-gate-5.md` and its slides post.
- **Results branches:**
  - `results/g5proxy-val`, `results/g5proxy-stream`
  - `results/score-g5-base-val-42705184463`
  - `results/g5-g5-a-42712276372`
  - `results/g5predict-g5-a-val`
  - `results/score-g5-a-val-42712917053`

## What it found (validation seed 314, ordinals 500–1499; panel round 2)

**The verdict.** The gate stopped at validation:
- **G5-d was void.** The learned head beat the classical rule (−0.081), but so did the head with
  its encoder input shuffled (−0.039 [−0.075, −0.005]).
- **G5-b was inconclusive** (calibration slope 1.25 [1.06, 1.47]).
- **G5-a, G5-c and G5-e passed.**
- **Seed 320 was not used.** It is now Gate H's tuning seed.

Findings that bear on Gate H and later work:
- **The statement form.** A course statement in the truncated form (P times a von Mises truncated
  to ±X, the rest uniform) is consistent by construction: its arc mass is exactly P. The earlier
  mixture with a normal approximation was off by up to 0.5 on broad rows.
- **Detecting fresh manoeuvres.** Recent bearing residuals catch fresh target manoeuvres only
  weakly: held-out AUC about 0.65, and the flag catches 42% of rows just after a manoeuvre. C's
  segmentation is weaker still (AUC 0.55). The residuals also respond to geometry, such as close
  range and ownship turns.
- **No learning from E-w's encoder state was shown.** A plain MLP without the encoder, trained
  post hoc, beat the learned head by 0.08 and the classical rule by 0.16. This is consistent with
  note 10's reading that learned components reduce to classical rules on this generator.
- **Process lessons** (also in that branch's AGENTS.md gotchas):
  - A synthetic check of a gate's bands must reproduce the real data's P spread and
    within-scenario correlation.
  - A Platt map fitted on about 2,000 tuning rows can make a calibrated P worse.
  - A statement parameter with a jump in the loss, like the arc edge, must be searched, not fitted
    by gradient.
