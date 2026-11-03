# Component: Evals harness

**Purpose:** Run labeled trials end to end and report metrics.
**Code:** `evals/`

- Input: `data/labels.csv` + clips (not committed if large; manifest committed).
- Run: `uv run --directory backend python ../evals/run.py`, which writes `evals/results/dev.json` and `dev.md`.
- Metrics per trial and overall: expected vs actual verdict, false-pass count, Inconclusive count, latency, cost, fill time from video vs typed.
- Runs on the development clips only: there is no held-out split (ADR-0011). It uses an empty cache, so latency and cost are real.
