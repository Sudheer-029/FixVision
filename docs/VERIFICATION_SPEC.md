# Verification specification

**Status:** v0.3 (2026-11-01, scope F1 only, see [ADR-0008](architecture/adr/ADR-0008-f1-only-relative-flow.md)) · **Owner:** Sudheer Bishnoi

This is the core of FixVision. It defines the functional test, the evidence each check needs, and the rules that turn evidence into a verdict. The verdict is computed by deterministic code (`backend/app/verification/`). Models supply **observations with confidence**; they never issue the verdict.

## 1. Principles

1. **No evidence, no verdict.** Missing or low-confidence evidence produces **Inconclusive**, never a guess.
2. **Functional, not cosmetic.** A repair passes only on measured function under load (water flowing) plus the fault-specific check. A clean-looking still frame proves nothing.
3. **Measured from the recording, not typed.** Every value a check depends on is read from the job's clips (the test clip, plus the post-repair close-up). Technician-entered values are cross-checks only ([ADR-0007](architecture/adr/ADR-0007-flow-timed-from-video.md)).
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

Each verdict includes `reasons[]`, `checks[]`, `conditions`, `uncertainties[]` and `requested_actions[]` (e.g., "Re-record with the jar in view").

## 3. Functional test protocol (after repair)

**Post-repair close-up (≤ 10 s, recorded before the test clip):** job token in view, then the clean intake in close-up.

**Test clip**, one continuous recording:

1. **Setup (≥ 3 s):** rig in view, pump submerged, hose visible, jar with its fill line visible, on-screen timer visible, **job token in view**.
2. **Power on:** switch turned on in view.
3. **Run (≥ 20 s):** water stream visible from the hose into the jar; the hose stays in view.
4. **Timed fill:** jar and outlet stay in frame from the first water entering the empty jar until the water reaches the fill line (a tape or string mark; its volume does not matter, only that every run uses the same line). The technician also types the fill time as a cross-check.
5. **Power off:** switch turned off in view.

Test conditions captured as form fields: supply (`battery_9v`, `usb_5v`), outlet head height (cm), water level (cm above pump), ambient notes.

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
| `fill_start_t` | test | number (s): first water enters the empty jar | C2 |
| `fill_line_t` | test | number (s): water reaches the fill line | C2 |
| `leak_at_hose` | test | bool, `t` = moments water leaks from the hose | C3 |
| `intake_clear` | closeup | bool | C4 |

An observation counts only with `confidence ≥ 0.7`; below that it is treated as absent.

### 4.2 Signals (SAM 3.1, perception)

Perception returns a **presence timeline** per concept: the sampled times (s) where a mask is present, plus the sample interval. A request that succeeds with no match gives an empty timeline (zero presence). A request that errors gives **no timeline**, and every value derived from it is missing (→ `insufficient_evidence`), never zero. Timelines are keyed by clip and concept (`intake` counts only from the close-up). "Seconds with a mask" = (distinct masked samples − 1) × sample interval, the span the samples prove; repeated times count once. SAM and Muse Spark run in parallel; the engine derives windowed values once the run window is known.

| Derived value | Definition | Used by |
|---|---|---|
| `visible_s[component]` | Seconds with a mask for `pump`, `hose`, `jar` in the first 5 s of the test clip | C0 |
| `stream_ratio` | Share of sampled times in the run window with a `water stream` mask | C1 |
| `jar_ratio_fill` | Share of sampled times between `fill_start_t` and `fill_line_t` with a `jar` mask | C2 |
| `hose_in_view_s` | Seconds with a `hose` mask inside the run window | C3 |
| `intake_visible_s` | Seconds with an `intake` mask in the close-up | C4 |

### 4.3 Inputs (technician)

`fill_time_s`, conditions (§3). Validated in `measurement`.

## 5. Checks

Run window = from `switch_on_shown.t` to `switch_off_shown.t` (or the end of the clip if switch-off is not shown or is earlier than switch-on; switch-off at the same moment gives a 0 s run).

Order inside each check: for C1, C3 and C4, an observed `fail` is decided first. For C0 and C2, `insufficient_evidence` is decided first (missing or disagreeing inputs make the measurement unusable). `pass` is decided last everywhere. Any case a row does not list as `pass` or `fail` is `insufficient_evidence`.

| Check ID | Pass | Fail | Insufficient evidence |
|---|---|---|---|
| `C0_preconditions` | `job_token_read` (test clip) equals the job's token (ignoring case and surrounding spaces); `timer_visible` and `pump_submerged` true; `visible_s ≥ 2` for `pump`, `hose`, `jar` | — | Any of these missing, or token mismatch (possible reused video) |
| `C1_running` | `switch_on_shown`; run window ≥ 20 s; `stream_ratio ≥ 0.8`; `pump_running` not `false` | `switch_on_shown`, run window ≥ 20 s and `stream_ratio < 0.1` | Switch-on not shown, no stream timeline, run window < 20 s, `stream_ratio` between 0.1 and 0.8, or `pump_running = false` while `stream_ratio ≥ 0.8` |
| `C2_flow` | `speed ≥ speed_pass` | `speed < speed_fail` | `fill_start_t` or `fill_line_t` missing; `video_fill_s ≤ 0`; either time outside the run window; `jar_ratio_fill < 0.8`; typed time missing; `|fill_time_s − video_fill_s| / video_fill_s > fill_time_tolerance`; or speed between thresholds |
| `C3_no_leak` | `leak_at_hose = false` and `hose_in_view_s ≥ 5` | `leak_at_hose = true` with at least one `t` inside the run window | Anything else (hose in view < 5 s, no hose timeline, low confidence, leak times outside the run window or empty) |
| `C4_cause_addressed` | Close-up token matches; `intake_clear = true` and `intake_visible_s ≥ 2` | Close-up token matches and `intake_clear = false` | Anything else |

`speed = baseline_fill_s / video_fill_s` (share of healthy speed), where `video_fill_s = fill_line_t − fill_start_t`. The typed `fill_time_s` is never used to compute speed.

C4 checks the close-up token first (`job_token_read` on the close-up equals the job token); a mismatch is `insufficient_evidence` and is decided before C4's fail rule, so a reused close-up cannot produce a verdict either way.

Scope is one fault, **F1 blocked inlet** ([ADR-0008](architecture/adr/ADR-0008-f1-only-relative-flow.md)). Required checks: C0, C1, C2, C4. C2 and C3 also run as **regression** checks. With a `battery_9v` supply, every record lists that the battery weakens with use in `uncertainties[]`.

## 6. Thresholds

Set from the **healthy baseline** measured on the rig (median healthy fill time to the line, stored in `config/rig_baseline.yaml` as `baseline_fill_s`):

- `speed_pass = 0.8` (fill no slower than baseline / 0.8)
- `speed_fail = 0.6` (fill slower than baseline / 0.6)
- `fill_time_tolerance = 0.15`
- Observation confidence threshold: `0.7`. Model confidence is not calibrated, so the threshold is swept on the **dev split only** and the false-pass rate at the chosen value is reported in EVALS.md.

Thresholds are versioned; every record stores the threshold version used.

## 7. Adversarial cases the system must handle

| Case | Expected verdict | Why |
|---|---|---|
| Pump never switched on (recorded: `adv_never_on_01`) | `INCONCLUSIVE` | C1: switch-on not shown |
| Pump covered at the start (recorded: `adv_pump_hidden_01`) | `INCONCLUSIVE`, request to re-record | C0: pump not visible / not shown submerged |
| Switch shown on, but no water flows | `FAILED` | C1 fails; step 3 decides before missing fill times matter |
| Pump runs but the fill is still slow after the "repair" | `FAILED` | C2 |
| Typed fill time faster than the video shows | `INCONCLUSIVE` | C2: typed and video times disagree |
| Fill cut out or jar out of frame during the fill | `INCONCLUSIVE` | C2: fill times outside the run window or jar not in view |
| Video of a different / previous job reused | `INCONCLUSIVE` | C0 (test clip) or C4 (close-up): job token mismatch |
| Unsupported equipment or unknown fault | `INCONCLUSIVE`, escalate | Scope step |

**Job token:** the capture screen shows a random 4-character code for each job; the technician holds it in view at the start of every post-repair clip. Muse Spark reads it (`job_token_read`); the engine compares.

## 8. Output schema (summary)

```json
{
  "job_id": "uuid",
  "fault_hypothesis": "F1|unknown",
  "verdict": "PASSED|FAILED|INCONCLUSIVE",
  "checks": [{"id": "C2_flow", "result": "pass|fail|insufficient_evidence", "evidence": ["test@14.2", "test@35.6", "input:fill_time_s=21.4"], "detail": "92% of healthy speed (fill 28.6 s, typed 28.0 s, healthy 26.3 s) vs pass 80%, fail below 60%"}],
  "conditions": {"supply": "battery_9v", "head_cm": 20, "water_level_cm": 8},
  "run_s": 30.0,
  "uncertainties": ["Powered by a 9 V battery that weakens with use; ..."],
  "requested_actions": [],
  "thresholds_version": "2026-10-30.1",
  "models": {"reasoning": "muse-spark-1.3", "segmentation": "sam-3.1"}
}
```

The full Pydantic models live in `backend/app/verification/schema.py`. Evidence is validated at load: NaN or infinite numbers, two observations with the same id and clip, a job token that is not 4 letters or digits, or a missing `equipment` are rejected. Thresholds outside their bounds (tolerance 0–0.3, confidence threshold 0.5–1, `speed_fail` below `speed_pass`) make the baseline invalid (→ "No rig baseline"). Missing test conditions are listed in `uncertainties[]`.
