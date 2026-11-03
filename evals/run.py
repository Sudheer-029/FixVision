"""Run the labelled rig trials through the real pipeline; writes evals/results/dev.{json,md}.

uv run --directory backend python ../evals/run.py

Uses an empty response cache, so latency and cost are those of fresh model calls.
"""

import csv
import json
import re
import sqlite3
import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.clients.meta_client import MetaClient  # noqa: E402
from app.config import Settings  # noqa: E402
from app.pipeline import collect_evidence  # noqa: E402
from app.verification.engine import verify  # noqa: E402
from app.verification.schema import Conditions  # noqa: E402
from app.verification.thresholds import load_thresholds  # noqa: E402

RAW = REPO / "data" / "raw"
ACCEPTED = {
    "FAILED": {"FAILED"},
    "INCONCLUSIVE": {"INCONCLUSIVE"},
    "PASSED": {"PASSED"},
    "PASSED_OR_INCONCLUSIVE": {"PASSED", "INCONCLUSIVE"},
}


def load_trials(labels: Path) -> list[dict]:
    """Rows with an expected verdict; baseline clips and bare close-ups are not trials."""
    rows = list(csv.DictReader(labels.open()))
    files = {r["clip_id"]: re.search(r"file (\S+?);?(?:\s|$)", r["notes"]).group(1) for r in rows}
    trials = []
    for r in rows:
        if r["expected_verdict"] not in ACCEPTED:
            continue
        fill = re.search(r"fill about ([\d.]+) s", r["notes"])
        trials.append(
            {
                "clip_id": r["clip_id"],
                "state": r["state"],
                "expected": r["expected_verdict"],
                "test": files[r["clip_id"]],
                "closeup": files.get(f"{r['clip_id']}_closeup"),
                "token": re.search(r"code (\w{4})", r["notes"]).group(1),
                "fill_time_s": float(fill.group(1)) if fill else None,
            }
        )
    return trials


def is_correct(expected: str, got: str) -> bool:
    return got in ACCEPTED[expected]


def summarize(results: list[dict]) -> dict:
    latencies = [r["latency_s"] for r in results]
    costs = [r["cost_usd"] for r in results]
    return {
        "trials": len(results),
        "correct": sum(r["correct"] for r in results),
        "false_passed": sum(r["verdict"] == "PASSED" and r["state"] != "repaired" for r in results),
        "inconclusive": sum(r["verdict"] == "INCONCLUSIVE" for r in results),
        "latency_p50_s": round(statistics.median(latencies), 1),
        "latency_max_s": round(max(latencies), 1),
        "cost_per_job_usd": round(statistics.mean(costs), 3),
    }


def job_cost(ledger: Path, job_id: str, since: str) -> float:
    db = sqlite3.connect(ledger)
    (total,) = db.execute(
        "SELECT COALESCE(SUM(est_cost_usd), 0) FROM cost_ledger WHERE job_id = ? AND ts >= ?",
        (job_id, since),
    ).fetchone()
    db.close()
    return total


def run_trial(t: dict, client: MetaClient, cfg: Settings, thresholds) -> dict:
    job_id = f"eval-{t['clip_id']}"
    since = datetime.now(UTC).isoformat()
    start = time.monotonic()
    collected = collect_evidence(
        client,
        cfg,
        RAW / t["test"],
        RAW / t["closeup"] if t["closeup"] else None,
        job_id=job_id,
        job_token=t["token"],
        fault="F1",
        fill_time_s=t["fill_time_s"],
        conditions=Conditions(supply="battery_9v"),
        model=cfg.reasoning_model,
    )
    v = verify(collected.evidence, thresholds)
    ev = collected.evidence
    start_o, line_o = (ev.observation(i, "test", 0.0) for i in ("fill_start_t", "fill_line_t"))
    video_fill = None
    if start_o and line_o and start_o.value is not None and line_o.value is not None:
        video_fill = round(line_o.value - start_o.value, 1)
    return {
        **t,
        "verdict": v.verdict,
        "correct": is_correct(t["expected"], v.verdict),
        "reasons": v.reasons,
        "video_fill_s": video_fill,
        "latency_s": round(time.monotonic() - start, 1),
        "cost_usd": round(job_cost(cfg.ledger_path, job_id, since), 4),
    }


def report(results: list[dict], summary: dict) -> str:
    lines = [
        "# Dev-split results (exploratory)",
        "",
        "Fresh model calls on the staged rig clips, which were also used during development.",
        "There is no held-out test split, so this is not a claim of general accuracy.",
        "",
        f"Trials: {summary['trials']}, as expected: {summary['correct']}, "
        f"false Passed: {summary['false_passed']}, Inconclusive: {summary['inconclusive']}, "
        f"latency p50 {summary['latency_p50_s']} s (max {summary['latency_max_s']} s), "
        f"cost per job ${summary['cost_per_job_usd']:.3f}.",
        "",
        "| Clip | Expected | Verdict | Fill, video / typed (s) | Latency (s) | Cost ($) | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        reason = "; ".join(r["reasons"]).replace("|", "/")
        fills = f"{r['video_fill_s'] or '–'} / {r['fill_time_s'] or '–'}"
        lines.append(
            f"| {r['clip_id']} | {r['expected']} | {r['verdict']} | {fills} | "
            f"{r['latency_s']} | {r['cost_usd']:.3f} | {reason} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Settings(cache_dir=Path(tmp))
        client = MetaClient(cfg)
        thresholds = load_thresholds(cfg.rig_baseline_path)
        results = []
        for t in load_trials(REPO / "data" / "labels.csv"):
            results.append(run_trial(t, client, cfg, thresholds))
            print(results[-1]["clip_id"], results[-1]["verdict"], results[-1]["cost_usd"], flush=True)
    summary = summarize(results)
    out = REPO / "evals" / "results"
    (out / "dev.json").write_text(json.dumps({"summary": summary, "trials": results}, indent=2))
    (out / "dev.md").write_text(report(results, summary))
    print(summary)


if __name__ == "__main__":
    main()
