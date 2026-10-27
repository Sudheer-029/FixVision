# Testing strategy

| Level | Scope | Tooling | Runs |
|---|---|---|---|
| Unit | Verification checks and combiner, parsers, state machine | pytest | Every commit (CI) |
| Contract | Model client against recorded responses (no network) | pytest + fixtures | CI |
| Integration | API end to end with mocked models | pytest + httpx | CI |
| Live smoke | One real call per model | `scripts/smoke.py` | Manually, daily |
| End to end | Web flow with sample clips | Playwright | Before demo |
| Evaluation | Labeled trials, metrics | `evals/` | Phase 3, final on test split |

Rules: the verification engine needs 100% branch coverage; every adversarial case in the spec has a fixture; no test spends money in CI.
