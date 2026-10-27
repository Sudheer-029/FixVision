# Product

**Status:** v0.1 (2026-10-27)

## One line

FixVision is an evidence-backed repair verification system: it guides a technician through diagnosing a supported pump fault and refuses to close the job until a functional test passes with sufficient evidence.

## Problem

- Service managers sign off repairs they did not see. Job reports are often a photo and a note.
- A "fixed" photo can be misleading: a leak disappears when the pump is off; a motor spins but under-performs.
- Repeat visits and disputed reports cost time and money. *(Hypothesis to validate, not a measured saving.)*

## Primary user

**Field technician** servicing small water pumps, with a **service manager** who approves completed jobs.

## Workflow

1. Technician starts a job, identifies the equipment, records the symptom and describes it by voice.
2. FixVision highlights the relevant component and asks for one targeted diagnostic check.
3. FixVision gives guidance from the approved pump guide, step by step, with technician approval and stop conditions.
4. After the repair, the technician runs the guided functional test (timed flow + leak check while running).
5. FixVision issues Passed / Failed / Inconclusive with a service record.
6. The manager reviews and approves; approved records enter the case library.

## Why Meta's models

- **Muse Spark** reasons over video, speech and documents in one model and returns structured observations.
- **SAM 3.1** turns "look at the joint" into a tracked, measurable region across frames.
- **Voice Transcribe** handles Hindi and English with code-switching.

## Out of scope (hackathon)

Home DIY use, mains-voltage equipment, other equipment families, automatic accuracy improvement claims, payments, multi-tenant accounts.

## Business hypotheses (to validate after the hackathon)

| Hypothesis | How we would test it |
|---|---|
| Service managers will pay for verified job records | 5 interviews with pump service companies |
| Verified records reduce repeat visits | Pilot with one company, compare repeat-visit rate |
| Equipment makers want verified field data | Talk to 2 pump manufacturers |

Pricing idea: per verified job or per technician seat. Later: other equipment families, insurer and warranty workflows.

## Future vision (not in demo)

Hands-free capture on smart glasses; more equipment families; supervised case library feeding retrieval and evaluation.
