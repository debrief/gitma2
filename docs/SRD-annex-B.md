# SRD Annex B: Ownship and target manoeuvres, steady-leg segmentation (owner's requirements)

Owner's document of 3–4 November 2026, committed verbatim below the rule. Status: accepted as
requirements for spec 005 on the day it was committed; the owner merges this annex. It supersedes
the owner's earlier draft of 3 November, which spec 005 was first written from.

**How it maps onto the repository** (this preface is the agent's, not the owner's):

- The document is titled "Spec 004 … Gate D" by the owner. In the repository spec 004 and Gate D
  are the earlier learned detector (Annex A §A.0–A.8, stopped at validation, test seed 305
  reserved). The owner's D1, D2 and D3 are spec 005's **O**, **C** and **L**, and its gate is
  **Gate S** (Annex A §A.9). Nothing in Gate D changes.
- Where this annex and spec 005 differ, this annex wins, and spec 005 is amended to follow it.
  The amendments made on the day it was committed are listed in spec 005's Clarifications
  (session 2026-11-04). Two of the owner's defaults are held open there: L_min (5 min here,
  2 min in spec 005 on the data's evidence) and T_min (1 min here, 30 s in spec 005). The owner's
  answer closes them.
- The generator changes the owner requires (FR-030–FR-033, and FR-006's wander and oscillation)
  are staged: spec 005 builds and gates O, C and L on generator 0.5.0 first, with O unit-tested on
  constructed wander and oscillation; generator 0.6.0 adds them behind new ranges fields so that
  0.5.0 ranges stay byte-identical, and is a separate spec with its own G0 run.
- "Future work: real time" is recorded as a later spec. Its live metrics (detection delay, false
  alarms per hour, how often a confirmed boundary later moves) are defined and reported, not
  gated, in spec 005 so the offline segmenter is not tuned to measures that will not transfer.

---

# gitma2 Spec 004 — Steady-Leg Detector (Gate D)

Nov 3, 2026 · @Ian Mayo

## Summary

Spec 004 replaces zig detection with steady-leg segmentation: it finds where the constant-velocity assumption holds, for ownship and target, and hands the target's leg boundaries to the physics layer for Gate 2.

It delivers three components:

- **D1 — ownship steady-leg detector** (classical, from navigation data).
- **D2 — classical target leg segmenter**, a joint search over leg count, boundaries and transition lengths. It is the reference for Gate D and the classical knot-search baseline that Gate 2 currently lacks.
- **D3 — learned target detector**, which adds per-bearing evidence to D2's search. Untrained, it equals D2, so it fails safe.

Status: draft for owner review. Depends on P0 (physics layer, passed). Thresholds marked *proposed* are for the Gate D decision record, not fixed here.

## Background: why existing detectors fall short

Every prior detector flags turn edges instead of finding legs, and none estimates how long a transition lasts.

| Detector | Method | Shortfall |
| --- | --- | --- |
| Debrief ArcTan slicing (2015) | One split of an ownship leg; a fixed buffer of cuts dropped around it; accepted if score < whole-leg score × ZigRatio | One zig only; buffer length fixed, not estimated; ZigRatio not tied to bearing noise |
| Multi-leg slicing (2017 note) | Repeat slicing, or split at ½ or ⅓ and ⅔ | With two real zigs the best single split lands between them; splits interact and must be searched jointly |
| Ownship single-pass | Heading difference across window W (≥ 20 s) against threshold DH (5°) | Heading only, no speed; timing depends on W |
| Ownship twin-pass | Adjacent 1-minute moving averages, then refinement | Averaging blunts real turns; heading only |
| gitma phase 3b | Learned two-hypothesis head with P(turned) | Flagged about 30% of held rows as turned; trained on a mixture, it hedges |

Two structural limits run through these. ArcTan assumes constant relative velocity, so target legs can only be found inside a steady ownship leg. And a turn takes minutes, not an instant: bearings inside it fit neither leg, and a detector that forces them into one biases the solve.

## Definitions

Each bearing time is labelled per vessel as steady, transition or unknown; truth labels use the same definitions applied to true kinematics.

| Term | Definition | Proposed default |
| --- | --- | --- |
| Steady leg | Course within ±C of the leg mean and speed within ±S, for at least L\_min | C = 5° (the helm wander), S = 0.5 kt, L\_min = 5 min |
| Deliberate course change | Adjacent non-overlapping moving averages of course differ by more than D | D = 10°, window 1 min; both configurable |
| Transition | Interval between two steady legs; no motion model assumed | Length ≥ T\_min = 1 min; estimated, not fixed |
| Unknown | Interval the data cannot classify (too short, or too little bearing information) | Reported, never forced into a leg |
| Gap knot | Pair (leg end, next leg start) handed to the physics layer | Bearings between them excluded from the solve |
| Contamination | Fraction of time labelled steady that is truly transition | Primary error measure |
| Coverage | Fraction of truly steady time labelled steady | Secondary measure |

The defaults are starting points for the decision record, not evidence-based; the 3-minute figure in the 2017 note was a search-window size, not a turn duration.

## Scope and constitution alignment

Segmentation is judgement, so a network may supply it; the estimate still comes only from the physics layer.

**In scope**

- Simulated scenarios from the spec 001 generator, extended as set out under Data.
- Course changes and speed changes, for ownship and target.
- Several target legs within one ownship leg, and target legs that span ownship turns.
- Offline (whole-window) segmentation, matching the batch physics layer.

**Out of scope**

- Real sensor data, navigation error and non-Gaussian bearing noise (as in the current SRD).
- Several contacts at once.
- Causal, real-time segmentation: deferred to a later spec (decided 4 Nov 2026). See Future work below.

**Constitution fit**

- D2 plays the role least squares plays in Gate 1: the classical reference a learned model must beat.
- D3 starts at the reference. Its evidence head is zero-initialised, so an untrained D3 returns D2's segmentation exactly.
- The shuffled-label control for D3 is judged against D2, consistent with constitution 1.2.0.

**Future work: real time**

The live problem differs in kind: ownship turns are known as they are ordered, a target turn can only be confirmed after enough bearings have departed from the current leg, and the analyst's question is whether the current solution still holds. The planned route reuses this spec: a running residual test (CUSUM or GLR) as a solution-validity alarm, D2 re-run on a sliding window with older legs frozen, and D3's causal evidence fed unchanged. Live metrics are detection delay, false alarms per hour, and how often a confirmed boundary later moves; they should be defined before the offline detector is tuned, so it is not fitted to measures that never transfer. The four R-Cloud tasking forms state no real-time requirement.

## Functional requirements

D1 and D2 are classical and deterministic; only D3 learns.

**D1 — ownship steady-leg detector**

- **FR-001** Segment recorded ownship course and speed into steady legs, transitions and unknown. The algorithm sees only the recorded track, never helm orders.
- **FR-002** Coarse pass: flag a deliberate course change when adjacent non-overlapping moving averages (window about 1 min) differ by more than D (10°). Handle course wrap at 360°. Apply the same test to speed with its own threshold.
- **FR-003** Fine pass: from the flagged window, walk back to the start of the turn, the last point where the smoothed turn rate changes sign or the course last sat inside the preceding leg's ±C band. Walk forward the same way for the end, declared with a delay, since turns end more slowly than they start.
- **FR-004** Accept a turn only if the cumulative signed course change between its ends is almost all one sign. A wander of ±C with no persistent direction is not a transition.
- **FR-005** Enforce L\_min and T\_min, and trim a margin (proposed 30 s) from each leg end.
- **FR-006** Make no transition calls on helmsman wander (irregular) or autopilot oscillation (cyclic) inside the ±C band; the generator must produce both noise types.
- **FR-007** Report boundary error stratified by turn size: a 10–15° turn can sit inside the moving-average noise for a while, so its boundaries will be less exact than a 30° turn's.

**D2 — classical target leg segmenter**

- **FR-010** Model the target as constant-velocity legs in absolute coordinates, separated by transitions of length ≥ T\_min. Legs may span ownship transitions.
- **FR-011** Search jointly over the number of legs, their boundaries and the transition lengths, by dynamic programming over bearing cuts.
- **FR-012** Score each candidate leg by the weighted residual of a constant-velocity fit from the physics layer with trivial inputs.
- **FR-013** Charge each extra leg a penalty derived from the known bearing noise σ (BIC-style), replacing ZigRatio.
- **FR-014** Label as unknown any interval whose best and second-best segmentations differ by less than a set margin, rather than forcing a choice.
- **FR-015** Meet a runtime budget per scenario (proposed ≤ 10 s at 300 cuts on a 4-core runner), using cached and warm-started leg fits.
- **FR-016** Report the chosen segmentation, its cost, and the cost margin to the runner-up.

**D3 — learned target detector**

- **FR-020** A network emits per-bearing evidence (log-likelihood ratio of steady against transition) that is added to D2's costs inside the same decoder.
- **FR-021** Zero-initialise the evidence head, so an untrained D3 reproduces D2 exactly.
- **FR-022** The decoder enforces L\_min and T\_min, so no isolated or hedged turn flags reach the output.
- **FR-023** Inputs are the existing per-bearing features plus D1's ownship labels and D2's per-bearing residuals.
- **FR-024** Train three seeds and carry the median by the existing rule; run a shuffled-label control.

## Data, truth labels and generator changes

The generator must produce turns and speed changes that take realistic time, and truth labels must come from kinematics, not from event times.

**Generator extensions** (new generator version; gitma byte-conformance no longer applies)

- **FR-030** Rate-limited course changes, with turn rate drawn from a configurable range (proposed 0.5–3°/s).
- **FR-031** Speed changes with limited acceleration, alone or combined with a turn.
- **FR-032** Zero to three target changes per scenario, including changes during ownship turns.
- **FR-033** Optional ownship helmsman wander and autopilot oscillation inside the tolerance bands.

**Truth labels**

- **FR-034** Derive each vessel's steady, transition and unknown labels by applying the Definitions to true course and speed.
- **FR-035** Store labels with each scenario under the existing provenance rule (generating commit and digest).

**Stratification for reporting**

Number of target changes, change size, transition duration, range, bearing noise, whether a target change overlaps an ownship turn, and speed-only changes.

## Metrics and Gate D criteria

Gate D judges segmentation by what it does to the estimate, not only by how close the boundaries are.

| Metric | Measures | Why |
| --- | --- | --- |
| Contamination (median, P90) | Transition time labelled steady | Biases the physics-layer solve directly |
| False-split rate | Single-leg scenarios split into two or more legs | gitma's failure: about 30% of held rows |
| Coverage | Steady time labelled steady | Lost data widens the bound |
| Leg-count accuracy | Detected legs equal true legs | Catches the phantom zig between two real ones |
| Boundary error (median, P90, s) | Leg start and end against truth | Diagnostic only |
| Gap recovered | (error with no knots − error with detected knots) ÷ (error with no knots − oracle error), in range and velocity per CRB | Ties segmentation to Gate 2 |

**Proposed Gate D criteria** (thresholds set in the decision record before training)

1. D1 contamination P90 ≤ a set limit on ownship legs; a sanity check, not a learning claim.
2. D3 contamination and false-split rate no worse than D2, with the whole bootstrap interval inside the limit.
3. D3 recovers more of the gap than D2, with the interval on the difference excluding zero.
4. If D3 fails item 3, D2 carries into Gate 2 and the learning claim is recorded as not shown.

Item 3 is the only one that credits learning. Gate 2's "half the gap to the oracle" target should also be reported for D2, so its gain is attributed correctly.

## Interfaces and integration

The detector's only output to the physics layer is a list of gap knots; it never touches the estimate.

&#91;embedded content: Spec 004 pipeline · D1, D2, D3 feeding the physics layer\]

D3's evidence is zero at initialisation, so with D3 removed the pipeline runs on D2 alone.

- **FR-040** Add a Segmentation type to the LinkML schema: vessel, legs, transitions, unknown intervals, and D2's cost margin.
- **FR-041** Extend the physics layer to accept gap knots and mask transition bearings. The existing weight head is bounded at e^±2, so it cannot zero a bearing; a mask is needed.
- **FR-042** Export the D3 network to ONNX as now. The decoder may run in host code if a dynamic-programming Loop cannot export cleanly.
- **FR-043** D2 runs standalone, so Gate 2 can report its result alongside the learned pipeline's.

## Risks, assumptions and open owner decisions

The biggest risk is that D2 already recovers most of the gap, leaving D3 little to add; that outcome is still a usable Gate 2 detector.

**Risks**

- **Weak observability.** Inside one ownship leg a target turn shows only as a slight bend in the bearing curve, and a speed-only change may be undetectable. Mitigation: report unknown (FR-014) and stratify results.
- **D2 compute.** The joint search fits many candidate legs; at 600 cuts it may exceed the budget. Mitigation: cached warm starts and a cap on candidate boundaries.
- **Tolerances drive results.** C, S, D, L\_min and T\_min shape every metric. Mitigation: fix them in the decision record before training.
- **Generator change.** New turn dynamics break byte-conformance with gitma and require re-frozen classical references.
- **Export.** The dynamic-programming decoder may not fit cleanly in the ONNX graph; it may need to run in host code beside the exported network.

**Assumptions**

- Gaussian bearing noise with known σ, and exact ownship navigation.
- The physics layer can accept gap knots and exclude transition bearings (an interface change).

**Open owner decisions**

- [ ] Values for C, S, D, L\_min and T\_min.
- [ ] Whether D2 alone is an acceptable deliverable if D3 shows no gain.
- [ ] Paid compute for D2 reference runs and D3 training.
