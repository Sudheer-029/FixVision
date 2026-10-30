---
description: T4 - SAM 3.1 perception service and signals
---
Use the meta-model-api skill. Read docs/components/perception-sam.md and the SAM section of docs/META_API_NOTES.md.

Implement `backend/app/perception/`:
- `frames.py`: ffmpeg trim + sample at SAM_SAMPLE_FPS, transcode to H.264 MP4 if needed, extract audio WAV (mono 24 kHz).
- `sam.py`: concept prompts one per request, only on the windows in perception-sam.md (`pump` on the first 5 s; `measuring jug`, `hose joint`, `water stream` on the whole test clip; `intake` on the F1 close-up), plus an optional `<0f>` point prompt for the joint when the technician tapped it; `include_confidence: "true"`; stream and parse (use `meta-sam-parser` if it installs, else a small parser for `<Nf>` records); sort frames by marker; cache by content hash.
- `signals.py`: per-concept presence timelines in seconds from clip start (+ sample interval; `None` when the request errored, empty list when there was no match), returned in the model the verification engine accepts (spec §4.2). Windowed values are derived by the engine, not here.
Empty SAM output = 0 signal, not an error.

Tests on saved stream fixtures (record 1–2 real responses into `backend/tests/fixtures/sam/`, strip nothing secret). Add `scripts/perceive.py <clip.mp4>` printing signals and cost.
Run /check, commit `feat: T4 SAM 3.1 perception and signals`.
