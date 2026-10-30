# ADR-0006: Fine-tune a Muse open-weight model on Fireworks as the test observer (stretch)

- **Status:** Proposed (stretch goal)
- **Date:** 2026-10-28
- **Pillars affected:** Cost optimization, Performance efficiency, Reliability

## Context
The `observe_test` step returns a fixed set of observations (the list in VERIFICATION_SPEC §4.1) in strict JSON. It is called on every test clip, so its cost and consistency matter. We have $100 of Fireworks credit, and Fireworks supports training and serving Muse open-weight models.

## Decision
If T1–T10 are complete by Mon Nov 2 midday IST, fine-tune a Muse open-weight model on Fireworks using **dev-split** labeled observations only, serve it through Fireworks inference, and compare base vs fine-tuned vs Muse Spark 1.3 on the **test split** (false passes, observation accuracy, latency, cost per job). The verification engine stays unchanged: the tuned model only supplies observations.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Muse Spark 1.3 only | Strongest model, no training work | Higher cost per job |
| Prompt optimization only (prompt-ops) | Cheap, fast | Less control over output format |
| Fine-tuned open model on Fireworks (chosen, stretch) | Cheaper, consistent JSON, qualifies as open-weight use | Needs enough labeled data; risk of overfitting to staged rig |

## Consequences
- Requires a clean dev/test split by recording session, and no test clips in training data.
- The model is adopted only if it does not increase false passes on the test split.
- With a small, staged dataset, results are reported as exploratory.
