# Generated from schema/tma.yaml by scripts/gen_types.py. Do not edit.
from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.12.0"
version = "0.26.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'tma',
     'default_range': 'string',
     'description': 'Single source of truth for every data type in the TMA via ML '
                    'proof of concept (constitution principle I). Frame: local '
                    'flat-earth Cartesian, x east, y north, metres, origin at '
                    "ownship's window-start position. Bearings and courses are "
                    'true, clockwise from north, radians in [0, 2π). Speeds in '
                    'm/s. Times in seconds since window start. All stored floats '
                    'are float32-rounded.',
     'id': 'https://github.com/debrief/gitma/schema/tma',
     'imports': ['linkml:types'],
     'license': 'Apache-2.0',
     'name': 'tma',
     'prefixes': {'UCUM': {'prefix_prefix': 'UCUM',
                           'prefix_reference': 'http://unitsofmeasure.org/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'tma': {'prefix_prefix': 'tma',
                          'prefix_reference': 'https://github.com/debrief/gitma/schema/tma/'}},
     'source_file': 'schema/tma.yaml',
     'title': 'TMA via ML data types'} )

class RecordKind(str, Enum):
    """
    Discriminator for records in NDJSON files.
    """
    header = "header"
    """
    Dataset or prediction file header (first line).
    """
    scenario = "scenario"
    """
    One Scenario.
    """
    prediction = "prediction"
    """
    One Prediction.
    """
    crb = "crb"
    """
    One CrbRecord (gitma2).
    """
    detector = "detector"
    """
    One DetectorRecord (gitma2, schema 0.21.0).
    """
    segmentation = "segmentation"
    """
    One Segmentation (gitma2, schema 0.23.0, spec 005).
    """


class Split(str, Enum):
    """
    Dataset split. Train/validation/test are 80/10/10 by scenario index.
    """
    train = "train"
    validation = "validation"
    test = "test"
    heldout = "heldout"
    """
    Held-out geometry with parameter ranges outside training.
    """


class TrackId(str, Enum):
    ownship = "ownship"
    target = "target"


class RangeDistribution(str, Enum):
    uniform = "uniform"
    log_uniform = "log_uniform"


class ZigRule(str, Enum):
    """
    How each zig's direction and size are chosen (generator 0.3.0, spec 007).
    """
    random = "random"
    """
    Size from zig_angle_abs_rad, side uniformly ±, regardless of the target.
    """
    across_los = "across_los"
    """
    Turn across the line of sight: the new course puts the target on the other bow at an angle off drawn from los_offset_rad, by the shorter turn. Uses the true bearing at the last sample before the turn.
    """


class ManoeuvreKind(str, Enum):
    """
    What a target manoeuvre changes (generator 0.5.0, SRD Annex C §C.2).
    """
    course = "course"
    """
    A rate-limited course change at constant speed (an arc).
    """
    speed = "speed"
    """
    A constant-acceleration speed change on a constant course.
    """
    both = "both"
    """
    A course change and a speed change starting together (generator 0.6.0, SRD Annex B): an arc while the speed changes linearly.
    """


class WanderKind(str, Enum):
    """
    Which ownship course-wander process a scenario drew (generator 0.6.0).
    """
    none = "none"
    wander = "wander"
    """
    Helm wander, an irregular first-order autoregressive course error.
    """
    oscillation = "oscillation"
    """
    Autopilot oscillation, a sinusoidal course error.
    """
    both = "both"


class CrbModel(str, Enum):
    """
    Which model the Cramér–Rao bound assumes (gitma2, references/crb.py).
    """
    full_window = "full_window"
    """
    Constant velocity over all bearings up to the row; right for a held-course target.
    """
    known_manoeuvres = "known_manoeuvres"
    """
    The generator's manoeuvre model with each manoeuvre's start time, duration and kind known and its size unknown, all bearings up to the row: the bound for an estimator that knows when and how the target manoeuvred (the oracle's regime).
    """
    per_leg = "per_leg"
    """
    Constant velocity over the current leg's bearings only. A diagnostic: it ignores earlier legs, so an estimator that knows the manoeuvre times can legitimately beat it.
    """


class PredictionMode(str, Enum):
    final = "final"
    """
    One row at the last timestep of the window.
    """
    per_timestep = "per_timestep"
    """
    One row per post-zig timestep using bearings up to that time.
    """


class GateId(str, Enum):
    P0 = "P0"
    """
    gitma2 pipeline gate (SRD §5): generator and references reproduce gitma, the physics layer equals batch least squares, the oracle ceiling is reproduced.
    """
    G0 = "G0"
    """
    Pipeline verified.
    """
    G1 = "G1"
    """
    gitma Gate 1; in gitma2 (spec 003) the constant-velocity gate of SRD §5: within 1.1 × batch least squares on every metric, gross errors no worse, efficiency ≤ 1.25 settled.
    """
    G2 = "G2"
    GD = "GD"
    """
    gitma2 Gate D (SRD Annex A §A.5, spec 004): the steady-leg detector against CUSUM and GLR at matched false-alarm rates, held-leg false alarms, and its downstream estimate.
    """
    G3 = "G3"
    G4 = "G4"
    """
    Better than the tuned tracker after a target turn (SRD Annex B §B.4).
    """
    G5 = "G5"
    """
    An end-to-end tracker better than the re-tuned reference overall, at most 10% worse when settled (SRD Annex C §C.5).
    """


class PhysicsHead(str, Enum):
    """
    How a gitma2 model produces its estimate (spec 003).
    """
    physics = "physics"
    """
    Heads feed the declared physics layer, which computes the estimate.
    """
    direct = "direct"
    """
    Control (a): the same encoder regresses the state directly; never carried (constitution III).
    """


class HeadActivation(str, Enum):
    """
    Hidden activation of a model's heads (schema 0.20.0, spec 004 R1).
    """
    relu = "relu"
    """
    Gate 1's heads (spec 003); a unit whose input stays negative never recovers.
    """
    tanh = "tanh"
    """
    Cannot die (its derivative is never zero); every configuration from spec 004.
    """


class DetectorVariant(str, Enum):
    """
    Causal (instantaneous) or time-late steady-leg detector (Annex A §A.1, D2).
    """
    causal = "causal"
    time_late = "time_late"


class ControlKind(str, Enum):
    """
    A non-learned manoeuvre detector used as a Gate D control (Annex A §A.2).
    """
    cusum = "cusum"
    """
    CUSUM on the per-timestep least-squares innovations (gated).
    """
    cusum_ekf = "cusum_ekf"
    """
    CUSUM on the frozen EKF's innovations (reported, not gated).
    """
    glr = "glr"
    """
    Linearised one-versus-two-leg GLR over a sliding window (research R6).
    """
    imm_mode = "imm_mode"
    """
    The frozen IMM's coordinated-turn mode probability.
    """


class ModelKind(str, Enum):
    """
    Model families of SRD §4.
    """
    instantaneous = "instantaneous"
    """
    Causal single-layer LSTM (operator's running solution).
    """
    time_late = "time_late"
    """
    Bidirectional LSTM over the whole window.
    """
    causal_cnn = "causal_cnn"
    """
    Causal 1-D CNN control for the instantaneous variant.
    """
    mlp = "mlp"
    """
    MLP over the flattened window, control for the time-late variant.
    """
    learned_gain_filter = "learned_gain_filter"
    """
    Phase 4 tracker T1 (spec 012, SRD Annex C §C.4): a constant-velocity filter with a bearings-only update whose gain a GRU of `units` computes each step, in one declared filter layer (constitution 1.3.0). Reads the raw feature set; outputs the velocity parameterisation.
    """


class StopReason(str, Enum):
    max_epochs = "max_epochs"
    early_stopping = "early_stopping"
    wall_clock = "wall_clock"
    diverged = "diverged"


class OutputParameterisation(str, Enum):
    """
    How the model's four output channels encode the target's course and speed (spec 008).
    """
    course_speed = "course_speed"
    """
    log_range_km, course_sin, course_cos, speed / speed_scale_mps (iterations 1–3).
    """
    velocity = "velocity"
    """
    log_range_km, vx / velocity_scale_mps, vy / velocity_scale_mps, and a fourth channel that carries no loss and is ignored; course and speed are derived from (vx, vy).
    """
    velocity_two_hypothesis = "velocity_two_hypothesis"
    """
    Spec 011 (phase 3b): seven channels per row. log_range_km, vx, vy (as velocity) under the hypothesis that the target has not turned; the same under the hypothesis that it has; and a logit of P(the target's turn has started by this row). Each hypothesis is trained only on rows where it is true (the label comes from the stored truth course); the logit by binary cross-entropy. The reported estimate is the more probable hypothesis's, never an average.
    """
    velocity_gaussian = "velocity_gaussian"
    """
    Spec 012 (phase 4, tracker T2): six channels per row. log_range_km, vx, vy (as velocity), then the log-variance of each, trained by the Gaussian negative log-likelihood. The reported estimate is the mean; prediction rows carry the standard deviations (log_range_sd, vx_sd_mps, vy_sd_mps), reported and their calibration measured, never gated.
    """


class FeatureSet(str, Enum):
    """
    Model input channel sets (spec 003 R6).
    """
    raw = "raw"
    """
    Iteration-1 layout, 10 input channels.
    """
    derived = "derived"
    """
    raw plus bearing_rate_scaled, rate_valid and intercept_scaled (13 channels), computed causally from bearings and ownship states up to each row.
    """


class GateResult(str, Enum):
    pass_ = "pass"
    fail = "fail"
    inconclusive = "inconclusive"
    """
    The 95% bootstrap interval straddles the threshold (G1 report, T033).
    """
    reported = "reported"
    """
    A figure reported beside the gate, not gated (schema 0.21.0).
    """


class SegmentKind(str, Enum):
    """
    An interval of a segmentation (spec 005, SRD Annex B).
    """
    steady = "steady"
    """
    A steady leg: course within ± C and speed within ± S of the leg mean, at least L_min.
    """
    transition = "transition"
    """
    Between two steady legs; no motion model assumed; at least T_min unless open.
    """
    unknown = "unknown"
    """
    Not classified (too little history, or the cost margin is below the declared value).
    """


class SegmentMode(str, Enum):
    """
    How a segmentation is handed to the physics layer (spec 005 FR-030).
    """
    gap = "gap"
    """
    Knots at both ends of each transition; its bearings excluded.
    """
    chord = "chord"
    """
    Knots at both ends; bearings kept; the speed prior across course-only transitions.
    """


class EComponent(str, Enum):
    """
    A learned part of Gate 2's model E (spec 007 research R2).
    """
    weights = "weights"
    """
    E-w: per-bearing log-weights and an initial-state correction on C's segmentation.
    """
    evidence = "evidence"
    """
    E-s: evidence that shifts C's confirmation threshold, trained over decision tables.
    """


class OpenHandover(str, Enum):
    """
    How a transition still open at the scored row k is handed to the physics layer (Gate S panel round 2: one convention for the oracle and the segmenters, fixed before Gate 2).
    """
    knot_at_k = "knot_at_k"
    """
    Spec 005's: knots at s and at k; in gap mode rows s … k − 1 excluded; the speed prior at k.
    """
    start_masked = "start_masked"
    """
    A knot at s only; rows s … k excluded (the oracle's mask_turns convention).
    """
    start_chord = "start_chord"
    """
    A knot at s only; the bearings kept (the oracle's default for a span in progress).
    """



class FloatRange(ConfiguredBaseModel):
    """
    Closed interval [min, max].
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    min: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FloatRange', 'LegLengthModel']} })
    max: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FloatRange']} })


class LegLengthModel(ConfiguredBaseModel):
    """
    Target leg lengths (generator 0.6.0): normal with this mean and standard deviation, clipped below at min. The MAN2 defaults are 1500, 546 and 300 s (5% of legs at or under 10 min).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    mean: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LegLengthModel'], 'unit': {'ucum_code': 's'}} })
    sd: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LegLengthModel'], 'unit': {'ucum_code': 's'}} })
    min: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FloatRange', 'LegLengthModel'], 'unit': {'ucum_code': 's'}} })


class ChangeKindWeights(ConfiguredBaseModel):
    """
    Relative weights of what ends a target leg (generator 0.6.0); normalised.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    course: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeKindWeights']} })
    speed: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeKindWeights']} })
    both: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeKindWeights', 'WanderWeights']} })


class HelmWanderRanges(ConfiguredBaseModel):
    """
    Helm wander (generator 0.6.0): a first-order autoregressive course error with standard deviation sd_rad, correlation time tau_s and a hard clip at ±clip_rad.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    sd_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 'rad'}} })
    tau_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'], 'unit': {'ucum_code': 's'}} })
    clip_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 'rad'}} })


class OscillationRanges(ConfiguredBaseModel):
    """
    Autopilot oscillation (generator 0.6.0): a sinusoidal course error with amplitude and period drawn uniformly from these ranges and a uniform phase.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    amp_rad: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OscillationRanges', 'OwnshipWander']} })
    period_s: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OscillationRanges', 'OwnshipWander']} })


class WanderWeights(ConfiguredBaseModel):
    """
    Relative weights of the ownship wander kinds per scenario (generator 0.6.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    none: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['WanderWeights']} })
    wander: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['WanderWeights']} })
    oscillation: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['WanderWeights']} })
    both: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeKindWeights', 'WanderWeights']} })


class OwnshipWander(ConfiguredBaseModel):
    """
    The ownship wander a scenario drew and its parameters (generator 0.6.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: WanderKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    sd_rad: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 'rad'}} })
    tau_s: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'], 'unit': {'ucum_code': 's'}} })
    clip_rad: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['HelmWanderRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 'rad'}} })
    amp_rad: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OscillationRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 'rad'}} })
    period_s: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OscillationRanges', 'OwnshipWander'],
         'unit': {'ucum_code': 's'}} })
    phase_rad: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander'], 'unit': {'ucum_code': 'rad'}} })


class ScenarioParameters(ConfiguredBaseModel):
    """
    The random draws that define one scenario.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    window_s: float = Field(default=..., description="""Window length; multiple of dt_s.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 's'}} })
    dt_s: float = Field(default=..., description="""Bearing interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 's'}} })
    ownship_speed_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 'm/s'}} })
    ownship_course0_rad: float = Field(default=..., description="""Ownship course on leg 1.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    zig_angle_rad: float = Field(default=..., description="""Signed course change at the zig; positive is clockwise.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    zig_fraction: float = Field(default=..., description="""Zig time as a fraction of the window.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    target_range0_m: float = Field(default=..., description="""Range at window start.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 'm'}} })
    target_bearing0_rad: float = Field(default=..., description="""True bearing at window start.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    target_speed_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 'm/s'}} })
    target_course_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    noise_sigma_rad: float = Field(default=..., description="""Bearing noise σ; 0 = noise-free.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    dropout_fraction: float = Field(default=..., description="""Probability each bearing is missing.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    ownship_turn_rate_rad_s: Optional[float] = Field(default=None, description="""Ownship turn rate at the zig (rate-limited turn, spec 003 US6). Absent or 0: the course changes instantaneously, as in generator 0.1.0.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 'rad/s'}} })
    zig2_delay_s: Optional[float] = Field(default=None, description="""Second zig (generator 0.3.0, spec 007): time from the first sample on leg 2 to the start of the second turn. Absent: one zig, two legs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 's'}} })
    zig2_angle_rad: Optional[float] = Field(default=None, description="""Signed course change at the second zig; positive is clockwise.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    target_manoeuvre_time_s: Optional[float] = Field(default=None, description="""Target course change (generator 0.4.0, SRD Annex B §B.2): time the target's turn starts, a whole number of samples. Absent: the target holds course.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 's'}} })
    target_manoeuvre_angle_rad: Optional[float] = Field(default=None, description="""Signed target course change; positive is clockwise.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters'], 'unit': {'ucum_code': 'rad'}} })
    target_turn_rate_rad_s: Optional[float] = Field(default=None, description="""Target turn rate through its course change.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 'rad/s'}} })
    target_manoeuvres: Optional[list[TargetManoeuvre]] = Field(default=None, description="""Target manoeuvres in time order (generator 0.5.0, SRD Annex C §C.2), none overlapping. Present (possibly empty) only under generator 0.5.0 ranges; then the single-turn fields above are absent.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters']} })


class TargetManoeuvre(ConfiguredBaseModel):
    """
    One target manoeuvre (generator 0.5.0). A course change is an arc at constant speed; a speed change is constant acceleration on a constant course.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: ManoeuvreKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    start_time_s: float = Field(default=..., description="""Time the manoeuvre starts, a whole number of samples.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre'], 'unit': {'ucum_code': 's'}} })
    change: float = Field(default=..., description="""Signed change: course in rad (positive clockwise) or speed in m/s (positive faster).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre', 'ChangeDecision']} })
    rate: float = Field(default=..., description="""Magnitude of the rate of change, rad/s (course) or m/s² (speed).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre']} })
    change2: Optional[float] = Field(default=None, description="""For kind both: the speed change (m/s) that accompanies the course change in `change` (generator 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre']} })
    rate2: Optional[float] = Field(default=None, description="""For kind both: the acceleration (m/s²) of that speed change.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre']} })


class ParameterRanges(ConfiguredBaseModel):
    """
    Ranges from which ScenarioParameters are drawn. Initial ownship course, target bearing and target course are always uniform on [0, 2π); zig sign is uniform ±.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    window_s: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    dt_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    ownship_speed_mps: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    zig_angle_abs_rad: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    zig_fraction: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    target_range0_m: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    range_distribution: RangeDistribution = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_speed_mps: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    noise_sigma_rad_values: list[float] = Field(default=..., description="""σ drawn uniformly from this set.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    dropout_fraction: FloatRange = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    ownship_turn_rate_rad_s: Optional[FloatRange] = Field(default=None, description="""Turn rate drawn uniformly per scenario; absent means an instantaneous zig.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    zig_rule: Optional[ZigRule] = Field(default=None, description="""How each zig is chosen; absent means random (generators 0.1.0–0.2.0). Under across_los zig_angle_abs_rad is still drawn but not used.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    los_offset_rad: Optional[FloatRange] = Field(default=None, description="""Angle off the line of sight, on the other bow, after an across_los turn; required when zig_rule is across_los.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    zig2_delay_s: Optional[FloatRange] = Field(default=None, description="""Delay from the start of leg 2 to the second turn; absent means one zig. The second zig follows zig_rule (and uses the same turn rate as the first).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges'],
         'unit': {'ucum_code': 's'}} })
    target_manoeuvre_fraction: Optional[float] = Field(default=None, description="""Probability a scenario's target makes one course change (generator 0.4.0, SRD Annex B §B.2); absent means the target always holds course, as generators 0.1.0–0.3.0. When present, every scenario draws the manoeuvre parameters (so the PRNG is consumed alike) and the window must fit a turn whether or not one is made.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_manoeuvre_angle_abs_rad: Optional[FloatRange] = Field(default=None, description="""Absolute target course change; the sign is uniform ±.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_turn_rate_rad_s: Optional[FloatRange] = Field(default=None, description="""Target turn rate, drawn uniformly per scenario.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioParameters', 'ParameterRanges']} })
    target_manoeuvre_after_zig_s: Optional[float] = Field(default=None, description="""Earliest start of the target's turn, after the first sample on leg 2.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges'], 'unit': {'ucum_code': 's'}} })
    target_manoeuvre_margin_s: Optional[float] = Field(default=None, description="""Least time from the end of the target's turn to the end of the window, so the gate point (manoeuvre + 5 min) is reached.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges'], 'unit': {'ucum_code': 's'}} })
    target_course_change_count_weights: Optional[list[float]] = Field(default=None, description="""Generator 0.5.0 (SRD Annex C §C.2): probabilities of 0, 1, 2, … target course changes (summing to 1). Present: every scenario draws its manoeuvres this way, with target_manoeuvre_angle_abs_rad, target_turn_rate_rad_s, target_manoeuvre_after_zig_s and target_manoeuvre_margin_s, and target_manoeuvre_fraction must be absent.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_speed_change_fraction: Optional[float] = Field(default=None, description="""Probability of one target speed change (generator 0.5.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_speed_change_abs_mps: Optional[FloatRange] = Field(default=None, description="""Absolute speed change; its sign is uniform ±, flipped if the new speed would leave target_speed_mps (redrawn if both signs would).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_speed_change_rate_mps2: Optional[FloatRange] = Field(default=None, description="""Magnitude of the target's acceleration during a speed change.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_manoeuvre_spacing_s: Optional[float] = Field(default=None, description="""Least time from the end of one target manoeuvre to the start of the next.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges'], 'unit': {'ucum_code': 's'}} })
    target_leg_length_s: Optional[LegLengthModel] = Field(default=None, description="""Generator 0.6.0 (SRD Annex B, MAN2): target legs are drawn from this law and laid end to end with a uniform first phase. Exclusive with the count weights, spacing, after-zig and margin fields.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    target_change_kind_weights: Optional[ChangeKindWeights] = Field(default=None, description="""What ends a target leg (generator 0.6.0); needs target_leg_length_s.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    ownship_wander: Optional[HelmWanderRanges] = Field(default=None, description="""Helm wander on the recorded ownship course (generator 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges', 'ScenarioMetadata']} })
    ownship_oscillation: Optional[OscillationRanges] = Field(default=None, description="""Autopilot oscillation on the recorded ownship course (generator 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    ownship_wander_weights: Optional[WanderWeights] = Field(default=None, description="""Per-scenario choice of ownship wander kind (generator 0.6.0); required when ownship_wander or ownship_oscillation is present.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges']} })
    min_range_m: float = Field(default=..., description="""Geometries closer than this at any sample are redrawn.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges', 'ScenarioMetadata']} })


class PlatformState(ConfiguredBaseModel):
    """
    One platform state. Stone Soup analogue GroundTruthState.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    timestamp_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'Observation', 'PredictionRow'],
         'unit': {'ucum_code': 's'}} })
    x_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'm'}} })
    y_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'm'}} })
    course_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'rad'}} })
    speed_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow', 'NaiveMeans'],
         'unit': {'ucum_code': 'm/s'}} })


class Track(ConfiguredBaseModel):
    """
    Time-ordered states of one platform. Stone Soup analogue GroundTruthPath.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: TrackId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    states: list[PlatformState] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track']} })


class Observation(ConfiguredBaseModel):
    """
    One bearing from ownship to target. Stone Soup analogue Detection. When valid is false (dropout) bearing_rad is 0 and must be ignored.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    timestamp_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'Observation', 'PredictionRow'],
         'unit': {'ucum_code': 's'}} })
    bearing_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Observation'], 'unit': {'ucum_code': 'rad'}} })
    valid: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Observation']} })


class ScenarioMetadata(ConfiguredBaseModel):
    """
    Seed, parameter draws and derived slicing keys for one scenario.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    seed: str = Field(default=..., description="""Scenario seed as a decimal uint64 string.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    index: int = Field(default=..., description="""Scenario index within the dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    parameters: ScenarioParameters = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata', 'SegmentationHeader', 'GateSDecision']} })
    samples: int = Field(default=..., description="""Number of timesteps (60–240).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig_index: int = Field(default=..., description="""First timestep on leg 2 (with a rate-limited turn, the first after it completes).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    turn_start_index: Optional[int] = Field(default=None, description="""First timestep after the turn starts (absent for an instantaneous zig).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig2_index: Optional[int] = Field(default=None, description="""First timestep on leg 3, after the second turn completes (absent with one zig). Gate times still count from zig_index.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    turn2_start_index: Optional[int] = Field(default=None, description="""First timestep after the second turn starts (absent with one zig or no turn rate).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvre_start_index: Optional[int] = Field(default=None, description="""First timestep after the target's turn starts (generator 0.4.0; absent when the target holds course). Under generator 0.5.0, after the first manoeuvre starts.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvre_index: Optional[int] = Field(default=None, description="""First timestep after the target's turn completes (generator 0.4.0; absent when the target holds course). Gate G4 counts time from here, as earlier gates count from zig_index. Under generator 0.5.0, after the last manoeuvre completes. Under 0.6.0 the last change may still be in progress at the window's end, and then this (and that span's end_index) is at or beyond `samples`: no row of the window is after it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvres: Optional[list[ManoeuvreSpan]] = Field(default=None, description="""Generator 0.5.0: each target manoeuvre's sample span, in time order (present, possibly empty, only under 0.5.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    ownship_wander: Optional[OwnshipWander] = Field(default=None, description="""The ownship course wander drawn for this scenario (generator 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges', 'ScenarioMetadata']} })
    zig_on_manoeuvre: Optional[bool] = Field(default=None, description="""The ownship's turn rows (from turn_start_index up to, not including, zig_index) share a row with a target manoeuvre span [start_index, end_index): the target manoeuvres while ownship turns (generator 0.6.0). Without a rate-limited turn, the zig row alone.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig_time_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata'], 'unit': {'ucum_code': 's'}} })
    mean_range_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata'], 'unit': {'ucum_code': 'm'}} })
    min_range_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges', 'ScenarioMetadata'],
         'unit': {'ucum_code': 'm'}} })


class ManoeuvreSpan(ConfiguredBaseModel):
    """
    Where one target manoeuvre lies in a scenario's samples (generator 0.5.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: ManoeuvreKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    start_index: int = Field(default=..., description="""First timestep after it starts.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })
    end_index: int = Field(default=..., description="""First timestep after it completes; at or beyond `samples` when the change is still in progress at the window's end (generator 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })


class Scenario(ConfiguredBaseModel):
    """
    One ownship-vs-target run over a window.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma',
         'tree_root': True})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    metadata: ScenarioMetadata = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    ownship: Track = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    target: Track = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    observations: list[Observation] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })


class DatasetHeader(ConfiguredBaseModel):
    """
    First record of every dataset file.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'ExperimentManifest',
                       'ModelManifest',
                       'PhysicsModelManifest']} })
    dataset_seed: str = Field(default=..., description="""Decimal uint64 string.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    split: Split = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'GateSRecord', 'Gate2Record']} })
    scenario_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    index_start: int = Field(default=..., description="""First scenario index (inclusive).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    index_end: int = Field(default=..., description="""Last scenario index (exclusive).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    parameter_ranges: ParameterRanges = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    redraw_count: int = Field(default=..., description="""Geometries rejected for violating min_range_m.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    created_by: str = Field(default=..., description="""Command line that produced the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    generator_git_commit: Optional[str] = Field(default=None, description="""Commit of the checkout that ran tma-generate (absent before schema 0.8.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    generator_git_dirty: Optional[bool] = Field(default=None, description="""True when that checkout had uncommitted changes (only allowed with --allow-dirty; absent before schema 0.8.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })


class NormalisationConstants(ConfiguredBaseModel):
    """
    Fixed scaling constants computed from the train split's input channels only.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    position_scale_km: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants']} })
    speed_scale_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants']} })
    time_scale_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants']} })
    computed_from: str = Field(default=..., description="""Always \"inputs_only\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants']} })
    train_header_digest: str = Field(default=..., description="""SHA-256 of the train header.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants']} })
    bearing_rate_scale_rad_s: Optional[float] = Field(default=None, description="""90th percentile of |trailing least-squares bearing rate| over train inputs; required for the derived feature set.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NormalisationConstants'], 'unit': {'ucum_code': 'rad/s'}} })


class FeatureLayout(ConfiguredBaseModel):
    """
    Documents the model tensors (not stored as records). inputs [N, 240, 10]: bearing_sin, bearing_cos, own_x_km, own_y_km, own_course_sin, own_course_cos, own_speed_scaled, time_scaled, valid, window_mask; the derived feature set appends bearing_rate_scaled, rate_valid, intercept_scaled [N, 240, 13]. targets [N, 240, 6]: log_range_km, course_sin, course_cos, speed_scaled, x_km, y_km. loss_mask [N, 240]: window_mask and t ≥ zig_time. Features file format 2 also embeds the source DatasetHeader and the source dataset SHA-256.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    feature_set: Optional[FeatureSet] = Field(default=None, description="""Absent means raw.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'TrainingConfig']} })
    rows: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'Prediction']} })
    input_channels: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout']} })
    target_channels: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout']} })


class PredictionRow(ConfiguredBaseModel):
    """
    An estimator's target estimate at one timestep.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    timestamp_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'Observation', 'PredictionRow'],
         'unit': {'ucum_code': 's'}} })
    range_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm'}} })
    course_rad: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'rad'}} })
    speed_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow', 'NaiveMeans'],
         'unit': {'ucum_code': 'm/s'}} })
    x_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'm'}} })
    y_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow'], 'unit': {'ucum_code': 'm'}} })
    converged: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    iterations: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow', 'PhysicsModelConfig', 'DetectorConfig']} })
    p_manoeuvre: Optional[float] = Field(default=None, description="""The estimator's probability that the target's turn has started by this timestep (velocity_two_hypothesis networks only; spec 011). Absent for other estimators.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    log_range_sd: Optional[float] = Field(default=None, description="""Standard deviation of the estimator's log range (natural log; about the relative range error): from a velocity_gaussian network (spec 012), or by first-order propagation of the row's covariance (physics-layer and tracker rows; spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    course_sd_rad: Optional[float] = Field(default=None, description="""First-order standard deviation of course from the row's covariance (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'rad'}} })
    speed_sd_mps: Optional[float] = Field(default=None, description="""First-order standard deviation of speed from the row's covariance (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm/s'}} })
    cov_xyvv: Optional[list[float]] = Field(default=None, description="""Upper triangle, row-major, of the 4 x 4 covariance of (x, y, vx, vy) at the row (10 values; m², m²/s, m²/s²), as the estimator states it (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    cov_ok: Optional[bool] = Field(default=None, description="""The covariance is usable: finite, positive definite, and the target not on ownship (range > 1 m) (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    cov_scale_log: Optional[float] = Field(default=None, description="""Calibrated rows only: the calibration's log-scale s; the stated covariance is e^(2s) times the solve's (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    vx_sd_mps: Optional[float] = Field(default=None, description="""Standard deviation of the estimated east velocity (velocity_gaussian only).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm/s'}} })
    vy_sd_mps: Optional[float] = Field(default=None, description="""Standard deviation of the estimated north velocity (velocity_gaussian only).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm/s'}} })


class Prediction(ConfiguredBaseModel):
    """
    One estimator's output for one scenario.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    mode: PredictionMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction', 'PredictionHeader', 'SegmentParameters']} })
    rows: list[PredictionRow] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'Prediction']} })


class PredictionHeader(ConfiguredBaseModel):
    """
    First record of every prediction file.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    mode: PredictionMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction', 'PredictionHeader', 'SegmentParameters']} })
    dataset_digest: str = Field(default=..., description="""SHA-256 of the truth file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    weights_digest: Optional[str] = Field(default=None, description="""SHA-256 of the learned estimator's weights file (schema 0.20.0; required by gate commands for learned estimators).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })


class CrbHeader(ConfiguredBaseModel):
    """
    First record of a tma2-crb file (gitma2).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    model: CrbModel = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CrbHeader', 'ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    dataset_digest: str = Field(default=..., description="""SHA-256 of the truth file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })


class CrbRecord(ConfiguredBaseModel):
    """
    Cramér–Rao bounds at the truth for one scenario's scored rows (zig_index + 1 … end); where the information is singular the bounds are 0 and singular is true (gitma2).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    first_row: int = Field(default=..., description="""Row index of the first entry.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbRecord']} })
    sd_range_rel: Optional[list[float]] = Field(default=None, description="""Bound on range error ÷ range.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbRecord']} })
    sd_course_deg: Optional[list[float]] = Field(default=None, description="""Bound on course error (degrees).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbRecord']} })
    sd_speed_kt: Optional[list[float]] = Field(default=None, description="""Bound on speed error (knots).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbRecord']} })
    singular: Optional[list[bool]] = Field(default=None, description="""True where no bound exists.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbRecord']} })


class MetricsRecord(ConfiguredBaseModel):
    """
    Metric values for one estimator on one slice at one evaluation point.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    slice: str = Field(default=..., description="""\"overall\" or e.g. \"range_band=5-10km\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'PairedComparison']} })
    point: str = Field(default=..., description="""\"final\" or \"zig+<n>s\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'PairedComparison']} })
    n: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'NaiveMeans', 'CurvePoint']} })
    excluded: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    range_rel_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    range_rel_p90: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    course_deg_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    course_deg_p90: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    speed_kt_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    speed_kt_p90: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    gross_error_rate: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    non_converged_rate: Optional[float] = Field(default=None, description="""Fraction of rows with no estimate (scored +∞; explains absent medians/P90).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })
    position_m_mean: Optional[float] = Field(default=None, description="""Mean position error over converged rows (non-converged rows count in gross_error_rate).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    position_window_m_median: Optional[float] = Field(default=None, description="""Median over scenarios of each scenario's mean position error over its predicted rows (time-late window-mean position, SRD §5; reported, not gated).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord'], 'unit': {'ucum_code': 'm'}} })
    position_window_m_p90: Optional[float] = Field(default=None, description="""90th percentile over scenarios of the same per-scenario mean.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord'], 'unit': {'ucum_code': 'm'}} })
    crb_range_rel_median: Optional[float] = Field(default=None, description="""Median over the slice's rows of the Cramér–Rao bound on relative range error (gitma2, schema 0.17.0; absent when no row has a regular bound).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    crb_course_deg_median: Optional[float] = Field(default=None, description="""Median Cramér–Rao bound on course error (degrees).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    crb_speed_kt_median: Optional[float] = Field(default=None, description="""Median Cramér–Rao bound on speed error (knots).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    efficiency_range: Optional[float] = Field(default=None, description="""Median over rows with a regular bound of (range error ÷ that row's range bound), divided by 0.6745 so that an unbiased estimator at the bound scores 1 (gitma2). A flat value across geometry slices marks an approximation floor rather than missing information.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })
    efficiency_course: Optional[float] = Field(default=None, description="""As efficiency_range, for course error ÷ the row's course bound.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })
    efficiency_speed: Optional[float] = Field(default=None, description="""As efficiency_range, for speed error ÷ the row's speed bound.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })
    crb_singular_rate: Optional[float] = Field(default=None, description="""Fraction of the slice's rows where the Fisher information is singular (no bound).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord']} })


class DatasetRef(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    path: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef', 'ArtefactRef']} })
    header: DatasetHeader = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef']} })
    digest: Optional[str] = Field(default=None, description="""SHA-256 of the dataset file (absent in manifests written before schema 0.4.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef', 'ArtefactRef']} })


class ArtefactRef(ConfiguredBaseModel):
    """
    A file an experiment read or wrote besides its datasets (gitma2, schema 0.17.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    path: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef', 'ArtefactRef']} })
    digest: str = Field(default=..., description="""SHA-256 of the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef', 'ArtefactRef']} })
    role: Optional[str] = Field(default=None, description="""What the file is, e.g. \"prediction cache\", \"export conformance results\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['ArtefactRef']} })


class PackageVersion(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PackageVersion', 'EstimatorRef', 'GateCheck']} })
    version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PackageVersion']} })


class RunEnvironment(ConfiguredBaseModel):
    """
    Software and hardware an experiment ran on (gitma2, schema 0.17.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    packages: Optional[list[PackageVersion]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment']} })
    lockfile_digest: Optional[str] = Field(default=None, description="""SHA-256 of uv.lock.""", json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment']} })
    cpu_model: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment', 'ModelManifest', 'JobRecord']} })
    cpu_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment']} })
    torch_threads: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment']} })


class EstimatorRef(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PackageVersion', 'EstimatorRef', 'GateCheck']} })
    settings_json: str = Field(default=..., description="""Estimator settings as JSON.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EstimatorRef']} })


class ExperimentManifest(ConfiguredBaseModel):
    """
    Everything needed to reproduce an experiment run.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    created: str = Field(default=..., description="""ISO 8601 timestamp.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: Optional[bool] = Field(default=None, description="""True when the working tree had uncommitted changes (absent before schema 0.4.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    node_version: Optional[str] = Field(default=None, description="""Node.js version that ran the experiment (byte identity is promised per pinned Node).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    python_version: Optional[str] = Field(default=None, description="""Python version that ran the experiment (gitma2, schema 0.17.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    torch_version: Optional[str] = Field(default=None, description="""PyTorch version that ran the experiment, when a physics layer or model was used (gitma2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'ExperimentManifest',
                       'ModelManifest',
                       'PhysicsModelManifest']} })
    datasets: list[DatasetRef] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    estimators: list[EstimatorRef] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    normalisation: Optional[NormalisationConstants] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    command_lines: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    environment: Optional[RunEnvironment] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    artefacts: Optional[list[ArtefactRef]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    amendments: Optional[list[ArtefactRef]] = Field(default=None, description="""Amendments of the decision record in force, by path and digest (schema 0.20.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })


class GateCheck(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PackageVersion', 'EstimatorRef', 'GateCheck']} })
    result: GateResult = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'GateVerdict']} })
    detail: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    value: Optional[float] = Field(default=None, description="""Statistic tested (e.g. median range error).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    threshold: Optional[float] = Field(default=None, description="""Limit the statistic is tested against.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'ControlSettings', 'GateDDecision']} })
    threshold_low: Optional[float] = Field(default=None, description="""Lower limit, for a check that passes inside an interval (gitma2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    ci_low: Optional[float] = Field(default=None, description="""Lower bound of the bootstrap interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    ci_high: Optional[float] = Field(default=None, description="""Upper bound of the bootstrap interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    ci_level: Optional[float] = Field(default=None, description="""Interval coverage, e.g. 0.95.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })


class GateVerdict(ConfiguredBaseModel):
    """
    Machine verdict for a gate; the team review records the final decision.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    gate: GateId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict']} })
    result: GateResult = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'GateVerdict']} })
    checks: list[GateCheck] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict']} })
    decided_by: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict', 'GateSRecord', 'Gate2Record']} })


class NaiveMeans(ConfiguredBaseModel):
    """
    Training-set means used by the naive baseline for one prediction mode.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    log_range_km: float = Field(default=..., description="""Mean of ln(range in km).""", json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveMeans']} })
    course_sin: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveMeans']} })
    course_cos: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveMeans']} })
    speed_mps: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PlatformState', 'PredictionRow', 'NaiveMeans'],
         'unit': {'ucum_code': 'm/s'}} })
    n: int = Field(default=..., description="""Number of labels averaged.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'NaiveMeans', 'CurvePoint']} })


class NaiveModel(ConfiguredBaseModel):
    """
    Naive baseline (SRD §5): predicts training-set means. final uses each scenario's last-sample label; per_timestep uses every post-zig label.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    train_digest: str = Field(default=..., description="""SHA-256 of the train file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveModel']} })
    final: NaiveMeans = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveModel']} })
    per_timestep: NaiveMeans = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['NaiveModel']} })


class CurvePoint(ConfiguredBaseModel):
    """
    One point of an error-vs-time-since-zig curve (curves.csv row).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    t_since_zig_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CurvePoint'], 'unit': {'ucum_code': 's'}} })
    n: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'NaiveMeans', 'CurvePoint']} })
    range_rel_median: Optional[float] = Field(default=None, description="""Absent when not finite (more than half the rows non-converged), as in MetricsRecord.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    range_rel_p90: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    course_deg_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    speed_kt_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    gross_error_rate: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    non_converged_rate: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })
    efficiency_range: Optional[float] = Field(default=None, description="""Range efficiency at this time, defined as in MetricsRecord (gitma2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })
    efficiency_speed: Optional[float] = Field(default=None, description="""Speed efficiency at this time, defined as in MetricsRecord (gitma2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint']} })


class TrainingConfig(ConfiguredBaseModel):
    """
    Hyperparameters and seeds for one training run (SRD §4; constitution III).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., description="""Estimator name used in predictions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    model_kind: ModelKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    units: int = Field(default=..., description="""LSTM units (per direction), conv filters or dense width.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    kernel_size: Optional[int] = Field(default=None, description="""Causal CNN kernel size.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    layers: Optional[int] = Field(default=None, description="""Stacked layers: causal CNN conv layers (no dilation; default 3), or recurrent layers for instantaneous and time_late (default 1; each returns sequences; spec 003 R20).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    learning_rate: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    batch_size: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    max_epochs: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    patience: int = Field(default=..., description="""Epochs without validation improvement before stopping.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    max_wall_s: float = Field(default=..., description="""Wall-clock cap in seconds.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_range: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_course: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_speed: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_manoeuvre: Optional[float] = Field(default=None, description="""Weight of the turn-probability cross-entropy term (velocity_two_hypothesis only; spec 011). Absent means 1.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    train_seed: str = Field(default=..., description="""Decimal uint64; derives initializer seeds and batch order.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig',
                       'TrainingPlan',
                       'GateSDecision',
                       'Gate2Decision']} })
    train_limit: Optional[int] = Field(default=None, description="""Use only the first N training scenarios (tests and smoke runs).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    shuffle_labels: bool = Field(default=..., description="""Permute targets across scenarios (leakage check).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig']} })
    feature_set: Optional[FeatureSet] = Field(default=None, description="""Input channel set; absent means raw. Must match the features files.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'TrainingConfig']} })
    output_parameterisation: Optional[OutputParameterisation] = Field(default=None, description="""Output encoding; absent means course_speed. With velocity, loss_weight_speed weights each velocity component and loss_weight_course is unused (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    velocity_scale_mps: Optional[float] = Field(default=None, description="""Velocity scale in m/s for the velocity parameterisation (required with it): the top of the generator's target speed range, a constant of the problem, never a truth statistic.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    length_bucketing: Optional[bool] = Field(default=None, description="""Length bucketing (research R15; default false). Each group of bucket_batches batches of the epoch's seeded permutation is sorted by valid length, cut into batches whose rows are trimmed to the longest window, and the batch order is shuffled with a seed derived from train_seed and the epoch. The model takes a variable time dimension. Not for mlp.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    bucket_batches: Optional[int] = Field(default=None, description="""Batches per length-bucketing group (default 16).""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    tfjs_threads: Optional[int] = Field(default=None, description="""TensorFlow intra-op and inter-op thread count, set by tma-train through TF_NUM_INTRAOP_THREADS and TF_NUM_INTEROP_THREADS before tfjs-node loads. Absent: the TensorFlow default (one per core) or whatever the environment sets.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })


class EpochRecord(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'CheckpointMeta']} })
    train_loss: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord']} })
    val_loss: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'Continuation']} })
    seconds: float = Field(default=..., description="""Cumulative wall time.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'JobRecord']} })


class Continuation(ConfiguredBaseModel):
    """
    The committed model a seeded continuation started from (scripts/train-continue.mjs; spec 003 decision 14, spec 004 decision 15). Its epoch records up to best_epoch are kept in the continued run's manifest, with their val_loss as recorded under the earlier config.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    weights_digest: str = Field(default=..., description="""SHA-256 of the weights the continuation resumed from (the source's best epoch).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest']} })
    val_loss: float = Field(default=..., description="""The source's best-epoch validation loss under the source's config.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'Continuation']} })
    rescored_val_loss: Optional[float] = Field(default=None, description="""The source's best weights re-scored under the continued run's loss, written by tma-train when it resumed (spec 004 FR-002). With best_epoch and best_val_loss it makes the kept weights auditable: a run whose best_epoch is the source's must have best_val_loss equal to this value and weights_digest equal to the source's.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation']} })
    git_commit: Optional[str] = Field(default=None, description="""The source model's training-code commit, when it recorded one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })


class ModelManifest(ConfiguredBaseModel):
    """
    Everything needed to reproduce and identify a trained model.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    config: TrainingConfig = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'PhysicsModelManifest']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'ExperimentManifest',
                       'ModelManifest',
                       'PhysicsModelManifest']} })
    train_features_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    val_features_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    normalisation: NormalisationConstants = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    epochs: list[EpochRecord] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'PhysicsModelConfig', 'DetectorConfig']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest']} })
    best_val_loss: Optional[float] = Field(default=None, description="""The validation loss a later epoch must beat, under this manifest's config: the best epoch's val_loss, or, after a continuation changed the loss, the best weights re-scored under the new loss (spec 004 FR-002). Persisted so a chained job resumes against the same value. Absent before schema 0.8.2 (then the best epoch's recorded val_loss).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'CheckpointMeta']} })
    continued_from: Optional[Continuation] = Field(default=None, description="""Present when the run was seeded from a committed model (absent before schema 0.8.2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    stop_reason: Optional[StopReason] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    complete: bool = Field(default=..., description="""False while training is in progress (checkpoint).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'CheckpointMeta']} })
    wall_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    parameter_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    tfjs_node_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    node_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    cpu_model: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment', 'ModelManifest', 'JobRecord']} })
    tf_intraop_threads: Optional[int] = Field(default=None, description="""TF_NUM_INTRAOP_THREADS in force when training ran (absent: unset, so the TensorFlow default of one per core).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    tf_interop_threads: Optional[int] = Field(default=None, description="""TF_NUM_INTEROP_THREADS in force when training ran (absent: unset).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    weights_digest: str = Field(default=..., description="""SHA-256 of best-epoch weights.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })
    git_commit: Optional[str] = Field(default=None, description="""Commit of the training code, read when training started (absent before schema 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: Optional[bool] = Field(default=None, description="""True when the working tree had uncommitted changes when training started (absent before schema 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    source_dataset_header: Optional[DatasetHeader] = Field(default=None, description="""Header of the dataset the train features came from (lineage; absent before schema 0.8.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    g0_experiment: Optional[str] = Field(default=None, description="""Id of the G0 experiment whose verdict the training guard accepted.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })


class PairedComparison(ConfiguredBaseModel):
    """
    A model and a reference estimator compared on rows both answered (converged and finite), with each estimator's coverage reported separately (spec 003 R9).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    reference: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    slice: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'PairedComparison']} })
    point: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'PairedComparison']} })
    n_common: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    coverage_estimator: float = Field(default=..., description="""Answered / scored.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    coverage_reference: float = Field(default=..., description="""Answered / scored.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    range_rel_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    range_rel_median_ref: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    range_rel_p90: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    range_rel_p90_ref: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    course_deg_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    course_deg_median_ref: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    speed_kt_median: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    speed_kt_median_ref: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })
    gross_error_rate: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MetricsRecord', 'CurvePoint', 'PairedComparison']} })
    gross_error_rate_ref: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PairedComparison']} })


class PhysicsModelConfig(ConfiguredBaseModel):
    """
    One gitma2 model's hyperparameters (spec 003 FR-010): encoder, heads, physics layer, loss, data sampling and optimiser; carried in its manifest.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., description="""Estimator name in predictions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    head: PhysicsHead = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'HeadLiveness']} })
    causal: bool = Field(default=..., description="""Causal encoder and physics layer up to the row (instantaneous); false is the time-late control.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    width: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    layers: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    heads: int = Field(default=..., description="""Attention heads.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    feedforward: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    weight_bound: float = Field(default=..., description="""Bound on per-bearing log-weights.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    scale_bound: float = Field(default=..., description="""Bound on the covariance log-scale.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    iterations: int = Field(default=..., description="""Physics-layer iterations K.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow', 'PhysicsModelConfig', 'DetectorConfig']} })
    train_iterations: Optional[int] = Field(default=None, description="""Iterations of the tape-free solve during training, before the implicit Newton step (schema 0.19.0; absent = iterations). Prediction, validation and the export use iterations.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    head_activation: Optional[HeadActivation] = Field(default=None, description="""Absent = relu (Gate 1's weights); tanh from spec 004.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    min_improvement: Optional[float] = Field(default=None, description="""Relative fall of the validation loss that counts as an improvement (absent = 0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    loss_init_weight: float = Field(default=..., description="""Weight of the auxiliary initial-state loss.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    loss_nll_weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    nll_beta: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    loss_cap: float = Field(default=..., description="""Cap on a row's normalised squared error.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    rows_per_scenario: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig']} })
    noise_draws: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    batch_scenarios: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    learning_rate: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    weight_decay: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    epochs: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'PhysicsModelConfig', 'DetectorConfig']} })
    patience: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    seed: int = Field(default=..., description="""Initialisation and row-sampling seed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    shuffle_labels: bool = Field(default=..., description="""Control (c).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig']} })
    threads: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'JobRecord', 'DetectorConfig']} })


class TrainingPlan(ConfiguredBaseModel):
    """
    A plan branch's content (spec 003): the data, the models and the decision it implements.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    ranges: ParameterRanges = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    train_seed: int = Field(default=..., description="""Generator seed of the on-the-fly training stream.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig',
                       'TrainingPlan',
                       'GateSDecision',
                       'Gate2Decision']} })
    scenarios_per_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    validation: DatasetRef = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    validation_scenarios: int = Field(default=..., description="""Validation scenarios scored each epoch.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    models: Optional[list[PhysicsModelConfig]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    detectors: Optional[list[DetectorConfig]] = Field(default=None, description="""Steady-leg detectors trained by the plan (schema 0.20.0, spec 004).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })
    decision: str = Field(default=..., description="""Path of the decision record it implements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingPlan']} })


class JobRecord(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    started: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['JobRecord']} })
    finished: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['JobRecord']} })
    seconds: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'JobRecord']} })
    first_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['JobRecord']} })
    last_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['JobRecord']} })
    cpu_model: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['RunEnvironment', 'ModelManifest', 'JobRecord']} })
    threads: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'JobRecord', 'DetectorConfig']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: Optional[bool] = Field(default=None, description="""The job's working tree had uncommitted changes (schema 0.20.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })


class CheckpointMeta(ConfiguredBaseModel):
    """
    The state beside a checkpoint's weights (spec 003 FR-015).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    model_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })
    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    epoch: int = Field(default=..., description="""Last completed epoch (0 = none).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'CheckpointMeta']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest']} })
    best_val_loss: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'CheckpointMeta']} })
    val_losses: Optional[list[float]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })
    train_losses: Optional[list[float]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })
    epoch_seconds: Optional[list[float]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })
    complete: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'CheckpointMeta']} })
    jobs: Optional[list[JobRecord]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })
    weights_digest: Optional[str] = Field(default=None, description="""SHA-256 of best.safetensors (schema 0.20.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })
    liveness: Optional[list[HeadLiveness]] = Field(default=None, description="""Per-head liveness after the last epoch.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta']} })


class HeadLiveness(ConfiguredBaseModel):
    """
    Whether a head still responds to its input (spec 004 R1).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    head: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'HeadLiveness']} })
    alive_share: float = Field(default=..., description="""Share of hidden units whose activation varies across rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['HeadLiveness']} })
    output_sd: float = Field(default=..., description="""Standard deviation of the head's output across rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['HeadLiveness']} })


class PhysicsModelManifest(ConfiguredBaseModel):
    """
    The exported artefact's manifest (spec 003 FR-022).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    config: PhysicsModelConfig = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'PhysicsModelManifest']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'ExperimentManifest',
                       'ModelManifest',
                       'PhysicsModelManifest']} })
    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    training_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelManifest']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest']} })
    weights_digest: str = Field(default=..., description="""SHA-256 of the safetensors file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })
    onnx_digest: Optional[str] = Field(default=None, description="""SHA-256 of the exported graph.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelManifest']} })
    window_rows: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelManifest', 'SegmentParameters']} })


class Gate1Decision(ConfiguredBaseModel):
    """
    The Gate 1 decision record (spec 003 FR-016, FR-021), committed before training: what is trained, how the carried weights are chosen, what is scored on test, and what follows.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., description="""SHA-256 of the plan file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    carried_models: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'ChangeDecision']} })
    control_models: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'GateDDecision']} })
    carried_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ChangeDecision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_count: int = Field(default=..., description="""Scenarios generated (the test split is 10%).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    gate_rows: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision']} })
    criterion: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    bootstrap_level: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    bootstrap_resamples: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    imm: str = Field(default=..., description="""Frozen IMM settings (JSON).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    ekf: str = Field(default=..., description="""Frozen EKF settings (JSON).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'Gate2Decision']} })
    forecast: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    if_failed: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision']} })
    validation_rule: str = Field(default=..., description="""When validation stops the phase before test.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'GateDDecision', 'Gate2Decision']} })


class ChangeDecision(ConfiguredBaseModel):
    """
    The single change of the iteration's change round, fixed from validation evidence and committed before phase B trains (spec 003 R5).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    phase_a_experiment: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    stalled: bool = Field(default=..., description="""Any gated criterion failed or was inconclusive on validation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    change: str = Field(default=..., description="""e.g. feature_set: derived""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre', 'ChangeDecision']} })
    rationale: str = Field(default=..., description="""Validation evidence cited.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    carried_set_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    decided_at: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    plan: Optional[str] = Field(default=None, description="""The plan this decision pre-registers (configs/<…>/plan.json). Required from iteration 3 (spec 007): tma-g2 scores a test split only with the decision that names its plan.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    test_seed: Optional[str] = Field(default=None, description="""Dataset seed of the test split the decision commits to (the plan's fresh_test seed, or its dataset seed); tma-g2 checks it against the plan.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ChangeDecision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    rescore_of: Optional[str] = Field(default=None, description="""The experiment directory of the inconclusive gate this decision re-scores (SRD §7: one re-score on a larger fresh-seed test set; e.g. experiments/20261024-i4-g2). When present, tma-g2 runs in re-score mode (--rescore-of): the frozen carried models are bound by model_digests instead of by training ancestry, the re-scored gate must be inconclusive and not itself a re-score, and the fresh test seed must differ from its test seed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    model_digests: Optional[list[ModelDigest]] = Field(default=None, description="""The frozen carried models a re-score scores, by manifest id, with the SHA-256 of each one's weights.bin, manifest.json and model.json; tma-g2 refuses a re-score whose carried set or any of those files differs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    fresh_test_count: Optional[int] = Field(default=None, description="""The dataset count whose test split a re-score scores (the plan's dataset.fresh_test.count; schema 0.11.1); tma-g2 refuses a plan with another count.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    reference_estimator: Optional[str] = Field(default=None, description="""G4 (spec 010, schema 0.13.0): the frozen reference tracker's estimator name, which encodes every tuning parameter (e.g. imm-cv0-ct0.03-w0.003-s0.0001-r4); tma-g4 refuses reference predictions with another name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    carried_model: Optional[str] = Field(default=None, description="""G4: the manifest id of the one carried network (Annex B §B.4); tma-g4 refuses network predictions from another model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    carried_models: Optional[list[str]] = Field(default=None, description="""G5 (spec 012, schema 0.16.0): the manifest ids of the carried trackers (one or both of T1 and T2, Annex C §C.5), each with its own plan in `plans`, in the same order; tma-g5 refuses tracker predictions from any other model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'ChangeDecision']} })
    plans: Optional[list[str]] = Field(default=None, description="""G5: the plan of each carried tracker (configs/phase4/<x>/plan.json), in the order of carried_models; they share one dataset and one fresh test seed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })


class ModelDigest(ConfiguredBaseModel):
    """
    A trained model named by its manifest id and the SHA-256 of its files (schema 0.11.0; manifest and model.json digests from 0.11.1).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    model: str = Field(default=..., description="""The model's manifest id.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbHeader', 'ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    weights_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's weights.bin; equals its manifest weights_digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    manifest_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's manifest.json (schema 0.11.1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })
    model_json_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's model.json, its topology (schema 0.11.1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })


class DetectorConfig(ConfiguredBaseModel):
    """
    A steady-leg detector's configuration (spec 004, SRD Annex A); carried in its manifest.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    variant: DetectorVariant = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'DetectorHeader']} })
    width: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    layers: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    heads: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    feedforward: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    head_activation: HeadActivation = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    now_window_s: float = Field(default=..., description="""A manoeuvre that began within this many seconds counts as now.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    tolerance_s: float = Field(default=..., description="""Half-width of the boundary targets and of matching (D1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'GateDDecision']} })
    held_leg_weight: float = Field(default=..., description="""Weight of held-leg rows in the now loss.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'GateDDecision']} })
    loss_now_weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    loss_boundary_weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    loss_kind_weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    loss_downstream_weight: float = Field(default=..., description="""0 for the classification-only control.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    knots: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'KnotSet', 'EModelConfig', 'Gate2Decision']} })
    iterations: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow', 'PhysicsModelConfig', 'DetectorConfig']} })
    train_iterations: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    downstream_rows: int = Field(default=..., description="""Rows per scenario scored by the downstream loss.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig']} })
    noise_draws: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    batch_scenarios: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    learning_rate: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    weight_decay: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    epochs: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest', 'PhysicsModelConfig', 'DetectorConfig']} })
    patience: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig', 'PhysicsModelConfig', 'DetectorConfig']} })
    min_improvement: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'DetectorConfig']} })
    seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    threads: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelConfig', 'JobRecord', 'DetectorConfig']} })


class ControlSettings(ConfiguredBaseModel):
    """
    A Gate D control's parameters and its tuned threshold (spec 004 R6).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: ControlKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    threshold: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'ControlSettings', 'GateDDecision']} })
    cusum_drift: Optional[float] = Field(default=None, description="""CUSUM drift δ.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings']} })
    glr_window: Optional[int] = Field(default=None, description="""GLR window in samples.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings', 'SegmentParameters']} })
    imm: Optional[str] = Field(default=None, description="""Frozen IMM setting name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    ekf: Optional[str] = Field(default=None, description="""Frozen EKF setting name (cusum_ekf).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'Gate2Decision']} })
    tuned_on: Optional[str] = Field(default=None, description="""SHA-256 of the validation file the threshold was tuned on.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings']} })
    target_false_alarm: Optional[float] = Field(default=None, description="""Held-leg G5 false-alarm fraction the threshold was tuned to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings']} })
    achieved_false_alarm: Optional[float] = Field(default=None, description="""Held-leg G5 false-alarm fraction at the tuned threshold on validation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings']} })


class DetectorHeader(ConfiguredBaseModel):
    """
    First record of a tma2-detect or tma2-controls file (spec 004 contracts/cli.md): which detector, on which truth file, with which weights; knots are exported with the threshold and count named here.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    detector: str = Field(default=..., description="""Detector id or control name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader', 'DetectionRecord']} })
    variant: Optional[DetectorVariant] = Field(default=None, description="""Learned detectors only.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'DetectorHeader']} })
    control: Optional[ControlSettings] = Field(default=None, description="""Controls only.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader']} })
    dataset_digest: str = Field(default=..., description="""SHA-256 of the truth file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    weights_digest: Optional[str] = Field(default=None, description="""SHA-256 of best.safetensors (learned detectors).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'Continuation',
                       'ModelManifest',
                       'CheckpointMeta',
                       'PhysicsModelManifest',
                       'DetectorHeader']} })
    knot_threshold: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader', 'GateDDecision']} })
    max_knots: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader']} })


class KnotEstimate(ConfiguredBaseModel):
    """
    One exported knot (a local maximum of w_change at or above the threshold).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    row: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['KnotEstimate']} })
    weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['KnotEstimate']} })
    p_kind: float = Field(default=..., description="""Probability of a course change (≥ 0.5: course).""", json_schema_extra = { "linkml_meta": {'domain_of': ['KnotEstimate']} })


class KnotSet(ConfiguredBaseModel):
    """
    The knots exported by the question asked at one row.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    query_row: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['KnotSet']} })
    knots: Optional[list[KnotEstimate]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'KnotSet', 'EModelConfig', 'Gate2Decision']} })


class DetectorRecord(ConfiguredBaseModel):
    """
    One scenario's detector outputs (spec 004 FR-013, R8): p_change at every row of the window (a control's alarm statistic mapped to [0, 1] where it has one, else 0/1 alarms), p_kind of the last row's question at every row, and the knot sets asked at the σ = 1° G5 rows and at the last row (learned detectors; empty for controls).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    p_change: list[float] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorRecord']} })
    p_kind_last: Optional[list[float]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorRecord']} })
    knot_sets: Optional[list[KnotSet]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorRecord']} })


class SpanDetection(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    start_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })
    end_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })
    outcome: str = Field(default=..., description="""detected | missed | unresolved.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SpanDetection']} })
    alarm_index: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['SpanDetection']} })
    delay_s: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['SpanDetection']} })
    kind_correct: Optional[bool] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['SpanDetection']} })


class DetectionRecord(ConfiguredBaseModel):
    """
    One scenario's detections by one detector (spec 004 R8).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    detector: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader', 'DetectionRecord']} })
    spans: Optional[list[SpanDetection]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DetectionRecord']} })
    held_leg_seconds: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectionRecord']} })
    held_leg_alarms: int = Field(default=..., description="""Rising edges on held legs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectionRecord']} })
    held_leg_g5_rows: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectionRecord']} })
    held_leg_g5_flagged: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectionRecord']} })


class GateDDecision(ConfiguredBaseModel):
    """
    The Gate D decision record (spec 004 FR-034), committed before training: what is trained, the defaults D1–D4, how controls are tuned, what is scored on test, and what follows.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    carried_variants: list[str] = Field(default=..., description="""Detector ids per carried variant (three seeds each).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision']} })
    control_models: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'GateDDecision']} })
    carried_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    threshold: float = Field(default=..., description="""D1 operating threshold on p_change.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'ControlSettings', 'GateDDecision']} })
    tolerance_s: float = Field(default=..., description="""D1 tolerance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'GateDDecision']} })
    knot_threshold: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorHeader', 'GateDDecision']} })
    bootstrap_level: float = Field(default=..., description="""D2.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    bootstrap_resamples: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    false_alarm_limit_rule: str = Field(default=..., description="""D3.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision']} })
    false_alarm_limit: float = Field(default=..., description="""D3's limit as a number: 0.05, or the frozen IMM's validation rate at μ_CT > 0.5 if lower.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision']} })
    validation_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    test_seed: int = Field(default=..., description="""D4.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ChangeDecision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    held_leg_weight: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'GateDDecision']} })
    controls_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision']} })
    imm: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    ekf: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'Gate2Decision']} })
    criterion: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    validation_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'GateDDecision', 'Gate2Decision']} })
    follow_on: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    forecast: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    architecture_check: str = Field(default=..., description="""FR-035: each registered check reviewed against the detector's architecture.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision']} })


class SegmentInterval(ConfiguredBaseModel):
    """
    One interval of a Segmentation; rows are inclusive sample indices.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: SegmentKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OwnshipWander',
                       'TargetManoeuvre',
                       'ManoeuvreSpan',
                       'ControlSettings',
                       'SpanDetection',
                       'SegmentInterval']} })
    start_index: int = Field(default=..., ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })
    end_index: int = Field(default=..., description="""Inclusive; ≥ start_index.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan', 'SpanDetection', 'SegmentInterval']} })
    open: bool = Field(default=..., description="""True only for the last interval when a transition is still in progress at the prefix end.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentInterval']} })


class SegmentParameters(ConfiguredBaseModel):
    """
    A segmenter's fixed parameters (spec 005 data-model.md; defaults from SRD Annex B and the MAN2 re-plan). Copied into each segmentation file's header.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    course_tol_deg: float = Field(default=..., description="""C: half-width of a steady leg's course band.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    speed_tol_kt: float = Field(default=..., description="""S: half-width of a steady leg's speed band.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    course_change_deg: float = Field(default=..., description="""D: a deliberate course change (ownship coarse pass).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    speed_change_kt: float = Field(default=..., description="""D_S: a deliberate speed change (ownship coarse pass).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    l_min_rows: int = Field(default=..., description="""L_min in rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    t_min_rows: int = Field(default=..., description="""T_min in rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    t_lengths_rows: list[int] = Field(default=..., description="""Transition lengths searched, in rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    search_penalty: float = Field(default=..., description="""Per-leg penalty of the additive search (decision record).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    nominator_far: float = Field(default=..., description="""GLR nominator's held-leg false-alarm fraction.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    retest_rows: int = Field(default=..., description="""Re-test interval of a raised alarm episode.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    tau: float = Field(default=..., description="""Confirmation threshold (χ², 4 dof, before scaling).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    margin: float = Field(default=..., description="""Cost margin below which differing intervals are unknown (FR-023).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters', 'Segmentation']} })
    mode: SegmentMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction', 'PredictionHeader', 'SegmentParameters']} })
    glr_threshold: float = Field(default=..., description="""GLR alarm threshold, tuned on the tuning scenarios' held-leg rows to nominator_far.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    glr_window: int = Field(default=..., description="""GLR window in rows (spec 004).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ControlSettings', 'SegmentParameters']} })
    window_rows: int = Field(default=..., description="""W: a nomination's candidates start in its last W rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicsModelManifest', 'SegmentParameters']} })
    candidate_step_rows: int = Field(default=..., description="""Spacing of candidate transition starts.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    search_every_rows: int = Field(default=..., description="""The search nominates from prefixes this many rows apart on its grid.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    search_step_rows: int = Field(default=..., description="""The search's grid step.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    search_horizon_rows: int = Field(default=..., description="""A search transition is tested on the prefix this many rows after its end.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    polish_rows: int = Field(default=..., description="""Each accepted boundary is re-optimised within ± this many rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })
    open_handover: Optional[OpenHandover] = Field(default=None, description="""How a transition open at k is handed over; absent means knot_at_k (spec 005). Absent fields are left out of the parameter digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters']} })


class SegmentationHeader(ConfiguredBaseModel):
    """
    First record of a tma2-segment file.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    segmenter: str = Field(default=..., description="""C, L-s<seed>, oracle, one-leg or glr-confirm.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentationHeader']} })
    segmenter_sha256: str = Field(default=..., description="""Configuration digest (C) or weights digest (L).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentationHeader']} })
    dataset_digest: str = Field(default=..., description="""SHA-256 of the truth file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    parameters: SegmentParameters = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata', 'SegmentationHeader', 'GateSDecision']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    code_sha256: Optional[str] = Field(default=None, description="""Digest of the segmenter's source files (segment.codeid), so a gate can refuse segmentations made by other code (Gate S panel round 2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })


class Segmentation(ConfiguredBaseModel):
    """
    One vessel's segmentation of the prefix [0, prefix_row] of one scenario (spec 005 FR-001, FR-003). Intervals tile [0, prefix_row] in order without overlap.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    vessel: TrackId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Segmentation', 'TruthLabels']} })
    prefix_row: int = Field(default=..., description="""k: only bearings at rows ≤ k were used.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Segmentation']} })
    intervals: list[SegmentInterval] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Segmentation']} })
    cost: Optional[float] = Field(default=None, description="""Physics-layer cost of the accepted segmentation on [0, k]; null for O.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Segmentation']} })
    margin: Optional[float] = Field(default=None, description="""Smallest cost drop among accepted transitions minus its threshold; null for O.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentParameters', 'Segmentation']} })


class TruthLabels(ConfiguredBaseModel):
    """
    Per-row truth labels for one vessel of one scenario (spec 005 FR-051, R4).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'CrbRecord',
                       'DetectorRecord',
                       'DetectionRecord',
                       'Segmentation',
                       'TruthLabels']} })
    vessel: TrackId = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Segmentation', 'TruthLabels']} })
    labels: list[SegmentKind] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TruthLabels']} })


class GateSDecision(ConfiguredBaseModel):
    """
    The Gate S decision record (spec 005 FR-070, contracts/decision-record.md), committed before any L training.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    validation_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    validation_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision']} })
    test_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ChangeDecision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    train_seed: int = Field(default=..., description="""L's training stream.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig',
                       'TrainingPlan',
                       'GateSDecision',
                       'Gate2Decision']} })
    parameters: SegmentParameters = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata', 'SegmentationHeader', 'GateSDecision']} })
    gap_normalisation: str = Field(default=..., description="""raw (R7).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    s1_limit: float = Field(default=..., description="""O's contamination P90 limit on ownship legs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    s3_contamination_limit: float = Field(default=..., description="""L's contamination may exceed the reference's by at most this.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    s3_false_split_limit: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    s2_validation: str = Field(default=..., description="""C − GLR + confirm on validation and the S4 reference it implies.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    s4_reference: str = Field(default=..., description="""C or glr-confirm.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision']} })
    imm: str = Field(default=..., description="""Frozen MAN2 IMM name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    glr_confirm: str = Field(default=..., description="""GLR + confirm configuration.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision']} })
    bootstrap_level: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    bootstrap_resamples: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    carried_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    shuffled_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision', 'Gate2Record']} })
    criterion: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    follow_on: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    forecast: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })


class GateSVerdicts(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    s1: str = Field(default=..., description="""pass | fail | inconclusive.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateSVerdicts']} })
    s2: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSVerdicts']} })
    s3: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSVerdicts']} })
    s4: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSVerdicts']} })


class GateSRecord(ConfiguredBaseModel):
    """
    The Gate S scoring record (spec 005 data-model.md); metrics live in metrics.json beside it.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    decision_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    split: Split = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'GateSRecord', 'Gate2Record']} })
    seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    dataset_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    segmenters: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord']} })
    metrics_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    verdicts: GateSVerdicts = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    decided_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict', 'GateSRecord', 'Gate2Record']} })


class EModelConfig(ConfiguredBaseModel):
    """
    Gate 2's model E (spec 007 data-model.md): the encoder and heads of E-w and the evidence network of E-s; untrained, E equals C (FR-022).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., description="""Model id in predictions, e.g. e-s1, ew-s2, e-shuffled.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest',
                       'PhysicsModelConfig',
                       'TrainingPlan',
                       'DetectorConfig',
                       'EModelConfig']} })
    seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    components: list[EComponent] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })
    encoder: PhysicsModelConfig = Field(default=..., description="""The Gate 1 encoder's hyperparameters (smooth heads, zero last layers).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })
    extra_channels: list[str] = Field(default=..., description="""Per-row inputs beyond spec 003's features: c_code (C's code at prefix k).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })
    knots: int = Field(default=..., description="""Physics-layer knot cap (12; research R5).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'KnotSet', 'EModelConfig', 'Gate2Decision']} })
    temperature: Optional[float] = Field(default=None, description="""E-s: T of the relaxed acceptance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })
    evidence_network_json: Optional[str] = Field(default=None, description="""E-s: the evidence network's configuration (spec 005's), as JSON.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })
    shuffled: bool = Field(default=..., description="""Trained on another scenario's truth labels (the shuffled-label control).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EModelConfig']} })


class DecisionTableHeader(ConfiguredBaseModel):
    """
    Header of an E-s decision table file (spec 007 research R2): C's confirmation decisions with the downstream errors with and without each.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    dataset_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    parameters_sha256: str = Field(default=..., description="""C's parameter digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DecisionTableHeader', 'EPredictionHeader']} })
    code_sha256: str = Field(default=..., description="""C's code digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    ordinals: list[int] = Field(default=..., description="""[first, last].""", json_schema_extra = { "linkml_meta": {'domain_of': ['DecisionTableHeader']} })
    decisions: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DecisionTableHeader']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })


class EPredictionHeader(ConfiguredBaseModel):
    """
    First record of a tma2-g2predict file (spec 007 contracts/cli.md).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario',
                       'DatasetHeader',
                       'Prediction',
                       'PredictionHeader',
                       'CrbHeader',
                       'CrbRecord',
                       'DetectorHeader',
                       'DetectorRecord',
                       'SegmentationHeader',
                       'Segmentation',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'CrbHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest',
                       'PhysicsModelManifest',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    model: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CrbHeader', 'ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    weights_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    plan_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EPredictionHeader']} })
    dataset_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    parameters_sha256: str = Field(default=..., description="""C's parameter digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DecisionTableHeader', 'EPredictionHeader']} })
    code_sha256: str = Field(default=..., description="""The code that made the prediction (C's and E's).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'JobRecord',
                       'ChangeDecision',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    git_dirty: bool = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'ModelManifest',
                       'JobRecord',
                       'SegmentationHeader',
                       'DecisionTableHeader',
                       'EPredictionHeader']} })
    model_settings: Optional[str] = Field(default=None, description="""The plan entry of the model that made the file, as canonical JSON (veto window, fade, kind, seed); binds a classical control's settings (spec 008, Gate 2 panel R2-7).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EPredictionHeader']} })
    segmentation_sha256: Optional[str] = Field(default=None, description="""SHA-256 of the C segmentation file read, when one was read (spec 008, panel G12).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EPredictionHeader']} })


class Gate2Decision(ConfiguredBaseModel):
    """
    The Gate 2 decision record (spec 007 FR-050, contracts/decision-record.md), committed before any E training.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    plan_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    plan_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CheckpointMeta',
                       'PhysicsModelManifest',
                       'Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    validation_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    validation_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision']} })
    train_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig',
                       'TrainingPlan',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ChangeDecision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    test_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    c_parameters: SegmentParameters = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    c_parameters_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    c_code_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    knots: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DetectorConfig', 'KnotSet', 'EModelConfig', 'Gate2Decision']} })
    imm: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    ekf: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'ControlSettings',
                       'GateDDecision',
                       'Gate2Decision']} })
    glr_confirm: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision']} })
    g2a_limit: float = Field(default=..., description="""E / IMM, median range and course, wholly below.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    g2b_limit: float = Field(default=..., description="""Settled rows, E / one leg, wholly below.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    g2c_limit: float = Field(default=..., description="""E's gap recovered, wholly above.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    bootstrap_level: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    bootstrap_resamples: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    carried_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    shuffled_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision', 'Gate2Record']} })
    validation_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision', 'GateDDecision', 'Gate2Decision']} })
    rescore: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Decision']} })
    criterion: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })
    follow_on: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateDDecision', 'GateSDecision', 'Gate2Decision']} })
    forecast: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate1Decision',
                       'GateDDecision',
                       'GateSDecision',
                       'Gate2Decision']} })


class Gate2Verdicts(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    g2a: str = Field(default=..., description="""pass | fail | inconclusive.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Verdicts']} })
    g2b: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Verdicts']} })
    g2c: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Verdicts']} })
    g2d: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Verdicts']} })
    overall: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Gate2Verdicts']} })


class Gate2Record(ConfiguredBaseModel):
    """
    The Gate 2 scoring record (spec 007 data-model.md); metrics live in metrics.json beside it.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    decision_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    split: Split = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'GateSRecord', 'Gate2Record']} })
    seed: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata',
                       'PhysicsModelConfig',
                       'DetectorConfig',
                       'GateSRecord',
                       'EModelConfig',
                       'Gate2Record']} })
    dataset_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader',
                       'CrbHeader',
                       'DetectorHeader',
                       'SegmentationHeader',
                       'GateSRecord',
                       'DecisionTableHeader',
                       'EPredictionHeader',
                       'Gate2Record']} })
    model: str = Field(default=..., description="""The carried E.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CrbHeader', 'ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    weights_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest', 'EPredictionHeader', 'Gate2Record']} })
    metrics_sha256: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    shuffled_rule: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSDecision', 'Gate2Decision', 'Gate2Record']} })
    verdicts: Gate2Verdicts = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateSRecord', 'Gate2Record']} })
    decided_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict', 'GateSRecord', 'Gate2Record']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
FloatRange.model_rebuild()
LegLengthModel.model_rebuild()
ChangeKindWeights.model_rebuild()
HelmWanderRanges.model_rebuild()
OscillationRanges.model_rebuild()
WanderWeights.model_rebuild()
OwnshipWander.model_rebuild()
ScenarioParameters.model_rebuild()
TargetManoeuvre.model_rebuild()
ParameterRanges.model_rebuild()
PlatformState.model_rebuild()
Track.model_rebuild()
Observation.model_rebuild()
ScenarioMetadata.model_rebuild()
ManoeuvreSpan.model_rebuild()
Scenario.model_rebuild()
DatasetHeader.model_rebuild()
NormalisationConstants.model_rebuild()
FeatureLayout.model_rebuild()
PredictionRow.model_rebuild()
Prediction.model_rebuild()
PredictionHeader.model_rebuild()
CrbHeader.model_rebuild()
CrbRecord.model_rebuild()
MetricsRecord.model_rebuild()
DatasetRef.model_rebuild()
ArtefactRef.model_rebuild()
PackageVersion.model_rebuild()
RunEnvironment.model_rebuild()
EstimatorRef.model_rebuild()
ExperimentManifest.model_rebuild()
GateCheck.model_rebuild()
GateVerdict.model_rebuild()
NaiveMeans.model_rebuild()
NaiveModel.model_rebuild()
CurvePoint.model_rebuild()
TrainingConfig.model_rebuild()
EpochRecord.model_rebuild()
Continuation.model_rebuild()
ModelManifest.model_rebuild()
PairedComparison.model_rebuild()
PhysicsModelConfig.model_rebuild()
TrainingPlan.model_rebuild()
JobRecord.model_rebuild()
CheckpointMeta.model_rebuild()
HeadLiveness.model_rebuild()
PhysicsModelManifest.model_rebuild()
Gate1Decision.model_rebuild()
ChangeDecision.model_rebuild()
ModelDigest.model_rebuild()
DetectorConfig.model_rebuild()
ControlSettings.model_rebuild()
DetectorHeader.model_rebuild()
KnotEstimate.model_rebuild()
KnotSet.model_rebuild()
DetectorRecord.model_rebuild()
SpanDetection.model_rebuild()
DetectionRecord.model_rebuild()
GateDDecision.model_rebuild()
SegmentInterval.model_rebuild()
SegmentParameters.model_rebuild()
SegmentationHeader.model_rebuild()
Segmentation.model_rebuild()
TruthLabels.model_rebuild()
GateSDecision.model_rebuild()
GateSVerdicts.model_rebuild()
GateSRecord.model_rebuild()
EModelConfig.model_rebuild()
DecisionTableHeader.model_rebuild()
EPredictionHeader.model_rebuild()
Gate2Decision.model_rebuild()
Gate2Verdicts.model_rebuild()
Gate2Record.model_rebuild()
