# Component: Reasoning agent (Muse Spark 1.3)

**Purpose:** Interpret symptoms, propose causes with evidence, request a targeted check, give grounded guidance, and extract observations from test clips.
**Code:** `backend/app/agents/reasoning.py`, prompts in `backend/app/agents/prompts/` (versioned, `<!-- id: name.vN -->` header); end to end in `backend/app/pipeline.py` and `scripts/run_clip.py`

## Tasks and outputs (structured JSON)
| Task | Input | Output schema |
|---|---|---|
| `triage` | Symptom clip (file_id), transcript, equipment, retrieved approved cases | `causes[] {fault_id, likelihood, evidence[]}`, `requested_check {instruction, component_concept}` |
| `guidance` | Confirmed cause, approved pump guide | `stop_conditions[]`, `steps[] {text, component_concept, requires_approval}`, `cited_sections[]` (must be guide ids, else repair retry) |
| `observe_test` | Test clip or close-up (720p MP4 via Files API) | One typed slot per id in [VERIFICATION_SPEC §4.1](../VERIFICATION_SPEC.md) for that clip, turned into `observations[] {id, clip, value, confidence, t[]}`; confidence clamped to 0–1 |
| `observe_fill` | One jar frame per second, cropped with SAM's jar box, each labelled "frame i" | A label per frame (`not_filling`, `below_line`, `at_line`); code derives `fill_start_t` / `fill_line_t` ([ADR-0010](../architecture/adr/ADR-0010-fill-times-from-labelled-jar-frames.md)) |

## Rules
- Guidance only from `data/guides/pump_guide.md` and approved cases; cite section ids.
- Never output a verdict or a measurement it did not observe.
- The job token is not sent to the model; it reports what it reads and the engine compares.
- Unknown → say unknown with low confidence.

## Model and settings
`REASONING_MODEL` (`muse-spark-1.3`). Structured output via JSON schema; timeouts 60 s; retries on 429/5xx with backoff.

## Failure modes
Schema-invalid output → one repair retry, then step error; low confidence → observation recorded as insufficient.

## Tests
`tests/test_agents.py`: golden answers recorded from real rig clips in `tests/fixtures/agents/`, repair retry, label count, guide citations, token never in the prompt. Eval metrics in `EVALS.md`.
