# Spec 035: interactive TMA demonstrator

**Created**: 2026-11-21

**Status**: built. Not a gate, nothing trained, no seed used. The noise generator on the page is
the page's own, outside the study seeds.

**Input**: the owner's draft "gitma2 Spec 005: Interactive TMA Demonstrator" (2026-11-21), kept
verbatim in `owner-draft.md`, then a short interview (below). It is numbered 035 here because
spec 005 is the steady-leg segmentation.

**SRD traceability**: §1 (scope: a demonstrator of the solvers on mock data), §7 step 5 (the
browser artefact, as specs 020 and 021).

## Summary

The page `/demo` on the Docusaurus site. A stakeholder drags a blue ownship track and a red target
track, adds steady turns and narrows the analysis window. The page then solves the target's track
over that window from bearings alone (time-late) and shows how well the solve did against the
truth. The aim is a feel for where the solvers do well and where the geometry or a target
manoeuvre breaks them, without reading gate reports.

## Decisions

### From the owner's draft

| # | Topic | Decision |
| --- | --- | --- |
| 1 | Solvers | Pluggable; the user picks one from a dropdown |
| 2 | Bearings | Truth plus Gaussian noise; a σ slider and a Reseed button |
| 3 | Turns | Waypoints joined by steady-rate arcs; the rate (°/s) is editable per waypoint |
| 4 | Kinematics | A drag handle on each leg sets its course **and** speed |
| 5 | Feedback | A full dashboard |
| 6 | Recompute | On drag release, not continuously |
| 7 | Hosting | A React page on the Docusaurus site, reusing the repo's types and solvers |
| 8 | Ownship | Fully free, including unobservable geometry (no zig), which the demo flags |
| 9 | Scenarios | Presets, URL sharing, and JSON import and export typed by LinkML |
| 10 | Handle | Rotating a leg rotates and moves every later waypoint with it |
| 11 | Time | Time-late only. The window slider starts at the full period; the analyst drags its ends in |
| 12 | Frame | Flat X/Y in nautical miles, with pan and zoom |

### From the interview (owner, 2026-11-21)

| Question | Answer |
| --- | --- |
| How solvers reach the browser (open decision 1) | **Both now.** JavaScript batch least squares (spec 021's port, checked against Python), and ONNX solvers in ONNX Runtime Web |
| Which ONNX solvers | **The physics layer and a learned model.** The physics layer runs (a) with one leg and (b) told the truth's manoeuvre times (an oracle). First built with Gate 2's real-time E; then (owner: "I'm not interested in a track of real-time estimates") **replaced by spec 016's time-late whole-period model, all three training seeds** |
| Defaults (open decision 3) | **Repo MAN2 style.** Bearings every 5 s, σ 1° (slider 0–5°), turn rate 1°/s (0.25–3°/s). The physics layer thins to at most 720 bearings; the learned model needs 5-second bearings and at most 1,440 (two hours) |
| Reference time (open decision 2) | **None.** In the owner's words, "This is a time-late scenario. We're optimising the error equally across the whole panel." The errors are read at every bearing time in the window and shown as a time graph |
| Error summary | **RMS and worst value over the window**, with the Cramér–Rao bound's RMS beside them |
| Covariance ellipses (open decision 5) | **Off by default; a toggle shows 1σ and 2σ.** Never drawn for E (Gate 3: overconfident). The bound sits beside the error so the luck of one noise draw shows |
| Which learned models (open decision 4) | E, the model carried from Gate 2 (Gates 2 passed; Gates 3 and 4 stopped), labelled with its limits |
| Learned model (after the PR) | Real-time E dropped; spec 016's three seeds added; the presets moved inside its training range (target at 4–17 km) |
| One screen (after the PR) | Full browser width: plot, the three time-down charts and the dashboard side by side at viewport height. Hiding a chart widens the others without making them taller |
| Layout (after the first screenshot) | In the lower charts, time runs down the left and the value across. Each chart has a toggle to hide it |
| Progress (after the PR) | A progress bar while a solver runs, with elapsed time. It is determinate for E (its stages and counts) and indeterminate otherwise. A badge sits on the plot, and Cancel and Solve again are offered |
| Plot (after the PR) | Each leg's speed labelled in knots; a faint grid labelled in NM. Turns are drawn round at any zoom (arcs sampled every 2 s). A click on a leg splits it (kept, with a hint on the plot); the mid-leg square keeps decision 10 |

Decided here, with the alternatives in the PR:

- **Units:** NM, kt, ° and s in the page and in `DemoScenario`; metres inside the solvers.
- **Truth timing:** an arc starts and ends where it touches both legs (radius v/ω, at the
  incoming leg's speed). The vessel runs the path in order, so the turns shorten the period
  slightly against the waypoint times.
- **Waypoint 0:** dragging the start moves the whole track. Other waypoints follow FR-002, and
  the legs keep their durations.
- **Observability (FR-035):** the bound on range at the window end, as a fraction of range.
  Green under 5%, amber under 25%, red otherwise or when the bound is unbounded. σ is floored at
  0.5° so that a noise-free run still shows its geometry. The condition number is shown beside.
- **The bound (FR-031, risk 2):** the information from the window's bearings at the truth, with
  the target's manoeuvre times known (one velocity increment at the middle of each manoeuvre).

## Functional requirements

These are the owner's draft (`owner-draft.md`), as built. Changes are marked **changed**.

**Track editing**: FR-001 to FR-007 as drafted. FR-002 and FR-003 run on the draft scenario while
dragging and commit on release. FR-004: a click on a leg inserts a waypoint; Delete, Backspace or
a right-click removes one. FR-007: undo and redo, through buttons or Ctrl+Z and Ctrl+Y.

**Bearings**: FR-010 and FR-011 as drafted, with a default interval of **5 s (changed)**. The
generator is xoshiro128** seeded by splitmix32 (32-bit integer arithmetic), with Box–Muller
draws in time order over the whole scenario. A seed therefore gives the same bearings whatever
the window.

**Window and solve**: FR-020 to FR-023 as drafted. The slider and σ commit on the native
`change` event (on release). The worker posts results with the request's id, and the page drops
any result older than its latest request. FR-024: the `TmaProblem`, `TmaSolution` and
`DemoSolverInfo` types are in LinkML (schema 0.38.0, with `manoeuvre_start_s`/`manoeuvre_end_s` on
`TmaSolution`). FR-025 **(changed)** ships five solvers:

| Name | What it is |
| --- | --- |
| `ls-js` | Batch least squares in JavaScript, spec 021's port, checked against Python's golden vectors |
| `layer-cv` | The physics layer of Gates 1–2 with no knots, as an ONNX graph (`tl-layer.onnx`) |
| `layer-oracle` | The same graph told the truth's manoeuvre spans as chord knots. An oracle, labelled as such; at most four manoeuvres |
| `tlm-s1`, `tlm-s2`, `tlm-s3` | Spec 016's whole-period learned model (a bidirectional transformer; three training seeds of 12.5 million simulated periods). It reads the whole window of 5-second bearings at once and states range and velocity every 30 s and a manoeuvre probability. The page draws its own track (spec 016's `direct_track`) and shades its manoeuvres. 26 MB each, exported from the results branches by `tma2.viewer.demo_tlm_export`; the ONNX digests equal spec 016's export check. Study L stopped it against the classical control |
| `tlm-s1-legs`, `-s2-`, `-s3-` | The same network **read as steady legs** (owner, 2026-11-21): its manoeuvre spans (spec 016's `spans_from_logit`: probability over 0.5, merged within 60 s, at least 10 s; the four most probable kept) handed to `tl-layer.onnx` as chord knots with course and speed free. The shape of spec 016's `learned-arc` read-out (which used the arc model and Annex B's prior), not its figures. On the presets the head stays under 0.2, so at 0.5 it declares no manoeuvre and reads as one leg. A **manoeuvre threshold** slider (0.05–0.95, shown for the learned solvers; `DemoScenario.manoeuvre_threshold`, in the URL) moves the threshold for the declared spans and the legs |

**Dashboard**: FR-030 to FR-036. **FR-031 changed:** errors across the window (RMS, worst, the
bound's RMS) instead of at one reference time. **FR-032:** a chart of range, bearing, course,
speed or position error against time, with ±2× the bound shaded and the target's manoeuvres
marked. **FR-033:** measured and predicted bearings, with residuals ÷ σ, each in its own chart.
Time runs down the left in every lower chart, and each can be hidden.

**Scenarios**: FR-040 to FR-043 as drafted, with five presets: good geometry, no zig, target turn,
near endfire and a short window across a zig. The URL fragment holds deflate-raw JSON in
base64url (`#s=`), or plain base64url (`#j=`) where `CompressionStream` is missing. Imports are
validated against the JSON Schema that LinkML generates for `DemoScenario`
(`site/static/demo-data/demo-scenario.schema.json`, kept current by
`scripts/site/demo_schema.py --check`).

**Non-functional**: NFR-1 to NFR-5 as drafted, with **NFR-4 changed**: the page is laid out for a
full-width browser (the owner's choice). Below 1,200 px it stacks. Least squares at 360 bearings takes about 30 ms
in Chromium.

## Acceptance (as checked)

| # | Criterion | Check |
| --- | --- | --- |
| 1 | Every preset loads, solves and shows every panel | `demo_page.mjs`, `demo_node.mjs` |
| 2 | Zero noise, good geometry: least-squares range error under 0.1% | `demo_node.mjs` |
| 3 | No zig: indicator red, solution shown | both |
| 4 | Target turn: mismatch flag shown; one target leg clears it and cuts the error (32% → 1.8% RMS) | both |
| 5 | The URL and JSON round trips give the same scenario and solution | both |
| 6 | The Docusaurus build and the PR preview work | CI `site`, `pages.yml` |

Also checked:

- The JavaScript least squares equals Python's `solve_batch` on 11 problems the page builds
  (state within 1e-6 relative, iterations equal; `conformance/onnx/demo/golden-ls.json`).
- The ONNX layer with one leg equals it on noise-free bearings.
- The oracle cuts the target-turn error to under 0.5% (noise-free).
- The learned model's float32 inputs equal Python's bit for bit and its own track within 1e-6;
  onnxruntime-web's manoeuvre probabilities are within 1e-3 of torch's.
- `tl-layer.onnx` re-exports byte for byte. onnxruntime agrees with torch within 1.7e-6
  (`tl-layer.json`).

## Critical analysis and risks (after building)

- **Two implementations of least squares.** This risk is answered: one port, checked against
  Python's golden vectors in CI on every change. The ONNX layer is a third, compared on
  noise-free data only. With noise, the layer thins the bearings to fit the graph's 720 rows, so
  its answer differs from the JavaScript solve.
- **One noise draw misread.** The bound's RMS sits beside each error, and the residual chart is
  scaled by σ. Users must still press Reseed to see the spread; a Monte Carlo cloud is out of
  scope.
- **The oracle is not a system.** It is told the truth. It shows what segmentation buys on the
  model-mismatch lesson, not what any segmenter achieves (spec 005's C, and Gate S's 0.90 of the
  gap).
- **The learned model is out of its training range easily.** It was trained on initial ranges of
  2–20 km and 5-second bearings. The presets keep the target there, but a user can drag the
  target out (the first presets at about 33 km gave it 18% range error). It does not state the
  presets' 40° target turn (at 50 min, between ownship turns, since the owner's change of 2026-11-21; where its head states anything it is at an ownship turn). Study L found it about 20% worse than the classical control in a
  tail, level at the median. With noise, it beats least squares where the geometry is weak (no
  zig: 6% against 130%) and loses where it is good (10% against 0.3%).
- **Size.** The three seeds add 78 MB to the site and to each PR preview. Each is loaded only
  when chosen.
- **Decision 10 surprises.** The handle's tooltip and the help text say that the rest of the
  track swings. Waypoint drag is the local alternative.
- **A screenshot of a failure out of context.** The observability and residual panels sit beside
  the errors, and the mismatch flag is a coloured panel. Nothing stops the screenshot.
- **Not done:** Monte Carlo clouds, continuous recompute, the time-late `ctl` system (Python only;
  minutes per period) and lat/long charts.
