---
description: T10 - evaluation harness and results report
---
Use the agent-eval-optimization skill if available. Read docs/EVALS.md, docs/RIG.md and docs/components/evals-harness.md.
Implement `evals/run.py --split dev|test --config <name>`: reads data/labels.csv, runs the full pipeline per clip with response caching, writes `evals/results/<config>-<split>.json` and a markdown report: verdict confusion matrix, false-pass count, inconclusive rate (overall and adversarial), triage top-1, latency p50/p95, cost per job. `--split test` refuses to run unless the config hash is frozen in `evals/frozen.json`.
Then fill the results table in docs/EVALS.md and the README Results table from the test run. Run /check, commit `feat: T10 evals and results`.
