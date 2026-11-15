# Feature Specification: The carried model end to end in the browser

**Feature Branch**: `021-browser-segmenter` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-15

**Status**: Draft

**Input**: Owner, 2026-11-15, after spec 020: option A, "port C to JavaScript so the viewer can
run live, without data prepared in Python first".

**SRD traceability**:
- §1 In scope: "a browser viewer on that artefact". Spec 020 met it for E-w alone, with C's
  segmentation shipped as data.
- Constitution VI: every carried model exports to ONNX, and "the algorithm note MUST state the
  physics layer's equations so that a port can be written by hand". The browser is one of the
  three runtimes.
- Spec 020's write-up, "Not achieved": C and its confirmation still run in Python.

**Owner decisions this spec implements**:
- 2026-11-15: option A.

## Background

The carried model E is three parts:
- **E-s** is a learned evidence network, exported to ONNX.
- **C** is the classical segmenter. Its confirmation uses E-s's evidence to shift its
  threshold.
- **E-w** is learned weights into the physics layer, exported to ONNX.

C is host code: a GLR statistic over batch least-squares states, an additive search, and a
confirmation step that compares physics-layer costs of candidate segmentations. Spec 020's
viewer therefore ships C's hand-over as data.

Measured before writing this spec, on the busiest demo engagement (seed 319, ordinal 3, 703
rows), C's confirmation made 63 physics-layer calls covering 582 rows. At the browser's
measured 0.25 s a row, that is about 2.5 minutes for C alone, and E's own confirmation needs
about as much again.

C's decisions are thresholds on cost differences, so a last-bit difference between runtimes can
flip a decision that sits near its threshold. AGENTS.md records that C's segmentation already
depends on the padding of its batch. A port cannot promise bit-identical segmentations. It can
promise identical ones wherever no decision is near its threshold, and it can report every
disagreement with its margin.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the whole model from bearings (Priority: P1)

The reader picks a demo engagement and chooses "live". The page computes everything in the
browser from the shipped bearings and ownship track, with nothing else shipped:
- E-s's evidence (exported graph);
- C's GLR statistic and search nominations (JavaScript);
- C's confirmation with E-s's evidence (JavaScript, with the physics layer as an exported
  graph);
- the hand-over and E-w's estimate.

The page draws the result as spec 020's page does, and compares it with the shipped Python
hand-over.

**Why this priority**: It is the owner's request: the viewer no longer depends on Python-side
preparation.

**Independent Test**: In a headless browser, run live mode on each demo engagement and compare
the browser's segmentation and estimate at every scored row with the shipped Python ones.

**Acceptance Scenarios**:

1. **Given** a demo engagement, **When** the reader starts live mode, **Then** the page shows
   progress through each stage (evidence, statistic, search, confirmation, estimate) and draws
   the estimate when done.
2. **Given** live mode has finished, **Then** the page says, row by row, whether the browser's
   segmentation equals Python's. Where it differs, it says which decision differed and by how
   much its margin was from the threshold.
3. **Given** live mode is running, **When** the reader switches engagement, **Then** the run
   stops and nothing from it is drawn on the new engagement.

---

### User Story 2 - Check the port against Python (Priority: P1)

CI runs the JavaScript port headless on a set of scenarios. For each one it compares:
- every intermediate (GLR statistic, LS states, search cost tables, nominations, each
  confirmation decision with its cost drop, the segmentation at every scored row, the hand-over
  arrays);
- with the same quantities from Python's C run on that scenario alone.

**Why this priority**: A port is only as good as its check. Without it the page could show a
segmentation the gates never measured.

**Independent Test**: A CI job runs the comparison and fails on any difference beyond the
stated tolerances that is not a reported near-threshold decision.

**Acceptance Scenarios**:

1. **Given** the check scenarios, **Then** numeric intermediates agree to 1e-6 relative
   (statistics, states, costs), and nominations and decisions are identical. The exception is a
   decision whose margin from its threshold is within a stated band. That one is reported as
   near-threshold, and its downstream rows are excluded from the identity count, with the count
   reported.
2. **Given** the check, **Then** at least 95% of all scored rows have identical segmentations.
   If fewer, the job fails, and the record says which decisions caused it.

---

### User Story 3 - A new engagement the page did not ship (Priority: P3)

The reader pastes one scenario record and the page runs live on it: its bearings, ownship and
(optionally) truth, in the project's NDJSON scenario format. Without truth, no errors are
shown.

**Why this priority**: It is what "live" means for a user with their own (simulated) data. It
depends on stories 1 and 2 and adds no new numerics.

**Independent Test**: Paste the NDJSON of a seed 319 scenario not among the demos; the page runs
it and the result equals Python's for that scenario, up to stories 1 and 2's tolerances.

**Acceptance Scenarios**:

1. **Given** a valid scenario record, **When** pasted, **Then** it runs live.
2. **Given** an invalid record (wrong window length, a σ the model was not trained for, missing
   fields), **Then** the page refuses it and says why. The model runs only on MAN2-shaped,
   σ = 1° inputs.

### Edge Cases

- The physics-layer graph returns a non-finite cost: treat it as Python does (a rejected
  candidate) and record it.
- A scenario with no valid zig leg, or one that ends before the first G5 row: E gives no answer,
  and the page says so.
- Very long engagements (720 rows, busy): live mode must stay responsive, with progress and a
  cancel.
- Python's chunk padding: the reference is Python's C on the scenario alone. Gate 2's chunked
  segmentation is compared too, and its differences are reported, not gated.

## Requirements *(mandatory)*

### Functional Requirements

**The port**

- **FR-001**: C's host logic MUST be ported to JavaScript from the Python code at C's frozen
  digest (`code_sha256` `4d2c084f…`, parameters `60e6ee63…`, hand-over `knot_at_k`). It covers:
  - the batch least-squares states the GLR statistic reads;
  - the GLR statistic and its nominations;
  - the additive search (segment costs by Levenberg–Marquardt, the dynamic programme) and its
    nominations;
  - confirmation (candidate grid, lengths, thresholds with evidence, polish, open and closed
    transitions);
  - `intervals_at`;
  - the hand-over (`segmentation_inputs`, `prefix_inputs`);
  - the code channel.

  Python's C stays the reference and MUST NOT change.
- **FR-002**: The physics-layer costs that confirmation needs MUST come from an exported ONNX
  graph of the physics layer, which outputs at least the cost and the plausibility flag. The
  layer is not hand-ported. The graph MUST pass the same three-runtime conformance as the
  project's other exports.
- **FR-003**: E-s's evidence MUST come from its exported graph (`segment.evidence_export` with
  the carried weights), run in the browser.
- **FR-004**: The port MUST reproduce Python's order of operations wherever a decision depends
  on it: candidate order, tie-breaking, the order of nominations. Unit-level comparisons with
  Python MUST cover each ported function.

**The check**

- **FR-005**: A Python command MUST write, for a set of check scenarios, every intermediate of
  C's run on each scenario alone, and of E's segmentation:
  - GLR statistic;
  - LS states;
  - search cost tables;
  - nominations;
  - every confirmation decision, with its candidate, cost drop, threshold and evidence shift;
  - the segmentation and hand-over at every scored row.
- **FR-006**: A headless-browser job MUST run the port on the same scenarios and compare. It
  uses the tolerances in User Story 2, reports near-threshold decisions with their margins, and
  fails beyond them. The check scenarios are the six demo engagements and at least 24 more of
  seed 319 (used, never fresh), chosen by a fixed rule.
- **FR-007**: The job MUST report the time of each stage per engagement.

**The page**

- **FR-008**: The viewer MUST gain a live mode. It reuses spec 020's drawing, keeps the shipped
  mode as the default, and states which mode produced what is drawn.
- **FR-009**: Live mode MUST run in a worker, compute the scored rows in time order, show
  progress by stage, and be cancellable.
- **FR-010**: Story 3's pasted-scenario input, with validation, if stories 1 and 2 are done.

### Key Entities

- **Check scenario**: a seed 319 scenario; its Python intermediates (FR-005) and the browser's.
- **Decision record**: one confirmation decision: prefix row, candidate (start, length),
  cost drop, threshold after evidence, accepted or not, and its margin.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the check scenarios, at least 95% of scored rows have a browser segmentation
  identical to Python's. Every difference is traced to a decision within the near-threshold
  band.
- **SC-002**: Where the segmentation is identical, the browser's live estimate agrees with
  Python's to spec 020's tolerances: state 1e-5, and covariance on its own scale 1e-5.
- **SC-003**: On a CI runner, live mode finishes the busiest demo engagement within 10 minutes
  and the quietest within 2. The first scored row appears within 1 minute.
- **SC-004**: Every ported function has a Python-comparison unit check.

## Assumptions

- The physics layer runs in the browser as an exported graph rather than a hand port. One
  implementation of the numerics, already conformance-checked, is safer than two. The
  constitution's "a port can be written by hand" is about the algorithm note, which exists.
  Alternative, not chosen: port `physics/reference.py` (the NumPy documentation of record) to
  JavaScript. It would be faster in the browser (no 100-iteration graph per request), but it
  would be a second implementation needing its own conformance.
- Near-threshold band: the plan sets it from the measured browser–Python cost differences, as
  ten times their largest value. It is reported, not tuned to pass.
- No fresh seed: check scenarios come from seed 319, which is used.
- Not a gate. Nothing is trained. No SRD amendment is needed: the viewer is in SRD §1's scope.
- Performance is within reach but unproven. If SC-003 fails, the record says so, and the page
  warns that live mode is slow. The plan may batch layer requests (Python batches them too).
