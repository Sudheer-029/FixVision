---
description: T4 - SAM 3.1 perception service and signals
---
Use the meta-model-api skill. Read docs/components/perception-sam.md and the SAM section of docs/META_API_NOTES.md.

Implement `backend/app/perception/`:
- `frames.py`: ffmpeg trim + sample at SAM_SAMPLE_FPS, transcode to H.264 MP4 if needed, extract audio WAV (mono 24 kHz).
- `sam.py`: concept prompts (`pump`, `water stream`, `hose`, `measuring jug`, `intake`) one per request, and a box prompt for the joint region (`<0f>` + box token); `include_confidence: "true"`; stream and parse (use `meta-sam-parser` if it installs, else a small parser for `<Nf>` records); sort frames by marker.
- `signals.py`: visible_ratio per component, stream_present per frame, joint_in_view_s, intake_occlusion — returned as a Signals model the verification engine accepts.
Empty SAM output = 0 signal, not an error.

Tests on saved stream fixtures (record 1–2 real responses into `backend/tests/fixtures/sam/`, strip nothing secret). Add `scripts/perceive.py <clip.mp4>` printing signals and cost.
Run /check, commit `feat: T4 SAM 3.1 perception and signals`.
