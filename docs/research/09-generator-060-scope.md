# Generator 0.6.0: the MAN2 simulation model (scoping)

Status: agent's scoping note, 4 November 2026, for the generator 0.6.0 spec. The owner's
decision (SRD §9, 2026-11-04): "the target will typically stay on one course from 10 to 40
minutes with a bell curve of leg length frequencies, only turning at 10 minutes on 5% of
occasions." Annex B adds helm wander, autopilot oscillation, target changes during ownship turns,
and transitions of about a minute. Nothing here is decided beyond the owner's sentence; every
default is a proposal for the spec.

## 1. What 0.5.0 does now (validation seed 304, σ = 1°, 1,000 scenarios)

- **Windows** 20–60 min, median 46 min.
- **Target changes per scenario** 0 / 1 / 2 / 3 / 4: 13% / 30% / 27% / 24% / 6%, drawn by count
  weights, then placed with a 3-minute minimum spacing, at least 2 min after the ownship zig and
  6 min from the window's end. Median gap between changes 4.2 min; the first change 2.3–10 min
  after the zig.
- **Turns** at 0.5–3°/s through 30–120°, so 20 s at the 10th percentile and 50 s at the median.
- **Ownship** exactly piecewise constant: no wander.

Against the owner's model the legs are 5× too short and the turns 2–3× too fast.

## 2. Proposed model

All new behaviour sits behind new ranges fields. Ranges without them reproduce 0.5.0 byte for
byte (the rule every version since 0.2.0 has kept), so gitma's conformance fixtures stand.

**Target legs.** A leg's length is drawn from a normal distribution with mean 25 min and standard
deviation 9.1 min, clipped below at 5 min. That puts 5% of legs at or under 10 min and 5% at or
over 40 min, which is one reading of "10 to 40 minutes … only turning at 10 minutes on 5% of
occasions". Legs are laid end to end from the window's start, with the first leg's phase drawn
uniformly, so the first change is not tied to the ownship zig. Fields:
`target_leg_length_s: {mean, sd, min}`. When present, the 0.5.0 count weights and spacing are
not used.

**What ends a leg.** Course change 80%, speed change 10%, both together 10% (Annex B FR-031
"alone or combined"). Field: `target_change_kind_weights`. Course changes keep the 0.5.0 angle
range, 30–120°.

**Transition length.** Annex B wants transitions of at least T_min = 1 min. At 0.5.0's turn rates
a 30° turn takes 10–60 s. Proposal: target turn rate 0.25–1°/s (30–120° turns take 30 s–8 min,
median about 2 min), and speed changes at 0.01–0.05 m/s² (a 2 kt change takes 20–100 s). Field
values only; no new field.

**Changes during ownship turns.** The 2-minute `target_manoeuvre_after_zig_s` guard is dropped
when the leg-length model is in use: a target change may start while ownship is turning. Zigs
are still planned on the target's straight track where possible; where a change falls inside
the zig, the ownship plan proceeds and the span is recorded (the G0 "before manoeuvre" check
already handles a change before the zig by scoring up to it).

**Ownship wander.** Two optional processes on the recorded ownship course, applied after the
exact track is simulated so that positions integrate the wandered course:
- helm wander, irregular: a first-order autoregressive course error with sd 1.5° and a 60 s time
  constant, clipped to ± 4°;
- autopilot oscillation, cyclic: a sinusoid of amplitude 1–3° and period 2–6 min.

Each scenario draws none, one or both (weights 0.4 / 0.3 / 0.3). Both stay inside Annex B's
± C = 5° band, so the ownship truth labels stay "steady" through them. Ownship navigation remains
exact (the recorded track is the true track). Fields: `ownship_wander`, `ownship_oscillation`.

**Speed wander** is not proposed: S = 0.5 kt leaves little room, and Annex B names course wander
only.

## 3. Consequences to decide in the spec

1. **Window length.** With legs of about 25 min, a 20–60 min window holds about one target change,
   and roughly a third of engagements hold none. That is enough spans statistically (10,000
   scenarios give about 10,000 spans) but few multi-leg engagements, which are the case Annex B
   is built for. Lengthening windows to 40–120 min gives 1–3 changes per engagement but doubles
   the padded row count (360 → 720), the physics-layer export window, and training cost per
   scenario. **Owner's call**; recommended default: keep 20–60 min for Gate S, and report the
   multi-change stratum, because the 720-row change touches every exported model.
2. **G5 rows** (zig + 5/10/15/20 min) and "settled" (> 5 min after the last change) keep their
   definitions; with long legs most G5 rows will be settled, so the all-rows and settled
   comparisons converge. Gate 2's criteria still read as written.
3. **References.** The IMM is re-tuned on 0.6.0 validation (slower turns favour a smaller
   coordinated-turn noise). Note 08's GLR + confirm reference and its 20% nomination threshold
   are re-run on 0.6.0 validation before Gate S's decision record.
4. **G0** re-runs on 0.6.0 (panel), as every generator version has.
5. **Detectability** shifts: long legs before a turn make the turn more detectable, slow turns
   less so per row. The bands of note 08 are kept and re-measured.

## 4. Order of work

1. Generator 0.6.0 spec (this scope, with the window decision), implementation, G0.
2. Validation and test seeds for MAN2; IMM re-tune; GLR + confirm re-run.
3. Spec 005's decision record, then O, C, L and Gate S on MAN2 data.
