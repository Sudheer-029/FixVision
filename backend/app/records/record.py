"""The service record (docs/components/service-record.md): facts from structured fields only."""

import json
from typing import Any

from sqlmodel import Session, select

from app.config import Settings
from app.jobs.models import Job, Media, ObservationRow, Record, Step, VerdictRow
from app.jobs.steps import evidence_on_disk
from app.verification.thresholds import load_thresholds


def _fill_from_video(observations: list[dict], min_confidence: float | None) -> float | None:
    """Only a time the rules could trust; no baseline means none could be trusted."""
    if min_confidence is None:
        return None
    values = {
        o["id"]: o["value"]
        for o in observations
        if o["clip"] == "test" and o["confidence"] >= min_confidence
    }
    start, line = values.get("fill_start_t"), values.get("fill_line_t")
    return None if start is None or line is None else round(line - start, 1)


def build(s: Session, cfg: Settings, job: Job, verdict_row: VerdictRow) -> dict[str, Any]:
    verdict = json.loads(verdict_row.data_json)
    thresholds = load_thresholds(cfg.rig_baseline_path)
    query = select(ObservationRow).where(
        ObservationRow.job_id == job.id, ObservationRow.step == verdict_row.step
    )
    observations = [json.loads(o.data_json) for o in s.exec(query).all()]
    step = s.get(Step, (job.id, verdict_row.step))
    typed = json.loads(step.result_json).get("fill_time_s") if step.result_json else None
    triage = s.get(Step, (job.id, "triage"))
    triage_result = json.loads(triage.result_json) if triage and triage.result_json else {}
    guidance = s.exec(
        select(Step).where(Step.job_id == job.id, Step.step == f"guidance:{job.fault}")
    ).first()
    review = s.get(Record, job.id)
    media = s.exec(select(Media).where(Media.job_id == job.id)).all()
    return {
        "job_id": job.id,
        "job_token": job.token,
        "data_class": job.data_class,
        "equipment": job.equipment,
        "fault_hypothesis": verdict["fault_hypothesis"],
        "symptom_transcript": triage_result.get("transcript", ""),
        "verdict": verdict["verdict"],
        "reasons": verdict["reasons"],
        "checks": verdict["checks"],
        "measurements": {
            "fill_time_video_s": _fill_from_video(
                observations, thresholds.confidence_threshold if thresholds else None
            ),
            "fill_time_typed_s": typed,
            "run_s": verdict["run_s"],
        },
        "conditions": verdict["conditions"],
        "uncertainties": verdict["uncertainties"],
        "requested_actions": verdict["requested_actions"],
        "observations": observations,
        "evidence_frames": evidence_on_disk(cfg, job.id, verdict_row.step),
        "media": [{"kind": m.kind, "uploaded_at": m.created_at} for m in media],
        "guide_sections": json.loads(guidance.result_json).get("cited_sections", [])
        if guidance and guidance.result_json
        else [],
        "models": verdict["models"],
        "thresholds_version": verdict["thresholds_version"],
        "created_at": job.created_at,
        "verified_at": verdict_row.created_at,
        "review": {
            "decision": review.review if review else None,
            "note": review.note if review else "",
            "reviewed_at": review.reviewed_at if review else None,
        },
    }
