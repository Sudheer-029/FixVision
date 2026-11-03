# Component: Voice input

**Purpose:** Transcribe symptom descriptions in Hindi and English.
**Code:** `backend/app/jobs/steps.py` (`triage`), `backend/app/pipeline.py` (`voice_wav`), `MetaClient.transcribe`

The app records a voice note (tap to start and stop, or choose an audio file) and uploads it as media kind `voice`. The triage step converts it to WAV mono 16-bit 24 kHz with ffmpeg, then calls `POST /v1/asr/transcribe` with `languageBias: ["Hindi","English"]` and keywords (`pump`, `hose`, `flow`, `leak`). Max 10 minutes / 32 MB.

The transcript, with any typed note, goes to triage and into the service record. The app shows it on the next screen. A transcription failure fails the triage step, which can be retried.
