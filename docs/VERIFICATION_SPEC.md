# Verification specification

**Status:** v0.1 (2026-10-27) · **Owner:** Sudheer Bishnoi

This is the core of FixVision. It defines the functional test, the evidence each check needs, and the rules that turn evidence into a verdict. The verdict is computed by deterministic code (`backend/app/verification/`). Models supply **observations with confidence**; they never issue the verdict.

## 1. Principles

1. **No evidence, no verdict.** Missing or low-confidence evidence produces **Inconclusive**, never a guess.
2. **Functional, not cosmetic.** A repair passes only on measured function under load (water flowing) plus the fault-specific check. A clean-looking still frame proves nothing.
3. **Stated conditions.** Every verdict names the conditions it was tested under (supply, duration, head height, water level).
4. **False Passed is the worst error.** Thresholds are tuned to keep false passes at zero, even at the cost of more Inconclusive results.
5. **Humans close the job.** A technician (or service manager) reviews and approves every record before it enters the case library.

## 2. Verdicts

| Verdict | Rule |
|---|---|
| `PASSED` | Every required check for the fault is `pass` |
| `FAILED` | At least one required check is `fail` and every required check has sufficient evidence |
| `INCONCLUSIVE` | Any required check is `insufficient_evidence`, or the test preconditions are not met |

Precedence: preconditions → evidence sufficiency → check results. A `fail` with insufficient evidence on another required check is still `INCONCLUSIVE`, with the failing check reported.

Each verdict includes `reasons[]`, `checks[]`, `conditions`, `uncertainties[]` and `requested_actions[]` (e.g., "Re-record with the hose joint in view").

## 3. Functional test protocol (after repair)

Recorded through the guided-capture screen in one continuous clip:

1. **Setup frame (≥ 3 s):** rig in view, pump submerged, outlet hose and joint visible, measuring jug visible, on-screen timer visible.
2. **Power on:** switch turned on in view.
3. **Run (≥ 20 s):** water stream visible from outlet into jug; camera holds on the joint region for ≥ 5 s while running.
4. **Timed fill:** fill the jug to the 500 mL mark; technician enters the fill time in seconds (timer visible in clip for cross-check).
5. **Power off:** switch turned off in view.

Test conditions captured as form fields: supply (fresh / used batteries or USB), outlet head height (cm), water level (cm above pump), ambient notes.

## 4. Checks

| Check ID | Applies to | Evidence | Pass | Fail | Insufficient evidence |
|---|---|---|---|---|---|
| `C0_preconditions` | all | Setup frame observations | Pump submerged, outlet, joint, jug and timer visible | — | Any of these not visible for ≥ 2 s |
| `C1_running` | all | SAM `water stream` mask present across run window; Muse Spark observation "pump running" | Stream present in ≥ 80% of sampled run frames | Stream present in < 10% of run frames while switch shown on | Run window < 20 s, or switch-on not shown, or stream signal between 10% and 80% |
| `C2_flow` | F1, F3 (and all, as regression) | Entered fill time `t` for 0.5 L; timer cross-check | `0.5 / t × 60 ≥ flow_pass_lpm` | `0.5 / t × 60 < flow_fail_lpm` | No time entered, timer not visible, or value between thresholds |
| `C3_no_leak` | F2 (and all, as regression) | SAM-tracked `hose joint` region during run; Muse Spark observation "drip at joint" with confidence | No drip observed with confidence ≥ 0.7 over ≥ 5 s of joint-in-view while running | Drip observed with confidence ≥ 0.7 while running | Joint visible < 5 s while running, or confidence < 0.7 either way |
| `C4_cause_addressed` | per fault | Fault-specific evidence (below) | Evidence present | Evidence contradicts repair | Evidence missing |

Fault-specific `C4`:

| Fault | Evidence required |
|---|---|
| F1 blocked inlet | Close-up of intake after repair, SAM `intake` mask with no occluding object |
| F2 leaking joint | Close-up of re-seated joint before power on |
| F3 weak supply | Supply recorded as fresh batteries / USB in conditions |

Required checks per fault: F1 → C0, C1, C2, C4 · F2 → C0, C1, C3, C4 · F3 → C0, C1, C2, C4. C2 and C3 also run as regression checks on every job when evidence exists; a regression `fail` makes the verdict `FAILED`.

## 5. Thresholds

Set from the **healthy baseline** measured on Day 1 (median of 5 healthy runs, stored in `config/rig_baseline.yaml`):

- `flow_pass_lpm = 0.8 × baseline_lpm`
- `flow_fail_lpm = 0.6 × baseline_lpm`
- Confidence threshold for model observations: `0.7` (tuned on the dev split only)

Thresholds are versioned; every record stores the threshold version used.

## 6. Adversarial cases the system must handle

| Case | Expected verdict | Why |
|---|---|---|
| Pump switched off, so the leak "disappears" | `INCONCLUSIVE` (C1 not shown) or `FAILED` (stream absent while switch shown on) | No functional evidence |
| Joint hidden by hand or out of frame | `INCONCLUSIVE` with request to re-record | C3 insufficient evidence |
| Pump runs but flow low (old batteries) | `FAILED` on C2 | Running is not performing |
| Video of a different / previous job reused | `INCONCLUSIVE` | Job token mismatch (see below) |
| Unsupported equipment | `INCONCLUSIVE`, escalate | Out of scope |

**Job token:** the capture screen shows a random 4-character code for each job; the technician holds it in view during the setup frame. Muse Spark reads it; mismatch → `INCONCLUSIVE`.

## 7. Output schema (summary)

```json
{
  "job_id": "uuid",
  "fault_hypothesis": "F1|F2|F3|unknown",
  "verdict": "PASSED|FAILED|INCONCLUSIVE",
  "checks": [{"id": "C2_flow", "result": "pass|fail|insufficient_evidence", "evidence": ["frame:123", "input:fill_time_s=21.4"], "detail": "1.40 L/min vs pass 1.28"}],
  "conditions": {"supply": "fresh_aa_x4", "head_cm": 20, "water_level_cm": 8},
  "uncertainties": ["Joint visible for 6.1 s only"],
  "requested_actions": [],
  "thresholds_version": "2026-10-28.1",
  "models": {"reasoning": "muse-spark-1.3", "segmentation": "sam-3.1"}
}
```

The full Pydantic models live in `backend/app/verification/schema.py`.
