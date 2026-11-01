"""Windowed values derived from SAM presence timelines (spec §4.2).

Every function returns None when its timeline is missing (SAM error): missing, never zero.
Seconds with a mask = (distinct masked samples − 1) × interval: the span the samples prove,
never one interval more (conservative, so short views do not round up to a pass).
"""

import math

from app.verification.schema import JobEvidence, Timeline

EPS = 1e-6
FIRST_WINDOW_S = 5.0

Window = tuple[float, float]


def _present(tl: Timeline, window: Window) -> int:
    a, b = window
    return len({t for t in tl.times if a - EPS <= t <= b + EPS})


def seconds_present(tl: Timeline | None, window: Window) -> float | None:
    if tl is None:
        return None
    return max(0, _present(tl, window) - 1) * tl.interval_s


def ratio_present(tl: Timeline | None, window: Window) -> float | None:
    """Share of sampled times in the window with a mask; None if the window holds no sample."""
    if tl is None:
        return None
    a, b = window
    samples = math.floor(b / tl.interval_s + EPS) - math.ceil(a / tl.interval_s - EPS) + 1
    if samples <= 0:
        return None
    return min(1.0, _present(tl, window) / samples)


def run_window(ev: JobEvidence, min_confidence: float) -> Window | None:
    """Switch-on to switch-off, or to clip end if switch-off is not shown or precedes switch-on."""
    on = ev.observation("switch_on_shown", "test", min_confidence)
    if on is None or on.value is not True or not on.t:
        return None
    start = on.t[0]
    off = ev.observation("switch_off_shown", "test", min_confidence)
    end = ev.test_clip_duration_s
    if off is not None and off.value is True and off.t and off.t[0] >= start:
        end = off.t[0]
    return start, end


def visible_s(ev: JobEvidence, component: str) -> float | None:
    return seconds_present(ev.timeline("test", component), (0.0, FIRST_WINDOW_S))


def jar_ratio_fill(ev: JobEvidence, fill_start_t: float, fill_line_t: float) -> float | None:
    return ratio_present(ev.timeline("test", "jar"), (fill_start_t, fill_line_t))


def intake_visible_s(ev: JobEvidence) -> float | None:
    return seconds_present(ev.timeline("closeup", "intake"), (0.0, math.inf))
