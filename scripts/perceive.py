"""Run SAM 3.1 perception on a test clip (and optional close-up); print timelines and cost.

uv run --project backend python scripts/perceive.py data/raw/f1_repaired_01.MOV \
    --closeup data/raw/f1_repaired_01_closeup.MOV
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.clients.meta_client import MetaClient  # noqa: E402
from app.config import Settings  # noqa: E402
from app.perception import frames  # noqa: E402
from app.perception.signals import perceive  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("clip", type=Path)
    p.add_argument("--closeup", type=Path)
    args = p.parse_args()
    cfg = Settings()
    timelines, cost = perceive(
        MetaClient(cfg),
        args.clip,
        args.closeup,
        cfg.sam_sample_fps,
        cfg.cache_dir / "perception",
    )
    for clip, concepts in timelines.items():
        path = args.clip if clip == "test" else args.closeup
        length = frames.duration_s(path)
        for concept, tl in concepts.items():
            if tl is None:
                print(f"{clip:8} {concept:7} ERROR (missing evidence)")
                continue
            span = f"{tl.times[0]:.1f}–{tl.times[-1]:.1f} s" if tl.times else "never"
            samples = round(length / tl.interval_s) + 1
            print(f"{clip:8} {concept:7} in {len(tl.times)}/{samples} samples, {span}")
    print(f"SAM cost ${cost:.4f}")


if __name__ == "__main__":
    main()
