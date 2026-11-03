"""Perception + observations + verification on one recorded job; prints the verdict.

uv run --project backend python scripts/run_clip.py data/raw/f1_repaired_01.MOV \
    --closeup data/raw/f1_repaired_01_closeup.MOV --token R2C6 --fault F1 \
    --fill-time 26.0 --supply battery_9v
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.clients.meta_client import MetaClient  # noqa: E402
from app.config import Settings  # noqa: E402
from app.pipeline import collect_evidence  # noqa: E402
from app.verification.engine import verify  # noqa: E402
from app.verification.schema import Conditions  # noqa: E402
from app.verification.thresholds import load_thresholds  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("clip", type=Path)
    p.add_argument("--closeup", type=Path)
    p.add_argument("--token", required=True, help="the job code shown in the clip")
    p.add_argument("--fault", default="F1")
    p.add_argument("--fill-time", type=float, help="technician-typed fill time (cross-check)")
    p.add_argument("--supply", choices=["battery_9v", "usb_5v"])
    p.add_argument("--evidence-out", type=Path, help="also save the evidence JSON here")
    p.add_argument("--baseline", type=Path, default=REPO / "config" / "rig_baseline.yaml")
    args = p.parse_args()

    cfg = Settings()
    client = MetaClient(cfg)
    collected = collect_evidence(
        client,
        cfg,
        args.clip,
        args.closeup,
        job_id=args.clip.stem,
        job_token=args.token,
        fault=args.fault,
        fill_time_s=args.fill_time,
        conditions=Conditions(supply=args.supply),
        model=cfg.reasoning_model,
    )
    ev = collected.evidence
    if args.evidence_out:
        args.evidence_out.write_text(ev.model_dump_json(indent=2))
    for o in ev.observations:
        print(f"  {o.clip:7} {o.id:16} {o.value!s:8} c={o.confidence:.2f} t={o.t}")
    v = verify(ev, load_thresholds(args.baseline))
    print(f"\nVERDICT {v.verdict}  (run {v.run_s} s)")
    for c in v.checks:
        print(f"  {c.id:20} {c.result:22} {c.detail}")
    for label, items in (("reasons", v.reasons), ("uncertainties", v.uncertainties),
                         ("actions", v.requested_actions)):  # fmt: skip
        for item in items:
            print(f"  {label}: {item}")
    print(f"\nSAM ${collected.sam_cost_usd:.4f}; Muse Spark cost is in the ledger")


if __name__ == "__main__":
    main()
