# Research: spec 015

## R1. Prior version 3: volume is the reciprocal of the density

- **Decision**: for a parameter θ whose prior factor p(θ) has no Gaussian residual in the
  fit, the stand-in precision is 2π·p(θ̂)², so the Gaussian volume √(2π/precision) is
  1/p(θ̂) and a direction the bearings leave wholly open contributes density × volume = 1.
  For a uniform of width W this is version 2's 2π/W². For a manoeuvre's duration d given
  its size a, p(d | a) = u(a/d)·a/d² with u the (soft) uniform density of the rate (turn rate
  for turns and combined manoeuvres, acceleration for speed changes): about 20 to 120 s of
  room for a minimum-size change, in place of version 2's fixed 600 s.
- `prior_precision` therefore needs the fit (θ, spans, kinds): a new function
  `open_precision(p, theta, spans, kinds, range0, t_end)`; `log_evidence` calls it for
  version 3 and the old function otherwise.
- With it: `_leg_sf` and `_leg_tail` use the renormalised leg density; the first start's
  stand-in becomes the reciprocal of the first gap's density (the forward recurrence), and
  the flat prior drops the m! it did not pair.
- **Not repaired here**: the Laplace approximation's Gaussian volume can exceed a
  parameter's feasible range at a bound (the 10 s duration floor: about +0.7). Recorded; a
  sampler is out of scope.
- **Alternatives**: the width of the conditional support (the reviewer's other variant; it
  is not the reciprocal of the density where the density is not flat); a residual for the
  rate (changes the fit as well as the evidence).

## R2. One rule for a history's identity

- `same_history(true, found, tol, cut)`: drop true manoeuvres flagged cut; drop each found
  manoeuvre whose mid-time is within `tol` of a cut manoeuvre's visible mid-time or within
  `tol` of the period's cut end; then equal counts and mid-times within `tol` in order.
- **Cut** means the engagement's manoeuvre extends beyond the period (starts before its
  first row or ends after its last), read from the engagement's own table.
- Kinds are not compared (as before); the share of "right" periods whose kinds differ is
  reported.

## R3. The reference

- Fit as spec 014 (neutral starts and the search's best track, times free, best evidence).
  If `same_history(true, fit, 120 s)` fails, refit to the posterior with times held at the
  truth, flag the period, and use that fit for the track and the evidence. A held fit's
  evidence is evaluated with the same parameter set as a free one.
- Every reading that uses the reference is also given without flagged periods.

## R4. The refit control's fall-back

- The refit is kept if its states are finite, its speed stays within twice the prior's
  fastest and its range within sixteen times the prior's farthest, and its bearing cost is
  either what the noise explains (within five sd of χ²) or no worse than C″'s own track's by
  more than 9. Otherwise C″'s own track stands. No truth is used. The number of fall-backs
  is reported, and D1 is given with and without them.
- **Changed on development data** (seed 335, spent): the first form compared the cost with
  C″'s track alone and fell back in 26 of 200 periods, because the chord track has four free
  unknowns a manoeuvre and can fit the bearings more closely than a sound arc refit. The
  "what the noise explains" branch was added before registration.

## R5. Keeping earlier registrations

- `run2.py`, `study.py`, `gate.py`, prior versions 1 and 2 are not edited in behaviour; both
  fixtures pin them. New code: `match.py`, `run3.py`, `study3.py`, prior version 3.

## R6. Development on spent seeds

- Seed 335's Annex B and held-course splits, re-run with `search2` beside `search3`:
  false-manoeuvre rate by period length, first-candidate accuracy (edge-aware), counts,
  track error, and the share of references flagged. The four refit runaways (ordinals 81,
  106, 232, 294) are the fall-back's test cases.

## R7. The registration

- **Decided** (test seed 337, Annex B unless said): D1 the refit's share of the gain
  (C″ → `search3`), with the fall-back; D2 class shares among wrong-history scored periods,
  edge-aware; D3 both headroom figures; D4 false-manoeuvre rate on held course for
  `search3`, C″, flat and mixed priors. D5 by spec 014's rule, unchanged.
- **Other estimands for D1**, declared here: the ratio of log medians; the registered share
  without periods where either system's period median exceeds 1.
- **Reported**: everything in FR-009 to FR-012; `search2` beside `search3`.
- **Soundness stop**: spec 014's, plus at most 25% of references flagged (15% were flagged
  on the development periods; the limit guards against most of them being held, not some).
