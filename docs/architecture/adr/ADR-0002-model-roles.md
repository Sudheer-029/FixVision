# ADR-0002: One necessary job per Meta model

- **Status:** Accepted
- **Date:** 2026-10-27
- **Pillars affected:** Performance efficiency, Cost optimization

## Context
Feedback: "each model doing a necessary job, not just appearing in the pitch". SAM 3.1 segments and tracks; it does not diagnose.

## Decision
Muse Spark 1.3: reasoning and observations. SAM 3.1: segmentation and tracking signals for the verification engine. Voice Transcribe: speech input. Muse Spark Open: record drafting and eval backend. Muse Image optional. Muse Wonder not used (it is a coding/agentic model).

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Use every model visibly | Bigger pitch | Decorative usage hurts the "Use of Meta tooling" score |
| Muse Spark only | Simpler | Loses frame-level measurable evidence |

## Consequences
Each model's contribution is visible in the trace view and measurable in evals.
