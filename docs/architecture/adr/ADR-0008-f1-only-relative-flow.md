# ADR-0008: One fault (F1), a 9 V battery rig, and flow as speed relative to the healthy baseline

- **Status:** Accepted
- **Date:** 2026-11-01
- **Pillars affected:** Reliability, Operational excellence

## Context
The rig as built on 2026-11-01 has two constraints:

1. **Supply.** It runs on one 9 V battery, which weakens with use: healthy fills slowed from about 26 s to about 34 s in an hour.
2. **Container.** The receiver is a tall jar with a string line at a fixed height; its volume is unknown.

## Decision
- Scope is **F1 blocked inlet** only. Anything else is `unknown` → `INCONCLUSIVE`, escalate.
- Flow is judged as **speed relative to the healthy rig**: `speed = baseline_fill_s / video_fill_s`, pass at ≥ 80%, fail below 60%. No litres are claimed, so the jar's volume does not matter.
- Supply values are `battery_9v` and `usb_5v`. Every `battery_9v` record lists that the battery weakens with use in `uncertainties[]`.
- C3 (no leak) stays as a regression check on the hose.
- The baseline comes from the two healthy clips recorded in the same session as the faulty and repaired clips, not from later runs, because later runs would be on a weaker battery.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Litres with an assumed volume | Familiar unit | Claims a number nobody measured |
| Relative speed, one fault (chosen) | Honest with this rig; works with any container | One fault; battery fade narrows the margin between healthy and repaired |

## Consequences
- The recorded clips cover FAILED and INCONCLUSIVE with one fault plus trick clips (pump never switched on, pump hidden). PASSED is covered by automated tests.
- The battery fade is a stated limitation. The repaired clip sits close to the pass line, so it may come out INCONCLUSIVE; thresholds are not changed to make it pass.
