# ADR-0007: Flow is timed from the test clip; the typed fill time is only a cross-check

- **Status:** Accepted; units and names updated by [ADR-0008](ADR-0008-f1-only-relative-flow.md) (fill line instead of 500 mL, speed relative to the healthy baseline instead of L/min)
- **Date:** 2026-10-30
- **Pillars affected:** Reliability, Security

## Context
C2 (flow) was computed from a fill time the technician typed in, with "timer visible" as the only cross-check. The headline claim is "evidence-backed", and a typed number is not evidence: a faster time can simply be entered.

## Decision
Muse Spark returns two timed observations from the test clip, `fill_start_t` (first water enters the empty jug) and `fill_mark_t` (water reaches the 500 mL mark). Flow is computed from `fill_mark_t − fill_start_t`. The typed `fill_time_s` is kept as a cross-check: if it differs from the video time by more than 15%, or either is missing, C2 is `insufficient_evidence`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Typed time only (previous) | Simple, robust | Not evidence; easy to game |
| Read the on-screen timer at both moments | Uses a visible clock | Two OCR reads, worse with motion blur |
| Video timestamps from Muse Spark, typed cross-check (chosen) | Measured from the clip; disagreement is caught | Depends on Muse Spark timing accuracy; measured in evals |

## Consequences
- The test protocol requires the jug and outlet to stay in frame for the whole fill.
- EVALS reports agreement between video and typed times; if Muse Spark timing is too coarse on the dev split, the tolerance is revisited there, never on test.
