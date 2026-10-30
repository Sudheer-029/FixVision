---
name: fixvision-rules
description: Non-negotiable product, verification and hackathon rules for FixVision; use whenever writing verification, agent, prompt, data or demo code in this repo.
---

# FixVision rules

## Product invariants
1. **The verdict comes only from `backend/app/verification/`** (deterministic rules in docs/VERIFICATION_SPEC.md). Models output observations with confidence and frame references; they never output Passed/Failed/Inconclusive.
2. **No evidence, no verdict.** Missing or low-confidence evidence → `insufficient_evidence` → `INCONCLUSIVE`. When in doubt, choose Inconclusive.
3. **False Passed is the worst error.** Any change that could increase false passes needs a test proving it does not.
4. **SAM 3.1 only segments and tracks.** Never describe or code it as diagnosing faults.
5. **Wording:** "Passed these checks under these conditions", never "proved fixed" or "guaranteed".
6. **Guidance** comes only from `data/guides/pump_guide.md` and approved cases, always with stop conditions, always requiring technician approval.
7. **Scope:** 3–6 V mini submersible pump, faults F1 blocked inlet, F2 leaking joint, F3 weak supply. Anything else → refuse / Inconclusive with escalation.
8. **Self-improvement claims** only from the held-out test split (ADR-0005). Never tune on test data.

## Data and safety
- Contributor-mode models and fine-tuning only with `data_class = staged` rig data.
- No copyrighted manuals, stock video or personal data in the repo. Only small curated clips under `data/samples/`.
- Low-voltage rig only; disclose staged faults.

## Hackathon rules (Meta Global AI Developer Hackathon)
- All work committed between Oct 26 and Nov 4, 2026; small, dated commits.
- Repo stays public; never commit `.env` or keys.
- In-product AI = Meta models (API or open weights). Claude Code / Muse Code are dev tools only.
- Credit every third-party tool in THIRD_PARTY.md; keep "Built during the hackathon" in README accurate.
- Do not create CLAUDE.md (owner's choice).

## Engineering conventions
- Python 3.12, type hints, Pydantic for every external payload, ruff + pytest; prompts in files with ids; all model calls via `backend/app/clients/`.
- Each component change updates its doc in docs/components/; real design choices get an ADR (`/adr`).
