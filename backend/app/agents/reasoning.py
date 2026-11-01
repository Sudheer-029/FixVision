"""Muse Spark tasks: triage, guidance, observe_test (docs/components/reasoning-agent.md).

Models observe; they never output a verdict (ADR-0001). Every call uses a JSON schema; an
answer that fails it gets one repair retry, then the step errors.
"""

import base64
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError, create_model

from app.clients.meta_client import MetaClient
from app.config import REPO_ROOT, Settings
from app.verification.schema import Clip, Observation

PROMPTS = Path(__file__).parent / "prompts"
GUIDE = REPO_ROOT / "data" / "guides" / "pump_guide.md"


class AgentError(RuntimeError):
    """The model answer did not match the schema after one repair retry."""


def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()


def prompt_id(text: str) -> str:
    return text.split("id:", 1)[1].split("-->", 1)[0].strip()


def model_for(cfg: Settings, data_class: str = "real", eval_mode: bool = False) -> str:
    """Contributor (cheap, may train Meta models) only for staged rig data in eval mode."""
    return cfg.reasoning_model_eval if eval_mode and data_class == "staged" else cfg.reasoning_model


def _structured(
    client: MetaClient,
    model: str,
    content: list[dict[str, Any]],
    schema: dict[str, Any],
    out: type[BaseModel],
    name: str,
    job_id: str | None,
    check: Callable[[Any], str | None] = lambda _: None,
) -> Any:
    messages: list[dict[str, Any]] = [{"type": "message", "role": "user", "content": content}]
    text = ""
    for attempt in range(2):
        r = client.respond(
            model, messages, schema, schema_name=name, job_id=job_id, component=name,
            use_cache=attempt == 0,
        )  # fmt: skip
        text = r.text
        try:
            parsed = out.model_validate_json(text)
            problem = check(parsed)
            if problem is None:
                return parsed
            repair = f"Your answer was invalid: {problem}. Answer again."
        except ValidationError as e:
            repair = f"Your answer did not match the JSON schema: {e.errors()[:3]}. Answer again."
        messages += [
            {"type": "message", "role": "assistant", "content": text},
            {"type": "message", "role": "user", "content": repair},
        ]
    raise AgentError(f"{name}: schema-invalid answer after one repair: {text[:200]}")


# -- observe_test -----------------------------------------------------------------

# spec §4.1, per clip: id → (JSON type of value, what to look for). fill_start_t and
# fill_line_t come from observe_fill on time-labelled jar frames: Muse Spark could not time
# the fill line from the video itself (it returned null at 720p and 1080p)
TEST_OBS: dict[str, tuple[str, str]] = {
    "job_token_read": ("string", "the handwritten code on the sticky note"),
    "timer_visible": ("boolean", "a running stopwatch or timer is visible"),
    "pump_submerged": (
        "boolean",
        "in the first seconds, the white pump is visible through the glass bowl and fully under "
        "water; null if something covers it",
    ),
    "switch_on_shown": ("boolean", "a hand switches the pump on in view; t = that moment"),
    "switch_off_shown": ("boolean", "a hand switches the pump off in view; t = that moment"),
    "pump_running": ("boolean", "the pump is running at some point in the video"),
    "water_flowing": (
        "boolean",
        "water flows from the hose end into the jar; t = first moment it is seen; "
        "false if the pump is switched on but no water comes out",
    ),
    "leak_at_hose": ("boolean", "water leaks or drips from the hose itself; t = moments seen"),
}
CLOSEUP_OBS: dict[str, tuple[str, str]] = {
    "job_token_read": ("string", "the handwritten code on the sticky note"),
    "intake_clear": (
        "boolean",
        "the pump's intake opening is shown close up and nothing covers or blocks it",
    ),
}


class _Slot(BaseModel):
    value: bool | float | str | None
    confidence: float
    t: list[float]


def _schema(obs: dict[str, tuple[str, str]]) -> dict[str, Any]:
    def slot(kind: str) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "value": {"type": [kind, "null"]},
                "confidence": {"type": "number"},
                "t": {"type": "array", "items": {"type": "number"}},
            },
            "required": ["value", "confidence", "t"],
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": {k: slot(kind) for k, (kind, _) in obs.items()},
        "required": list(obs),
        "additionalProperties": False,
    }


def observe_test(
    client: MetaClient,
    model: str,
    clip_path: str | Path,
    clip: Clip,
    job_id: str | None = None,
) -> list[Observation]:
    """Observations for one clip (spec §4.1). The job token is never sent to the model."""
    obs = TEST_OBS if clip == "test" else CLOSEUP_OBS
    listing = "Report these observations:\n" + "\n".join(
        f"- `{k}` ({kind}): {what}" for k, (kind, what) in obs.items()
    )
    if clip == "closeup":
        listing += "\nThis is a close-up recorded after the repair, not the full test."
    text = prompt("observe_test").replace("{observations}", listing)
    content = [
        {"type": "input_text", "text": text},
        {"type": "input_video", "file_id": client.upload_file(clip_path)},
    ]
    out_model = create_model(f"Obs_{clip}", **{k: (_Slot, ...) for k in obs})
    parsed = _structured(client, model, content, _schema(obs), out_model, f"observe_{clip}", job_id)
    observations = []
    for k in obs:
        s: _Slot = getattr(parsed, k)
        # clamp: model confidence is uncalibrated and may stray outside 0..1
        conf = min(max(s.confidence, 0.0), 1.0)
        observations.append(Observation(id=k, clip=clip, value=s.value, confidence=conf, t=s.t))
    return observations


# -- observe_fill ----------------------------------------------------------------------

FillLabel = Literal["not_filling", "below_line", "at_line"]
FILL_ORDER: dict[str, int] = {"not_filling": 0, "below_line": 1, "at_line": 2}
FILL_CONFIDENCE = 0.9  # labels that never step back; shortcut: fixed, revisit with dev-split evals
FILL_JUMBLED = 0.5  # below the 0.7 threshold, so C2 is insufficient_evidence


class _Fill(BaseModel):
    frames: list[FillLabel]


def fill_times(labels: list[str], fps: float) -> list[Observation]:
    """fill_start_t / fill_line_t from per-frame labels (frame i at i / fps s).

    Labels that step back (e.g. at_line then below_line) get low confidence, so a muddled
    reading becomes missing evidence instead of a fill time.
    """
    ranks = [FILL_ORDER[x] for x in labels]
    steady = all(a <= b for a, b in zip(ranks, ranks[1:], strict=False))
    conf = FILL_CONFIDENCE if steady else FILL_JUMBLED

    def first(rank: int) -> Observation:
        i = next((k for k, r in enumerate(ranks) if r >= rank), None)
        t = None if i is None else round(i / fps, 1)
        name = "fill_start_t" if rank == 1 else "fill_line_t"
        return Observation(
            id=name, clip="test", value=t, confidence=conf, t=[] if t is None else [t]
        )

    return [first(1), first(2)]


def observe_fill(
    client: MetaClient,
    model: str,
    frame_paths: list[Path],
    fps: float = 1.0,
    job_id: str | None = None,
) -> list[Observation]:
    """Muse Spark labels each jar frame; the times come from the frame labels, not the model."""
    n = len(frame_paths)
    content: list[dict[str, Any]] = [
        {"type": "input_text", "text": prompt("observe_fill").replace("{n}", str(n))}
    ]
    for i, path in enumerate(frame_paths):
        data = base64.b64encode(path.read_bytes()).decode()
        content += [
            {"type": "input_text", "text": f"frame {i}"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{data}"},
        ]
    schema = {
        "type": "object",
        "properties": {
            "frames": {"type": "array", "items": {"type": "string", "enum": list(FILL_ORDER)}}
        },
        "required": ["frames"],
        "additionalProperties": False,
    }

    def one_per_frame(parsed: _Fill) -> str | None:
        got = len(parsed.frames)
        return None if got == n else f"expected {n} labels, got {got}"

    parsed = _structured(
        client, model, content, schema, _Fill, "observe_fill", job_id, check=one_per_frame
    )
    return fill_times(parsed.frames, fps)


# -- triage and guidance --------------------------------------------------------------

FAULTS = ("F1", "unknown")


class Cause(BaseModel):
    fault_id: str
    likelihood: float
    evidence: list[str]


class RequestedCheck(BaseModel):
    instruction: str
    component_concept: str


class Triage(BaseModel):
    causes: list[Cause]
    requested_check: RequestedCheck


class Step(BaseModel):
    text: str
    component_concept: str
    requires_approval: bool


class Guidance(BaseModel):
    stop_conditions: list[str]
    steps: list[Step]
    cited_sections: list[str]


def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


_STR = {"type": "string"}
_STRS = {"type": "array", "items": _STR}
TRIAGE_SCHEMA = _obj(
    {
        "causes": {
            "type": "array",
            "items": _obj(
                {
                    "fault_id": {"type": "string", "enum": list(FAULTS)},
                    "likelihood": {"type": "number"},
                    "evidence": _STRS,
                }
            ),
        },
        "requested_check": _obj({"instruction": _STR, "component_concept": _STR}),
    }
)
GUIDANCE_SCHEMA = _obj(
    {
        "stop_conditions": _STRS,
        "steps": {
            "type": "array",
            "items": _obj(
                {"text": _STR, "component_concept": _STR, "requires_approval": {"type": "boolean"}}
            ),
        },
        "cited_sections": _STRS,
    }
)


def triage(
    client: MetaClient,
    model: str,
    symptom_clip: str | Path | None,
    transcript: str,
    job_id: str | None = None,
) -> Triage:
    text = prompt("triage").replace("{transcript}", transcript or "(none)")
    text = text.replace("{guide}", GUIDE.read_text())
    content: list[dict[str, Any]] = [{"type": "input_text", "text": text}]
    if symptom_clip is not None:
        content.append({"type": "input_video", "file_id": client.upload_file(symptom_clip)})
    return _structured(client, model, content, TRIAGE_SCHEMA, Triage, "triage", job_id)


def guidance(client: MetaClient, model: str, fault_id: str, job_id: str | None = None) -> Guidance:
    text = prompt("guidance").replace("{fault_id}", fault_id)
    text = text.replace("{guide}", GUIDE.read_text())
    content = [{"type": "input_text", "text": text}]
    sections = set(re.findall(r"^## (G-[A-Z0-9]+):", GUIDE.read_text(), flags=re.M))

    def cites_guide(g: Guidance) -> str | None:
        unknown = set(g.cited_sections) - sections
        if not g.cited_sections or unknown:
            return f"cited_sections must be guide section ids from {sorted(sections)}"
        return None

    return _structured(
        client, model, content, GUIDANCE_SCHEMA, Guidance, "guidance", job_id, check=cites_guide
    )


def as_json(m: BaseModel) -> str:
    return json.dumps(m.model_dump(), indent=2)
