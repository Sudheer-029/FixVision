"""Clips → JobEvidence: SAM perception + Muse Spark observations (the verdict is not made here).

SAM finds the jar; ffmpeg crops time-labelled jar frames; Muse Spark observes the scene
video, labels the jar frames and observes the close-up.
"""

from dataclasses import dataclass
from pathlib import Path

from app.agents import reasoning
from app.clients.meta_client import Cache, MetaClient, file_sha256
from app.config import Settings
from app.perception import frames
from app.perception.signals import perceive
from app.verification.schema import SUPPORTED_EQUIPMENT, Conditions, JobEvidence, Observation

FILL_FPS = 1.0


@dataclass
class Collected:
    evidence: JobEvidence
    sam_cost_usd: float


def model_copy(cfg: Settings, clip: Path) -> Path:
    """The 720p H.264 copy sent to Muse Spark."""
    out = cfg.cache_dir / "perception" / f"{Cache.key(file_sha256(clip), 'model')}.mp4"
    return frames.for_model(clip, out)


def collect_evidence(
    client: MetaClient,
    cfg: Settings,
    test_clip: Path,
    closeup_clip: Path | None,
    *,
    job_id: str,
    job_token: str,
    fault: str,
    fill_time_s: float | None,
    conditions: Conditions,
    model: str,
) -> Collected:
    work = cfg.cache_dir / "perception"
    timelines, boxes, sam_cost = perceive(
        client, test_clip, closeup_clip, cfg.sam_sample_fps, work, job_id=job_id
    )

    observations: list[Observation] = reasoning.observe_test(
        client, model, model_copy(cfg, test_clip), "test", job_id
    )
    if (box := boxes.get("jar")) is not None:  # no jar box → no fill times → C2 insufficient
        out = work / f"{Cache.key(file_sha256(test_clip), box, FILL_FPS)}-jar"
        jar = frames.crop_frames(test_clip, box, out, FILL_FPS)
        observations += reasoning.observe_fill(client, model, jar, FILL_FPS, job_id)
    if closeup_clip is not None:
        observations += reasoning.observe_test(
            client, model, model_copy(cfg, closeup_clip), "closeup", job_id
        )
    evidence = JobEvidence(
        job_id=job_id,
        job_token=job_token,
        equipment=SUPPORTED_EQUIPMENT,
        fault_hypothesis=fault,
        test_clip_duration_s=frames.duration_s(test_clip),
        observations=observations,
        timelines=timelines,
        fill_time_s=fill_time_s,
        conditions=conditions,
        models={"reasoning": model, "segmentation": cfg.segmentation_model},
    )
    return Collected(evidence, sam_cost)
