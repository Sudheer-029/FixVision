# ADR-0005: Case library uses retrieval of approved cases; no automatic accuracy claims

- **Status:** Accepted
- **Date:** 2026-10-27
- **Pillars affected:** Reliability, Operational excellence

## Context
A model approving its own repairs does not create reliable ground truth.

## Decision
Only technician- or manager-approved records enter the case library. The reasoning agent retrieves similar approved cases as context. Any claim of improvement (including prompt-ops or Meta-Harness runs) is reported only from the held-out test split.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Auto-learn from every verified job | Sounds impressive | Circular, unreliable |
| Retrieval of approved cases (chosen) | Honest, simple | Improvement is slower and must be measured |

## Consequences
Evals doc separates dev and test splits; improvement claims cite test-split numbers only.
