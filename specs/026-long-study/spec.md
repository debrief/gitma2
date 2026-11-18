# Feature Specification: Long engagements, a registered study (spec 026)

**Feature Branch**: `026-long-study` (developed on `ccr-fd0a0c59-4nxg4k`, PR 47)

**Created**: 2026-11-18

**Status**: Done: a registered study, not a gate. Nothing trained, no GPU. Test record `experiments/20261118-ls/`; panel round 1, three approve with findings.

**Input**: Owner, 2026-11-18, on PR 47: "registered study". This is note 13's proposal.

**SRD traceability**: §1 (scope). No gate criterion is touched. The study is registered
in a decision record before its seeds exist (constitution: pre-registered decision records,
fresh seeds).

## Questions

1. **E1**: on a contact the ownship tends, is `ctl-carry` no worse than `ctl`? The test is
   non-inferiority at 5%: the geometric mean of the per-window ratio ctl ÷ carry must have a
   lower limit of at least 0.95. If so, carrying is adopted for long chains as a cost measure.
2. **E2**: how much worse is the standing control on a contact the ownship does not tend? The
   measure is the ratio of median errors, contact 2 ÷ contact 1, banded by true range. A
   magnitude; no rule.
3. **E3**: does the IMM drift over 12 hours? The measure is median error in hours 6–12 ÷ hours
   0–6. Drift is shown if the interval lies wholly above 1.

Soundness, read on validation: S1, at least 95% of windows ran; S2, ctl ÷ the true-history fit
lies in [0.8, 4]; S3, contact 1's share of bearings held lies in [0.6, 0.95]. A failure stops
the study.

## Design (decided before tuning, in `src/tma2/long/study.py`)

- Engagements are realistic (`configs/long/realistic.json`'s realism), 6 and 12 hours. They are
  `configs/long/study-{tuning,val,test}.json` on seeds 349 (6 + 6), 350 (10 + 10) and
  351 (30 + 30).
- Systems run unchanged from spec 024:
  - `ctl` and `ctl-carry` on 2-hour windows overlapping by 30 minutes, contacts 1 and 2;
  - the frozen IMM over each 12-hour engagement, read every 10 minutes.
- Intervals come from a bootstrap over engagements (2,000 resamples, seed 25).
- Order: tuning, then the decision record (plan, run files and code by digest), then
  validation, then the test, scored once, then the agent review panel and the write-up.

## Known limits (stated before any result)

- One family of realistic engagements: the realism parameters are spec 024's choices, not
  measured ones.
- E2 confounds geometry with tending. It is meant to: the untended contact is farther and
  less observable, and that is the cost being measured.
- E3 reads one IMM tuning (MAN2's); drift could be the tuning's.
- E1's 5% margin is a choice. 0.95 is the conventional "no worse than" margin for a cost
  measure; the owner may set another before validation.
