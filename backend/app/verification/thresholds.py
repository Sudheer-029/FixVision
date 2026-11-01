"""Thresholds from the measured healthy-rig baseline (spec §6)."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.verification.schema import Thresholds

PASS_FACTOR = 0.8
FAIL_FACTOR = 0.6


def load_thresholds(path: str | Path) -> Thresholds | None:
    """None when the baseline is missing, invalid or not yet measured → INCONCLUSIVE."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict) or raw.get("measured") is not True:
        return None
    baseline = raw.get("baseline_lpm")
    try:
        return Thresholds(
            version=str(raw["version"]),
            baseline_lpm=baseline,
            flow_pass_lpm=PASS_FACTOR * baseline,
            flow_fail_lpm=FAIL_FACTOR * baseline,
            fill_time_tolerance=raw.get("fill_time_tolerance", 0.15),
            confidence_threshold=raw.get("confidence_threshold", 0.7),
        )
    except (KeyError, TypeError, ValidationError):
        return None
