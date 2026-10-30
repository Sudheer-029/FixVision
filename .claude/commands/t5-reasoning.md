---
description: T5 - Muse Spark reasoning agent (triage, guidance, observe_test)
---
Use the meta-model-api and fixvision-rules skills. Read docs/components/reasoning-agent.md and docs/VERIFICATION_SPEC.md §3–4.

First write `data/guides/pump_guide.md` in our own words: sections with ids (G-F1, G-F2, G-F3, G-SAFETY) covering symptoms, causes, diagnostic check, repair steps, stop conditions for the 3–6 V mini pump faults F1–F3. No copied manual text.

Implement `backend/app/agents/`:
- prompts as files in `prompts/` (versioned, id in header).
- `triage(job)` → causes[] {fault_id, likelihood, evidence[]}, requested_check {instruction, component_concept}.
- `guidance(job, fault_id)` → stop_conditions[], steps[] {text, component_concept, requires_approval}, cited guide section ids.
- `observe_test(job, clip, signals)` → observations[] {id, value, confidence, frames[]} for switch_on_shown, pump_running, drip_at_joint, timer_visible, job_token_read, intake_clear.
- JSON-schema structured output; one repair retry on schema failure; model from REASONING_MODEL (or REASONING_MODEL_EVAL when job.data_class == "staged" and eval mode).
Never let the agent output a verdict.

Golden-file tests with recorded responses. Add `scripts/run_clip.py <test_clip> --fault F2 --fill-time 21.4 --supply fresh_aa_x4` that runs perception + observe_test + verification and prints the verdict.
Run /check, commit `feat: T5 reasoning agent and end-to-end CLI`.
