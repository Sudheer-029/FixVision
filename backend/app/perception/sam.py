"""SAM 3.1 concept prompts → presence timelines (spec §4.2, perception-sam.md).

SAM only segments and tracks. On the rig it reliably finds the glass jar and, in the
close-up, the pump out of the water; the stream, clear hose and submerged pump are left
to Muse Spark (ADR-0009).
"""

import logging
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


def presence_times(text: str, start: float, fps: float) -> list[float] | None:
    """Seconds (clip timeline) of sampled frames with a mask; [] = no match, None = garbled."""
    parser = video_segmentation_format().create_parser()
    parser.push(text)
    result = parser.finish(CompletedOutcome()).result
    if any(d.severity == "error" for d in result.diagnostics):
        return None  # a garbled stream is missing evidence, never "not in view"
    frames_seen = {r.frame.frame_index for r in result.records if r.kind == "mask" and r.frame}
    return [round(start + k / fps, 3) for k in sorted(frames_seen)]


def segment(
    client: MetaClient,
    clip: str | Path,
    prompt: str,
    fps: float,
    workdir: str | Path,
    start: float = 0.0,
    duration: float | None = None,
    job_id: str | None = None,
) -> tuple[Timeline | None, float]:
    """Sample the window, run one concept prompt; (None, cost) when the request fails."""
    window = f"{start}:{duration}:{fps}"
    sampled = Path(workdir) / f"{Cache.key(file_sha256(Path(clip)), window)}.mp4"
    if not sampled.exists():
        frames.sample(clip, sampled, fps, start, duration)
    try:
        r = client.sam_segment(sampled, prompt, job_id=job_id, component="perception")
    except (OpenAIError, httpx.HTTPError, SpendLimitExceeded) as e:
        log.warning("SAM %r failed: %s", prompt, e)
        return None, 0.0
    times = presence_times(r.text, start, fps)
    return (None if times is None else Timeline(times=times, interval_s=1 / fps)), r.cost_usd
