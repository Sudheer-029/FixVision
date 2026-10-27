# ADR-0003: Call the Meta Model API through the OpenAI SDK

- **Status:** Accepted
- **Date:** 2026-10-27
- **Pillars affected:** Operational excellence, Reliability

## Context
The Meta Model API at `https://api.meta.ai/v1` is OpenAI-compatible (Responses, Chat Completions) per the quickstart. The older `llama-api-client` SDK targets the Llama API.

## Decision
Use the official `openai` Python SDK with `base_url` and `api_key=MODEL_API_KEY`, wrapped in one `meta_client.py` module that adds retries, timeouts, cost logging and caching. Voice uses `httpx` against `/v1/asr/transcribe`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| `llama-api-client` | Meta-branded | Not documented for this API |
| Raw `httpx` everywhere | No dependency | Re-implements streaming, parsing |

## Consequences
One place to change models, retries and logging.
