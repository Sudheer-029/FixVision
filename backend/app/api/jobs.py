"""REST API (docs/components/orchestrator.md). Verdicts only come from app/verification."""

import json
import secrets
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.jobs import steps as S
from app.jobs.models import Job, Media, Record, Step, VerdictRow, now
from app.jobs.state import State
from app.verification.schema import SUPPORTED_EQUIPMENT, Conditions, Fault

router = APIRouter(prefix="/jobs", tags=["jobs"])

MediaKind = Literal["symptom", "check", "closeup", "test", "voice"]
SUFFIXES = {".mp4", ".mov", ".webm", ".m4a", ".wav"}
MAX_UPLOAD_BYTES = 300 * 1024 * 1024
TOKEN_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I: the code is handwritten
MEDIA_TARGET = {
    "symptom": State.SYMPTOM_CAPTURED,
    "check": State.CHECK_CAPTURED,
    "closeup": State.CLOSEUP_CAPTURED,
    "test": State.TEST_CAPTURED,
}


class CreateJob(BaseModel):
    equipment: Literal[SUPPORTED_EQUIPMENT] = SUPPORTED_EQUIPMENT  # type: ignore[valid-type]
    data_class: Literal["staged", "customer"] = "staged"


class TriageIn(BaseModel):
    transcript: str = Field("", max_length=5000)


class GuidanceIn(BaseModel):
    fault_id: Fault


class TestIn(BaseModel):
    fill_time_s: float | None = Field(None, gt=0, le=600)
    conditions: Conditions = Conditions()


class ReviewIn(BaseModel):
    approved: bool
    note: str = Field("", max_length=2000)


def get_deps(request: Request) -> S.Deps:
    return request.app.state.deps or S.default_deps()


DepsDep = Annotated[S.Deps, Depends(get_deps)]


def load_job(s: Session, job_id: str) -> Job:
    job = s.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job


def require_state(job: Job, *states: State) -> None:
    if job.state not in states:
        allowed = ", ".join(states)
        raise HTTPException(409, f"job is {job.state}; this needs {allowed}")


def enqueue(request: Request, deps: S.Deps, s: Session, job_id: str, step: str, fn: Any) -> dict:
    if S.claim(s, job_id, step):
        request.app.state.worker.submit(S.run_step, deps, job_id, step, fn)
    return {"step": step, "status": s.get(Step, (job_id, step)).status}


def save_upload(file: UploadFile, path: Path) -> None:
    written = 0
    with path.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                break
            out.write(chunk)
    if written > MAX_UPLOAD_BYTES:
        path.unlink()
        raise HTTPException(413, "file too large")


@router.post("", status_code=201)
def create_job(body: CreateJob, deps: DepsDep) -> dict[str, str]:
    token = "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(4))
    job = Job(
        id=uuid4().hex[:12], token=token, equipment=body.equipment,
        data_class=body.data_class, state=State.CREATED,
    )  # fmt: skip
    with Session(deps.engine) as s:
        s.add(job)
        s.commit()
        return {"id": job.id, "token": job.token, "state": job.state}


@router.post("/{job_id}/media", status_code=201)
def upload_media(
    job_id: str,
    deps: DepsDep,
    kind: Annotated[MediaKind, Form()],
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    suffix = "." + (file.filename or "").rsplit(".", 1)[-1].lower()
    if suffix not in SUFFIXES:
        raise HTTPException(415, f"unsupported file type; use one of {sorted(SUFFIXES)}")
    with Session(deps.engine) as s:
        job = load_job(s, job_id)
        if job.state in (State.VERIFYING, State.REVIEWED):
            raise HTTPException(409, f"job is {job.state}; media cannot change now")
        target = MEDIA_TARGET.get(kind)
        if target is not None and job.state != target:  # same state: a re-record of that clip
            if kind == "closeup" and job.state == State.GUIDANCE_ISSUED:
                S.advance(job, State.REPAIR_REPORTED)  # uploading the close-up reports the repair
            S.advance(job, target)
        folder = deps.cfg.jobs_dir / job_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{uuid4().hex[:8]}-{kind}{suffix}"  # never the client's file name
        save_upload(file, path)
        media = Media(job_id=job_id, kind=kind, path=str(path))
        s.add_all([media, job])
        s.commit()
        return {"id": media.id, "kind": kind, "state": job.state}


@router.post("/{job_id}/triage", status_code=202)
def start_triage(job_id: str, body: TriageIn, deps: DepsDep, request: Request) -> dict:
    with Session(deps.engine) as s:
        require_state(load_job(s, job_id), State.SYMPTOM_CAPTURED)
        symptom = S.latest_media(s, job_id, "symptom").path

        def fn(job: Job) -> S.Outcome:
            return S.triage(deps, symptom, body.transcript, job)

        return enqueue(request, deps, s, job_id, "triage", fn)


@router.post("/{job_id}/guidance", status_code=202)
def start_guidance(job_id: str, body: GuidanceIn, deps: DepsDep, request: Request) -> dict:
    with Session(deps.engine) as s:
        require_state(load_job(s, job_id), State.CHECK_CAPTURED)

        def fn(job: Job) -> S.Outcome:
            return S.guidance(deps, body.fault_id, job)

        return enqueue(request, deps, s, job_id, f"guidance:{body.fault_id}", fn)


@router.post("/{job_id}/test", status_code=202)
def start_test(job_id: str, body: TestIn, deps: DepsDep, request: Request) -> dict:
    with Session(deps.engine) as s:
        job = load_job(s, job_id)
        require_state(job, State.TEST_CAPTURED, State.VERIFYING)  # VERIFYING: retry a failed step
        test = S.latest_media(s, job_id, "test")
        closeup = S.latest_media(s, job_id, "closeup")
        test_path, closeup_path = test.path, closeup.path if closeup else None
        step = f"verify:{test.id}"  # each recorded test is its own attempt
        if job.state == State.TEST_CAPTURED:
            S.advance(job, State.VERIFYING)
            s.add(job)
            s.commit()

        def fn(j: Job) -> S.Outcome:
            return S.verify_job(
                deps, step, test_path, closeup_path, body.fill_time_s, body.conditions, j
            )

        return enqueue(request, deps, s, job_id, step, fn)


@router.get("/{job_id}")
def get_job(job_id: str, deps: DepsDep) -> dict[str, Any]:
    with Session(deps.engine) as s:
        job = load_job(s, job_id)
        media = s.exec(select(Media).where(Media.job_id == job_id)).all()
        steps = s.exec(select(Step).where(Step.job_id == job_id)).all()
        query = select(VerdictRow).where(VerdictRow.job_id == job_id)
        verdict = s.exec(query.order_by(VerdictRow.id.desc())).first()  # type: ignore[union-attr]
        record = s.get(Record, job_id)
        return {
            "id": job.id,
            "token": job.token,
            "equipment": job.equipment,
            "data_class": job.data_class,
            "state": job.state,
            "fault": job.fault,
            "media": [{"id": m.id, "kind": m.kind} for m in media],
            "steps": [
                {
                    "step": st.step,
                    "status": st.status,
                    "error": st.error,
                    "result": json.loads(st.result_json) if st.result_json else None,
                }
                for st in steps
            ],
            "verdict": json.loads(verdict.data_json) if verdict else None,
            "record": record.model_dump() if record else None,
        }


@router.get("/{job_id}/trace")
def get_trace(job_id: str, deps: DepsDep) -> dict[str, Any]:
    with Session(deps.engine) as s:
        load_job(s, job_id)
    return S.trace(deps, job_id)


@router.post("/{job_id}/review")
def review(job_id: str, body: ReviewIn, deps: DepsDep) -> dict[str, Any]:
    with Session(deps.engine) as s:
        job = load_job(s, job_id)
        S.advance(job, State.REVIEWED)
        record = s.get(Record, job_id)
        record.review = "approved" if body.approved else "rejected"
        record.note, record.reviewed_at = body.note, now()
        s.add_all([job, record])
        s.commit()
        return {"state": job.state, "review": record.review, "verdict": record.verdict}
