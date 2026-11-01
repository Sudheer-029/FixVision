# ADR-0009: SAM 3.1 only for parts it segments on the rig; Muse Spark observes the water flow

- **Status:** Accepted
- **Date:** 2026-11-01
- **Pillars affected:** Reliability

## Context
The spec had SAM 3.1 track `pump`, `hose`, `water stream` and `measuring jug`, and C1 ("is water flowing") used the share of run-window frames with a `water stream` mask. Running real SAM calls on the recorded clips (about 25 requests, about $0.25) gave:

| Prompt | Result |
|---|---|
| `glass jar` | masks on every frame, confidence ≈ 0.9 |
| `white pump` (close-up, pump out of the water) | masks on every frame |
| `water` | blobs for the water in the jar, bowl and bottle; not the falling stream |
| `jar`, `pump`, `water stream`, `hose`, `tube`, `bowl` | no masks, also at 1080p |

The stream and the hose are thin, clear water and plastic, and the pump sits behind the glass bowl. A stream-based C1 would make every clip Inconclusive.

## Decision
- SAM tracks `glass jar` on the test clip (C0 jar in view, C2 jar in view during the fill) and `white pump` on the close-up (C4 intake visible).
- C1 uses a new Muse Spark observation, `water_flowing` (bool, `t` = first moment water is seen flowing). `false` while switched on for ≥ 20 s is `fail`; missing, low confidence or a time outside the run window is `insufficient_evidence`.
- The pump being in view at the start comes from Muse Spark's `pump_submerged`; C3 (no leak) relies on `leak_at_hose` alone.
- Engine keys stay logical (`jar`, `intake`); the prompt strings live in `backend/app/perception/sam.py`, so a rig change only changes prompts.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Box prompt on the stream region | Keeps C1 in SAM | A box tracked over clear water can "find" a stream that is not there, the risky direction for false passes; untested |
| Keep SAM stream, accept Inconclusive | No change | Every job Inconclusive; useless |
| Muse Spark observes the flow (chosen) | Works on the rig; fail and missing evidence stay distinct | C1 now rests on a model observation with confidence, not a pixel measurement |

## Consequences
- SAM's role in the demo is narrower but real: the jar must stay in view while the flow is timed, and the intake must be visible in the close-up.
- `water_flowing` accuracy is measured on the dev split in EVALS, like every other observation.
- Prompts are rig-specific; a different rig re-checks them with `scripts/perceive.py`.
