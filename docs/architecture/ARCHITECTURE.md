# Architecture

**Status:** v0.1 (2026-10-27) · Diagrams: generate with Archify from this document once code exists (`docs/architecture/diagrams/`).

## 1. Context

```
Technician (phone browser) ──HTTPS──> FixVision ──HTTPS──> Meta Model API (Muse Spark, SAM 3.1, Voice Transcribe)
Service manager (browser)  ──HTTPS──> FixVision ──HTTPS──> Baseten (Muse Spark Open, optional)
```

## 2. Containers

| Container | Tech | Responsibility |
|---|---|---|
| Web app | Next.js (mobile-first) | Guided capture, job timeline, verdict and record view, manager review |
| API | Python 3.12, FastAPI | REST endpoints, uploads, job state machine |
| Worker | Same codebase, async tasks | Calls models, runs perception and verification off the request path |
| Database | SQLite (hackathon) → Postgres later | Jobs, observations, verdicts, records, case library, traces, cost ledger |
| Media store | Local disk (hackathon) → object storage later | Clips, sampled frames, audio; retention limit |

## 3. Components

| Component | Doc | Model / logic |
|---|---|---|
| Capture web app | [capture-web-app](../components/capture-web-app.md) | — |
| Job orchestrator | [orchestrator](../components/orchestrator.md) | State machine |
| Guard layer | [guard-layer](../components/guard-layer.md) | LlamaFirewall + rules |
| Reasoning agent | [reasoning-agent](../components/reasoning-agent.md) | `muse-spark-1.3` |
| Perception service | [perception-sam](../components/perception-sam.md) | `sam-3.1` |
| Voice input | [voice-input](../components/voice-input.md) | `muse-voice-transcribe-1.0` |
| Measurement input | [measurement](../components/measurement.md) | Form + timer cross-check |
| Verification engine | [verification-engine](../components/verification-engine.md) | Deterministic rules |
| Service record | [service-record](../components/service-record.md) | Template + optional Muse Spark Open summary |
| Case library | [case-library](../components/case-library.md) | Approved records, retrieval |
| Evals harness | [evals-harness](../components/evals-harness.md) | Trial runner, metrics |

## 4. Job lifecycle

```
CREATED → SYMPTOM_CAPTURED → TRIAGED → CHECK_REQUESTED → CHECK_CAPTURED
        → GUIDANCE_ISSUED → REPAIR_REPORTED → TEST_CAPTURED → VERIFYING
        → PASSED | FAILED | INCONCLUSIVE → REVIEWED (approved | rejected)
FAILED or INCONCLUSIVE → (re-record or further repair) → TEST_CAPTURED
```

## 5. Data flow for verification

1. Test clip uploaded → ffmpeg samples frames at `SAM_SAMPLE_FPS` and extracts audio.
2. Perception: SAM 3.1 concept prompts (`pump`, `water stream`, `hose`, `measuring jug`) and a box prompt on the joint region chosen at check time → masks per frame → signals (visibility ratio per component, stream presence per frame).
3. Reasoning: Muse Spark receives the clip (Files API) + check list + signals and returns structured observations (`switch_on_shown`, `drip_at_joint`, `job_token_read`, `timer_visible`) each with confidence and frame references.
4. Measurement: technician-entered fill time and conditions.
5. Verification engine applies [VERIFICATION_SPEC](../VERIFICATION_SPEC.md) → verdict.
6. Service record generated; manager reviews.

## 6. Model roles (what each model must and must not do)

| Model | Does | Does not |
|---|---|---|
| Muse Spark 1.3 | Interpret symptoms, rank causes with evidence, request checks, extract observations, ground guidance in the approved guide | Issue the verdict, invent measurements |
| SAM 3.1 | Segment and track named components and the water stream | Judge whether something is faulty |
| Voice Transcribe | Transcribe | Interpret |
| Verification engine | Decide verdict from checks | Call any model |

## 7. Trust boundaries

- Untrusted: uploaded media, transcripts, technician free text, retrieved case text. All text passes the guard layer before reaching the reasoning prompt.
- Trusted: verification rules, thresholds, approved guide (repo-controlled).

## 8. Observability

Every model call logs: job id, component, model id, latency, input/output tokens or frames, estimated cost, outcome. Per-job trace view in the web app (useful for the demo and for debugging).

## 9. Deployment (hackathon)

Web app on Vercel; API + worker on Modal or Render; SQLite on a persistent volume. See [DEPLOYMENT](../development/DEPLOYMENT.md).
