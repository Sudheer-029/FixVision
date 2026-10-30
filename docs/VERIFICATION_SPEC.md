# Verification specification

**Status:** v0.2 (2026-10-30) · **Owner:** Sudheer Bishnoi

This is the core of FixVision. It defines the functional test, the evidence each check needs, and the rules that turn evidence into a verdict. The verdict is computed by deterministic code (`backend/app/verification/`). Models supply **observations with confidence**; they never issue the verdict.

## 1. Principles

1. **No evidence, no verdict.** Missing or low-confidence evidence produces **Inconclusive**, never a guess.
2. **Functional, not cosmetic.** A repair passes only on measured function under load (water flowing) plus the fault-specific check. A clean-looking still frame proves nothing.
3. **Measured from the recording, not typed.** Every value a check depends on is read from the job's clips (the test clip, plus the post-repair close-up for F1/F2). Technician-entered values are cross-checks only ([ADR-0007](architecture/adr/ADR-0007-flow-timed-from-video.md)). The one declared value is the F3 supply type, which is always listed as an uncertainty (§5).
4. **Stated conditions.** Every verdict names the conditions it was tested under (supply, duration, head height, water level).
5. **False Passed is the worst error.** Thresholds are tuned to keep false passes at zero, even at the cost of more Inconclusive results.
6. **Humans close the job.** A technician (or service manager) reviews and approves every record before it enters the case library.

**Timeline:** every time is in **seconds from the start of its clip**, and every evidence reference names the clip: `test@12.4`, `closeup@3.1`. Perception and reasoning convert frame indices to this timeline before returning results.

## 2. Verdicts

| Verdict | Rule |
|---|---|
| `PASSED` | Every required check is `pass` and no check is `fail` |
| `FAILED` | Preconditions met and at least one required or regression check is `fail` |
| `INCONCLUSIVE` | Out of scope, no baseline, preconditions not met, or (with no check failed) any required check is `insufficient_evidence` |

The engine applies these steps in order and stops at the first that decides:

1. **Scope.** Unsupported equipment or `fault_hypothesis = unknown` → `INCONCLUSIVE`, requested action "Escalate to a senior technician". Missing or invalid `config/rig_baseline.yaml`, or `measured: false` → `INCONCLUSIVE`, reason "No rig baseline". No checks run.
2. **Preconditions.** `C0_preconditions` not `pass` → `INCONCLUSIVE`.
3. **Observed failure.** Any required or regression check `fail` → `FAILED`. A failure seen on video stands even if another check lacks evidence; those checks are listed in `uncertainties[]`.
4. **Evidence sufficiency.** Any **required** check `insufficient_evidence` → `INCONCLUSIVE`.
5. Otherwise → `PASSED`.

Regression checks (§5) with insufficient evidence never change the verdict; they are listed in `uncertainties[]`.

Each verdict includes `reasons[]`, `checks[]`, `conditions`, `uncertainties[]` and `requested_actions[]` (e.g., "Re-record with the hose joint in view").

## 3. Functional test protocol (after repair)

**Post-repair close-up (F1 and F2 only, ≤ 10 s, recorded before the test clip):** job token in view, then the intake (F1) or the re-seated joint (F2) in close-up.

**Test clip**, one continuous recording:

1. **Setup (≥ 3 s):** rig in view, pump submerged, outlet hose and joint visible, measuring jug visible, on-screen timer visible, **job token held in view**.
2. **Power on:** switch turned on in view.
3. **Run (≥ 20 s):** water stream visible from outlet into jug; camera holds on the joint region for ≥ 5 s while running.
4. **Timed fill:** jug and outlet stay in frame from the first water entering the empty jug until the 500 mL mark. The technician also types the fill time as a cross-check.
5. **Power off:** switch turned off in view.

Test conditions captured as form fields: supply (`fresh_aa_x4`, `used_aa_x4`, `usb_5v`), outlet head height (cm), water level (cm above pump), ambient notes.

## 4. Evidence

### 4.1 Observations (Muse Spark, `observe_test`)

The canonical list. Every other doc refers here. Each observation is `{id, clip, value, confidence, t[]}`; `t[]` are seconds on that clip's timeline.

| ID | Clip | Value | Used by |
|---|---|---|---|
| `job_token_read` | test, closeup | string (4 chars) or `null` | C0, C4 |
| `timer_visible` | test | bool | C0 |
| `pump_submerged` | test | bool | C0 |
| `switch_on_shown` | test | bool, `t` = moment of switching on | C1 |
| `switch_off_shown` | test | bool, `t` = moment of switching off | C1 |
| `pump_running` | test | bool | C1 |
| `fill_start_t` | test | number (s): first water enters the empty jug | C2 |
| `fill_mark_t` | test | number (s): water reaches the 500 mL mark | C2 |
| `drip_at_joint` | test | bool, `t` = drip moments | C3 |
| `intake_clear` | closeup | bool (F1) | C4 |
| `joint_reseated_shown` | closeup | bool (F2) | C4 |
| `power_source_shown` | test | bool, battery pack or USB source visible (F3) | C4 |

An observation counts only with `confidence ≥ 0.7`; below that it is treated as absent.

### 4.2 Signals (SAM 3.1, perception)

Perception returns a **presence timeline** per concept: the sampled times (s) where a mask is present, plus the sample interval. A request that succeeds with no match gives an empty timeline (zero presence). A request that errors gives **no timeline**, and every value derived from it is missing (→ `insufficient_evidence`), never zero. SAM and Muse Spark run in parallel; the engine derives windowed values once the run window is known.

| Derived value | Definition | Used by |
|---|---|---|
| `visible_s[component]` | Seconds with a mask for `pump`, `measuring jug`, `hose joint` in the first 5 s of the test clip | C0 |
| `stream_ratio` | Share of sampled times in the run window with a `water stream` mask | C1 |
| `jug_ratio_fill` | Share of sampled times between `fill_start_t` and `fill_mark_t` with a `measuring jug` mask | C2 |
| `joint_in_view_s` | Seconds with a `hose joint` mask inside the run window | C3 |
| `intake_visible_s` | Seconds with an `intake` mask in the close-up | C4 (F1) |

### 4.3 Inputs (technician)

`fill_time_s`, conditions (§3). Validated in `measurement`.

## 5. Checks

Run window = from `switch_on_shown.t` to `switch_off_shown.t` (or the end of the clip if switch-off is not shown or is earlier than switch-on).

Order inside each check: for C1, C3 and C4, an observed `fail` is decided first. For C0 and C2, `insufficient_evidence` is decided first (missing or disagreeing inputs make the measurement unusable). `pass` is decided last everywhere. Any case a row does not list as `pass` or `fail` is `insufficient_evidence`.

| Check ID | Pass | Fail | Insufficient evidence |
|---|---|---|---|
| `C0_preconditions` | `job_token_read` (test clip) equals the job's token; `timer_visible` and `pump_submerged` true; `visible_s ≥ 2` for `pump`, `hose joint`, `measuring jug` | — | Any of these missing, or token mismatch (possible reused video) |
| `C1_running` | `switch_on_shown`; run window ≥ 20 s; `stream_ratio ≥ 0.8`; `pump_running` not `false` | `switch_on_shown`, run window ≥ 20 s and `stream_ratio < 0.1` | Switch-on not shown, no stream timeline, run window < 20 s, `stream_ratio` between 0.1 and 0.8, or `pump_running = false` while `stream_ratio ≥ 0.8` |
| `C2_flow` | `flow_lpm ≥ flow_pass_lpm` | `flow_lpm < flow_fail_lpm` | `fill_start_t` or `fill_mark_t` missing; `video_fill_s ≤ 0`; either time outside the run window; `jug_ratio_fill < 0.8`; typed time missing; `|fill_time_s − video_fill_s| / video_fill_s > fill_time_tolerance`; or flow between thresholds |
| `C3_no_leak` | `drip_at_joint = false` and `joint_in_view_s ≥ 5` | `drip_at_joint = true` with at least one `t` inside the run window | Anything else (joint in view < 5 s, no joint timeline, low confidence, drip times outside the run window or empty) |
| `C4_cause_addressed` | Fault-specific, below | Fault-specific, below | Anything else |

`flow_lpm = 0.5 / video_fill_s × 60`, where `video_fill_s = fill_mark_t − fill_start_t`. The typed `fill_time_s` is never used to compute flow.

Fault-specific `C4`. For F1 and F2 the close-up must first show the job's token (`job_token_read` on the close-up equals the job token); otherwise C4 is `insufficient_evidence`, and this token check runs before C4's fail rule.

| Fault | Pass | Fail |
|---|---|---|
| F1 blocked inlet | `intake_clear = true` and `intake_visible_s ≥ 2` | `intake_clear = false` |
| F2 leaking joint | `joint_reseated_shown = true` | — |
| F3 weak supply | Supply recorded as `fresh_aa_x4` or `usb_5v` and `power_source_shown = true` | Supply recorded as `used_aa_x4` |

For F3, battery freshness is declared, not observed. F3 records always list this in `uncertainties[]`; the functional evidence for F3 is C2.

Required checks per fault: F1 → C0, C1, C2, C4 · F2 → C0, C1, C3, C4 · F3 → C0, C1, C2, C4. C2 and C3 also run as **regression** checks on every job.

## 6. Thresholds

Set from the **healthy baseline** measured on the rig (median of 5 healthy runs, stored in `config/rig_baseline.yaml`):

- `flow_pass_lpm = 0.8 × baseline_lpm`
- `flow_fail_lpm = 0.6 × baseline_lpm`
- `fill_time_tolerance = 0.15`
- Observation confidence threshold: `0.7`. Model confidence is not calibrated, so the threshold is swept on the **dev split only** and the false-pass rate at the chosen value is reported in EVALS.md.

Thresholds are versioned; every record stores the threshold version used.

## 7. Adversarial cases the system must handle

| Case | Expected verdict | Why |
|---|---|---|
| Pump never switched on, so the leak "disappears" | `INCONCLUSIVE` | C1: switch-on not shown |
| Switch shown on, but no water flows | `FAILED` | C1 fails; step 3 decides before missing fill times matter |
| Joint hidden by hand or out of frame | `INCONCLUSIVE`, request to re-record | C3 insufficient (required for F2) |
| Pump runs but flow low (old batteries) | `FAILED` | C2 |
| Typed fill time faster than the video shows | `INCONCLUSIVE` | C2: typed and video times disagree |
| Fill cut out or jug out of frame during the fill | `INCONCLUSIVE` | C2: fill times outside the run window or jug not in view |
| Video of a different / previous job reused | `INCONCLUSIVE` | C0 (test clip) or C4 (close-up): job token mismatch |
| Unsupported equipment or unknown fault | `INCONCLUSIVE`, escalate | Scope step |

**Job token:** the capture screen shows a random 4-character code for each job; the technician holds it in view at the start of every post-repair clip. Muse Spark reads it (`job_token_read`); the engine compares.

## 8. Output schema (summary)

```json
{
  "job_id": "uuid",
  "fault_hypothesis": "F1|F2|F3|unknown",
  "verdict": "PASSED|FAILED|INCONCLUSIVE",
  "checks": [{"id": "C2_flow", "result": "pass|fail|insufficient_evidence", "evidence": ["test@14.2", "test@35.6", "input:fill_time_s=21.4"], "detail": "1.40 L/min (video 21.4 s, typed 21.4 s) vs pass 1.28"}],
  "conditions": {"supply": "fresh_aa_x4", "head_cm": 20, "water_level_cm": 8},
  "uncertainties": ["Joint visible for 6.1 s only"],
  "requested_actions": [],
  "thresholds_version": "2026-10-30.1",
  "models": {"reasoning": "muse-spark-1.3", "segmentation": "sam-3.1"}
}
```

The full Pydantic models live in `backend/app/verification/schema.py`.
