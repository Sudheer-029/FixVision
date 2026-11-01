"""Perception on recorded SAM 3.1 responses from the rig (tests/fixtures/sam/)."""

import shutil
import subprocess
from pathlib import Path

import pytest
from openai import APIConnectionError

from app.clients.meta_client import CallResult
from app.perception import frames, sam
from app.perception.signals import perceive

FIX = Path(__file__).parent / "fixtures" / "sam"


def fixture(name: str) -> str:
    return (FIX / name).read_text()


def test_real_jar_masks_become_seconds():
    assert sam.presence_times(fixture("glass_jar_4frames.txt"), 10.0, 3) == [
        10.0,
        10.333,
        10.667,
        11.0,
    ]


def test_no_match_is_empty_not_missing():
    assert sam.presence_times(fixture("pump_no_match.txt"), 0.0, 3) == []


def test_garbled_stream_is_missing():
    assert sam.presence_times("<0f>0<|box;x1=1|>\n", 0.0, 3) is None


class FakeClient:
    def __init__(self, texts=None, error=None):
        self.texts, self.error, self.prompts = texts or {}, error, []

    def sam_segment(self, media, prompt, **_):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return CallResult(text=self.texts.get(prompt, ""), cost_usd=0.01)


@pytest.fixture
def no_ffmpeg(monkeypatch):
    monkeypatch.setattr(frames, "sample", lambda src, dst, *a, **k: Path(dst))


def test_perceive_builds_engine_timelines(tmp_path, no_ffmpeg):
    clip = tmp_path / "test.mp4"
    clip.write_bytes(b"x")
    closeup = tmp_path / "closeup.mp4"
    closeup.write_bytes(b"y")
    client = FakeClient(
        {"glass jar": fixture("glass_jar_4frames.txt"),
         "white pump": fixture("white_pump_closeup_3frames.txt")}
    )  # fmt: skip
    timelines, cost = perceive(client, clip, closeup, 3, tmp_path)
    assert timelines["test"]["jar"].times == [0.0, 0.333, 0.667, 1.0]
    assert timelines["closeup"]["intake"].times == [0.0, 0.333, 0.667]
    assert timelines["test"]["jar"].interval_s == pytest.approx(1 / 3)
    assert cost == pytest.approx(0.02)


def test_request_error_gives_no_timeline(tmp_path, no_ffmpeg):
    clip = tmp_path / "test.mp4"
    clip.write_bytes(b"x")
    client = FakeClient(error=APIConnectionError(request=None))
    timelines, cost = perceive(client, clip, None, 3, tmp_path)
    assert timelines == {"test": {"jar": None}} and cost == 0.0


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_sample_trims_and_resamples(tmp_path):
    src = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=4:size=160x120:rate=30",
         "-f", "lavfi", "-i", "sine=duration=4", "-c:v", "libx264", "-c:a", "aac", str(src)],
        check=True,
    )  # fmt: skip
    out = frames.sample(src, tmp_path / "s.mp4", fps=3, start=1, duration=2)
    assert frames.duration_s(out) == pytest.approx(2, abs=0.4)
    wav = frames.extract_audio(src, tmp_path / "a.wav")
    assert wav.read_bytes()[:4] == b"RIFF" and frames.duration_s(wav) == pytest.approx(4, abs=0.1)
