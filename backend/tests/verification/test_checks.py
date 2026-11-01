"""Table-driven boundary tests, one table per check (spec §5)."""

import pytest

from app.verification import checks, signals
from app.verification.schema import Timeline
from tests.verification.factory import (
    CLIP_S,
    OFF_T,
    ON_T,
    THRESHOLDS,
    healthy,
    replace_obs,
    timeline,
    with_timeline,
)

T = THRESHOLDS


def fill(ev, start, mark, typed=None):
    ev = replace_obs(ev, "fill_start_t", value=start)
    ev = replace_obs(ev, "fill_line_t", value=mark)
    return ev.model_copy(update={"fill_time_s": mark - start if typed is None else typed})


def no_off(ev):
    """Run window extends to clip end (40 s), room for slow fills."""
    return replace_obs(ev, "switch_off_shown", drop=True)


# -- signals ---------------------------------------------------------------------


def test_missing_timeline_is_missing_not_zero():
    ev = with_timeline(healthy(), "water stream", None)
    assert signals.stream_ratio(ev, (ON_T, OFF_T)) is None
    empty = with_timeline(healthy(), "water stream", Timeline(times=[], interval_s=1 / 3))
    assert signals.stream_ratio(empty, (ON_T, OFF_T)) == 0.0
    assert signals.seconds_present(None, (0, 5)) is None


def test_ratio_window_without_samples_is_missing():
    tl = Timeline(times=[0.0, 1.0], interval_s=1.0)
    assert signals.ratio_present(tl, (0.2, 0.8)) is None


def test_visible_s_counts_first_five_seconds():
    assert signals.visible_s(healthy(), "pump") == pytest.approx(5.0)


@pytest.mark.parametrize(
    "off, expected_end",
    [
        (dict(value=True, t=[OFF_T]), OFF_T),
        (dict(value=True, t=[ON_T - 1]), CLIP_S),  # switch-off before switch-on
        (dict(value=True, t=[ON_T]), ON_T),  # same moment: 0 s run, not clip end
        (dict(value=False), CLIP_S),
        (dict(value=True, t=[]), CLIP_S),
        (dict(drop=True), CLIP_S),
    ],
)
def test_run_window_end(off, expected_end):
    ev = replace_obs(healthy(), "switch_off_shown", **off)
    assert signals.run_window(ev, 0.7) == (ON_T, expected_end)


@pytest.mark.parametrize(
    "on", [dict(value=False), dict(t=[]), dict(drop=True), dict(confidence=0.69)]
)
def test_run_window_needs_switch_on(on):
    assert signals.run_window(replace_obs(healthy(), "switch_on_shown", **on), 0.7) is None


# -- C0 ----------------------------------------------------------------------------


C0_CASES = [
    ("healthy", lambda ev: ev, "pass"),
    ("token mismatch", lambda ev: replace_obs(ev, "job_token_read", value="ZZZZ"), "insufficient"),
    ("token lowercase ok", lambda ev: replace_obs(ev, "job_token_read", value=" k7q2 "), "pass"),
    ("token null", lambda ev: replace_obs(ev, "job_token_read", value=None), "insufficient"),
    ("token conf 0.69", lambda ev: replace_obs(ev, "job_token_read", confidence=0.69), "insufficient"),
    ("token conf 0.70", lambda ev: replace_obs(ev, "job_token_read", confidence=0.70), "pass"),
    ("timer hidden", lambda ev: replace_obs(ev, "timer_visible", value=False), "insufficient"),
    ("not submerged", lambda ev: replace_obs(ev, "pump_submerged", value=False), "insufficient"),
    ("pump 2.0 s", lambda ev: with_timeline(ev, "pump", timeline(0, 2)), "pass"),
    ("pump 1.67 s", lambda ev: with_timeline(ev, "pump", timeline(0, 5 / 3)), "insufficient"),
    ("hose SAM error", lambda ev: with_timeline(ev, "hose", None), "insufficient"),
    ("jar absent", lambda ev: with_timeline(ev, "jar", Timeline(times=[], interval_s=1)), "insufficient"),
]  # fmt: skip


@pytest.mark.parametrize("name, mutate, expected", C0_CASES, ids=[c[0] for c in C0_CASES])
def test_c0(name, mutate, expected):
    r = checks.c0_preconditions(mutate(healthy()), T)
    assert r.result.startswith(expected)


# -- C1 ----------------------------------------------------------------------------


def stream(ev, present_share):
    """Stream mask on the first `present_share` of the 91 run-window samples."""
    n = round(91 * present_share)
    times = [(12 + k) / 3 for k in range(n)]
    return with_timeline(ev, "water stream", Timeline(times=times, interval_s=1 / 3))


C1_CASES = [
    ("healthy", lambda ev: ev, "pass"),
    ("never switched on", lambda ev: replace_obs(ev, "switch_on_shown", drop=True), "insufficient"),
    ("ratio 0.80", lambda ev: stream(ev, 73 / 91), "pass"),
    ("ratio 0.79", lambda ev: stream(ev, 72 / 91), "insufficient"),
    ("ratio 0.10", lambda ev: stream(ev, 10 / 91), "insufficient"),
    ("ratio 0.099", lambda ev: stream(ev, 9 / 91), "fail"),
    ("no stream at all", lambda ev: stream(ev, 0), "fail"),
    ("stream SAM error", lambda ev: with_timeline(ev, "water stream", None), "insufficient"),
    ("run 20.0 s", lambda ev: replace_obs(ev, "switch_off_shown", t=[ON_T + 20]), "pass"),
    ("run 19.9 s", lambda ev: replace_obs(ev, "switch_off_shown", t=[ON_T + 19.9]), "insufficient"),
    ("run 19.9 s, no flow", lambda ev: stream(replace_obs(ev, "switch_off_shown", t=[ON_T + 19.9]), 0), "insufficient"),
    ("pump_running false", lambda ev: replace_obs(ev, "pump_running", value=False), "insufficient"),
    ("pump_running false low conf", lambda ev: replace_obs(ev, "pump_running", value=False, confidence=0.5), "pass"),
    ("pump_running missing", lambda ev: replace_obs(ev, "pump_running", drop=True), "pass"),
]  # fmt: skip


@pytest.mark.parametrize("name, mutate, expected", C1_CASES, ids=[c[0] for c in C1_CASES])
def test_c1(name, mutate, expected):
    assert checks.c1_running(mutate(healthy()), T).result.startswith(expected)


# -- C2 ----------------------------------------------------------------------------
# thresholds: healthy fill 20 s; pass ≥ 80% speed (fill ≤ 25 s), fail < 60% (fill > 33.3 s)

C2_CASES = [
    ("healthy speed", lambda ev: ev, "pass"),
    ("exactly 80%", lambda ev: fill(ev, 5.0, 30.0), "pass"),
    ("just below pass", lambda ev: fill(ev, 5.0, 30.1), "insufficient"),
    ("just above fail 61%", lambda ev: fill(no_off(ev), 5.0, 38.0), "insufficient"),
    ("just below fail", lambda ev: fill(no_off(ev), 5.0, 38.4), "fail"),
    ("fill start missing", lambda ev: replace_obs(ev, "fill_start_t", drop=True), "insufficient"),
    ("fill line low conf", lambda ev: replace_obs(ev, "fill_line_t", confidence=0.6), "insufficient"),
    ("fill line bool", lambda ev: replace_obs(ev, "fill_line_t", value=True), "insufficient"),
    ("fill line string", lambda ev: replace_obs(ev, "fill_line_t", value="28"), "insufficient"),
    ("zero duration", lambda ev: fill(ev, 10.0, 10.0, typed=10), "insufficient"),
    ("start before switch-on", lambda ev: fill(ev, 3.0, 23.0), "insufficient"),
    ("line after switch-off", lambda ev: fill(ev, 15.0, 35.0), "insufficient"),
    ("no run window", lambda ev: replace_obs(ev, "switch_on_shown", drop=True), "insufficient"),
    ("jar SAM error", lambda ev: with_timeline(ev, "jar", None), "insufficient"),
    ("jar out of frame mid-fill", lambda ev: with_timeline(ev, "jar", timeline(0, 14)), "insufficient"),
    ("typed missing", lambda ev: ev.model_copy(update={"fill_time_s": None}), "insufficient"),
    ("typed zero", lambda ev: ev.model_copy(update={"fill_time_s": 0}), "insufficient"),
    ("typed +15% ok", lambda ev: ev.model_copy(update={"fill_time_s": 23.0}), "pass"),
    ("typed -15% ok", lambda ev: ev.model_copy(update={"fill_time_s": 17.0}), "pass"),
    ("typed -15.5% too fast", lambda ev: ev.model_copy(update={"fill_time_s": 16.9}), "insufficient"),
    ("typed +16% too slow", lambda ev: ev.model_copy(update={"fill_time_s": 23.2}), "insufficient"),
]  # fmt: skip


@pytest.mark.parametrize("name, mutate, expected", C2_CASES, ids=[c[0] for c in C2_CASES])
def test_c2(name, mutate, expected):
    assert checks.c2_flow(mutate(healthy()), T).result.startswith(expected)


def test_c2_flow_uses_video_not_typed_time():
    r = checks.c2_flow(healthy(), T)
    assert "100% of healthy speed" in r.detail
    assert r.evidence == ["test@8.0", "test@28.0", "input:fill_time_s=20"]


# -- C3 ----------------------------------------------------------------------------

C3_CASES = [
    ("healthy", lambda ev: ev, "pass"),
    ("drip in run", lambda ev: replace_obs(ev, "leak_at_hose", value=True, t=[12.0]), "fail"),
    ("drip at switch-on", lambda ev: replace_obs(ev, "leak_at_hose", value=True, t=[ON_T]), "fail"),
    ("drip only after off", lambda ev: replace_obs(ev, "leak_at_hose", value=True, t=[36.0]), "insufficient"),
    ("drip no times", lambda ev: replace_obs(ev, "leak_at_hose", value=True, t=[]), "insufficient"),
    ("drip low conf", lambda ev: replace_obs(ev, "leak_at_hose", value=True, t=[12.0], confidence=0.5), "insufficient"),
    ("drip but never switched on", lambda ev: replace_obs(replace_obs(ev, "leak_at_hose", value=True, t=[12.0]), "switch_on_shown", drop=True), "insufficient"),
    ("hose 5.0 s", lambda ev: with_timeline(ev, "hose", timeline(10, 15)), "pass"),
    ("hose 4.67 s", lambda ev: with_timeline(ev, "hose", timeline(10, 10 + 14 / 3)), "insufficient"),
    ("hose SAM error", lambda ev: with_timeline(ev, "hose", None), "insufficient"),
    ("hose hidden in run", lambda ev: with_timeline(ev, "hose", timeline(0, 3)), "insufficient"),
    ("leak unobserved", lambda ev: replace_obs(ev, "leak_at_hose", drop=True), "insufficient"),
]  # fmt: skip


@pytest.mark.parametrize("name, mutate, expected", C3_CASES, ids=[c[0] for c in C3_CASES])
def test_c3(name, mutate, expected):
    assert checks.c3_no_leak(mutate(healthy()), T).result.startswith(expected)


# -- C4 ----------------------------------------------------------------------------


def closeup_token(ev, value):
    return replace_obs(ev, "job_token_read", clip="closeup", value=value)


C4_CASES = [
    ("F1 healthy", "F1", lambda ev: ev, "pass"),
    ("F1 still blocked", "F1", lambda ev: replace_obs(ev, "intake_clear", clip="closeup", value=False), "fail"),
    ("F1 blocked but reused close-up", "F1", lambda ev: closeup_token(replace_obs(ev, "intake_clear", clip="closeup", value=False), "AAAA"), "insufficient"),
    ("F1 intake 2.0 s", "F1", lambda ev: with_timeline(ev, "intake", timeline(0, 2)), "pass"),
    ("F1 intake 1.67 s", "F1", lambda ev: with_timeline(ev, "intake", timeline(0, 5 / 3)), "insufficient"),
    ("F1 intake SAM error", "F1", lambda ev: with_timeline(ev, "intake", None), "insufficient"),
    ("F1 intake_clear missing", "F1", lambda ev: replace_obs(ev, "intake_clear", clip="closeup", drop=True), "insufficient"),
    ("F1 close-up token mismatch", "F1", lambda ev: closeup_token(ev, "AAAA"), "insufficient"),
    ("F1 test-clip token is not enough", "F1", lambda ev: replace_obs(ev, "job_token_read", clip="closeup", drop=True), "insufficient"),
]  # fmt: skip


@pytest.mark.parametrize("name, fault, mutate, expected", C4_CASES, ids=[c[0] for c in C4_CASES])
def test_c4(name, fault, mutate, expected):
    assert checks.c4_cause_addressed(mutate(healthy(fault)), T).result.startswith(expected)


def test_repeated_times_count_once():
    """One mask per object at the same sample must not double the seconds in view."""
    tl = timeline(10, 13)
    doubled = Timeline(times=tl.times * 2, interval_s=tl.interval_s)
    assert signals.seconds_present(doubled, (0, 40)) == signals.seconds_present(tl, (0, 40)) == 3.0


def test_intake_timeline_must_come_from_closeup():
    ev = healthy("F1")
    moved = ev.model_copy(
        update={"timelines": {"test": {**ev.timelines["test"], "intake": timeline(0, 5)}}}
    )
    assert checks.c4_cause_addressed(moved, T).result == "insufficient_evidence"
