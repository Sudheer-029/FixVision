"""Thresholds from the measured healthy-rig baseline (spec §6)."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.verification.schema import Thresholds


def load_thresholds(path: str | Path) -> Thresholds | None:
    """None when the baseline is missing, invalid or not yet measured → INCONCLUSIVE."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict) or raw.get("measured") is not True:
        return None
    try:
        return Thresholds(
            version=str(raw["version"]),
            baseline_fill_s=raw.get("baseline_fill_s"),
            fill_time_tolerance=raw.get("fill_time_tolerance", 0.15),
            confidence_threshold=raw.get("confidence_threshold", 0.7),
        )
    except (KeyError, TypeError, ValidationError):
        return None
