---
description: T3 - verification engine (the core), fully tested
---
Use the fixvision-rules skill. Read docs/VERIFICATION_SPEC.md, docs/components/verification-engine.md and ADR-0007.

Implement in `backend/app/verification/` (pure Python, no network, no model calls):
- `schema.py`: Pydantic models for JobEvidence (observations from spec §4.1 with value/confidence/t[] in seconds, SAM presence timelines from §4.2, technician inputs, conditions, equipment, fault hypothesis, job token), CheckResult, Verdict (exact output schema in spec §8), Thresholds.
- `thresholds.py`: load `config/rig_baseline.yaml`, compute flow_pass/flow_fail from baseline, fill_time_tolerance, confidence threshold, version string.
- `signals.py`: derive visible_s, stream_ratio, jug_ratio_fill, joint_in_view_s and intake_visible_s from presence timelines and the run window; a missing timeline (SAM error) gives a missing value, never zero.
- `checks.py`: c0_preconditions, c1_running, c2_flow (flow from video times, typed time as cross-check), c3_no_leak, c4_cause_addressed — each returns pass | fail | insufficient_evidence + evidence refs + human-readable detail.
- `engine.py`: `verify(evidence, thresholds) -> Verdict` with the ordered steps in spec §2 (scope incl. missing baseline → preconditions → observed failure → evidence sufficiency → passed), required checks per fault, regression checks, reasons, uncertainties (the battery note on every F3 job), requested_actions.

Tests in `backend/tests/verification/`: table-driven boundaries for every check; every adversarial case in spec §7 as a named fixture; a property test (hypothesis) that PASSED never occurs when any required check is insufficient or any check fails. 100% branch coverage (`pytest --cov=app/verification --cov-branch`).
Also add `scripts/verify_json.py` that reads an evidence JSON file and prints the verdict.
Run /check, commit `feat: T3 verification engine with adversarial tests`.
