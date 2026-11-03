"""SAM 3.1 concept prompts → presence timelines (spec §4.2, perception-sam.md).

SAM only segments and tracks. On the rig it reliably finds the glass jar and, in the
close-up, the pump out of the water; the stream, clear hose and submerged pump are left
to Muse Spark (ADR-0009).
"""

import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from meta_sam_parser import CompletedOutcome, video_segmentation_format
from openai import OpenAIError

from app.clients.meta_client import Cache, MetaClient, SpendLimitExceeded, file_sha256
from app.perception import frames
from app.verification.schema import Clip, Timeline

log = logging.getLogger(__name__)

# engine concept → (clip, prompt). Prompts are the phrasings SAM matched on real rig clips.
CONCEPTS: dict[str, tuple[Clip, str]] = {
    "jar": ("test", "glass jar"),
    "intake": ("closeup", "white pump"),
}


Box = tuple[float, float, float, float]  # x1, y1, x2, y2 in source pixels
BOX_SIDES = ("left", "top", "right", "bottom")


@dataclass
class Segmented:
    timeline: Timeline | None  # None = request failed or garbled stream (missing evidence)
    box: Box | None  # median box of the most-seen object; used to crop the jar for Muse Spark
    cost_usd: float
    track: dict[float, Box] = field(default_factory=dict)  # clip seconds → that frame's box


def parse(text: str) -> list | None:
    """SAM records, or None for a garbled stream (missing evidence, never "not in view")."""
    parser = video_segmentation_format().create_parser()
    parser.push(text)
    result = parser.finish(CompletedOutcome()).result
    if any(d.severity == "error" for d in result.diagnostics):
        return None
    return list(result.records)


def presence_times(records: list, start: float, fps: float) -> list[float]:
    """Seconds (clip timeline) of sampled frames with a mask; [] = no match."""
    frames_seen = {r.frame.frame_index for r in records if r.kind == "mask" and r.frame}
    return [round(start + k / fps, 3) for k in sorted(frames_seen)]


def _main_object_boxes(records: list) -> list:
    boxes = [r for r in records if r.kind == "box"]
    if not boxes:
        return []
    ids = [r.object_id for r in boxes]
    # most-seen object; ties go to SAM's first object id (set order alone is random per run)
    main = max(sorted(set(ids), key=int), key=ids.count)
    return [r for r in boxes if r.object_id == main]


def median_box(records: list) -> Box | None:
    own = _main_object_boxes(records)
    if not own:
        return None
    x1, y1, x2, y2 = (statistics.median(getattr(r, k) for r in own) for k in BOX_SIDES)
    return x1, y1, x2, y2


def box_track(records: list, start: float, fps: float) -> dict[float, Box]:
    """The main object's own box per sampled frame: a moving part is not at its median box."""
    return {
        round(start + r.frame.frame_index / fps, 3): tuple(getattr(r, k) for k in BOX_SIDES)
        for r in _main_object_boxes(records)
        if r.frame
    }


def segment(
    client: MetaClient,
    clip: str | Path,
    prompt: str,
    fps: float,
    workdir: str | Path,
    start: float = 0.0,
    duration: float | None = None,
    job_id: str | None = None,
) -> Segmented:
    """Sample the window and run one concept prompt."""
    window = f"{start}:{duration}:{fps}"
    sampled = Path(workdir) / f"{Cache.key(file_sha256(Path(clip)), window)}.mp4"
    if not sampled.exists():
        frames.sample(clip, sampled, fps, start, duration)
    try:
        r = client.sam_segment(sampled, prompt, job_id=job_id, component="perception")
    except (OpenAIError, httpx.HTTPError, SpendLimitExceeded) as e:
        log.warning("SAM %r failed: %s", prompt, e)
        return Segmented(None, None, 0.0)
    records = parse(r.text)
    if records is None:
        return Segmented(None, None, r.cost_usd)
    timeline = Timeline(times=presence_times(records, start, fps), interval_s=1 / fps)
    return Segmented(timeline, median_box(records), r.cost_usd, box_track(records, start, fps))
