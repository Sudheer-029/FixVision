"""The one place FixVision calls the Meta Model API (ADR-0003).

Adds retries, a 60 s timeout, a content-hash disk cache, a SQLite cost ledger
and the daily spend limit on top of the OpenAI SDK (Responses, Files) and httpx (voice).
"""

import base64
import hashlib
import json
import mimetypes
import sqlite3
import subprocess
import time
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import openai

from app.config import Settings, settings

TIMEOUT_S = 60.0
VOICE_MODEL = "muse-voice-transcribe-1.0"

# USD per unit, from docs/META_API_NOTES.md (2026-10-27)
PRICES: dict[str, dict[str, float]] = {
    "muse-spark-1.3": {"input": 1.25e-6, "cached_input": 0.15e-6, "output": 4.25e-6},
    "muse-spark-1.3-contributor": {"input": 0.10e-6, "cached_input": 0.10e-6, "output": 0.20e-6},
    "sam-3.1": {"frame": 0.20e-3, "min_frames": 50, "image": 2.50e-3},
    VOICE_MODEL: {"audio_hour": 0.18},
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


class SpendLimitExceeded(RuntimeError):
    pass


@dataclass
class CallResult:
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    latency_ms: int = 0
    cached: bool = False

    def json(self) -> Any:
        return json.loads(self.text)

    @property
    def lines(self) -> list[str]:
        return [line for line in self.text.splitlines() if line.strip()]


def estimate_cost(model: str, usage: dict[str, Any]) -> float:
    p = PRICES.get(model)
    if p is None:
        return 0.0
    if model == "sam-3.1":
        if usage.get("images"):
            return usage["images"] * p["image"]
        return max(usage.get("frames", 0), p["min_frames"]) * p["frame"]
    if model == VOICE_MODEL:
        return usage.get("audio_ms", 0) / 3_600_000 * p["audio_hour"]
    cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0
    fresh = usage.get("input_tokens", 0) - cached
    return (
        fresh * p["input"]
        + cached * p["cached_input"]
        + usage.get("output_tokens", 0) * p["output"]
    )


def _status(exc: Exception) -> int | None:
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code
    return None


def is_retryable(exc: Exception) -> bool:
    status = _status(exc)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, openai.APIConnectionError | httpx.TransportError)


def with_retries[T](
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Exponential backoff (1, 2, 4 s) on 429 / 5xx / connection errors; 400s raise at once."""
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts - 1 or not is_retryable(exc):
                raise
            sleep(base_delay * 2**attempt)
    raise AssertionError("unreachable")


class Ledger:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS cost_ledger (
                ts TEXT NOT NULL, job_id TEXT, component TEXT, model TEXT NOT NULL,
                latency_ms INTEGER, usage_json TEXT, est_cost_usd REAL NOT NULL,
                cached INTEGER NOT NULL)"""
        )

    def record(self, *, job_id: str | None, component: str, model: str, result: CallResult) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO cost_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    job_id,
                    component,
                    model,
                    result.latency_ms,
                    json.dumps(result.usage),
                    result.cost_usd,
                    int(result.cached),
                ),
            )

    def spent_today(self) -> float:
        today = datetime.now(UTC).date().isoformat()
        (total,) = self._db.execute(
            "SELECT COALESCE(SUM(est_cost_usd), 0) FROM cost_ledger WHERE ts >= ?", (today,)
        ).fetchone()
        return total


class Cache:
    def __init__(self, directory: Path):
        self.dir = directory
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(*parts: Any) -> str:
        return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        path = self.dir / f"{key}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def put(self, key: str, value: dict) -> None:
        (self.dir / f"{key}.json").write_text(json.dumps(value))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_video_frames(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return int(out.strip())


class MetaClient:
    def __init__(
        self,
        cfg: Settings = settings,
        *,
        oa: Any = None,
        http: httpx.Client | None = None,
        ledger: Ledger | None = None,
        cache: Cache | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cfg = cfg
        # SDK retries off: ours are uniform across SDK and httpx calls and testable
        self.oa = oa or openai.OpenAI(
            base_url=cfg.model_api_base_url,
            api_key=cfg.model_api_key,
            timeout=TIMEOUT_S,
            max_retries=0,
        )
        self.http = http or httpx.Client(timeout=TIMEOUT_S)
        self.ledger = ledger or Ledger(cfg.ledger_path)
        self.cache = cache or Cache(cfg.cache_dir)
        self.sleep = sleep

    # -- shared plumbing ---------------------------------------------------

    def _call(
        self,
        *,
        model: str,
        cache_key: str,
        use_cache: bool,
        job_id: str | None,
        component: str,
        fn: Callable[[], tuple[str, dict[str, Any]]],
    ) -> CallResult:
        if use_cache and (hit := self.cache.get(cache_key)) is not None:
            result = CallResult(text=hit["text"], usage=hit["usage"], cached=True)
            self.ledger.record(job_id=job_id, component=component, model=model, result=result)
            return result
        spent = self.ledger.spent_today()
        if spent >= self.cfg.daily_spend_limit_usd:
            raise SpendLimitExceeded(
                f"Spent ${spent:.2f} today, limit ${self.cfg.daily_spend_limit_usd:.2f}"
            )
        start = time.monotonic()
        text, usage = with_retries(fn, sleep=self.sleep)
        result = CallResult(
            text=text,
            usage=usage,
            cost_usd=estimate_cost(model, usage),
            latency_ms=int((time.monotonic() - start) * 1000),
        )
        self.ledger.record(job_id=job_id, component=component, model=model, result=result)
        self.cache.put(cache_key, {"text": text, "usage": usage})
        return result

    # -- public API ----------------------------------------------------------

    def respond(
        self,
        model: str,
        input: str | list[dict[str, Any]],
        schema: dict[str, Any] | None = None,
        *,
        schema_name: str = "output",
        job_id: str | None = None,
        component: str = "",
        use_cache: bool = True,
    ) -> CallResult:
        kwargs: dict[str, Any] = {"model": model, "input": input}
        if schema is not None:
            kwargs["text"] = {
                "format": {"type": "json_schema", "name": schema_name, "schema": schema}
            }

        def fn() -> tuple[str, dict[str, Any]]:
            r = self.oa.responses.create(**kwargs)
            return r.output_text, (r.usage.model_dump() if r.usage else {})

        return self._call(
            model=model,
            cache_key=Cache.key("respond", kwargs),
            use_cache=use_cache,
            job_id=job_id,
            component=component,
            fn=fn,
        )

    def upload_file(self, path: str | Path, *, use_cache: bool = True) -> str:
        """Upload to the Files API (purpose user_data) and return the file id."""
        path = Path(path)
        # shortcut: assumes uploaded files never expire server-side; re-upload with use_cache=False
        key = Cache.key("upload", self.cfg.model_api_base_url, file_sha256(path))
        if use_cache and (hit := self.cache.get(key)) is not None:
            return hit["file_id"]

        def fn() -> str:
            with path.open("rb") as f:
                return self.oa.files.create(file=f, purpose="user_data").id

        file_id = with_retries(fn, sleep=self.sleep)
        self.cache.put(key, {"file_id": file_id})
        return file_id

    def sam_segment(
        self,
        media: str | Path,
        prompt: str,
        *,
        metadata: dict[str, str] | None = None,
        job_id: str | None = None,
        component: str = "perception",
        use_cache: bool = True,
    ) -> CallResult:
        """Stream SAM 3.1 over a local image or (already sampled) video; `.lines` = raw records.

        Frame sampling and trimming happen before this call (perception, T4): SAM bills
        every frame it receives.
        """
        path = Path(media)
        is_image = path.suffix.lower() in IMAGE_SUFFIXES
        model = self.cfg.segmentation_model
        meta = {"include_confidence": "true", **(metadata or {})}
        key = Cache.key("sam", model, file_sha256(path), prompt, meta)

        def fn() -> tuple[str, dict[str, Any]]:
            if is_image:
                mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
                data = base64.b64encode(path.read_bytes()).decode()
                part = {"type": "input_image", "image_url": f"data:{mime};base64,{data}"}
                usage: dict[str, Any] = {"images": 1}
            else:
                part = {"type": "input_video", "file_id": self.upload_file(path)}
                usage = {"frames": count_video_frames(path)}
            stream = self.oa.responses.create(
                model=model,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}, part],
                    }
                ],
                metadata=meta,
                stream=True,
            )
            chunks = []
            for event in stream:
                if event.type == "response.output_text.delta":
                    chunks.append(event.delta)
                elif event.type == "response.completed" and event.response.usage:
                    usage["reported"] = event.response.usage.model_dump()
            return "".join(chunks), usage

        return self._call(
            model=model,
            cache_key=key,
            use_cache=use_cache,
            job_id=job_id,
            component=component,
            fn=fn,
        )

    def transcribe(
        self,
        wav_path: str | Path,
        language_bias: Sequence[str] = ("Hindi", "English"),
        *,
        keywords: Sequence[str] = (),
        job_id: str | None = None,
        component: str = "voice",
        use_cache: bool = True,
    ) -> CallResult:
        """WAV (mono 16-bit PCM, 16 or 24 kHz) → transcript via POST /v1/asr/transcribe."""
        path = Path(wav_path)
        request = {
            "mode": "PUSH_TO_TALK",
            "model": VOICE_MODEL,
            "audioEncoding": "WAV",
            "languageBias": list(language_bias),
            "keywords": list(keywords),
        }
        with wave.open(str(path)) as w:
            local_ms = int(w.getnframes() / w.getframerate() * 1000)

        def fn() -> tuple[str, dict[str, Any]]:
            r = self.http.post(
                f"{self.cfg.model_api_base_url.rstrip('/')}/asr/transcribe",
                headers={"Authorization": f"Bearer {self.cfg.model_api_key}"},
                files={
                    "request": (None, json.dumps(request), "application/json"),
                    "audio": (path.name, path.read_bytes(), "audio/wav"),
                },
            )
            r.raise_for_status()
            body = r.json()
            return body["transcript"], {"audio_ms": body.get("audioDurationMs", local_ms)}

        return self._call(
            model=VOICE_MODEL,
            cache_key=Cache.key("asr", file_sha256(path), request),
            use_cache=use_cache,
            job_id=job_id,
            component=component,
            fn=fn,
        )
