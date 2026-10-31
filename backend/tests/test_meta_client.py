import json
import wave
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

from app.clients.meta_client import (
    Cache,
    CallResult,
    Ledger,
    MetaClient,
    SpendLimitExceeded,
    estimate_cost,
    with_retries,
)
from app.config import Settings

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "meta_responses.json").read_text())
REQ = httpx.Request("POST", "https://api.meta.ai/v1/responses")


def api_error(status: int) -> openai.APIStatusError:
    return openai.APIStatusError("err", response=httpx.Response(status, request=REQ), body=None)


class Usage(SimpleNamespace):
    def model_dump(self):
        return dict(vars(self))


class FakeResponses:
    def __init__(self, errors=()):
        self.errors = list(errors)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        if kwargs.get("stream"):
            return [
                SimpleNamespace(**e, response=SimpleNamespace(usage=None))
                for e in FIXTURES["sam_stream"]
            ]
        f = FIXTURES["respond"]
        return SimpleNamespace(output_text=f["output_text"], usage=Usage(**f["usage"]))


@pytest.fixture
def make_client(tmp_path):
    def make(errors=(), limit=10.0, http=None):
        cfg = Settings(model_api_key="test", daily_spend_limit_usd=limit)
        oa = SimpleNamespace(responses=FakeResponses(errors), files=SimpleNamespace(create=None))
        return MetaClient(
            cfg,
            oa=oa,
            http=http,
            ledger=Ledger(tmp_path / "ledger.sqlite"),
            cache=Cache(tmp_path / "cache"),
            sleep=lambda s: None,
        )

    return make


def ledger_rows(client):
    return client.ledger._db.execute(
        "SELECT component, model, est_cost_usd, cached FROM cost_ledger"
    ).fetchall()


# -- retries ----------------------------------------------------------------


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retries_then_succeeds_on_429_and_5xx(status):
    sleeps, calls = [], []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise api_error(status)
        return "ok"

    assert with_retries(fn, sleep=sleeps.append) == "ok"
    assert sleeps == [1.0, 2.0]  # exponential backoff


@pytest.mark.parametrize("status", [400, 401, 404])
def test_never_retries_client_errors(status):
    calls = []

    def fn():
        calls.append(1)
        raise api_error(status)

    with pytest.raises(openai.APIStatusError):
        with_retries(fn, sleep=lambda s: None)
    assert len(calls) == 1


def test_gives_up_after_max_attempts():
    calls = []

    def fn():
        calls.append(1)
        raise api_error(503)

    with pytest.raises(openai.APIStatusError):
        with_retries(fn, attempts=4, sleep=lambda s: None)
    assert len(calls) == 4


def test_retries_httpx_5xx():
    calls = []

    def fn():
        calls.append(1)
        if len(calls) == 1:
            raise httpx.HTTPStatusError("x", request=REQ, response=httpx.Response(502, request=REQ))
        return "ok"

    assert with_retries(fn, sleep=lambda s: None) == "ok"


def test_respond_retries_through_client(make_client):
    client = make_client(errors=[api_error(429)])
    r = client.respond("muse-spark-1.3", "hi")
    assert r.json() == {"ok": True}
    assert len(client.oa.responses.calls) == 2


# -- cache ------------------------------------------------------------------


def test_cache_hit_skips_network(make_client):
    client = make_client()
    first = client.respond("muse-spark-1.3", "hi")
    second = client.respond("muse-spark-1.3", "hi")
    assert not first.cached and second.cached
    assert second.text == first.text
    assert len(client.oa.responses.calls) == 1


def test_use_cache_false_calls_again(make_client):
    client = make_client()
    client.respond("muse-spark-1.3", "hi")
    client.respond("muse-spark-1.3", "hi", use_cache=False)
    assert len(client.oa.responses.calls) == 2


def test_cache_key_depends_on_schema(make_client):
    client = make_client()
    client.respond("muse-spark-1.3", "hi")
    client.respond("muse-spark-1.3", "hi", schema={"type": "object"})
    assert len(client.oa.responses.calls) == 2
    assert client.oa.responses.calls[1]["text"]["format"]["type"] == "json_schema"


# -- ledger and costs -------------------------------------------------------


def test_ledger_row_per_call_with_cost(make_client):
    client = make_client()
    client.respond("muse-spark-1.3", "hi", component="reasoning")
    client.respond("muse-spark-1.3", "hi", component="reasoning")  # cached
    rows = ledger_rows(client)
    expected = 600 * 1.25e-6 + 400 * 0.15e-6 + 200 * 4.25e-6
    assert rows[0][:2] == ("reasoning", "muse-spark-1.3")
    assert rows[0][2] == pytest.approx(expected)
    assert rows[1][2:] == (0.0, 1)


def test_sam_cost_minimum_and_images():
    assert estimate_cost("sam-3.1", {"frames": 10}) == pytest.approx(50 * 0.20e-3)
    assert estimate_cost("sam-3.1", {"frames": 90}) == pytest.approx(90 * 0.20e-3)
    assert estimate_cost("sam-3.1", {"images": 1}) == pytest.approx(2.5e-3)


def test_voice_and_unknown_model_cost():
    assert estimate_cost("muse-voice-transcribe-1.0", {"audio_ms": 3_600_000}) == 0.18
    assert estimate_cost("some-other-model", {"input_tokens": 10**6}) == 0.0


# -- spend limit --------------------------------------------------------------


def test_refuses_calls_once_limit_reached(make_client):
    client = make_client(limit=0.01)
    client.ledger.record(
        job_id=None, component="x", model="muse-spark-1.3", result=CallResult("", cost_usd=0.01)
    )
    with pytest.raises(SpendLimitExceeded):
        client.respond("muse-spark-1.3", "hi")
    assert client.oa.responses.calls == []


def test_cache_hits_still_served_over_limit(make_client):
    client = make_client(limit=0.01)
    client.respond("muse-spark-1.3", "hi")
    client.ledger.record(
        job_id=None, component="x", model="muse-spark-1.3", result=CallResult("", cost_usd=1.0)
    )
    assert client.respond("muse-spark-1.3", "hi").cached


# -- SAM and voice -------------------------------------------------------------


def test_sam_image_collects_stream_lines(make_client, tmp_path):
    img = tmp_path / "frame.png"
    img.write_bytes(b"\x89PNG fake")
    client = make_client()
    r = client.sam_segment(img, "pump")
    assert len(r.lines) == 2 and r.lines[0].startswith("<0f>")
    sent = client.oa.responses.calls[0]
    assert sent["stream"] is True
    assert sent["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,")
    assert sent["metadata"]["include_confidence"] == "true"
    assert r.usage["images"] == 1


def test_transcribe_posts_multipart(make_client, tmp_path):
    wav = tmp_path / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\0\0" * 24000 * 3)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json=FIXTURES["asr"])

    client = make_client(http=httpx.Client(transport=httpx.MockTransport(handler)))
    r = client.transcribe(wav)
    assert r.text == FIXTURES["asr"]["transcript"]
    assert seen["url"].endswith("/v1/asr/transcribe")
    assert b'"languageBias": ["Hindi", "English"]' in seen["body"]
    assert r.cost_usd == pytest.approx(3 / 3600 * 0.18)
