# ADR-0011: Final hackathon scope

- **Status:** Accepted
- **Date:** 2026-11-03
- **Pillars affected:** Security, Operational excellence

## Context
The plan included a LlamaFirewall guard layer, a case library, Baseten and Fireworks models, and a hosted deployment. The submission needs a public repo and a demo video, with only work that was really built. The Meta Model API has no guard model (`GET /v1/models`, 2026-11-03), so LlamaFirewall would need a separate local model download.

## Decision
- No guard layer. Untrusted text can reach Muse Spark, but answers must match a strict schema and verdicts come only from deterministic rules, so a model can never output a verdict directly.
- No case library: with so few jobs it could not retrieve anything useful.
- No Baseten, Fireworks or image models in the product flow.
- Local only: the API has no login, so it stays off public URLs.
- Evals are reported on the development clips as exploratory, because there is no held-out split.

## Consequences
- A prompt injection could still distort triage text or observations, and a false observation can affect a verdict. Every required check must still pass, but this risk is not scanned for.
- A real deployment needs login, a manager role and an injection review first.
