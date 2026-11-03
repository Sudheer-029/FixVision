"""Worker steps: model calls run off the request path, one at a time, idempotent by job + step.

Model calls hold no database session. A step's result, rows and state change commit together,
so a crash between them leaves the step re-runnable, never half applied.
"""

import json
import logging
import sqlite3
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select

from app.agents import reasoning
from app.clients.meta_client import MetaClient
from app.config import Settings, settings
from app.jobs.models import (
    Job,
    Media,
    ObservationRow,
    Record,
    Step,
    VerdictRow,
    make_engine,
    now,
)
from app.jobs.state import State, check
from app.pipeline import collect_evidence, evidence_frames, model_copy
from app.verification.engine import verify
from app.verification.schema import Conditions
from app.verification.thresholds import load_thresholds

log = logging.getLogger(__name__)
Apply = Callable[[Session, Job], None]
Outcome = tuple[dict[str, Any], Apply]


@dataclass
class Deps:
    cfg: Settings
    engine: Engine
    client: Any
    collect: Callable[..., Any] = field(default=collect_evidence)
    prepare: Callable[[Settings, Path], Path] = field(default=model_copy)


@cache
def default_deps() -> Deps:
    return Deps(settings, make_engine(settings.db_path), MetaClient(settings))


def advance(job: Job, *to: State) -> None:
    for state in to:
        check(job.state, state)
        job.state = state


def latest_media(s: Session, job_id: str, kind: str) -> Media | None:
    query = select(Media).where(Media.job_id == job_id, Media.kind == kind)
    return s.exec(query.order_by(Media.id.desc())).first()  # type: ignore[union-attr]


def latest_verdict(s: Session, job_id: str) -> VerdictRow | None:
    query = select(VerdictRow).where(VerdictRow.job_id == job_id)
    return s.exec(query.order_by(VerdictRow.id.desc())).first()  # type: ignore[union-attr]


def evidence_dir(cfg: Settings, job_id: str, step: str) -> Path:
    return cfg.jobs_dir / job_id / "evidence" / step.replace(":", "-")


def claim(s: Session, job_id: str, step: str) -> bool:
    """False if the step is queued, running or done; an errored step can be claimed again."""
    row = s.get(Step, (job_id, step))
    if row is not None and row.status != "error":
        return False
    row = row or Step(job_id=job_id, step=step)
    row.status, row.error = "queued", None
    s.add(row)
    s.commit()
    return True


def run_step(deps: Deps, job_id: str, step: str, fn: Callable[[Job], Outcome]) -> None:
    with Session(deps.engine) as s:
        row = s.get(Step, (job_id, step))
        row.status, row.started_at, row.finished_at = "running", now(), None
        s.add(row)
        s.commit()
        job = s.get(Job, job_id)
        s.expunge(job)
    try:
        result, apply = fn(job)
        with Session(deps.engine) as s:
            apply(s, s.get(Job, job_id))
            row = s.get(Step, (job_id, step))
            row.status, row.finished_at = "done", now()
            row.result_json = json.dumps(result)
            s.add(row)
            s.commit()
    except Exception as e:  # any failure leaves the step retryable; details stay in the log
        log.exception("step %s failed for job %s", step, job_id)
        with Session(deps.engine) as s:
            row = s.get(Step, (job_id, step))
            row.status, row.finished_at, row.error = "error", now(), type(e).__name__
            s.add(row)
            s.commit()


def triage(deps: Deps, symptom_path: str, transcript: str, job: Job) -> Outcome:
    model = reasoning.model_for(deps.cfg, job.data_class)
    clip = deps.prepare(deps.cfg, Path(symptom_path))
    t = reasoning.triage(deps.client, model, clip, transcript, job.id)

    def apply(s: Session, j: Job) -> None:
        advance(j, State.TRIAGED, State.CHECK_REQUESTED)
        s.add(j)

    return t.model_dump(), apply


def guidance(deps: Deps, fault: str, job: Job) -> Outcome:
    model = reasoning.model_for(deps.cfg, job.data_class)
    g = reasoning.guidance(deps.client, model, fault, job.id)

    def apply(s: Session, j: Job) -> None:
        advance(j, State.GUIDANCE_ISSUED)
        j.fault = fault
        s.add(j)

    return g.model_dump(), apply


def verify_job(
    deps: Deps,
    step: str,
    test_path: str,
    closeup_path: str | None,
    fill_time_s: float | None,
    conditions: Conditions,
    job: Job,
) -> Outcome:
    collected = deps.collect(
        deps.client,
        deps.cfg,
        Path(test_path),
        Path(closeup_path) if closeup_path else None,
        job_id=job.id,
        job_token=job.token,
        fault=job.fault or "unknown",
        fill_time_s=fill_time_s,
        conditions=conditions,
        model=reasoning.model_for(deps.cfg, job.data_class),
    )
    evidence = collected.evidence
    verdict = verify(evidence, load_thresholds(deps.cfg.rig_baseline_path))
    closeup = Path(closeup_path) if closeup_path else None
    try:
        evidence_frames(collected, Path(test_path), closeup, evidence_dir(deps.cfg, job.id, step))
    except (subprocess.CalledProcessError, OSError):  # an illustration never blocks a verdict
        log.exception("evidence frames failed for job %s", job.id)

    def apply(s: Session, j: Job) -> None:
        for o in evidence.observations:
            s.add(ObservationRow(job_id=j.id, step=step, data_json=o.model_dump_json()))
        s.add(
            VerdictRow(
                job_id=j.id, step=step, verdict=verdict.verdict,
                data_json=verdict.model_dump_json(),
            )
        )  # fmt: skip
        s.merge(Record(job_id=j.id, verdict=verdict.verdict))  # a new attempt resets the review
        advance(j, State(verdict.verdict))
        s.add(j)

    return {"verdict": verdict.verdict, "sam_cost_usd": collected.sam_cost_usd}, apply


def trace(deps: Deps, job_id: str) -> dict[str, Any]:
    """Each model call from the ledger, under the step whose time window contains it."""
    with Session(deps.engine) as s:
        steps = s.exec(select(Step).where(Step.job_id == job_id)).all()
    calls = []
    if deps.cfg.ledger_path.exists():
        db = sqlite3.connect(deps.cfg.ledger_path)
        try:
            calls = db.execute(
                "SELECT ts, component, model, latency_ms, est_cost_usd, cached "
                "FROM cost_ledger WHERE job_id = ? ORDER BY ts",
                (job_id,),
            ).fetchall()
        except sqlite3.OperationalError:  # no ledger table yet: no calls were made
            pass
        finally:
            db.close()

    out = []
    for st in steps:
        mine = [
            {"ts": c[0], "component": c[1], "model": c[2], "latency_ms": c[3],
             "cost_usd": c[4], "cached": bool(c[5])}
            for c in calls
            if st.started_at and st.started_at <= c[0] <= (st.finished_at or "9")
        ]  # fmt: skip
        out.append(
            {
                "step": st.step,
                "status": st.status,
                "started_at": st.started_at,
                "finished_at": st.finished_at,
                "error": st.error,
                "calls": mine,
                "latency_ms": sum(c["latency_ms"] or 0 for c in mine),
                "cost_usd": round(sum(c["cost_usd"] for c in mine), 6),
            }
        )
    out.sort(key=lambda x: x["started_at"] or "")
    return {
        "job_id": job_id,
        "steps": out,
        "total_cost_usd": round(sum(c[4] for c in calls), 6),
        "total_calls": len(calls),
    }
