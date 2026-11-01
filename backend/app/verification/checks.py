"""The five checks of spec §5. Each is pure: evidence + thresholds → CheckResult.

C1, C3, C4 decide `fail` first; C0, C2 decide `insufficient_evidence` first; `pass` last;
anything not listed as pass or fail is `insufficient_evidence`.
"""

from app.verification import signals
from app.verification.schema import CheckResult, Clip, JobEvidence, Observation, Thresholds

MIN_VISIBLE_S = 2.0
MIN_RUN_S = 20.0
STREAM_PASS = 0.8
STREAM_FAIL = 0.1
JAR_MIN_RATIO = 0.8
MIN_HOSE_S = 5.0
MIN_INTAKE_S = 2.0

C0_COMPONENTS = ("pump", "hose", "jar")


def _ref(o: Observation) -> list[str]:
    return [f"{o.clip}@{t:.1f}" for t in o.t]


def _is(o: Observation | None, value: bool) -> bool:
    return o is not None and o.value is value


def _token_matches(ev: JobEvidence, clip: Clip, min_confidence: float) -> bool:
    o = ev.observation("job_token_read", clip, min_confidence)
    return (
        o is not None
        and isinstance(o.value, str)
        and o.value.strip().upper() == ev.job_token.strip().upper()
    )


def _fmt(x: float | None, unit: str = "s") -> str:
    return "missing" if x is None else f"{x:.1f} {unit}"


def c0_preconditions(ev: JobEvidence, thr: Thresholds) -> CheckResult:
    c = thr.confidence_threshold
    problems = []
    if not _token_matches(ev, "test", c):
        problems.append("job token not read or does not match (possible reused video)")
    if not _is(ev.observation("timer_visible", "test", c), True):
        problems.append("timer not visible")
    if not _is(ev.observation("pump_submerged", "test", c), True):
        problems.append("pump not shown submerged")
    for comp in C0_COMPONENTS:
        v = signals.visible_s(ev, comp)
        if v is None or v < MIN_VISIBLE_S:
            problems.append(f"{comp} visible {_fmt(v)} in first 5 s (need ≥ {MIN_VISIBLE_S:g} s)")
    if problems:
        return CheckResult(
            id="C0_preconditions", result="insufficient_evidence", detail="; ".join(problems)
        )
    return CheckResult(
        id="C0_preconditions",
        result="pass",
        evidence=[
            *_ref(ev.observation("job_token_read", "test", c)),
            *(f"sam:{comp}" for comp in C0_COMPONENTS),
        ],
        detail="Job token, timer, submerged pump, hose and jar in view at the start",
    )


def c1_running(ev: JobEvidence, thr: Thresholds) -> CheckResult:
    c = thr.confidence_threshold
    window = signals.run_window(ev, c)
    if window is None:
        return CheckResult(
            id="C1_running", result="insufficient_evidence", detail="Switch-on not shown"
        )
    run_s = window[1] - window[0]
    ratio = signals.stream_ratio(ev, window)
    running = ev.observation("pump_running", "test", c)
    evidence = [f"test@{window[0]:.1f}", f"test@{window[1]:.1f}", "sam:water stream"]
    detail = f"Run {run_s:.1f} s, water stream in {_fmt(ratio and ratio * 100, '%')} of samples"
    if run_s < MIN_RUN_S or ratio is None:
        reason = f"run {run_s:.1f} s < {MIN_RUN_S:g} s" if run_s < MIN_RUN_S else "no stream data"
        return CheckResult(id="C1_running", result="insufficient_evidence", detail=reason)
    if ratio < STREAM_FAIL:
        return CheckResult(id="C1_running", result="fail", evidence=evidence, detail=detail)
    if ratio >= STREAM_PASS and not _is(running, False):
        return CheckResult(id="C1_running", result="pass", evidence=evidence, detail=detail)
    if _is(running, False):
        detail += "; model reports pump not running"
    return CheckResult(
        id="C1_running", result="insufficient_evidence", evidence=evidence, detail=detail
    )


def c2_flow(ev: JobEvidence, thr: Thresholds) -> CheckResult:
    c = thr.confidence_threshold

    def insufficient(detail: str) -> CheckResult:
        return CheckResult(id="C2_flow", result="insufficient_evidence", detail=detail)

    start = ev.observation("fill_start_t", "test", c)
    mark = ev.observation("fill_line_t", "test", c)
    numeric = (int, float)
    if (
        start is None
        or mark is None
        or isinstance(start.value, bool)
        or isinstance(mark.value, bool)
        or not isinstance(start.value, numeric)
        or not isinstance(mark.value, numeric)
    ):
        return insufficient("Fill start or water reaching the fill line not seen in the test clip")
    t0, t1 = float(start.value), float(mark.value)
    video_s = t1 - t0
    if video_s <= 0:
        return insufficient(f"Fill line ({t1:.1f} s) not after fill start ({t0:.1f} s)")
    window = signals.run_window(ev, c)
    if window is None or not (window[0] <= t0 and t1 <= window[1]):
        return insufficient("Fill times outside the run window")
    jar = signals.jar_ratio_fill(ev, t0, t1)
    if jar is None or jar < JAR_MIN_RATIO:
        return insufficient(f"Jar in view for {_fmt(jar and jar * 100, '%')} of the fill")
    typed = ev.fill_time_s
    if typed is None or typed <= 0:
        return insufficient("Typed fill time missing")
    disagreement = abs(typed - video_s) / video_s
    if disagreement > thr.fill_time_tolerance:
        return insufficient(
            f"Typed fill time {typed:.1f} s disagrees with video {video_s:.1f} s "
            f"({disagreement:.0%} > {thr.fill_time_tolerance:.0%})"
        )
    speed = thr.baseline_fill_s / video_s
    evidence = [f"test@{t0:.1f}", f"test@{t1:.1f}", f"input:fill_time_s={typed:g}"]
    detail = (
        f"{speed:.0%} of healthy speed (fill {video_s:.1f} s, typed {typed:.1f} s, "
        f"healthy {thr.baseline_fill_s:.1f} s) vs pass {thr.speed_pass:.0%}, "
        f"fail below {thr.speed_fail:.0%}"
    )
    if speed < thr.speed_fail:
        return CheckResult(id="C2_flow", result="fail", evidence=evidence, detail=detail)
    if speed >= thr.speed_pass:
        return CheckResult(id="C2_flow", result="pass", evidence=evidence, detail=detail)
    return CheckResult(
        id="C2_flow",
        result="insufficient_evidence",
        evidence=evidence,
        detail=detail + " (between thresholds)",
    )


def c3_no_leak(ev: JobEvidence, thr: Thresholds) -> CheckResult:
    c = thr.confidence_threshold
    window = signals.run_window(ev, c)
    drip = ev.observation("leak_at_hose", "test", c)
    if window is not None and _is(drip, True):
        inside = [t for t in drip.t if window[0] <= t <= window[1]]
        if inside:
            return CheckResult(
                id="C3_no_leak",
                result="fail",
                evidence=[f"test@{t:.1f}" for t in inside],
                detail=f"Leak from the hose at {', '.join(f'{t:.1f} s' for t in inside)}",
            )
    hose = signals.hose_in_view_s(ev, window) if window is not None else None
    if _is(drip, False) and hose is not None and hose >= MIN_HOSE_S:
        return CheckResult(
            id="C3_no_leak",
            result="pass",
            evidence=["sam:hose", *_ref(drip)],
            detail=f"No leak; hose in view {hose:.1f} s while running",
        )
    return CheckResult(
        id="C3_no_leak",
        result="insufficient_evidence",
        detail=f"Hose in view {_fmt(hose)} while running (need ≥ {MIN_HOSE_S:g} s), "
        "or leak not clearly observed",
    )


def c4_cause_addressed(ev: JobEvidence, thr: Thresholds) -> CheckResult:
    c = thr.confidence_threshold

    def result(r, detail: str, evidence: list[str] | None = None) -> CheckResult:
        return CheckResult(
            id="C4_cause_addressed", result=r, evidence=evidence or [], detail=detail
        )

    if not _token_matches(ev, "closeup", c):
        return result(
            "insufficient_evidence", "Close-up job token not read or does not match this job"
        )
    # F1, the only fault in scope (engine returns earlier for anything else)
    clear = ev.observation("intake_clear", "closeup", c)
    if _is(clear, False):
        return result("fail", "Intake still blocked in the close-up", _ref(clear))
    visible = signals.intake_visible_s(ev)
    if _is(clear, True) and visible is not None and visible >= MIN_INTAKE_S:
        evidence = [*_ref(clear), "sam:intake"]
        return result("pass", f"Intake clear, visible {visible:.1f} s", evidence)
    return result("insufficient_evidence", f"Intake clear not confirmed (visible {_fmt(visible)})")
