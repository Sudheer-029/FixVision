"""Verdict steps (spec §2), every adversarial case of spec §7, and the no-false-pass property."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.verification.engine import F3_UNCERTAINTY, REQUIRED, verify
from app.verification.schema import Conditions, JobEvidence, Thresholds, Timeline
from app.verification.thresholds import load_thresholds
from tests.verification.factory import (
    THRESHOLDS,
    healthy,
    obs,
    replace_obs,
    timeline,
    with_timeline,
)


def run(ev, thresholds=THRESHOLDS):
    return verify(ev, thresholds)


def check(v, id):
    return next(c for c in v.checks if c.id == id).result


@pytest.mark.parametrize("fault", ["F1", "F2", "F3"])
def test_healthy_job_passes(fault):
    v = run(healthy(fault))
    assert v.verdict == "PASSED", v.reasons
    assert v.reasons[0].startswith("Passed these checks under these conditions")
    assert v.thresholds_version == "test.1"
    assert (F3_UNCERTAINTY in v.uncertainties) == (fault == "F3")


# -- spec §7 adversarial cases, one named fixture each ------------------------------


def never_switched_on():
    """F2: leak 'disappears' because the pump never ran."""
    ev = replace_obs(healthy("F2"), "switch_on_shown", drop=True)
    ev = replace_obs(ev, "switch_off_shown", drop=True)
    return with_timeline(ev, "water stream", Timeline(times=[], interval_s=1 / 3))


def switched_on_no_flow():
    ev = with_timeline(healthy("F1"), "water stream", Timeline(times=[], interval_s=1 / 3))
    ev = replace_obs(ev, "fill_start_t", drop=True)
    return replace_obs(ev, "fill_mark_t", drop=True)


def joint_hidden():
    return with_timeline(healthy("F2"), "hose joint", timeline(0, 3))


def low_flow_old_batteries():
    ev = replace_obs(healthy("F3"), "switch_off_shown", drop=True)
    ev = replace_obs(ev, "fill_start_t", value=5.0)
    ev = replace_obs(ev, "fill_mark_t", value=39.0)  # 34 s → 0.88 L/min
    return ev.model_copy(
        update={"fill_time_s": 34.0, "conditions": Conditions(supply="fresh_aa_x4")}
    )


def typed_time_too_fast():
    return healthy("F1", fill_time_s=15.0)  # video shows 20 s


def fill_cut_out():
    return replace_obs(healthy("F1"), "fill_mark_t", value=36.0)  # after switch-off at 34 s


def jug_out_of_frame():
    return with_timeline(healthy("F1"), "measuring jug", timeline(0, 12))


def reused_test_clip():
    return replace_obs(healthy("F2"), "job_token_read", value="B3X9")


def reused_closeup():
    return replace_obs(healthy("F1"), "job_token_read", clip="closeup", value="B3X9")


def unsupported_equipment():
    return healthy("F1", equipment="aquarium_pump_230v")


def unknown_fault():
    return healthy("unknown")


ADVERSARIAL = [
    (never_switched_on, "INCONCLUSIVE", "C1_running", "insufficient_evidence"),
    (switched_on_no_flow, "FAILED", "C1_running", "fail"),
    (joint_hidden, "INCONCLUSIVE", "C3_no_leak", "insufficient_evidence"),
    (low_flow_old_batteries, "FAILED", "C2_flow", "fail"),
    (typed_time_too_fast, "INCONCLUSIVE", "C2_flow", "insufficient_evidence"),
    (fill_cut_out, "INCONCLUSIVE", "C2_flow", "insufficient_evidence"),
    (jug_out_of_frame, "INCONCLUSIVE", "C2_flow", "insufficient_evidence"),
    (reused_test_clip, "INCONCLUSIVE", "C0_preconditions", "insufficient_evidence"),
    (reused_closeup, "INCONCLUSIVE", "C4_cause_addressed", "insufficient_evidence"),
    (unsupported_equipment, "INCONCLUSIVE", None, None),
    (unknown_fault, "INCONCLUSIVE", None, None),
]


@pytest.mark.parametrize(
    "make, verdict, check_id, result", ADVERSARIAL, ids=[a[0].__name__ for a in ADVERSARIAL]
)
def test_adversarial(make, verdict, check_id, result):
    v = run(make())
    assert v.verdict == verdict, v.reasons
    if check_id is None:
        assert v.checks == [] and v.requested_actions == ["Escalate to a senior technician"]
    else:
        assert check(v, check_id) == result


def test_joint_hidden_requests_rerecord():
    v = run(joint_hidden())
    assert v.requested_actions == [
        "Re-record with the hose joint in view for at least 5 s while running"
    ]


def test_switched_on_no_flow_lists_missing_fill_as_uncertainty():
    v = run(switched_on_no_flow())
    assert any(u.startswith("C2_flow") for u in v.uncertainties)


# -- other steps ---------------------------------------------------------------------


def test_missing_baseline_is_inconclusive():
    v = run(healthy("F1"), thresholds=None)
    assert v.verdict == "INCONCLUSIVE" and v.reasons == ["No rig baseline"] and v.checks == []


@pytest.mark.parametrize("thresholds", [None, THRESHOLDS])
def test_f3_battery_uncertainty_on_every_path(thresholds):
    for ev in (healthy("F3"), healthy("F3", equipment="other")):
        assert F3_UNCERTAINTY in run(ev, thresholds).uncertainties


def test_verdict_reports_run_duration_and_missing_conditions():
    v = run(healthy("F1", conditions=Conditions(supply="fresh_aa_x4")))
    assert v.run_s == 30.0
    assert "Test conditions not recorded: head_cm, water_level_cm" in v.uncertainties
    assert run(replace_obs(healthy("F1"), "switch_on_shown", drop=True)).run_s is None


# -- trust boundary: evidence that could fake a pass is rejected at load -------------


def as_dict(ev):
    return ev.model_dump(mode="json")


def test_duplicate_observation_rejected():
    """A second, contradicting drip reading must not be silently ignored."""
    data = as_dict(healthy("F2"))
    data["observations"].append(as_dict(obs("drip_at_joint", True, t=[12.0])))
    with pytest.raises(ValidationError, match="duplicate observations"):
        JobEvidence.model_validate(data)


@pytest.mark.parametrize(
    "path",
    [
        ("fill_time_s",),
        ("test_clip_duration_s",),
        ("observations", 6, "value"),
        ("observations", 3, "t", 0),
        ("timelines", "test", "hose joint", "times", 0),
    ],
)
def test_nan_rejected(path):
    data = as_dict(healthy("F1"))
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = float("nan")
    with pytest.raises(ValidationError):
        JobEvidence.model_validate(data)


@pytest.mark.parametrize(
    "field, value",
    [("job_token", ""), ("job_token", "K7Q"), ("job_token", "K7Q2X"), ("equipment", None)],
)
def test_bad_token_or_missing_equipment_rejected(field, value):
    data = as_dict(healthy("F1"))
    if value is None:
        del data[field]
    else:
        data[field] = value
    with pytest.raises(ValidationError):
        JobEvidence.model_validate(data)


@pytest.mark.parametrize(
    "overrides",
    [
        {"fill_time_tolerance": float("nan")},
        {"fill_time_tolerance": 10},
        {"fill_time_tolerance": 0},
        {"confidence_threshold": 0},
        {"confidence_threshold": True},
        {"baseline_lpm": True},
        {"flow_fail_lpm": 1.2},
    ],
)
def test_bad_thresholds_rejected(overrides):
    with pytest.raises(ValidationError):
        Thresholds(**{**THRESHOLDS.model_dump(), **overrides})


def test_sam_error_is_missing_evidence_not_zero():
    """A SAM error on the stream must not read as 'no water' (which would be FAILED)."""
    v = run(with_timeline(healthy("F1"), "water stream", None))
    assert v.verdict == "INCONCLUSIVE"
    assert check(v, "C1_running") == "insufficient_evidence"


def test_preconditions_decide_before_failures():
    ev = replace_obs(switched_on_no_flow(), "timer_visible", value=False)
    v = run(ev)
    assert v.verdict == "INCONCLUSIVE" and v.reasons[0].startswith("Preconditions not met")


def test_regression_failure_fails_the_job():
    ev = replace_obs(healthy("F1"), "drip_at_joint", value=True, t=[12.0])  # C3 not required for F1
    assert run(ev).verdict == "FAILED"


def test_regression_insufficient_is_only_an_uncertainty():
    v = run(joint_hidden().model_copy(update={"fault_hypothesis": "F1"}))
    assert v.verdict == "PASSED"
    assert any(u.startswith("C3_no_leak") for u in v.uncertainties)


def test_requested_action_per_fault_for_c4():
    v = run(replace_obs(healthy("F3"), "power_source_shown", value=False))
    assert v.requested_actions == [
        "Record the supply type and show the power source in the test clip"
    ]


# -- thresholds loader ------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        None,  # file missing
        "measured: [unclosed",
        "- just a list",
        "measured: false\nversion: v\nbaseline_lpm: 1.5",
        "measured: true\nversion: v\nbaseline_lpm: null",
        "measured: true\nversion: v\nbaseline_lpm: -1",
        "measured: true\nbaseline_lpm: 1.5",
        "measured: true\nversion: v\nbaseline_lpm: true",
        "measured: true\nversion: v\nbaseline_lpm: 1.5\nfill_time_tolerance: .nan",
        "measured: true\nversion: v\nbaseline_lpm: 1.5\nconfidence_threshold: 0",
    ],
)
def test_invalid_baseline_gives_none(tmp_path, text):
    path = tmp_path / "rig_baseline.yaml"
    if text is not None:
        path.write_text(text)
    assert load_thresholds(path) is None


def test_baseline_thresholds(tmp_path):
    path = tmp_path / "rig_baseline.yaml"
    path.write_text("measured: true\nversion: '2026-10-31.1'\nbaseline_lpm: 1.5\n")
    t = load_thresholds(path)
    assert (t.flow_pass_lpm, t.flow_fail_lpm) == pytest.approx((1.2, 0.9))
    assert (t.version, t.fill_time_tolerance, t.confidence_threshold) == ("2026-10-31.1", 0.15, 0.7)


def test_repo_placeholder_baseline_is_not_measured():
    from app.config import REPO_ROOT

    assert load_thresholds(REPO_ROOT / "config" / "rig_baseline.yaml") is None


# -- property: no false PASSED ----------------------------------------------------------

OBS_IDS = [
    ("job_token_read", "test"),
    ("timer_visible", "test"),
    ("pump_submerged", "test"),
    ("switch_on_shown", "test"),
    ("switch_off_shown", "test"),
    ("pump_running", "test"),
    ("fill_start_t", "test"),
    ("fill_mark_t", "test"),
    ("drip_at_joint", "test"),
    ("power_source_shown", "test"),
    ("job_token_read", "closeup"),
    ("intake_clear", "closeup"),
    ("joint_reseated_shown", "closeup"),
]
times = st.floats(0, 40, allow_nan=False)
values = st.one_of(st.none(), st.booleans(), times, st.sampled_from(["K7Q2", "B3X9"]))
timelines = st.one_of(
    st.none(),
    st.builds(
        lambda a, b: timeline(min(a, b), max(a, b)),
        st.integers(0, 120).map(lambda k: k / 3),
        st.integers(0, 120).map(lambda k: k / 3),
    ),
)


@st.composite
def evidence(draw):
    ev = healthy(draw(st.sampled_from(["F1", "F2", "F3"])))
    observations = []
    for id, clip in OBS_IDS:
        o = next(o for o in ev.observations if o.id == id and o.clip == clip)
        if draw(st.booleans()):  # perturb about half of them
            if draw(st.booleans()):
                continue
            o = obs(
                id,
                draw(values),
                clip=clip,
                confidence=draw(st.floats(0, 1)),
                t=draw(st.lists(times, max_size=3)),
            )
        observations.append(o)
    tls = {
        clip: {k: (draw(timelines) if draw(st.booleans()) else v) for k, v in concepts.items()}
        for clip, concepts in ev.timelines.items()
    }
    return ev.model_copy(
        update={
            "observations": observations,
            "timelines": tls,
            "fill_time_s": draw(st.one_of(st.none(), st.floats(0, 60))),
            "conditions": Conditions(
                supply=draw(st.sampled_from([None, "fresh_aa_x4", "used_aa_x4", "usb_5v"]))
            ),
        }
    )


@settings(max_examples=2000, deadline=None)
@given(evidence())
def test_passed_only_when_every_required_check_passes_and_none_fail(ev: JobEvidence):
    v = run(ev)
    results = {c.id: c.result for c in v.checks}
    if v.verdict == "PASSED":
        assert all(results[c] == "pass" for c in REQUIRED[ev.fault_hypothesis])
        assert "fail" not in results.values()
    if "fail" in results.values() and results["C0_preconditions"] == "pass":
        assert v.verdict == "FAILED"
