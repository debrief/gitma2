# Feature Specification: a carried prior across gaps (development study)

**Feature Branch**: `028-carried-prior` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-19

**Status**: Draft

**Input**: Owner decision, 2026-11-19, option A after spec 027: carry a prior across the gap,
scored on spent seeds first (spec 027 panel, first in its order). Classical, CPU only,
nothing trained.

**SRD traceability**: §1 (time-late consumer), §5 (references on the same rows, paired
statistics), §9 (owner's decisions). Spec 027's panel (`experiments/20261119-tl9/review.md`):
"A carried prior: the previous period's state and covariance, widened through the gap by
Annex B's manoeuvre rates, as a prior in the period's evidence. Score it against joint and
alone on spent seeds first; this decides whether joining is needed."

## Background

Spec 027's carry gave the next period only a start for its search, which can change only which
minimum its own fit lands in; joining had to win. A carried *prior* puts the earlier period's
information into the next period's evidence: a Gaussian on the period's starting state from the
previous declared state and its uncertainty, run through the gap with process noise for a
manoeuvre the gap may hide. This is the sequential approximation to the joint solve. If it
comes close to joining, an analyst can solve period by period; if not, the joint solve is needed.

## What this spec is

A **development study on spent seeds**, not a registered result: spec 027's test engagements
(seed 361, spent) on Annex B and busier targets. It reads carried prior ÷ joint, alone ÷
carried prior and carried start ÷ carried prior, and proposes to the owner whether to register
a study on fresh seeds.

## Requirements

- **FR-001**: `ctl`, the joint solve, the carried start and every registered code path are not
  edited. The carried prior is applied through wrappers around the evidence's prior functions,
  active only during a carried solve; with no carried prior a solve equals `ctl` (checked on
  every engagement's first period).
- **FR-002**: The carried prior: mean = the previous period's declared state at its last row
  run forward at constant velocity to the period's first row; covariance = that state's
  Laplace covariance from the previous period's posterior fit, propagated through the gap, plus
  isotropic process noise from Annex B (chance of a manoeuvre in the gap, mean squared turn and
  speed change); converted to (x, y, course, speed). It replaces the state factors of the
  standing evidence (position, course, first-leg speed) for the four starting parameters. The
  search also starts from the carried state (spec 027's start).
- **FR-003**: Readings over periods after the first, on spec 025's rows and with spec 027's
  bootstrap: cprior ÷ joint, alone ÷ cprior, carry ÷ cprior, by own ownship turn, on rows a
  period determines alone, with ties reported.
- **FR-004**: The carried uncertainty is checked: how often the true starting state lies inside
  the carried prior's two-sigma ellipse (an overconfident carry is the expected failure).
- **FR-005**: A record with tables by script and a proposal to the owner; no panel unless a
  registered study follows.

## Assumptions

- Gaussian process noise is a crude stand-in for "a manoeuvre may have happened": a mixture
  (no manoeuvre / manoeuvre) would be the correct form, and is the first refinement if the
  Gaussian proves too blunt.
- The previous period's Laplace covariance is known to be overconfident where its fit is
  wrong (Gate 3's lesson); the smoke run on three engagements already shows it.

## Registration (2026-11-19, owner: register k4)

After the development run (`experiments/20261119-tl10-dev/`) and the refinement
(`experiments/20261119-tl10-refine/`), the carried prior with its covariance inflated 4× in sd (k4)
is registered against `ctl` alone: decision record `experiments/20261119-tl10-decision/`, plan
`configs/timelate/tl-o.json`, validation seed 362, test seed 363.
