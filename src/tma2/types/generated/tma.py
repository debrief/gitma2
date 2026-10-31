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
version = "0.16.0"


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
    G0 = "G0"
    """
    Pipeline verified.
    """
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    """
    Better than the tuned tracker after a target turn (SRD Annex B §B.4).
    """
    G5 = "G5"
    """
    An end-to-end tracker better than the re-tuned reference overall, at most 10% worse when settled (SRD Annex C §C.5).
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



class FloatRange(ConfiguredBaseModel):
    """
    Closed interval [min, max].
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    min: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FloatRange']} })
    max: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FloatRange']} })


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

    kind: ManoeuvreKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre', 'ManoeuvreSpan']} })
    start_time_s: float = Field(default=..., description="""Time the manoeuvre starts, a whole number of samples.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre'], 'unit': {'ucum_code': 's'}} })
    change: float = Field(default=..., description="""Signed change: course in rad (positive clockwise) or speed in m/s (positive faster).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre', 'ChangeDecision']} })
    rate: float = Field(default=..., description="""Magnitude of the rate of change, rad/s (course) or m/s² (speed).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre']} })


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
                       'ModelManifest']} })
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

    seed: str = Field(default=..., description="""Scenario seed as a decimal uint64 string.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    index: int = Field(default=..., description="""Scenario index within the dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    parameters: ScenarioParameters = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    samples: int = Field(default=..., description="""Number of timesteps (60–240).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig_index: int = Field(default=..., description="""First timestep on leg 2 (with a rate-limited turn, the first after it completes).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    turn_start_index: Optional[int] = Field(default=None, description="""First timestep after the turn starts (absent for an instantaneous zig).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig2_index: Optional[int] = Field(default=None, description="""First timestep on leg 3, after the second turn completes (absent with one zig). Gate times still count from zig_index.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    turn2_start_index: Optional[int] = Field(default=None, description="""First timestep after the second turn starts (absent with one zig or no turn rate).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvre_start_index: Optional[int] = Field(default=None, description="""First timestep after the target's turn starts (generator 0.4.0; absent when the target holds course). Under generator 0.5.0, after the first manoeuvre starts.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvre_index: Optional[int] = Field(default=None, description="""First timestep after the target's turn completes (generator 0.4.0; absent when the target holds course). Gate G4 counts time from here, as earlier gates count from zig_index. Under generator 0.5.0, after the last manoeuvre completes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    manoeuvres: Optional[list[ManoeuvreSpan]] = Field(default=None, description="""Generator 0.5.0: each target manoeuvre's sample span, in time order (present, possibly empty, only under 0.5.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata']} })
    zig_time_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata'], 'unit': {'ucum_code': 's'}} })
    mean_range_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ScenarioMetadata'], 'unit': {'ucum_code': 'm'}} })
    min_range_m: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ParameterRanges', 'ScenarioMetadata'],
         'unit': {'ucum_code': 'm'}} })


class ManoeuvreSpan(ConfiguredBaseModel):
    """
    Where one target manoeuvre lies in a scenario's samples (generator 0.5.0).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    kind: ManoeuvreKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TargetManoeuvre', 'ManoeuvreSpan']} })
    start_index: int = Field(default=..., description="""First timestep after it starts.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan']} })
    end_index: int = Field(default=..., description="""First timestep after it completes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ManoeuvreSpan']} })


class Scenario(ConfiguredBaseModel):
    """
    One ownship-vs-target run over a window.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma',
         'tree_root': True})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario', 'DatasetHeader', 'Prediction', 'PredictionHeader']} })
    metadata: ScenarioMetadata = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    ownship: Track = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    target: Track = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })
    observations: list[Observation] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario']} })


class DatasetHeader(ConfiguredBaseModel):
    """
    First record of every dataset file.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario', 'DatasetHeader', 'Prediction', 'PredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'ExperimentManifest', 'ModelManifest']} })
    dataset_seed: str = Field(default=..., description="""Decimal uint64 string.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
    split: Split = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader']} })
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
    iterations: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    p_manoeuvre: Optional[float] = Field(default=None, description="""The estimator's probability that the target's turn has started by this timestep (velocity_two_hypothesis networks only; spec 011). Absent for other estimators.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    log_range_sd: Optional[float] = Field(default=None, description="""Standard deviation of the estimator's log range (natural log; about the relative range error), from a velocity_gaussian network (spec 012). Absent for other estimators.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow']} })
    vx_sd_mps: Optional[float] = Field(default=None, description="""Standard deviation of the estimated east velocity (velocity_gaussian only).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm/s'}} })
    vy_sd_mps: Optional[float] = Field(default=None, description="""Standard deviation of the estimated north velocity (velocity_gaussian only).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionRow'], 'unit': {'ucum_code': 'm/s'}} })


class Prediction(ConfiguredBaseModel):
    """
    One estimator's output for one scenario.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario', 'DatasetHeader', 'Prediction', 'PredictionHeader']} })
    scenario_index: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction']} })
    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    mode: PredictionMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction', 'PredictionHeader']} })
    rows: list[PredictionRow] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'Prediction']} })


class PredictionHeader(ConfiguredBaseModel):
    """
    First record of every prediction file.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    record: RecordKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Scenario', 'DatasetHeader', 'Prediction', 'PredictionHeader']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest']} })
    estimator: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction',
                       'PredictionHeader',
                       'MetricsRecord',
                       'CurvePoint',
                       'PairedComparison']} })
    mode: PredictionMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Prediction', 'PredictionHeader']} })
    dataset_digest: str = Field(default=..., description="""SHA-256 of the truth file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['PredictionHeader']} })


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


class DatasetRef(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    path: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef']} })
    header: DatasetHeader = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef']} })
    digest: Optional[str] = Field(default=None, description="""SHA-256 of the dataset file (absent in manifests written before schema 0.4.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetRef']} })


class EstimatorRef(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EstimatorRef', 'GateCheck']} })
    settings_json: str = Field(default=..., description="""Estimator settings as JSON.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EstimatorRef']} })


class ExperimentManifest(ConfiguredBaseModel):
    """
    Everything needed to reproduce an experiment run.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest']} })
    created: str = Field(default=..., description="""ISO 8601 timestamp.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    git_commit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'ChangeDecision']} })
    git_dirty: Optional[bool] = Field(default=None, description="""True when the working tree had uncommitted changes (absent before schema 0.4.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    node_version: Optional[str] = Field(default=None, description="""Node.js version that ran the experiment (byte identity is promised per pinned Node).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'ExperimentManifest', 'ModelManifest']} })
    datasets: list[DatasetRef] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    estimators: list[EstimatorRef] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })
    normalisation: Optional[NormalisationConstants] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    command_lines: list[str] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest']} })


class GateCheck(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    name: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EstimatorRef', 'GateCheck']} })
    result: GateResult = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck', 'GateVerdict']} })
    detail: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    value: Optional[float] = Field(default=None, description="""Statistic tested (e.g. median range error).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
    threshold: Optional[float] = Field(default=None, description="""Limit the statistic is tested against.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GateCheck']} })
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
    decided_by: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GateVerdict']} })


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
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest']} })
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


class TrainingConfig(ConfiguredBaseModel):
    """
    Hyperparameters and seeds for one training run (SRD §4; constitution III).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., description="""Estimator name used in predictions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest']} })
    model_kind: ModelKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    units: int = Field(default=..., description="""LSTM units (per direction), conv filters or dense width.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    kernel_size: Optional[int] = Field(default=None, description="""Causal CNN kernel size.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    layers: Optional[int] = Field(default=None, description="""Stacked layers: causal CNN conv layers (no dilation; default 3), or recurrent layers for instantaneous and time_late (default 1; each returns sequences; spec 003 R20).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    learning_rate: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    batch_size: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    max_epochs: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    patience: int = Field(default=..., description="""Epochs without validation improvement before stopping.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    max_wall_s: float = Field(default=..., description="""Wall-clock cap in seconds.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_range: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_course: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_speed: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    loss_weight_manoeuvre: Optional[float] = Field(default=None, description="""Weight of the turn-probability cross-entropy term (velocity_two_hypothesis only; spec 011). Absent means 1.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    train_seed: str = Field(default=..., description="""Decimal uint64; derives initializer seeds and batch order.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    train_limit: Optional[int] = Field(default=None, description="""Use only the first N training scenarios (tests and smoke runs).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    shuffle_labels: bool = Field(default=..., description="""Permute targets across scenarios (leakage check).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    feature_set: Optional[FeatureSet] = Field(default=None, description="""Input channel set; absent means raw. Must match the features files.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FeatureLayout', 'TrainingConfig']} })
    output_parameterisation: Optional[OutputParameterisation] = Field(default=None, description="""Output encoding; absent means course_speed. With velocity, loss_weight_speed weights each velocity component and loss_weight_course is unused (spec 008).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    velocity_scale_mps: Optional[float] = Field(default=None, description="""Velocity scale in m/s for the velocity parameterisation (required with it): the top of the generator's target speed range, a constant of the problem, never a truth statistic.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    length_bucketing: Optional[bool] = Field(default=None, description="""Length bucketing (research R15; default false). Each group of bucket_batches batches of the epoch's seeded permutation is sorted by valid length, cut into batches whose rows are trimmed to the longest window, and the batch order is shuffled with a seed derived from train_seed and the epoch. The model takes a variable time dimension. Not for mlp.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    bucket_batches: Optional[int] = Field(default=None, description="""Batches per length-bucketing group (default 16).""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })
    tfjs_threads: Optional[int] = Field(default=None, description="""TensorFlow intra-op and inter-op thread count, set by tma-train through TF_NUM_INTRAOP_THREADS and TF_NUM_INTEROP_THREADS before tfjs-node loads. Absent: the TensorFlow default (one per core) or whatever the environment sets.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['TrainingConfig']} })


class EpochRecord(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord']} })
    train_loss: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord']} })
    val_loss: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'Continuation']} })
    seconds: float = Field(default=..., description="""Cumulative wall time.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord']} })


class Continuation(ConfiguredBaseModel):
    """
    The committed model a seeded continuation started from (scripts/train-continue.mjs; spec 003 decision 14, spec 004 decision 15). Its epoch records up to best_epoch are kept in the continued run's manifest, with their val_loss as recorded under the earlier config.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    weights_digest: str = Field(default=..., description="""SHA-256 of the weights the continuation resumed from (the source's best epoch).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation', 'ModelManifest']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation', 'ModelManifest']} })
    val_loss: float = Field(default=..., description="""The source's best-epoch validation loss under the source's config.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EpochRecord', 'Continuation']} })
    rescored_val_loss: Optional[float] = Field(default=None, description="""The source's best weights re-scored under the continued run's loss, written by tma-train when it resumed (spec 004 FR-002). With best_epoch and best_val_loss it makes the kept weights auditable: a run whose best_epoch is the source's must have best_val_loss equal to this value and weights_digest equal to the source's.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation']} })
    git_commit: Optional[str] = Field(default=None, description="""The source model's training-code commit, when it recorded one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'ChangeDecision']} })


class ModelManifest(ConfiguredBaseModel):
    """
    Everything needed to reproduce and identify a trained model.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Track',
                       'ExperimentManifest',
                       'TrainingConfig',
                       'ModelManifest']} })
    config: TrainingConfig = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    schema_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader',
                       'PredictionHeader',
                       'ExperimentManifest',
                       'NaiveModel',
                       'ModelManifest']} })
    generator_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['DatasetHeader', 'ExperimentManifest', 'ModelManifest']} })
    train_features_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    val_features_digest: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    normalisation: NormalisationConstants = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    epochs: list[EpochRecord] = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    best_epoch: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation', 'ModelManifest']} })
    best_val_loss: Optional[float] = Field(default=None, description="""The validation loss a later epoch must beat, under this manifest's config: the best epoch's val_loss, or, after a continuation changed the loss, the best weights re-scored under the new loss (spec 004 FR-002). Persisted so a chained job resumes against the same value. Absent before schema 0.8.2 (then the best epoch's recorded val_loss).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    continued_from: Optional[Continuation] = Field(default=None, description="""Present when the run was seeded from a committed model (absent before schema 0.8.2).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    stop_reason: Optional[StopReason] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    complete: bool = Field(default=..., description="""False while training is in progress (checkpoint).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    wall_s: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    parameter_count: int = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    tfjs_node_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    node_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
    cpu_model: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    tf_intraop_threads: Optional[int] = Field(default=None, description="""TF_NUM_INTRAOP_THREADS in force when training ran (absent: unset, so the TensorFlow default of one per core).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    tf_interop_threads: Optional[int] = Field(default=None, description="""TF_NUM_INTEROP_THREADS in force when training ran (absent: unset).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelManifest']} })
    weights_digest: str = Field(default=..., description="""SHA-256 of best-epoch weights.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Continuation', 'ModelManifest']} })
    git_commit: Optional[str] = Field(default=None, description="""Commit of the training code, read when training started (absent before schema 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest',
                       'Continuation',
                       'ModelManifest',
                       'ChangeDecision']} })
    git_dirty: Optional[bool] = Field(default=None, description="""True when the working tree had uncommitted changes when training started (absent before schema 0.6.0).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExperimentManifest', 'ModelManifest']} })
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
                       'ChangeDecision']} })
    plan: Optional[str] = Field(default=None, description="""The plan this decision pre-registers (configs/<…>/plan.json). Required from iteration 3 (spec 007): tma-g2 scores a test split only with the decision that names its plan.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    test_seed: Optional[str] = Field(default=None, description="""Dataset seed of the test split the decision commits to (the plan's fresh_test seed, or its dataset seed); tma-g2 checks it against the plan.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    rescore_of: Optional[str] = Field(default=None, description="""The experiment directory of the inconclusive gate this decision re-scores (SRD §7: one re-score on a larger fresh-seed test set; e.g. experiments/20261024-i4-g2). When present, tma-g2 runs in re-score mode (--rescore-of): the frozen carried models are bound by model_digests instead of by training ancestry, the re-scored gate must be inconclusive and not itself a re-score, and the fresh test seed must differ from its test seed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    model_digests: Optional[list[ModelDigest]] = Field(default=None, description="""The frozen carried models a re-score scores, by manifest id, with the SHA-256 of each one's weights.bin, manifest.json and model.json; tma-g2 refuses a re-score whose carried set or any of those files differs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    fresh_test_count: Optional[int] = Field(default=None, description="""The dataset count whose test split a re-score scores (the plan's dataset.fresh_test.count; schema 0.11.1); tma-g2 refuses a plan with another count.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    reference_estimator: Optional[str] = Field(default=None, description="""G4 (spec 010, schema 0.13.0): the frozen reference tracker's estimator name, which encodes every tuning parameter (e.g. imm-cv0-ct0.03-w0.003-s0.0001-r4); tma-g4 refuses reference predictions with another name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    carried_model: Optional[str] = Field(default=None, description="""G4: the manifest id of the one carried network (Annex B §B.4); tma-g4 refuses network predictions from another model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    carried_models: Optional[list[str]] = Field(default=None, description="""G5 (spec 012, schema 0.16.0): the manifest ids of the carried trackers (one or both of T1 and T2, Annex C §C.5), each with its own plan in `plans`, in the same order; tma-g5 refuses tracker predictions from any other model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })
    plans: Optional[list[str]] = Field(default=None, description="""G5: the plan of each carried tracker (configs/phase4/<x>/plan.json), in the order of carried_models; they share one dataset and one fresh test seed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ChangeDecision']} })


class ModelDigest(ConfiguredBaseModel):
    """
    A trained model named by its manifest id and the SHA-256 of its files (schema 0.11.0; manifest and model.json digests from 0.11.1).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://github.com/debrief/gitma/schema/tma'})

    model: str = Field(default=..., description="""The model's manifest id.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })
    weights_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's weights.bin; equals its manifest weights_digest.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })
    manifest_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's manifest.json (schema 0.11.1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })
    model_json_sha256: str = Field(default=..., description="""SHA-256 (hex) of the model's model.json, its topology (schema 0.11.1).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ModelDigest']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
FloatRange.model_rebuild()
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
MetricsRecord.model_rebuild()
DatasetRef.model_rebuild()
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
ChangeDecision.model_rebuild()
ModelDigest.model_rebuild()
