"""Print the verdict for an evidence JSON file (schema: backend/app/verification/schema.py).

uv run --project backend python scripts/verify_json.py evidence.json [--baseline rig.yaml]
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.verification.engine import verify  # noqa: E402
from app.verification.schema import JobEvidence  # noqa: E402
from app.verification.thresholds import load_thresholds  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence", type=Path)
    p.add_argument("--baseline", type=Path, default=REPO / "config" / "rig_baseline.yaml")
    args = p.parse_args()
    ev = JobEvidence.model_validate_json(args.evidence.read_text())
    print(verify(ev, load_thresholds(args.baseline)).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
