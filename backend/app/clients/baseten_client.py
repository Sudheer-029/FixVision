"""Muse Spark Open on Baseten (ADR-0004), OpenAI-compatible Chat Completions.

Billed to Baseten partner credit, so ledger rows carry est_cost_usd = 0 and do not
count toward the Meta daily spend limit.
"""

import time
from typing import Any

import openai

from app.clients.meta_client import TIMEOUT_S, CallResult, Ledger, with_retries
from app.config import Settings, settings

BASETEN_BASE_URL = "https://inference.baseten.co/v1"


class BasetenClient:
    def __init__(self, cfg: Settings = settings, *, oa: Any = None, ledger: Ledger | None = None):
        self.cfg = cfg
        self.oa = oa or openai.OpenAI(
            base_url=BASETEN_BASE_URL,
            api_key=cfg.baseten_api_key,
            timeout=TIMEOUT_S,
            max_retries=0,
        )
        self.ledger = ledger or Ledger(cfg.ledger_path)

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        job_id: str | None = None,
        component: str = "",
    ) -> CallResult:
        start = time.monotonic()
        r = with_retries(
            lambda: self.oa.chat.completions.create(model=self.cfg.baseten_model, messages=messages)
        )
        result = CallResult(
            text=r.choices[0].message.content or "",
            usage=r.usage.model_dump() if r.usage else {},
            latency_ms=int((time.monotonic() - start) * 1000),
        )
        self.ledger.record(
            job_id=job_id, component=component, model=self.cfg.baseten_model, result=result
        )
        return result
