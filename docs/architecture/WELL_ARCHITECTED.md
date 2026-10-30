# Well-Architected review

**Framework:** AWS Well-Architected Framework (six pillars), applied as a review method; the agent design is also checked against the Generative AI Lens themes (model selection, guardrails, evaluation). FixVision does not have to run on AWS for this review to apply.

**Review dates:** end of Phase 2 and end of Phase 4. Status values: Met / Partial / Gap.

| Pillar | Design choice in FixVision | Evidence | Status | Next action |
|---|---|---|---|---|
| Operational excellence | Per-call traces, cost ledger, CI on every PR, runbook, ADRs | `RUNBOOK.md`, `adr/`, CI config | — | — |
| Security | Guard layer on all untrusted text, secrets only in env, least-privilege keys, media retention limit, no personal data in demo | `SECURITY.md`, `guard-layer.md` | — | — |
| Reliability | Timeouts, retries with backoff on 429/5xx, no retry on 400, idempotent job steps, Inconclusive instead of failure when a model is down | Component docs (failure modes) | — | — |
| Performance efficiency | Frame sampling, async worker, parallel SAM + Spark calls, cached responses for repeated clips | `ARCHITECTURE.md`, `EVALS.md` latency | — | — |
| Cost optimization | Daily spend limit, cost per job tracked, contributor-mode models for staged eval data, open weights for bulk runs, a small fine-tuned observer on Fireworks (if it matches accuracy) | `EVALS.md`, ADR-0004 | — | — |
| Sustainability | Sample only needed frames, trim clips to the test window, avoid recomputation via cache | Config defaults | — | — |

## Generative AI checks

| Theme | FixVision answer |
|---|---|
| Model selection | Each model has one necessary job (ADR-0002) |
| Grounding | Guidance only from the approved pump guide and approved cases |
| Guardrails | LlamaFirewall + stop conditions + scope limits |
| Human oversight | Technician approval per step; manager approval per record |
| Evaluation | Held-out trial set; false-pass rate is the headline metric |
| Data use | Contributor-mode models used only with staged rig data |
