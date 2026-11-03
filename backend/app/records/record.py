"""The service record (docs/components/service-record.md): facts from structured fields only."""

import json
from typing import Any

from sqlmodel import Session, select

from app.config import Settings
from app.jobs.models import Job, Media, ObservationRow, Record, Step, VerdictRow


def _fill_from_video(observations: list[dict]) -> float | None:
    values = {o["id"]: o["value"] for o in observations if o["clip"] == "test"}
    start, line = values.get("fill_start_t"), values.get("fill_line_t")
    return None if start is None or line is None else round(line - start, 1)


def build(s: Session, cfg: Settings, job: Job, verdict_row: VerdictRow) -> dict[str, Any]:
    verdict = json.loads(verdict_row.data_json)
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
    evidence_dir = cfg.jobs_dir / job.id / "evidence" / verdict_row.step.replace(":", "-")
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
            "fill_time_video_s": _fill_from_video(observations),
            "fill_time_typed_s": typed,
            "run_s": verdict["run_s"],
        },
        "conditions": verdict["conditions"],
        "uncertainties": verdict["uncertainties"],
        "requested_actions": verdict["requested_actions"],
        "observations": observations,
        "evidence_frames": [c for c in ("jar", "intake") if (evidence_dir / f"{c}.jpg").exists()],
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
