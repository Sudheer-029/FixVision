# ADR-0008: One fault (F1), a 9 V battery rig, and flow as speed relative to the healthy baseline

- **Status:** Accepted
- **Date:** 2026-11-01
- **Pillars affected:** Reliability, Operational excellence

## Context
Building the real rig on 2026-11-01 changed three assumptions:

1. **Supply.** Only a 9 V battery was available, not 4×AA or USB. A weak-supply fault (fresh against drained batteries) cannot be staged on demand with one battery, and the battery itself weakens with use: healthy fills slowed from about 26 s to about 34 s in an hour.
2. **Leak.** A pinhole in the narrow hose did not leak visibly under pressure, so a "leaking joint" could not be staged reliably.
3. **Container.** There is no measuring jug. The receiver is a tall jar with a string line at a fixed height; its volume is unknown.

## Decision
- Scope is **F1 blocked inlet** only. Anything else (including a weak supply) is `unknown` → `INCONCLUSIVE`, escalate.
- Flow is judged as **speed relative to the healthy rig**: `speed = baseline_fill_s / video_fill_s`, pass at ≥ 80%, fail below 60% (the same factors as before). No litres are claimed, so the jar's volume does not matter.
- Supply values are `battery_9v` and `usb_5v`. Every `battery_9v` record lists that the battery weakens with use in `uncertainties[]`.
- C3 (no leak) stays as a regression check on the hose.
- The baseline comes from the two healthy clips recorded in the same session as the faulty and repaired clips, not from later runs, because later runs would be on a weaker battery.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Keep F2/F3, re-record with new hardware | Broader scope | No time before the deadline; F3 needs a second battery or supply |
| Keep litres with an assumed volume | Familiar unit | Claims a number nobody measured |
| Relative speed, one fault (chosen) | Honest with this rig; same thresholds; works with any container | One fault; battery fade narrows the margin between healthy and repaired |

## Consequences
- The demo covers PASSED, FAILED and INCONCLUSIVE with one fault plus recorded trick clips (pump never switched on, pump hidden).
- The battery fade is a stated limitation. The repaired clip sits close to the pass line, so it may come out INCONCLUSIVE; thresholds are not changed to make it pass.
- Earlier commits still describe F2/F3; this ADR supersedes those parts of spec v0.2.
