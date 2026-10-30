---
description: T8 - guard layer, measurement input, voice input
---
Read docs/components/guard-layer.md, measurement.md and voice-input.md. Use the llm-agent-guardrails skill if available.

- Guard: LlamaFirewall PROMPT_GUARD (+ HIDDEN_ASCII) on transcripts, free text and retrieved case text; scope rules (unsupported equipment, mains, gas, pressure) → refusal; guidance must contain stop conditions. Fail closed for guidance. If llamafirewall cannot install, implement the scope rules and leave the scanner behind a feature flag, and record that in an ADR (/adr).
- Measurement: fields and validation per measurement.md. Flow is computed by the verification engine from video times (ADR-0007); the typed fill time is only the cross-check.
- Voice: ffmpeg → WAV mono 24 kHz → /v1/asr/transcribe with languageBias Hindi, English and keywords.
Tests: 20-string injection red-team set, measurement validation, voice request shape (mocked).
Run /check, commit `feat: T8 guard, measurement and voice`.
