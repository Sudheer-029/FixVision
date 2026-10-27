# Component: Evals harness

**Purpose:** Run labeled trials end to end and report metrics.
**Code:** `evals/`

- Input: `data/labels.csv` + clips (not committed if large; manifest committed).
- Runs the full pipeline with a fixed config; caches model responses by content hash.
- Metrics: confusion matrix over verdicts, false-pass count, inconclusive rate, latency p50/p95, cost per job.
- Splits: `dev` (tuning) and `test` (held out). `--split test` requires a frozen config hash.
- Stretch: prompt-ops and Meta-Harness runs on `dev`, final comparison on `test`.
