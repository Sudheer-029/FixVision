---
description: T2 - Meta Model API client, cost ledger and smoke test
---
Use the meta-model-api skill. Read docs/META_API_NOTES.md and docs/architecture/adr/ADR-0003-openai-sdk-client.md.

Implement `backend/app/clients/meta_client.py`:
- OpenAI SDK with `base_url=MODEL_API_BASE_URL`, `api_key=MODEL_API_KEY`.
- `respond(model, input, schema=None)` (Responses API; JSON-schema output when schema given), `upload_file(path)` (Files API, purpose user_data), `sam_segment(media, prompt, fps)` (streams SAM output, returns raw lines), `transcribe(wav_path, language_bias)` via httpx to `/v1/asr/transcribe`.
- Retries with exponential backoff on 429/5xx, never on 400; 60 s timeout.
- Content-hash cache on disk (`data/cache/`), skip with `use_cache=False`.
- Cost ledger: one SQLite row per call (job_id, component, model, latency_ms, tokens or frames, est_cost_usd) using prices from META_API_NOTES; refuse calls once DAILY_SPEND_LIMIT_USD is reached.
- `backend/app/clients/baseten_client.py` (OpenAI-compatible; base URL from Baseten docs, model BASETEN_MODEL) — leave a TODO if the base URL is unknown.

`scripts/smoke.py`: one call each to muse-spark-1.3 (text), muse-spark-1.3 with a short sample video from data/samples/, sam-3.1 on an image, voice transcribe on a 3 s WAV, Baseten if a key is set. Print model, latency, usage, estimated cost. Print the token usage of the video call clearly.

Tests: fixtures only (no network in CI) for retry logic, cache, ledger, spend limit.
Done when tests pass and `uv run python scripts/smoke.py` prints all calls OK. Run /check, commit `feat: T2 Meta API client and smoke test`.
