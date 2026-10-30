# Component: Verification engine

**Purpose:** Apply `VERIFICATION_SPEC.md` to observations, signals and measurements and return a verdict.
**Code:** `backend/app/verification/` (pure Python, no network)

## Interface
`verify(job: JobEvidence, thresholds: Thresholds) -> Verdict`

## Design
- Derives windowed values (`visible_s`, `stream_ratio`, `jug_ratio_fill`, `joint_in_view_s`, `intake_visible_s`) from SAM presence timelines once the run window is known (spec §4.2). A missing timeline gives a missing value, never zero.
- One function per check (`c0_preconditions`, `c1_running`, `c2_flow`, `c3_no_leak`, `c4_cause_addressed`), each returning `pass | fail | insufficient_evidence` + evidence refs + detail.
- Verdict combiner implements the ordered steps in spec §2: scope (incl. missing baseline) → preconditions → observed failure → evidence sufficiency → passed.
- Thresholds loaded from `config/rig_baseline.yaml`, versioned.

## Tests (most important in the repo)
- Table-driven unit tests for every check boundary.
- Adversarial fixtures, one per row of spec §7: never switched on, switched on with no flow, joint hidden, low flow, typed time disagrees with video, fill cut out / jug out of frame, reused video (token mismatch on test clip or close-up), unsupported equipment / unknown fault; plus missing baseline and SAM error (no timeline).
- Property: no path returns `PASSED` if any required check lacks evidence or any check fails.
