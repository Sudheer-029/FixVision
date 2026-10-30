---
description: T3 - verification engine (the core), fully tested
---
Use the fixvision-rules skill. Read docs/VERIFICATION_SPEC.md and docs/components/verification-engine.md.

Implement in `backend/app/verification/` (pure Python, no network, no model calls):
- `schema.py`: Pydantic models for JobEvidence (observations with value/confidence/frames, SAM signals, measurements, conditions, fault hypothesis, job token), CheckResult, Verdict (exact output schema in spec §7), Thresholds.
- `thresholds.py`: load `config/rig_baseline.yaml`, compute flow_pass/flow_fail from baseline, version string.
- `checks.py`: c0_preconditions, c1_running, c2_flow, c3_no_leak, c4_cause_addressed — each returns pass | fail | insufficient_evidence + evidence refs + human-readable detail.
- `engine.py`: `verify(evidence, thresholds) -> Verdict` with required checks per fault, regression checks, precedence (preconditions → evidence sufficiency → results), reasons, uncertainties, requested_actions.

Tests in `backend/tests/verification/`: table-driven boundaries for every check; every adversarial case in spec §6 as a named fixture; a property test (hypothesis) that PASSED never occurs when any required check is insufficient. 100% branch coverage (`pytest --cov=app/verification --cov-branch`).
Also add `scripts/verify_json.py` that reads an evidence JSON file and prints the verdict.
Run /check, commit `feat: T3 verification engine with adversarial tests`.
