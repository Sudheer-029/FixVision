"""Label parsing and scoring in evals/run.py, on the real labels file."""

import importlib.util

from app.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("evals_run", REPO_ROOT / "evals" / "run.py")
evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evals)


def test_trials_come_from_the_labels():
    trials = {t["clip_id"]: t for t in evals.load_trials(REPO_ROOT / "data" / "labels.csv")}
    assert "healthy_01" not in trials and "f1_repaired_01_closeup" not in trials
    repaired = trials["f1_repaired_01"]
    assert repaired["closeup"] == "f1_repaired_01_closeup.MOV" and repaired["token"] == "R2C6"
    assert repaired["fill_time_s"] == 33.0
    assert trials["adv_reused_01"]["test"] == "Healthy_01.MOV"
    assert trials["adv_reused_01"]["token"] == "R2C6"


def test_a_pass_on_a_faulty_or_trick_clip_counts_as_false_passed():
    def row(state, expected, verdict):
        return {
            "state": state, "expected": expected, "verdict": verdict,
            "correct": evals.is_correct(expected, verdict), "latency_s": 1.0, "cost_usd": 0.1,
        }  # fmt: skip

    s = evals.summarize(
        [
            row("faulty", "FAILED", "PASSED"),
            row("adversarial", "INCONCLUSIVE", "PASSED"),
            row("repaired", "PASSED_OR_INCONCLUSIVE", "PASSED"),
        ]
    )
    assert s["false_passed"] == 2 and s["correct"] == 1
