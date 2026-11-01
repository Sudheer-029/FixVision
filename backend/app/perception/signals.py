"""Per-clip presence timelines in the shape `JobEvidence.timelines` accepts (spec §4.2).

Windowed values (seconds in view, share of the fill) are derived by the engine, not here.
"""

from pathlib import Path

from app.clients.meta_client import MetaClient
from app.perception.sam import CONCEPTS, segment
from app.verification.schema import Clip, Timeline


def perceive(
    client: MetaClient,
    test_clip: str | Path,
    closeup_clip: str | Path | None,
    fps: float,
    workdir: str | Path,
    job_id: str | None = None,
) -> tuple[dict[Clip, dict[str, Timeline | None]], float]:
    """Run every concept on its clip (whole clip); returns timelines and SAM cost in USD."""
    clips: dict[Clip, str | Path | None] = {"test": test_clip, "closeup": closeup_clip}
    timelines: dict[Clip, dict[str, Timeline | None]] = {}
    cost = 0.0
    for concept, (clip, prompt) in CONCEPTS.items():
        path = clips[clip]
        if path is None:
            continue  # no close-up: concept absent → engine treats it as missing
        tl, c = segment(client, path, prompt, fps, workdir, job_id=job_id)
        timelines.setdefault(clip, {})[concept] = tl
        cost += c
    return timelines, cost
