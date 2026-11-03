# Evaluation

**Status:** exploratory results from 2026-11-03.

## Data
Staged trials on the rig ([RIG.md](RIG.md)), labeled at recording time in `data/labels.csv`. All clips are from one recording session and were used during development.

## Metrics
| Metric | Why |
|---|---|
| False Passed (count and rate) | The error that matters most |
| Correct Passed / Failed | Usefulness |
| Inconclusive rate (overall and on adversarial cases) | Honesty vs friction |
| Latency p50 / p95 per job | Demo and field usability |
| Cost per job (USD) | Viability |
| Flow time agreement (video vs typed, median % difference) | Muse Spark timing accuracy (ADR-0007) |

## Results (2026-11-03, exploratory)
Five trials with fresh model calls (`evals/run.py`, details in [evals/results/dev.md](../evals/results/dev.md)). These clips were also used during development and there is no held-out split, so this is not a claim of general accuracy (ADR-0011).

| Trials | As expected | False Passed | Inconclusive | p50 latency | Max latency | Cost per job |
|---|---|---|---|---|---|---|
| 5 | 4 | 0 | 5 | 154.8 s | 222.7 s | $0.105 |

**Repeat runs vary.** On this run `f1_faulty_01` came back Inconclusive (pump not shown submerged), not the expected Failed, though its fill was 51 s against 26 s healthy. Across 4 further fresh observation calls on that clip, Muse Spark reported the pump submerged above the 0.7 confidence threshold 3 times and gave no answer once (confidence 0.4). `f1_repaired_01` measured 76% of healthy speed here and 79% on an earlier run. The uncertain case fell to Inconclusive, the safe direction.

**Not tested on real clips:** no real clip reached Passed, so 0 false passes is only lightly tested. The Passed path is covered by automated tests with constructed evidence. Triage accuracy and the confidence-threshold sweep were not measured.

Faults are staged and the sample is small.
