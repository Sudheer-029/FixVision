"""Job lifecycle (ARCHITECTURE.md §4). Illegal transitions raise; the API maps them to 409."""

from enum import StrEnum


class State(StrEnum):
    CREATED = "CREATED"
    SYMPTOM_CAPTURED = "SYMPTOM_CAPTURED"
    TRIAGED = "TRIAGED"
    CHECK_REQUESTED = "CHECK_REQUESTED"
    CHECK_CAPTURED = "CHECK_CAPTURED"
    GUIDANCE_ISSUED = "GUIDANCE_ISSUED"
    REPAIR_REPORTED = "REPAIR_REPORTED"
    CLOSEUP_CAPTURED = "CLOSEUP_CAPTURED"
    TEST_CAPTURED = "TEST_CAPTURED"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REVIEWED = "REVIEWED"


NEXT: dict[State, set[State]] = {
    State.CREATED: {State.SYMPTOM_CAPTURED},
    State.SYMPTOM_CAPTURED: {State.TRIAGED},
    State.TRIAGED: {State.CHECK_REQUESTED},
    State.CHECK_REQUESTED: {State.CHECK_CAPTURED},
    State.CHECK_CAPTURED: {State.GUIDANCE_ISSUED},
    State.GUIDANCE_ISSUED: {State.REPAIR_REPORTED},
    State.REPAIR_REPORTED: {State.CLOSEUP_CAPTURED},
    State.CLOSEUP_CAPTURED: {State.TEST_CAPTURED},
    State.TEST_CAPTURED: {State.VERIFYING},
    State.VERIFYING: {State.PASSED, State.FAILED, State.INCONCLUSIVE},
    State.PASSED: {State.REVIEWED},
    State.FAILED: {State.REVIEWED, State.CLOSEUP_CAPTURED},
    State.INCONCLUSIVE: {State.REVIEWED, State.CLOSEUP_CAPTURED},
    State.REVIEWED: set(),
}


class IllegalTransition(ValueError):
    pass


def check(current: str, to: State) -> None:
    if to not in NEXT[State(current)]:
        raise IllegalTransition(f"cannot go from {current} to {to}")
