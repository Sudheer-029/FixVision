# ADR-0001: Verdicts are decided by deterministic rules, not by a model

- **Status:** Accepted
- **Date:** 2026-10-27
- **Pillars affected:** Reliability, Security, Operational excellence

## Context
A model asked "does this look fixed?" can be fooled (pump switched off, pump hidden) and cannot be audited. Judges and service managers need to know why a job passed.

## Decision
Models return observations with confidence and frame references. A rule engine in our code applies the checks in `VERIFICATION_SPEC.md` and returns Passed / Failed / Inconclusive with reasons.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| LLM-as-judge verdict | Fast to build | Unauditable, easy to fool, inconsistent |
| Rules over observations (chosen) | Auditable, testable, conservative | More engineering; thresholds need tuning |

## Consequences
Unit-testable verdict logic; thresholds must be set from a measured baseline; more Inconclusive results by design.
