# Component: Verification engine

**Purpose:** Apply `VERIFICATION_SPEC.md` to observations, signals and measurements and return a verdict.
**Code:** `backend/app/verification/` (pure Python, no network)

## Interface
`verify(job: JobEvidence, thresholds: Thresholds) -> Verdict`

## Design
- One function per check (`c0_preconditions`, `c1_running`, `c2_flow`, `c3_no_leak`, `c4_cause_addressed`), each returning `pass | fail | insufficient_evidence` + evidence refs + detail.
- Verdict combiner implements precedence from the spec.
- Thresholds loaded from `config/rig_baseline.yaml`, versioned.

## Tests (most important in the repo)
- Table-driven unit tests for every check boundary.
- Adversarial fixtures: switched off, joint hidden, low flow, reused video, unsupported equipment.
- Property: no path returns `PASSED` if any required check lacks evidence.
