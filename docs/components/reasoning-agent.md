# Component: Reasoning agent (Muse Spark 1.3)

**Purpose:** Interpret symptoms, propose causes with evidence, request a targeted check, give grounded guidance, and extract observations from test clips.
**Code:** `backend/app/agents/reasoning.py`, prompts in `backend/app/agents/prompts/`

## Tasks and outputs (structured JSON)
| Task | Input | Output schema |
|---|---|---|
| `triage` | Symptom clip (file_id), transcript, equipment, retrieved approved cases | `causes[] {fault_id, likelihood, evidence[]}`, `requested_check {instruction, component_concept}` |
| `guidance` | Confirmed cause, approved pump guide section | `stop_conditions[]`, `steps[] {text, component_concept, requires_approval}` |
| `observe_test` | Test clip (+ close-up clip for F1/F2), check list, SAM signals | `observations[] {id, clip, value, confidence, t[]}`, exactly the list in [VERIFICATION_SPEC §4.1](../VERIFICATION_SPEC.md); `t[]` in seconds from that clip's start |

## Rules
- Guidance only from `data/guides/pump_guide.md` and approved cases; cite section ids.
- Never output a verdict or a measurement it did not observe.
- The job token is not sent to the model; it reports what it reads and the engine compares.
- Unknown → say unknown with low confidence.

## Model and settings
`REASONING_MODEL` (`muse-spark-1.3`); evals may use `REASONING_MODEL_EVAL`. Structured output via JSON schema; timeouts 60 s; retries on 429/5xx with backoff.

## Failure modes
Schema-invalid output → one repair retry, then step error; low confidence → observation recorded as insufficient.

## Tests
Golden-file tests with recorded responses; eval metrics in `EVALS.md`.
