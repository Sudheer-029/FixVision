# Dev-split results (exploratory)

Fresh model calls on the staged rig clips, which were also used during development.
There is no held-out test split, so this is not a claim of general accuracy.

Trials: 5, as expected: 4, false Passed: 0, Inconclusive: 5, latency p50 154.8 s (max 222.7 s), cost per job $0.105.

| Clip | Expected | Verdict | Fill, video / typed (s) | Latency (s) | Cost ($) | Reason |
|---|---|---|---|---|---|---|
| f1_faulty_01 | FAILED | INCONCLUSIVE | 51.0 / 52.0 | 156.5 | 0.134 | Preconditions not met: pump not shown submerged |
| f1_repaired_01 | PASSED_OR_INCONCLUSIVE | INCONCLUSIVE | 34.0 / 33.0 | 222.7 | 0.118 | C2_flow: 76% of healthy speed (fill 34.0 s, typed 33.0 s, healthy 26.0 s) vs pass 80%, fail below 60% (between thresholds) |
| adv_never_on_01 | INCONCLUSIVE | INCONCLUSIVE | – / – | 79.3 | 0.055 | C1_running: Switch-on not shown; C2_flow: Fill start or water reaching the fill line not seen in the test clip; C4_cause_addressed: Close-up job token not read or does not match this job |
| adv_pump_hidden_01 | INCONCLUSIVE | INCONCLUSIVE | 47.0 / – | 154.8 | 0.134 | Preconditions not met: job token not read or does not match (possible reused video); pump not shown submerged |
| adv_reused_01 | INCONCLUSIVE | INCONCLUSIVE | 26.0 / – | 105.9 | 0.084 | Preconditions not met: job token not read or does not match (possible reused video) |
