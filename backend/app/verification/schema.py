"""Evidence in, verdict out (docs/VERIFICATION_SPEC.md §4 and §8).

Evidence is a trust boundary: NaN/inf, duplicate observations and malformed tokens are
rejected at load, so no check ever sees them.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Clip = Literal["test", "closeup"]
Fault = Literal["F1", "unknown"]
Result = Literal["pass", "fail", "insufficient_evidence"]
Supply = Literal["battery_9v", "usb_5v"]
VerdictId = Literal["PASSED", "FAILED", "INCONCLUSIVE"]
CheckId = Literal["C0_preconditions", "C1_running", "C2_flow", "C3_no_leak", "C4_cause_addressed"]

SUPPORTED_EQUIPMENT = "mini_pump_3_6v"
Token = Annotated[str, Field(pattern=r"^[A-Za-z0-9]{4}$")]


class Strict(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class Observation(Strict):
    """One Muse Spark observation (spec §4.1); `t` in seconds on `clip`'s timeline."""

    id: str
    clip: Clip
    value: bool | float | str | None
    confidence: float = Field(ge=0, le=1)
    t: list[float] = []


class Timeline(Strict):
    """SAM presence timeline (spec §4.2): sampled times (s) with a mask, sampling from t = 0."""

    times: list[float]
    interval_s: float = Field(gt=0)


class Conditions(Strict):
    supply: Supply | None = None
    head_cm: float | None = None
    water_level_cm: float | None = None
    notes: str = ""


class JobEvidence(Strict):
    job_id: str
    job_token: Token
    equipment: str
    fault_hypothesis: Fault
    test_clip_duration_s: float = Field(gt=0)
    observations: list[Observation] = []
    # clip -> concept -> timeline; a missing key or None means the SAM request errored
    timelines: dict[Clip, dict[str, Timeline | None]] = {}
    fill_time_s: float | None = None
    conditions: Conditions = Conditions()
    models: dict[str, str] = {"reasoning": "muse-spark-1.3", "segmentation": "sam-3.1"}

    @model_validator(mode="after")
    def _unique_observations(self):
        keys = [(o.id, o.clip) for o in self.observations]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        if dupes:
            # a second, contradicting reading could otherwise hide an observed failure
            raise ValueError(f"duplicate observations: {dupes}")
        return self

    def observation(self, id: str, clip: Clip, min_confidence: float) -> Observation | None:
        """The observation, or None if absent or below the confidence threshold."""
        for o in self.observations:
            if o.id == id and o.clip == clip:
                return o if o.confidence >= min_confidence else None
        return None

    def timeline(self, clip: Clip, concept: str) -> Timeline | None:
        return self.timelines.get(clip, {}).get(concept)


class Thresholds(Strict):
    """Flow is judged as speed relative to the healthy rig: baseline fill time / video fill time."""

    version: str
    baseline_fill_s: float = Field(gt=0)
    speed_pass: float = Field(0.8, gt=0, le=1)
    speed_fail: float = Field(0.6, gt=0, le=1)
    # §6 fixes 0.15; bounds stop a typo from switching the cross-check off
    fill_time_tolerance: float = Field(0.15, gt=0, le=0.3)
    # swept on the dev split only (§6)
    confidence_threshold: float = Field(0.7, ge=0.5, le=1)

    @field_validator(
        "baseline_fill_s",
        "speed_pass",
        "speed_fail",
        "fill_time_tolerance",
        "confidence_threshold",
        mode="before",
    )
    @classmethod
    def _no_bool(cls, v):
        if isinstance(v, bool):
            raise ValueError("must be a number")
        return v

    @model_validator(mode="after")
    def _ordered(self):
        if self.speed_fail >= self.speed_pass:
            raise ValueError("speed_fail must be below speed_pass")
        return self


class CheckResult(BaseModel):
    id: CheckId
    result: Result
    evidence: list[str] = []
    detail: str


class Verdict(BaseModel):
    job_id: str
    fault_hypothesis: Fault
    verdict: VerdictId
    reasons: list[str] = []
    checks: list[CheckResult] = []
    conditions: Conditions
    run_s: float | None = None
    uncertainties: list[str] = []
    requested_actions: list[str] = []
    thresholds_version: str | None = None
    models: dict[str, str]
