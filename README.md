# FixVision

**See it. Fix it. Verify it.**
Evidence-backed repair verification for small water pumps, built on Meta's models.

> Meta Global AI Developer Hackathon 2026 · Indie Developer track · Problem statement: *Push the Frontier* (manufacturing / physical systems)

FixVision helps field technicians diagnose supported water-pump faults and document whether a repair **passes defined functional checks**. Muse Spark interprets symptoms and retrieves approved repair guidance, while SAM 3.1 highlights and tracks the relevant components. After the repair, FixVision combines guided video capture with measured test results to produce an evidence-backed service record, or **refuses verification when the evidence is insufficient**.

It is not "a chatbot that knows repairs". It is a system that refuses to close a repair without sufficient evidence.

| | |
|---|---|
| Demo video | _link added at submission_ |
| Live app | _link added at submission_ |
| Repository | https://github.com/Sudheer-029/FixVision |
| Built | Oct 26 – Nov 4, 2026 (see [Built during the hackathon](#built-during-the-hackathon)) |

---

## What it does

1. **Capture the symptom.** The technician records a short video and describes the problem by voice (Hindi or English).
2. **Focus the inspection.** Muse Spark proposes likely causes and asks for one targeted diagnostic check. SAM 3.1 highlights and tracks the component being inspected.
3. **Guide the repair.** Step-by-step guidance from our approved pump guide, with technician approval and clear stop conditions.
4. **Run the functional test.** After the repair, a guided test: measured flow (timed fill) plus a visible leak check while the pump is running.
5. **Issue a verdict.** A deterministic verification engine decides **Passed**, **Failed** or **Inconclusive** from the test evidence, and produces a service record with before/after evidence, measurements, test conditions and unresolved uncertainty.

### Verdicts

| Verdict | Meaning |
|---|---|
| **Passed** | All required functional checks passed under the stated test conditions |
| **Failed** | The fault remains, or a required check failed |
| **Inconclusive** | Not enough evidence to decide (e.g., component not visible, pump not shown running). FixVision asks for a new recording instead of guessing |

FixVision never claims a machine is "proven fixed". It reports which checks passed under which conditions.

### Supported scope (hackathon)

One equipment family (small low-voltage DC submersible pumps), three staged faults:

| ID | Fault | Typical symptom |
|---|---|---|
| F1 | Blocked inlet | Pump runs, flow is low |
| F2 | Leaking hose joint | Water drips at the joint while running |
| F3 | Weak power supply | Pump runs, flow is low, inlet is clear |

All faults are staged on a safe, low-voltage rig. See [docs/RIG.md](docs/RIG.md).

## Meta models and what each one does

| Model | Job | Why it is necessary |
|---|---|---|
| `muse-spark-1.3` | Interprets symptom video + transcript, retrieves approved guidance, proposes causes, requests diagnostic checks, extracts observations from test videos | The only component that reasons over video, speech and documents together |
| `sam-3.1` | Segments and tracks the inspected component, water stream and joint region across frames | Gives frame-level, measurable evidence (visibility, stream presence, drip region) that the verification engine uses |
| `muse-voice-transcribe-1.0` | Hindi / English symptom descriptions | Technicians describe faults by voice, hands busy |
| Muse Spark Open (open weights, via Baseten) | Service-record drafting and an alternate reasoning backend for evals | Runs the eval loop cheaply on open weights |
| `muse-image-1.0` *(optional)* | Annotated step cards | Visual guidance |

The verdict itself is made by **our deterministic verification engine**, not by a model. Models produce observations with confidence; rules decide. See [docs/VERIFICATION_SPEC.md](docs/VERIFICATION_SPEC.md).

## Architecture

See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md).

```
Web app (guided capture) ──> API + job orchestrator ──> Guard layer (LlamaFirewall)
                                   │
          ┌────────────────────────┼─────────────────────────┐
     Reasoning agent         Perception (SAM 3.1)      Measurement input
     (Muse Spark 1.3)        masks, tracks, signals    timed fill, conditions
          └────────────────────────┼─────────────────────────┘
                                   ▼
                     Verification engine (rules, our code)
                                   ▼
               Service record ──> Technician review ──> Case library
```

## Quickstart

```bash
git clone https://github.com/Sudheer-029/FixVision.git
cd FixVision
cp .env.example .env        # add MODEL_API_KEY (and BASETEN_API_KEY if used)
# backend
cd backend && uv sync && uv run uvicorn app.main:app --reload
# frontend
cd ../frontend && npm install && npm run dev
```

Full setup: [docs/development/DEVELOPMENT.md](docs/development/DEVELOPMENT.md).

## Results

Measured on staged trials. See [docs/EVALS.md](docs/EVALS.md). _Filled in after Phase 3._

| Metric | Value |
|---|---|
| Trials | — |
| Correct Passed | — |
| False Passed (most important to keep at 0) | — |
| Correct Failed / Inconclusive | — |
| Median latency per job | — |
| Cost per job (USD) | — |

Faults are staged and the sample is small; numbers are reported as exploratory.

## Built during the hackathon

Everything in this repository was created between Oct 26 and Nov 4, 2026, except the third-party tools listed in [THIRD_PARTY.md](THIRD_PARTY.md).

**Ours:** the guided-capture web app, the job orchestrator, the reasoning and perception integrations, the verification engine and its rules, the service-record generator, the case library, the evaluation harness, the pump guide and test protocol, all documentation.

**Third-party (integrated, not built by us):** Meta's models via the Model API, LlamaFirewall (PurpleLlama), and optionally prompt-ops, synthetic-data-kit and Meta-Harness. Daily progress: [docs/HACKATHON_LOG.md](docs/HACKATHON_LOG.md).

## Documentation

| Doc | Purpose |
|---|---|
| [PRODUCT](docs/PRODUCT.md) | Problem, user, workflow, business hypotheses |
| [VERIFICATION_SPEC](docs/VERIFICATION_SPEC.md) | Test protocol and verdict rules (the core of FixVision) |
| [RIG](docs/RIG.md) | Demo rig, staged faults, safety |
| [ARCHITECTURE](docs/architecture/ARCHITECTURE.md) | System design, data flow, model roles |
| [WELL_ARCHITECTED](docs/architecture/WELL_ARCHITECTED.md) | Review against the AWS Well-Architected pillars |
| [ADRs](docs/architecture/adr/) | Architecture decision records |
| [Components](docs/components/) | One doc per component |
| [Development](docs/development/) | Setup, testing, deployment, runbook, security |
| [EVALS](docs/EVALS.md) | Evaluation method and results |
| [META_API_NOTES](docs/META_API_NOTES.md) | Verified Meta Model API facts used in the build |
| [BUILD_PLAN](docs/BUILD_PLAN.md) | Phased plan and task prompts |
| [DEMO_SCRIPT](docs/DEMO_SCRIPT.md) | The 3-minute demo |

## Safety and limits

- Supported equipment and faults only. Anything else returns **Inconclusive** with a recommendation to escalate.
- Low-voltage demonstration rig. FixVision does not guide mains-voltage, gas or high-pressure work.
- Guidance requires technician approval at each step and lists stop conditions.
- A verdict describes checks under stated conditions. It is not a guarantee of safe operation.

## License

MIT, see [LICENSE](LICENSE). Third-party components keep their own licenses, see [THIRD_PARTY.md](THIRD_PARTY.md).
