# ADR-0011: Final hackathon scope

- **Status:** Accepted
- **Date:** 2026-11-03
- **Pillars affected:** Security, Operational excellence

## Context
Decide what the submitted product includes, so the repo describes only what was really built. The Meta Model API has no guard model (`GET /v1/models`, 2026-11-03).

## Decision
- No guard layer. Untrusted text can reach Muse Spark, but answers must match a strict schema and verdicts come only from deterministic rules, so a model can never output a verdict directly.
- No case library: with so few jobs it could not retrieve anything useful.
- Only Muse Spark, SAM 3.1 and Voice Transcribe are in the product flow.
- Local only: the API has no login, so the app listens on this machine only.
- Evals are reported on the development clips as exploratory, because there is no held-out split.

## Consequences
- A prompt injection could still distort triage text or observations, and a false observation can affect a verdict. Every required check must still pass, but this risk is not scanned for.
- A real deployment needs login, a manager role and an injection review first.
