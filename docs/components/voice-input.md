# Component: Voice input

**Purpose:** Transcribe symptom descriptions in Hindi and English.
**Code:** `backend/app/voice/`

Convert to WAV mono 16-bit 24 kHz with ffmpeg, then `POST /v1/asr/transcribe` with `languageBias: ["Hindi","English"]` and keywords (`pump`, `hose`, `leak`, `flow`). Max 10 minutes / 32 MB. `429` → backoff; `500` → retry once.

Output: transcript + duration, passed to the guard layer, then to triage.
