# Meta Model API notes (verified 2026-10-27)

Facts below were read from Meta's developer docs on 2026-10-27. Re-check before relying on them; links are the source of truth.

## Access

- Base URL: `https://api.meta.ai/v1` · Auth: `Authorization: Bearer $MODEL_API_KEY` ([quickstart](https://dev.meta.ai/docs/quickstart))
- OpenAI-compatible: use `pip install openai` with `base_url` set; pass `api_key` explicitly (the SDK does not read `MODEL_API_KEY`). Responses API, Chat Completions and Anthropic Messages are supported.
- List models: `GET /v1/models`.

```python
import os
from openai import OpenAI
client = OpenAI(base_url="https://api.meta.ai/v1", api_key=os.environ["MODEL_API_KEY"])
r = client.responses.create(model="muse-spark-1.3", input="Hello")
print(r.output_text)
```

## Models ([models](https://dev.meta.ai/docs/models))

| Model ID | Use in FixVision | Notes |
|---|---|---|
| `muse-spark-1.3` | Reasoning agent | Text, image, video, audio, PDF in; 1M context |
| `muse-spark-1.3-contributor` | Evals on staged rig data only | Much cheaper; content may be used to train Meta models |
| `sam-3.1` | Perception | Image/video segmentation and tracking via Responses API |
| `muse-voice-transcribe-1.0` | Voice symptoms | `POST /v1/asr/transcribe`; Hindi supported |
| `muse-image-1.0` | Optional step cards | Image generation/editing |
| `muse-wonder-1.0` | Not used | Coding / agentic model (not video generation) |

Open weights (not on Model API): Muse Spark Open, Muse Glimmer. Hackathon Baseten model ID: `meta-models/muse-spark-open-1026`.

## Pricing ([pricing](https://dev.meta.ai/docs/pricing-rate-limits))

| Model | Price |
|---|---|
| Muse Spark 1.3 standard | $1.25 / 1M input, $4.25 / 1M output, $0.15 cached input |
| Muse Spark contributor | $0.10 / 1M input, $0.20 / 1M output |
| SAM 3.1 video | $0.20 per 1,000 frames, minimum 50 frames per request |
| SAM 3.1 images | $2.50 per 1,000 images |
| Voice Transcribe | $0.18 per hour of audio |
| Muse Image | $0.01 per image |

How video input is tokenized for Muse Spark is not documented; measure on Day 1.
Rate limits (per team): Muse Spark 3,000 RPM / 4M TPM; SAM 3,000 RPM; Muse Image 150 RPM.

## SAM 3.1 ([segmenting](https://dev.meta.ai/docs/sam/segmenting))

- `POST /v1/responses`, `model: "sam-3.1"`, `stream: true` recommended.
- One user message: an `input_text` part (prompt) + one media part (`input_image` with `image_url`, or `input_video` with `video_url` or `file_id`).
- Concept prompt = a short noun phrase, one concept per request ("water stream", "hose", "pump"). Lists, negation and spatial phrasing are unreliable.
- Box / point prompts: `<0f>` frame marker + tokens like `<|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>`; up to 16 objects.
- Output streams `response.output_text.delta`; each record = box then mask, tagged with frame marker and ordinal. `metadata.include_confidence: "true"` adds confidence. Client libraries: `meta-sam-parser` (Python), `@meta-sam/parser` (npm).
- Video: MP4/MOV (H.264/H.265/MPEG-4), up to 15,000 frames; `metadata.propagation_direction`. Frames may arrive out of order.
- No matches → empty output (not an error). `400` = fix the prompt, do not retry unchanged.
- SAM does **segmentation and tracking only**; reasoning about faults is Muse Spark's job.

## Video to Muse Spark ([video understanding](https://dev.meta.ai/docs/video-understanding))

Upload via Files API (`POST /v1/files`, `purpose: "user_data"`), then reference by `file_id` (`input_video` / `input_file`), or pass `video_url`. MP4 supported. Embedded audio is read too.

## Structured output ([structured output](https://dev.meta.ai/docs/structured-output))

Chat Completions: `response_format={"type":"json_schema","json_schema":{"name":..., "schema":...}}`, or `client.beta.chat.completions.parse()` with Pydantic. Responses API: `text.format`. Recursive schemas are rejected.

## Voice ([speech-to-text](https://dev.meta.ai/docs/speech-to-text/))

`POST /v1/asr/transcribe`, multipart: `request` (JSON: `mode`, `model`, `audioEncoding`, optional `languageBias`, `keywords`) + `audio` (WAV, mono 16-bit PCM, 16 or 24 kHz). Max 32 MB / 10 minutes. Convert: `ffmpeg -i in.m4a -ac 1 -ar 24000 -c:a pcm_s16le out.wav`.
