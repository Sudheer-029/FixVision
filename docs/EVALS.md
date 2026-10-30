# Evaluation

**Status:** method defined 2026-10-27; results pending.

## Data
Staged trials on the rig ([RIG.md](RIG.md)), labeled at recording time in `data/labels.csv`. Split by recording session into `dev` and `test`. The test split is untouched until the final run.

## Metrics
| Metric | Why |
|---|---|
| False Passed (count and rate) | The error that matters most |
| Correct Passed / Failed | Usefulness |
| Inconclusive rate (overall and on adversarial cases) | Honesty vs friction |
| Triage top-1 fault accuracy | Diagnosis quality |
| Latency p50 / p95 per job | Demo and field usability |
| Cost per job (USD) | Viability |
| Flow time agreement (video vs typed, median % difference) | Muse Spark timing accuracy (ADR-0007) |
| False-pass rate across confidence thresholds (dev sweep) | Justifies the 0.7 cut-off |

## Results (test split)
| Configuration | Trials | False Passed | Correct Passed | Correct Failed | Inconclusive | Triage top-1 | p50 latency | Cost/job |
|---|---|---|---|---|---|---|---|---|
| Baseline v1 | — | — | — | — | — | — | — | — |
| Tuned (dev-tuned prompts / thresholds) | — | — | — | — | — | — | — | — |
| Muse open model, base (Fireworks) | — | — | — | — | — | — | — | — |
| Muse open model, fine-tuned on dev split (Fireworks) | — | — | — | — | — | — | — | — |

Faults are staged, the sample is small, and results are exploratory.

## Optional optimization (stretch)
prompt-ops on the triage prompt and Meta-Harness on the reasoning harness, run on `dev` with contributor-mode or open-weight models; improvement claimed only from the `test` split.
