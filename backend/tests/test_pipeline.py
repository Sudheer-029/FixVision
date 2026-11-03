"""collect_evidence assembles what the rules judge: each result must land in the right field."""

import json
import subprocess
from pathlib import Path

import pytest

from app import pipeline
from app.clients.meta_client import CallResult
from app.config import Settings
from app.perception import frames
from app.verification.schema import Conditions, Timeline

FIX = Path(__file__).parent / "fixtures" / "agents"
JAR_BOX = (10.0, 10.0, 100.0, 100.0)
CLOSEUP = json.dumps(
    {
        "job_token_read": {"value": "R2C6", "confidence": 0.9, "t": [0.5]},
        "intake_clear": {"value": True, "confidence": 0.9, "t": [3.0]},
    }
)


class FakeClient:
    def __init__(self):
        self.components = []

    def upload_file(self, path):
        return "file-1"

    def respond(self, model, input, schema=None, component="", **_):
        self.components.append((component, model))
        name = {"observe_test": "observe_test_healthy_01.json",
                "observe_fill": "observe_fill_healthy_01.json"}.get(component)  # fmt: skip
        return CallResult(text=(FIX / name).read_text() if name else CLOSEUP)


@pytest.fixture
def collect(tmp_path, monkeypatch):
    """Runs collect_evidence with SAM and ffmpeg faked; `jar_box` decides if frames exist."""
    test_clip, closeup_clip = tmp_path / "test.mp4", tmp_path / "closeup.mp4"
    test_clip.write_bytes(b"test")
    closeup_clip.write_bytes(b"closeup")
    frame_files = [tmp_path / f"f{i:04d}.jpg" for i in range(35)]
    for f in frame_files:
        f.write_bytes(b"\xff\xd8")
    monkeypatch.setattr(frames, "for_model", lambda src, dst: Path(src))
    monkeypatch.setattr(frames, "crop_frames", lambda *a, **k: frame_files)
    monkeypatch.setattr(frames, "duration_s", lambda _: 40.0)

    def run(jar_box=JAR_BOX, closeup=True):
        jar = Timeline(times=[0.0, 1.0], interval_s=1.0)
        monkeypatch.setattr(
            pipeline,
            "perceive",
            lambda *a, **k: ({"test": {"jar": jar}}, {"jar": jar_box}, 0.02, {"jar": {}}),
        )
        client = FakeClient()
        collected = pipeline.collect_evidence(
            client,
            Settings(_env_file=None, cache_dir=tmp_path / "cache"),
            test_clip,
            closeup_clip if closeup else None,
            job_id="job-1",
            job_token="R2C6",
            fault="F1",
            fill_time_s=26.0,
            conditions=Conditions(supply="battery_9v", head_cm=2),
            model="the-model",
        )
        return collected, client

    return run


def test_results_land_in_the_right_evidence_fields(collect):
    collected, client = collect()
    ev = collected.evidence
    assert (ev.job_id, ev.job_token, ev.fault_hypothesis) == ("job-1", "R2C6", "F1")
    assert (ev.fill_time_s, ev.test_clip_duration_s) == (26.0, 40.0)
    assert ev.conditions.supply == "battery_9v" and ev.conditions.head_cm == 2
    assert ev.timelines["test"]["jar"].times == [0.0, 1.0]
    assert collected.sam_cost_usd == 0.02
    assert ev.observation("fill_start_t", "test", 0.0).value == 2.0
    assert ev.observation("fill_line_t", "test", 0.0).value == 28.0
    assert ev.observation("job_token_read", "test", 0.0).value == "K7M4"
    assert ev.observation("job_token_read", "closeup", 0.0).value == "R2C6"
    assert ev.observation("intake_clear", "closeup", 0.0).value is True
    assert {model for _, model in client.components} == {"the-model"}


def test_no_jar_box_means_no_fill_times(collect):
    collected, client = collect(jar_box=None)
    assert collected.evidence.observation("fill_line_t", "test", 0.0) is None
    assert "observe_fill" not in [c for c, _ in client.components]


def test_no_closeup_means_no_closeup_observations(collect):
    collected, client = collect(closeup=False)
    assert collected.evidence.observation("intake_clear", "closeup", 0.0) is None
    assert "observe_closeup" not in [c for c, _ in client.components]


def test_a_hung_ffmpeg_is_stopped(monkeypatch):
    monkeypatch.setattr(frames, "FFMPEG_TIMEOUT_S", 0.01)
    with pytest.raises(subprocess.TimeoutExpired):
        frames._run(["sleep", "1"])
