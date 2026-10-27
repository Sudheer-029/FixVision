# ADR-0004: Bulk evaluation on contributor-mode or open-weight models

- **Status:** Accepted
- **Date:** 2026-10-27
- **Pillars affected:** Cost optimization, Security

## Context
Evaluation runs repeat many calls. Contributor-mode Muse Spark costs $0.10/$0.20 per 1M tokens versus $1.25/$4.25 standard, but content may be used to train Meta models. Muse Spark Open runs on Baseten with partner credits and qualifies for the open-weights prize.

## Decision
Use contributor-mode models and/or Muse Spark Open (Baseten, `meta-models/muse-spark-open-1026`) for evaluation runs on staged rig data only. Use standard mode for anything that could contain personal or customer data.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Standard mode everywhere | Simplest data story | Higher cost |
| Contributor mode everywhere | Cheapest | Not acceptable for customer data |

## Consequences
A `data_class` flag (`staged` / `customer`) on each job selects the allowed model tier.
