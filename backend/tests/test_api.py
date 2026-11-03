"""Job API end to end with mocked model clients and a real worker thread, SQLite and ledger."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.meta_client import CallResult, Ledger
from app.config import Settings
from app.jobs.models import make_engine
from app.jobs.state import NEXT, IllegalTransition, State, check
from app.jobs.steps import Deps
from app.main import create_app
from app.pipeline import Collected
from tests.verification.factory import THRESHOLDS, healthy, replace_obs

AGENTS = Path(__file__).parent / "fixtures" / "agents"
CONDITIONS = {"supply": "usb_5v", "head_cm": 20, "water_level_cm": 8}


class FakeClient:
    """Answers by schema name and writes the real ledger, as MetaClient does."""

    def __init__(self, ledger: Ledger):
        self.ledger, self.calls, self.sent, self.fail = ledger, [], [], False

    def respond(self, model, input, schema=None, schema_name="", job_id=None, component="", **_):
        self.calls.append(component)
        self.sent.append(input)
        if self.fail:
            raise TimeoutError("model timed out")
        name = {"triage": "triage_slow_fill.json", "guidance": "guidance_f1.json"}[component]
        result = CallResult(text=(AGENTS / name).read_text(), cost_usd=0.01, latency_ms=120)
        self.ledger.record(job_id=job_id, component=component, model=model, result=result)
        return result

    def upload_file(self, path):
        return "file-123"

    def transcribe(self, wav, keywords=(), job_id=None):
        result = CallResult(text="पानी धीरे आ रहा है", cost_usd=0.001, latency_ms=50)
        self.ledger.record(job_id=job_id, component="voice", model="voice", result=result)
        return result


class Rig:
    def __init__(self, tmp_path: Path):
        baseline = tmp_path / "baseline.yaml"
        baseline.write_text(
            f"measured: true\nversion: t\nbaseline_fill_s: {THRESHOLDS.baseline_fill_s}\n"
        )
        cfg = Settings(
            _env_file=None,
            cache_dir=tmp_path / "cache",
            ledger_path=tmp_path / "ledger.sqlite",
            db_path=tmp_path / "app.sqlite",
            jobs_dir=tmp_path / "jobs",
            rig_baseline_path=str(baseline),
        )
        self.client = FakeClient(Ledger(cfg.ledger_path))
        self.break_evidence = lambda ev: ev
        self.seen_collect = []
        self.tracks = {}
        self.clip_bytes = b"video-bytes"
        deps = Deps(
            cfg,
            make_engine(cfg.db_path),
            self.client,
            self.collect,
            lambda _cfg, clip: clip,
            lambda _cfg, audio: audio,
        )
        self.app = create_app(deps)
        self.api = TestClient(self.app)

    def collect(self, client, cfg, test, closeup, *, job_id, job_token, fault, fill_time_s,
                conditions, model):  # fmt: skip
        self.seen_collect.append({"test": test, "closeup": closeup, "fault": fault, "model": model})
        ev = healthy(fault=fault, job_id=job_id, job_token=job_token, conditions=conditions)
        for clip in ("test", "closeup"):
            ev = replace_obs(ev, "job_token_read", clip, value=job_token)
        return Collected(self.break_evidence(ev), 0.02, self.tracks)

    def drain(self) -> None:
        self.app.state.worker.submit(lambda: None).result()

    def job(self, job_id: str) -> dict:
        return self.api.get(f"/jobs/{job_id}").json()

    def upload(self, job_id: str, kind: str, name: str = "clip.mp4"):
        return self.api.post(
            f"/jobs/{job_id}/media", data={"kind": kind}, files={"file": (name, self.clip_bytes)}
        )

    def to_test_captured(self) -> str:
        job_id = self.api.post("/jobs", json={"data_class": "staged"}).json()["id"]
        assert self.upload(job_id, "symptom").status_code == 201
        assert self.api.post(f"/jobs/{job_id}/triage", json={}).status_code == 202
        self.drain()
        assert self.job(job_id)["state"] == "CHECK_REQUESTED"
        assert self.upload(job_id, "check").status_code == 201
        assert self.api.post(f"/jobs/{job_id}/guidance", json={"fault_id": "F1"}).status_code == 202
        self.drain()
        assert self.job(job_id)["state"] == "GUIDANCE_ISSUED"
        assert self.upload(job_id, "closeup").json()["state"] == "CLOSEUP_CAPTURED"
        assert self.upload(job_id, "test").json()["state"] == "TEST_CAPTURED"
        return job_id

    def run_test(self, job_id: str) -> str:
        r = self.api.post(
            f"/jobs/{job_id}/test", json={"fill_time_s": 20.0, "conditions": CONDITIONS}
        )
        assert r.status_code == 202
        self.drain()
        return self.job(job_id)["state"]


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


def test_every_transition_outside_the_table_is_illegal():
    for current in State:
        for to in State:
            if to in NEXT[current]:
                check(current, to)
            else:
                with pytest.raises(IllegalTransition):
                    check(current, to)


def test_create_returns_a_token_the_engine_accepts(rig):
    r = rig.api.post("/jobs", json={})
    assert r.status_code == 201
    assert re.fullmatch(r"[A-HJ-NP-Z2-9]{4}", r.json()["token"])
    assert r.json()["state"] == "CREATED"


def test_staged_job_can_keep_the_code_in_its_clip(rig):
    assert rig.api.post("/jobs", json={"token": "R2C6"}).json()["token"] == "R2C6"
    assert rig.api.post("/jobs", json={"token": "bad code"}).status_code == 422


def test_customer_job_cannot_choose_its_token(rig):
    r = rig.api.post("/jobs", json={"data_class": "customer", "token": "R2C6"})
    assert r.status_code == 422


def test_unsupported_equipment_is_refused(rig):
    assert rig.api.post("/jobs", json={"equipment": "diesel_pump"}).status_code == 422


def test_happy_path_ends_passed_then_reviewed(rig):
    job_id = rig.to_test_captured()
    assert rig.run_test(job_id) == "PASSED"

    job = rig.job(job_id)
    assert job["fault"] == "F1"
    assert job["verdict"]["verdict"] == "PASSED"
    assert job["record"]["verdict"] == "PASSED" and job["record"]["review"] is None
    results = {s["step"]: s["result"] for s in job["steps"]}
    assert results["triage"]["causes"] and results["guidance:F1"]["stop_conditions"]
    assert rig.seen_collect[0]["fault"] == "F1"
    assert rig.seen_collect[0]["closeup"].name.endswith("-closeup.mp4")

    r = rig.api.post(f"/jobs/{job_id}/review", json={"approved": True, "note": "ok"})
    assert r.json() == {"state": "REVIEWED", "review": "approved", "verdict": "PASSED"}


def test_trace_puts_calls_under_their_steps(rig):
    job_id = rig.to_test_captured()
    rig.run_test(job_id)
    trace = rig.api.get(f"/jobs/{job_id}/trace").json()
    by_step = {s["step"]: s for s in trace["steps"]}
    assert [c["component"] for c in by_step["triage"]["calls"]] == ["triage"]
    assert by_step["guidance:F1"]["cost_usd"] == 0.01
    assert by_step["guidance:F1"]["latency_ms"] == 120
    assert trace["total_calls"] == 2 and trace["total_cost_usd"] == 0.02


def test_wrong_token_is_inconclusive_and_can_be_re_recorded(rig):
    rig.break_evidence = lambda ev: replace_obs(ev, "job_token_read", "test", value="ZZZZ")
    job_id = rig.to_test_captured()
    assert rig.run_test(job_id) == "INCONCLUSIVE"
    assert rig.job(job_id)["verdict"]["verdict"] == "INCONCLUSIVE"

    rig.break_evidence = lambda ev: ev
    assert rig.upload(job_id, "closeup").json()["state"] == "CLOSEUP_CAPTURED"
    assert rig.upload(job_id, "test").json()["state"] == "TEST_CAPTURED"
    assert rig.run_test(job_id) == "PASSED"  # a new recording is a new attempt
    assert rig.job(job_id)["record"]["verdict"] == "PASSED"
    assert len(rig.seen_collect) == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda rig, j: rig.upload(j, "test"),
        lambda rig, j: rig.upload(j, "closeup"),
        lambda rig, j: rig.api.post(f"/jobs/{j}/triage", json={}),
        lambda rig, j: rig.api.post(f"/jobs/{j}/guidance", json={"fault_id": "F1"}),
        lambda rig, j: rig.api.post(f"/jobs/{j}/test", json={}),
        lambda rig, j: rig.api.post(f"/jobs/{j}/review", json={"approved": True}),
    ],
)
def test_out_of_order_calls_get_409(rig, call):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    assert call(rig, job_id).status_code == 409
    assert rig.job(job_id)["state"] == "CREATED"
    assert not list((rig.app.state.deps.cfg.jobs_dir).glob(f"{job_id}/*"))  # nothing was stored


def test_passed_job_cannot_go_back_to_capture(rig):
    job_id = rig.to_test_captured()
    rig.run_test(job_id)
    assert rig.upload(job_id, "closeup").status_code == 409


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_evidence_frames_are_served(rig, tmp_path):
    clip = tmp_path / "real.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=30:size=320x240:rate=2",
         str(clip)],
        check=True,
    )  # fmt: skip
    rig.clip_bytes = clip.read_bytes()
    rig.tracks = {"jar": {1.0: (10, 10, 100, 100)}, "intake": {}}
    job_id = rig.to_test_captured()
    rig.run_test(job_id)
    assert rig.job(job_id)["evidence"] == ["jar"]
    r = rig.api.get(f"/jobs/{job_id}/evidence/jar")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert rig.api.get(f"/jobs/{job_id}/evidence/intake").status_code == 404
    assert rig.api.get(f"/jobs/{job_id}/evidence/secrets").status_code == 422


def test_broken_evidence_frame_does_not_block_the_verdict(rig):
    rig.tracks = {"jar": {1.0: (10, 10, 100, 100)}}  # the clip bytes are not a video: ffmpeg fails
    job_id = rig.to_test_captured()
    assert rig.run_test(job_id) == "PASSED"
    assert rig.job(job_id)["evidence"] == []


def test_unknown_job_is_404(rig):
    assert rig.api.get("/jobs/nope").status_code == 404
    assert rig.api.get("/jobs/nope/trace").status_code == 404


def test_voice_note_reaches_triage_and_the_trace(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    rig.upload(job_id, "symptom")
    assert rig.upload(job_id, "voice", "note.m4a").json()["state"] == "SYMPTOM_CAPTURED"
    rig.api.post(f"/jobs/{job_id}/triage", json={"transcript": "typed note"})
    rig.drain()
    assert rig.job(job_id)["state"] == "CHECK_REQUESTED"
    triage = rig.job(job_id)["steps"][0]["result"]
    assert triage["transcript"] == "typed note\nपानी धीरे आ रहा है"
    sent = json.dumps(rig.client.sent, ensure_ascii=False)
    assert "पानी धीरे" in sent and "typed note" in sent
    calls = rig.api.get(f"/jobs/{job_id}/trace").json()["steps"][0]["calls"]
    assert [c["component"] for c in calls] == ["voice", "triage"]


def test_service_record_holds_every_field(rig):
    job_id = rig.to_test_captured()
    assert rig.api.get(f"/jobs/{job_id}/record").status_code == 404  # no verdict yet
    rig.run_test(job_id)
    rec = rig.api.get(f"/jobs/{job_id}/record").json()
    assert rec["verdict"] == "PASSED" and rec["fault_hypothesis"] == "F1"
    assert rec["measurements"] == {
        "fill_time_video_s": 20.0,
        "fill_time_typed_s": 20.0,
        "run_s": 30.0,
    }
    assert rec["conditions"]["supply"] == "usb_5v" and rec["checks"] and rec["observations"]
    assert rec["guide_sections"] and rec["thresholds_version"] == "t"
    assert rec["models"]["reasoning"] and rec["created_at"] and rec["verified_at"]
    assert rec["review"]["decision"] is None
    assert {m["kind"] for m in rec["media"]} == {"symptom", "check", "closeup", "test"}

    rig.api.post(f"/jobs/{job_id}/review", json={"approved": False, "note": "redo"})
    review = rig.api.get(f"/jobs/{job_id}/record").json()["review"]
    assert (review["decision"], review["note"]) == ("rejected", "redo") and review["reviewed_at"]


def test_upload_names_never_reach_the_disk_and_types_are_limited(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    assert rig.upload(job_id, "symptom", "evil.sh").status_code == 415
    assert rig.upload(job_id, "symptom", "noextension").status_code == 415
    assert rig.upload(job_id, "symptom", "../../../evil.mp4").status_code == 201
    stored = [p.name for p in (rig.app.state.deps.cfg.jobs_dir / job_id).iterdir()]
    assert len(stored) == 1 and "evil" not in stored[0]


def test_oversized_upload_is_refused_before_parsing(rig, monkeypatch):
    monkeypatch.setattr("app.api.jobs.MAX_UPLOAD_BYTES", 0)
    monkeypatch.setattr("app.main.MULTIPART_OVERHEAD", 10)
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    assert rig.upload(job_id, "symptom").status_code == 413
    assert rig.job(job_id)["state"] == "CREATED"


def test_upload_without_content_length_is_refused(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    r = rig.api.post(f"/jobs/{job_id}/media", content=iter([b"x"]))
    assert r.status_code == 411


def test_repeated_step_is_not_run_twice(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    rig.upload(job_id, "symptom")
    gate = rig.app.state.worker.submit(lambda: __import__("time").sleep(0.2))  # hold the worker
    first = rig.api.post(f"/jobs/{job_id}/triage", json={})
    second = rig.api.post(f"/jobs/{job_id}/triage", json={})
    assert first.status_code == second.status_code == 202
    gate.result()
    rig.drain()
    assert rig.client.calls == ["triage"]


def test_model_failure_marks_the_step_and_a_retry_works(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    rig.upload(job_id, "symptom")
    rig.client.fail = True
    rig.api.post(f"/jobs/{job_id}/triage", json={})
    rig.drain()
    job = rig.job(job_id)
    assert job["state"] == "SYMPTOM_CAPTURED"
    assert job["steps"][0]["status"] == "error" and job["steps"][0]["error"] == "TimeoutError"

    rig.client.fail = False
    rig.api.post(f"/jobs/{job_id}/triage", json={})
    rig.drain()
    assert rig.job(job_id)["state"] == "CHECK_REQUESTED"


def test_verify_failure_never_gives_a_verdict_and_can_retry(rig):
    job_id = rig.to_test_captured()
    good = rig.app.state.deps.collect

    def boom(*a, **k):
        raise RuntimeError("ffmpeg broke")

    rig.app.state.deps.collect = boom
    assert rig.run_test(job_id) == "VERIFYING"
    assert rig.job(job_id)["verdict"] is None

    rig.app.state.deps.collect = good
    assert rig.run_test(job_id) == "PASSED"


def test_restart_makes_unfinished_steps_retryable(rig):
    job_id = rig.api.post("/jobs", json={}).json()["id"]
    rig.upload(job_id, "symptom")
    deps = rig.app.state.deps
    with deps.engine.begin() as db:
        db.exec_driver_sql(
            "INSERT INTO steps (job_id, step, status) VALUES (?, 'triage', 'running')", (job_id,)
        )
    make_engine(deps.cfg.db_path)  # what a new process does
    assert rig.job(job_id)["steps"][0]["status"] == "error"
    rig.api.post(f"/jobs/{job_id}/triage", json={})
    rig.drain()
    assert rig.job(job_id)["state"] == "CHECK_REQUESTED"


def test_customer_data_never_uses_the_contributor_model(rig):
    job_id = rig.api.post("/jobs", json={"data_class": "customer"}).json()["id"]
    assert json.loads(rig.upload(job_id, "symptom").text)["kind"] == "symptom"
    rig.api.post(f"/jobs/{job_id}/triage", json={})
    rig.drain()
    assert rig.job(job_id)["state"] == "CHECK_REQUESTED"
    with rig.client.ledger._db as db:
        models = {m for (m,) in db.execute("SELECT model FROM cost_ledger")}
    assert models == {rig.app.state.deps.cfg.reasoning_model}
