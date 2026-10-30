---
name: meta-model-api
description: How to call Meta's Model API (Muse Spark, SAM 3.1, Voice Transcribe, Muse Image) correctly from Python in FixVision; use before writing or changing any code that calls a Meta model.
---

# Meta Model API (verified 2026-10-27; source of truth: docs/META_API_NOTES.md and https://dev.meta.ai/docs)

## Client
- Base URL `https://api.meta.ai/v1`, key in `MODEL_API_KEY`. Use the `openai` Python SDK with `base_url` and pass `api_key` explicitly (the SDK will not read MODEL_API_KEY).
- All calls go through `backend/app/clients/meta_client.py` (retries, timeouts, cache, cost ledger, spend limit). Never call the SDK directly elsewhere.

```python
client = OpenAI(base_url=settings.model_api_base_url, api_key=settings.model_api_key)
r = client.responses.create(model="muse-spark-1.3", input=[...])
```

## Models
| ID | Use |
|---|---|
| `muse-spark-1.3` | Reasoning, video understanding, observations |
| `muse-spark-1.3-contributor` | Cheap; content may train Meta models → staged rig data only |
| `sam-3.1` | Segmentation + tracking (no diagnosis) |
| `muse-voice-transcribe-1.0` | `POST /v1/asr/transcribe` (multipart) |
| `muse-image-1.0` | Optional images |
Do not use `muse-wonder-1.0` (coding model). Check availability with `GET /v1/models`.

## Video to Muse Spark
Upload with Files API (`purpose="user_data"`), then reference `file_id` in an `input_video` (or `input_file`) content block, or pass `video_url`. MP4. Embedded audio is read too. Token cost of video is undocumented: log `usage` for every call.

## Structured output
Chat Completions: `response_format={"type":"json_schema","json_schema":{"name":..., "schema":...}}` or `client.beta.chat.completions.parse(..., response_format=PydanticModel)`. Responses API: `text={"format": {...}}`. No recursive schemas; nesting ≤ 10. Use `strict: true` only with additionalProperties false and all properties required.

## SAM 3.1
- `POST /v1/responses`, `model="sam-3.1"`, `stream=True`. One user message: `input_text` (prompt) + one media part (`input_image` {image_url} or `input_video` {video_url | file_id}).
- Concept prompt = one short noun phrase ("water stream"). No lists, negation, or spatial words.
- Box/point prompts: `<0f>` frame marker + `<|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>` (pixels; w/h = media size). ≤ 16 objects.
- `metadata`: `include_confidence: "true"`, `propagation_direction` (`both`|`forward`|`backward`), `mask_encoding`.
- Output: `response.output_text.delta` lines; each record `<Nf>ordinal<|box;...|><|mask;...|>`; frames may be out of order → sort. Parsers: `meta-sam-parser` (pip), `@meta-sam/parser` (npm).
- Empty output = no match (not an error). 400 = fix prompt; never retry unchanged.
- Video: MP4/MOV (H.264/H.265/MPEG-4), ≤ 15,000 frames. Cost $0.20 / 1,000 frames (min 50 per request) → sample frames (SAM_SAMPLE_FPS) and trim first.

## Voice
WAV mono 16-bit PCM at 16 or 24 kHz (`ffmpeg -i in -ac 1 -ar 24000 -c:a pcm_s16le out.wav`), ≤ 10 min / 32 MB. Multipart fields `request` (JSON: mode, model, audioEncoding "WAV", languageBias ["Hindi","English"], keywords) and `audio`. Response JSON has `transcript`.

## Prices (for the cost ledger)
Muse Spark standard $1.25 / $4.25 per 1M in/out ($0.15 cached in); contributor $0.10 / $0.20; SAM video $0.20 per 1k frames, images $2.50 per 1k; Voice $0.18 per hour; Muse Image $0.01 per image.

## Errors
429 / 5xx → exponential backoff; 400 → do not retry; 404 `model_not_found` → wrong id or no access.

## Open weights
Baseten: `meta-models/muse-spark-open-1026` (OpenAI-compatible). Fireworks: base URL `https://api.fireworks.ai/inference/v1`; model id from the Fireworks docs.
