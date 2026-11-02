"""SQLite tables. The cost ledger is the `cost_ledger` table MetaClient writes (ledger_path)."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text
from sqlmodel import Field, SQLModel, create_engine


def now() -> str:
    return datetime.now(UTC).isoformat()  # same format as cost_ledger.ts, so they compare


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    id: str = Field(primary_key=True)
    token: str
    equipment: str
    data_class: str
    state: str
    fault: str | None = None
    created_at: str = Field(default_factory=now)


class Media(SQLModel, table=True):
    __tablename__ = "media"
    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    kind: str
    path: str
    created_at: str = Field(default_factory=now)


class Step(SQLModel, table=True):
    """One unit of worker work; the key makes it idempotent (a done step never runs twice)."""

    __tablename__ = "steps"
    job_id: str = Field(foreign_key="jobs.id", primary_key=True)
    step: str = Field(primary_key=True)
    status: str = "queued"  # queued | running | done | error
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result_json: str | None = None


class ObservationRow(SQLModel, table=True):
    __tablename__ = "observations"
    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    step: str
    data_json: str


class VerdictRow(SQLModel, table=True):
    __tablename__ = "verdicts"
    id: int | None = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    step: str
    verdict: str
    data_json: str
    created_at: str = Field(default_factory=now)


class Record(SQLModel, table=True):
    """The job's current outcome and its manager review (rendered in T9)."""

    __tablename__ = "records"
    job_id: str = Field(foreign_key="jobs.id", primary_key=True)
    verdict: str
    review: str | None = None  # approved | rejected
    note: str = ""
    reviewed_at: str | None = None


def make_engine(path: Path) -> Engine:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    # shortcut: assumes one API process; steps it left unfinished can only be retried
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE steps SET status = 'error', error = 'interrupted by a restart' "
                "WHERE status IN ('queued', 'running')"
            )
        )
    return engine
