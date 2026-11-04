# Feature Specification: Generator 0.6.0, the MAN2 simulation model

**Feature Branch**: `006-generator-man2` (developed on `claude/inspiring-curie-j192v9`)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: generator 0.6.0, the MAN2 simulation model: target legs of 10–40 min
with a bell-shaped length distribution and 5% at 10 min, in 40–120 min windows; transitions of
about a minute; target changes allowed during ownship turns; helm wander and autopilot
oscillation on ownship inside the ± 5° band; all behind new ranges fields so that 0.5.0 ranges
reproduce 0.5.0 byte for byte; the 720-row window carried through; fresh seeds; the pipeline
gate re-run; references re-tuned and frozen.

**SRD traceability**: SRD §2 (MAN2 variant) and §9 (owner decisions of 2026-11-04); SRD Annex B
FR-006 and FR-030–FR-035; SRD §3 (generation on the fly, conformance to gitma, labels);
constitution 1.2.0 II (determinism), IV (references on the same rows), V (pipeline gate before
training). Scoping: `docs/research/09-generator-060-scope.md`.

**Why**: spec 005's steady-leg thresholds (L_min = 5 min, T_min = 1 min, from Annex B) do not fit
generator 0.5.0, whose target legs last 4 min at the median and whose turns take 50 s. The owner
chose to change the simulation to the stated manoeuvre model rather than the thresholds to the
simulation. Spec 005 is gated on this generator's data.

## Owner decisions carried (2026-11-04)

| Decision | Value |
| --- | --- |
| Target leg length | "typically 10 to 40 minutes with a bell curve of leg length frequencies, only turning at 10 minutes on 5% of occasions" |
| Window length | 40–120 min |
| Steady-leg thresholds | L_min = 5 min, T_min = 1 min stand (Annex B) |

## Decisions taken as a careful colleague (the owner may overrule on review)

| Item | Choice | Alternative |
| --- | --- | --- |
| Reading of the leg-length sentence | Normal, mean 25 min, sd 9.1 min, floor 5 min: 5% of legs at or under 10 min and 5% at or over 40 min | A hard floor at 10 min with the bell above it (then "5% at 10 minutes" would need a spike at the floor) |
| What ends a leg | Course change 80%, speed change 10%, both 10% | 0.5.0's one speed change in 30% of scenarios |
| Transition durations | Turn rate 0.25–1°/s and speed-change rate 0.01–0.05 m/s², so a transition takes about a minute or more | Keep 0.5.0's 0.5–3°/s (transitions of 20–50 s, below T_min) |
| Wander | Helm wander as a first-order autoregressive course error (sd 1.5°, 60 s time constant, clipped at ± 4°); autopilot oscillation as a sinusoid (amplitude 1–3°, period 2–6 min); per scenario none / wander / oscillation at 0.4 / 0.3 / 0.3 | Both at once (set to 0; the spec allows a weight) |
| Seeds | Validation 314, test 315 (reserved for Gate S), noise-free pipeline-gate data 316; spec 005's 312/313 are superseded and recorded as unused | — |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nothing already generated changes (Priority: P1)

A researcher regenerates any 0.5.0 (or earlier) dataset with the new generator and gets the same
bytes. gitma's conformance fixtures still pass. The new behaviour appears only when a ranges file
names it.

**Why this priority**: every gate so far, and the reserved test seeds, rest on byte-identical
reproduction. A silent change to old data would invalidate them.

**Independent Test**: run the golden and gitma-conformance tests with the new generator; regenerate
seed 304's validation split and compare digests.

**Acceptance Scenarios**:

1. **Given** a ranges file without the new fields, **When** a dataset is generated, **Then** every
   record is byte-identical to the 0.5.0 output and the header's generator version is 0.6.0.
2. **Given** the gitma fixtures, **When** the conformance tests run, **Then** they pass unchanged.

---

### User Story 2 - Target legs follow the owner's model (Priority: P1)

An analyst generates 10,000 MAN2 scenarios and sees target legs whose lengths follow the declared
bell curve, each leg ending in a course change, a speed change or both, with transitions lasting
about a minute, and some changes starting while ownship is turning.

**Why this priority**: it is the point of the version. Spec 005's thresholds and Gate S depend on
it.

**Independent Test**: generate seed 314, measure leg lengths, change kinds, transition durations
and overlaps with ownship turns from the stored truth, and compare with the declared model.

**Acceptance Scenarios**:

1. **Given** 10,000 MAN2 scenarios, **When** complete leg lengths are measured, **Then** their
   distribution is not rejected as the declared normal at the 1% level, and 4–6% of legs are
   10 min or shorter.
2. **Given** the same scenarios, **When** transitions are measured, **Then** their median
   duration is between 60 and 180 s.
3. **Given** the same scenarios, **When** changes are counted, **Then** at least 60% of
   engagements have two or more target changes, and some changes begin inside an ownship turn.

---

### User Story 3 - Ownship wanders, inside the band (Priority: P2)

Ownship's recorded course shows helm wander or autopilot oscillation in some engagements, never
more than 5° from the leg's course, and its recorded positions follow that wandering course
exactly.

**Why this priority**: Annex B requires it so the ownship detector is tested on realistic
tracks. It does not change the bearing problem (navigation stays exact).

**Independent Test**: generate MAN2 data, check the recorded course against each leg's planned
course and the positions against the integrated course.

**Acceptance Scenarios**:

1. **Given** a scenario with wander, **When** the recorded course is compared with the leg's
   planned course, **Then** every row is within 5°, and the scenario header names the wander
   kind and its drawn parameters.
2. **Given** a scenario without wander, **When** it is regenerated with wander disabled in the
   ranges, **Then** it is byte-identical: wander draws come from their own random stream.

---

### User Story 4 - The pipeline still passes, and the references are re-frozen (Priority: P2)

Before any training on MAN2 data, the pipeline gate passes on it, the IMM and EKF are re-tuned on
its validation split and frozen, note 08's GLR + confirm reference is re-measured on it, and
everything downstream accepts 720-row windows.

**Why this priority**: constitution V forbids training before the pipeline gate; IV requires the
references on the same rows.

**Independent Test**: run the pipeline gate on seeds 314 and 316, the tune on 314, and the note 08
scripts on 314.

**Acceptance Scenarios**:

1. **Given** MAN2 data, **When** the pipeline gate runs, **Then** it passes by the agent panel,
   including the physics layer's recovery of noise-free truth and the tracker checks.
2. **Given** the 720-row window, **When** the conformance export runs, **Then** a 720-row export
   exists and agrees across the three runtimes to 1e-5, and the 360-row artefacts still build.

### Edge Cases

- **A leg longer than the window.** The engagement has no target change; it is kept (the
  zero-change stratum).
- **A change whose transition runs past the window end.** The span is recorded as open-ended at
  the last row.
- **A change during an ownship turn.** Allowed. The ownship zig is still planned on a straight
  stretch of the target's track when one exists; otherwise the plan proceeds and the scenario
  records `zig_on_manoeuvre`.
- **A speed change that would take the target below the minimum speed or above the maximum.**
  Redrawn as in 0.5.0.
- **Wander near a leg boundary.** Wander applies to the recorded course within steady legs only;
  the turn itself is the planned rate-limited turn.
- **The first leg's phase.** Drawn uniformly over one leg length, so changes are not aligned to the
  window start or to the ownship zig.

## Requirements *(mandatory)*

### Functional Requirements

**Compatibility**

- **FR-001**: Every new behaviour MUST be enabled only by new fields in the ranges file. A ranges
  file without them MUST produce output byte-identical to generator 0.5.0 (and, by 0.5.0's own
  rule, to earlier versions for their ranges).
- **FR-002**: The generator version becomes 0.6.0; files from 0.1.0–0.6.0 stay readable. New
  ranges and header fields are added to the schema once, with a version bump, and regenerated.
- **FR-003**: Random draws for the new behaviour MUST come from streams of their own, so that
  enabling or disabling wander, or the leg model, does not change any other draw.

**Target legs and changes**

- **FR-010**: When `target_leg_length_s` (mean, sd, min) is present, target leg lengths MUST be
  drawn from a normal distribution with that mean and sd, clipped below at min, and laid end to
  end from the window start with the first leg's phase drawn uniformly. The 0.5.0 count weights,
  spacing and after-zig and margin guards MUST NOT apply. Changes starting after the window end
  are dropped.
- **FR-011**: Each leg end MUST draw its kind from `target_change_kind_weights` (course, speed,
  both). Course changes keep 0.5.0's angle range and sign rule; "both" starts the speed change
  with the turn.
- **FR-012**: A target change MAY start during an ownship turn.
- **FR-013**: The MAN2 ranges file MUST set turn rates and speed-change rates so that transitions
  last about T_min or longer (proposed 0.25–1°/s and 0.01–0.05 m/s²), windows of 40–120 min,
  dt 10 s, σ ∈ {1°, 2°}, dropouts 0–10%, and phase-4 geometry otherwise. It is committed as
  `configs/man2-ranges.json` with a noise-free twin for the pipeline gate.

**Ownship wander**

- **FR-020**: When `ownship_wander` or `ownship_oscillation` is present, each scenario MUST draw
  none, wander or oscillation (or both, if its weight is non-zero) from `ownship_wander_weights`,
  and record the kind and drawn parameters in the scenario header.
- **FR-021**: Helm wander MUST be an irregular course error with the declared sd, time constant
  and clip; autopilot oscillation MUST be a sinusoidal course error with a drawn amplitude and
  period. Both MUST stay within ± 5° of the leg's planned course on every row.
- **FR-022**: The wandered course MUST be integrated into the recorded ownship positions, so the
  recorded track is the true track and ownship navigation stays exact. Wander applies inside
  steady legs; the planned turn is unchanged.

**Zig planning**

- **FR-030**: Ownship zigs MUST still be planned on a straight stretch of the target's track where
  one long enough exists; otherwise the plan proceeds on the track as is and the scenario records
  `zig_on_manoeuvre: true`.

**Window carry-through**

- **FR-040**: Padded rows per window follow the ranges (720 for MAN2). Batches, the physics
  layer's maximum rows, the fixed-window model exports and the conformance export MUST accept
  720 rows. The 360-row artefacts remain for 0.5.0 data.
- **FR-041**: The physics layer's cost per solve and the training throughput per scenario at 720
  rows MUST be measured and recorded against the budgets of specs 003 and 005.

**Data, gate and references**

- **FR-050**: Validation seed 314 (10,000 scenarios), test seed 315 (reserved for Gate S) and
  noise-free seed 316 MUST be generated from a clean tree with digests pinned. Spec 005's seeds
  312 and 313 are recorded as superseded and unused.
- **FR-051**: The pipeline gate MUST be re-run on 0.6.0 (conformance for 0.5.0 ranges; noise-free
  recovery on MAN2; the tracker checks, including the before-manoeuvre and NIS checks) and decided
  by the agent panel, before any training on MAN2 data.
- **FR-052**: The IMM and EKF MUST be re-tuned on seed 314 with the declared grids and frozen;
  note 08's GLR + confirm reference and its nomination threshold MUST be re-measured on seed 314;
  the detectability distribution MUST be re-measured. All are recorded in the experiment folder.
- **FR-053**: The generate CLI MUST accept the new ranges; the pipeline-gate CLI MUST run on
  MAN2; a command MUST print the effective manoeuvre model of a ranges file (leg model, change
  kinds, rates, wander) so a reader can check what was generated.

### Key Entities

- **Ranges (0.6.0 fields)**: `target_leg_length_s`, `target_change_kind_weights`,
  `ownship_wander`, `ownship_oscillation`, `ownship_wander_weights`; all optional.
- **Scenario header additions**: `ownship_wander` (kind, drawn parameters), `zig_on_manoeuvre`.
- **ManoeuvreSpan**: unchanged (start, end, kind); an open span ends at the last row.
- **MAN2 ranges file**: `configs/man2-ranges.json` and its noise-free twin.
- **Reference records**: the re-tuned IMM/EKF names and grids; GLR + confirm's threshold and
  downstream ratios on seed 314; the detectability quantiles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All golden and gitma-conformance tests pass unchanged, and seed 304's validation
  split regenerates with the same digest.
- **SC-002**: On seed 314, leg lengths are not rejected as the declared normal at the 1% level;
  4–6% of complete legs are at or under 10 min; the median transition lasts 60–180 s; at least
  60% of engagements have two or more target changes.
- **SC-003**: In every wander scenario, 100% of rows are within 5° of the leg's course; a scenario
  without wander regenerates byte-identically with wander disabled.
- **SC-004**: Kernel throughput stays at or above 10,000 scenarios per second at 720 rows.
- **SC-005**: The pipeline gate passes on 0.6.0 by panel verdict; the IMM, EKF and GLR + confirm
  references are frozen with records; the 720-row conformance export agrees across runtimes to
  1e-5.
- **SC-006**: Spec 005's decision record can cite a MAN2 validation split, frozen references and
  measured budgets at 720 rows, with nothing left to generate.

## Assumptions

- The owner's "10 to 40 minutes … 5% at 10 minutes" is read as the 5th and 95th percentiles of a
  normal distribution (see the colleague decisions); a different reading changes two numbers in
  the ranges file, not the design.
- Ownship speed does not wander (Annex B names course wander only; S = 0.5 kt leaves no room).
- G5 rows (zig + 5 to 20 min) and the settled definition are unchanged; with 40–120 min windows
  and a zig at 40–60% of the window there are always at least 16 min after the zig.
- The 2017 note's 3-minute window is not used anywhere in this model.

## Out of Scope

- Real data, navigation error, non-Gaussian noise, several contacts.
- Speed wander on ownship.
- Any change to 0.5.0 semantics or to gitma conformance fixtures.
- The segmenters themselves (spec 005).

## Risks

- **720 rows doubles costs.** Physics-layer solves, batch memory, training time per scenario and
  the export size all grow. FR-041 measures them before spec 005 commits to its budgets.
- **Fewer changes per hour than 0.5.0.** Long legs mean fewer manoeuvres per scenario-minute;
  training sets for spec 005's L may need more scenarios for the same number of transitions.
- **Zig planning on long legs.** With legs of 25 min a straight stretch for the zig almost always
  exists; the fallback (FR-030) is for the rare case and must be counted.
- **Reading of the owner's sentence.** If a hard 10-minute floor was meant, the normal's lower
  tail (5% below 10 min) is wrong; the alternative is one ranges change.
