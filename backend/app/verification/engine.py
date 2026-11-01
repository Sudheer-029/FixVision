"""Verdict combiner: the ordered steps of spec §2. The only place a verdict is decided."""

from app.verification import checks, signals
from app.verification.schema import (
    SUPPORTED_EQUIPMENT,
    CheckId,
    CheckResult,
    JobEvidence,
    Thresholds,
    Verdict,
)

REQUIRED: dict[str, tuple[CheckId, ...]] = {
    "F1": ("C0_preconditions", "C1_running", "C2_flow", "C4_cause_addressed"),
    "F2": ("C0_preconditions", "C1_running", "C3_no_leak", "C4_cause_addressed"),
    "F3": ("C0_preconditions", "C1_running", "C2_flow", "C4_cause_addressed"),
}
REGRESSION: tuple[CheckId, ...] = ("C2_flow", "C3_no_leak")

CHECKS = {
    "C0_preconditions": checks.c0_preconditions,
    "C1_running": checks.c1_running,
    "C2_flow": checks.c2_flow,
    "C3_no_leak": checks.c3_no_leak,
    "C4_cause_addressed": checks.c4_cause_addressed,
}

ACTIONS: dict[str, str] = {
    "C0_preconditions": "Re-record the test clip with this job's token, the timer, the submerged "
    "pump, the hose joint and the jug in view for the first 5 s",
    "C1_running": "Re-record showing the switch turned on and at least 20 s of running",
    "C2_flow": "Keep the jug and outlet in frame for the whole fill and re-enter the fill time",
    "C3_no_leak": "Re-record with the hose joint in view for at least 5 s while running",
    "C4_cause_addressed:F1": "Record a close-up of the clean intake with this job's token",
    "C4_cause_addressed:F2": "Record a close-up of the re-seated joint with this job's token",
    "C4_cause_addressed:F3": "Record the supply type and show the power source in the test clip",
}
ESCALATE = "Escalate to a senior technician"
F3_UNCERTAINTY = "Battery freshness is declared by the technician, not observed"


def _action(check: CheckResult, fault: str) -> str:
    key = f"{check.id}:{fault}" if check.id == "C4_cause_addressed" else check.id
    return ACTIONS[key]


def verify(ev: JobEvidence, thresholds: Thresholds | None) -> Verdict:
    fault = ev.fault_hypothesis
    uncertainties = [F3_UNCERTAINTY] if fault == "F3" else []
    missing_conditions = [
        name
        for name in ("supply", "head_cm", "water_level_cm")
        if getattr(ev.conditions, name) is None
    ]
    if missing_conditions:
        uncertainties.append(f"Test conditions not recorded: {', '.join(missing_conditions)}")
    base = {
        "job_id": ev.job_id,
        "fault_hypothesis": fault,
        "conditions": ev.conditions,
        "models": ev.models,
    }

    # 1. Scope
    if ev.equipment != SUPPORTED_EQUIPMENT or fault == "unknown":
        return Verdict(
            **base,
            verdict="INCONCLUSIVE",
            reasons=["Out of scope: unsupported equipment or unknown fault"],
            uncertainties=uncertainties,
            requested_actions=[ESCALATE],
        )
    if thresholds is None:
        return Verdict(
            **base, verdict="INCONCLUSIVE", reasons=["No rig baseline"], uncertainties=uncertainties
        )

    required = REQUIRED[fault]
    results = [fn(ev, thresholds) for fn in CHECKS.values()]
    by_id = {r.id: r for r in results}
    window = signals.run_window(ev, thresholds.confidence_threshold)
    common = {
        **base,
        "checks": results,
        "thresholds_version": thresholds.version,
        "run_s": None if window is None else round(window[1] - window[0], 1),
    }
    insufficient = [r for r in results if r.result == "insufficient_evidence"]

    # 2. Preconditions
    c0 = by_id["C0_preconditions"]
    if c0.result != "pass":
        return Verdict(
            **common,
            verdict="INCONCLUSIVE",
            reasons=[f"Preconditions not met: {c0.detail}"],
            uncertainties=uncertainties,
            requested_actions=[_action(c0, fault)],
        )

    # 3. Observed failure (all checks are required or regression)
    failed = [r for r in results if r.result == "fail"]
    if failed:
        return Verdict(
            **common,
            verdict="FAILED",
            reasons=[f"{r.id}: {r.detail}" for r in failed],
            uncertainties=uncertainties + [f"{r.id}: {r.detail}" for r in insufficient],
            requested_actions=["Repair again, then record a new test"],
        )

    # 4. Evidence sufficiency
    missing = [r for r in insufficient if r.id in required]
    if missing:
        return Verdict(
            **common,
            verdict="INCONCLUSIVE",
            reasons=[f"{r.id}: {r.detail}" for r in missing],
            uncertainties=uncertainties
            + [f"{r.id}: {r.detail}" for r in insufficient if r.id not in required],
            requested_actions=[_action(r, fault) for r in missing],
        )

    # 5. Passed
    return Verdict(
        **common,
        verdict="PASSED",
        reasons=[
            "Passed these checks under these conditions: "
            + ", ".join(r.id for r in results if r.id in required)
        ],
        uncertainties=uncertainties + [f"{r.id}: {r.detail}" for r in insufficient],
    )
