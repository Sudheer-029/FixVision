# Build plan

**Builder:** solo, Indie Developer track · **Tools:** Claude Code (dev), Muse Code (selected modules) · **Deadline:** Nov 4, 9:00 PM ET = **Nov 5, 7:30 AM IST**; target submission Nov 4 evening IST.

## Phases

| Phase | Dates (IST) | Goal | Done when |
|---|---|---|---|
| 0 Setup | Oct 27–28 | Accounts, repo, smoke calls, rig built, baseline measured | Every model answers a smoke call; `rig_baseline.yaml` filled; repo public |
| 1 Core pipeline | Oct 28–30 | Upload → perception signals → observations → verification engine → verdict (CLI) | 3 faults × repaired / faulty produce correct verdicts on sample clips from CLI |
| 2 Product | Oct 31–Nov 1 | Web app capture flow, triage, guidance, voice, records, trace view, guard | Full flow on a phone; guard blocks a test injection; deployed |
| 3 Evidence | Nov 1–2 | Record trials, run evals, fill results, open-weight step | `EVALS.md` results table filled from the test split |
| 4 Ship | Nov 3–4 | Video, README, diagrams, Well-Architected review, submission | Submitted; X post live |

**Cut order if behind:** Fireworks fine-tuning → Muse Image step cards → prompt-ops / Meta-Harness → case-library retrieval → voice (fallback: typed symptom) → PDF export. Never cut: verification engine, adversarial cases, trace view.

## Budget

| Item | Estimate |
|---|---|
| Muse Spark 1.3 (standard), ~300 dev jobs | ~$25–40 (video token cost to be measured Day 1) |
| SAM 3.1 video, ~450 clips × ~300 frames | ~$27 |
| Voice Transcribe | < $1 |
| Evals on contributor mode / Baseten | ~$5 Meta + partner credits |
| Muse Image (optional) | < $2 |
| **Total Meta API** | **~$60–75 of the $150 credit** |
| Baseten (Muse Spark Open evals, record summaries) | ~$30–60 of the $100 credit |
| Fireworks (one fine-tuning job + eval inference, stretch) | ~$20–50 of the $100 credit |

Daily spend check on the Billing page; `DAILY_SPEND_LIMIT_USD` enforced in the client.

## Phase 0 checklist

- [x] Meta Model API account, $150 credit claimed (spend limit set)
- [x] Baseten $100 credit received
- [x] Fireworks $100 credit received (2026-10-28); API key in local `.env`, usage alert set
- [ ] Modal credit requested (pending)
- [ ] Watch the Fireworks session Fri Oct 30, 9:30 PM IST (fine-tuning Muse open models); note the base model id
- [x] Public GitHub repo created: https://github.com/Sudheer-029/FixVision (commit these docs)
- [ ] `scripts/smoke.py` calls each model once
- [ ] Rig assembled; 5 healthy baseline runs recorded; `config/rig_baseline.yaml`
- [ ] `data/guides/pump_guide.md` written (our own words: symptoms, causes, steps, stop conditions for F1–F3)
- [ ] Ask in #office-hours: SAM 3.1 video limits for hackathon accounts; Muse Spark video token cost

## Task prompts for Claude Code

The same tasks exist as slash commands in `.claude/commands/` (`/t1-scaffold` … `/t12-fireworks`); follow [WEEKEND_RUNBOOK.md](WEEKEND_RUNBOOK.md) for the order.

Use one prompt per session. Always attach the referenced docs.

**T1 Repo scaffold** — "Read README.md, docs/development/DEVELOPMENT.md and docs/architecture/ARCHITECTURE.md. Create the backend (FastAPI, uv, ruff, pytest) and frontend (Next.js, TypeScript strict) skeletons in the target layout, a GitHub Actions CI running ruff, pytest and eslint, and no business logic yet. Do not create a CLAUDE.md."

**T2 Meta client** — "Read docs/META_API_NOTES.md and ADR-0003. Implement backend/app/clients/meta_client.py using the openai SDK with base_url and MODEL_API_KEY: responses + chat completions with JSON-schema output, file upload, retries with exponential backoff on 429/5xx, no retry on 400, 60 s timeout, content-hash response cache, and a cost ledger row per call using the prices in the notes. Add scripts/smoke.py. Tests use recorded fixtures only."

**T3 Verification engine** — "Read docs/VERIFICATION_SPEC.md and docs/components/verification-engine.md. Implement the Pydantic schema, the five checks and the verdict combiner as pure functions with table-driven tests covering every boundary and every adversarial case in §6. 100% branch coverage."

**T4 Perception** — "Read docs/components/perception-sam.md and the SAM section of META_API_NOTES.md. Implement frame sampling with ffmpeg, SAM 3.1 concept and box prompts over the Responses API with streaming, parsing with meta-sam-parser, and the signals table. Tests on saved stream fixtures."

**T5 Reasoning agent** — "Read docs/components/reasoning-agent.md. Implement triage, guidance and observe_test with JSON-schema outputs, prompt files, grounding in data/guides/pump_guide.md, and golden-file tests."

**T6 Orchestrator + API** — "Read docs/components/orchestrator.md. Implement the state machine and endpoints, async worker, SQLite models, trace endpoint. API tests with mocked clients."

**T7 Web app** — "Read docs/components/capture-web-app.md. Build the mobile-first capture flow, verdict view, trace view and manager review against the API."

**T8 Voice + measurement + guard** — "Read voice-input.md, measurement.md and guard-layer.md. Implement each with tests, including the 20-string injection red-team set."

**T9 Records + case library** — "Read service-record.md and case-library.md. Implement the record (HTML + JSON), manager approval, and retrieval of approved cases."

**T10 Evals** — "Read docs/EVALS.md and evals-harness.md. Implement the trial runner over data/labels.csv with dev/test splits, frozen-config guard for test, caching, and a markdown report that fills the EVALS results table."

**T11 Open weights** — "Read ADR-0004. Add a Baseten client for meta-models/muse-spark-open-1026 used for record summaries and as an alternate eval backend, selected by config."

**T12 Fireworks fine-tune (stretch, only if Phases 1–2 are done by Nov 1)** — "Read ADR-0006, docs/EVALS.md and docs/components/evals-harness.md. Export the dev-split observe_test examples (input: sampled frames + check list + SAM signals; output: the labeled observations JSON) to Fireworks' supervised fine-tuning format, never including test-split clips. Add a Fireworks client (OpenAI-compatible, FIREWORKS_BASE_URL) selectable by config, a script to launch the fine-tuning job on FIREWORKS_BASE_MODEL, and an eval config that runs observe_test with the base and tuned models on the test split and adds both rows to the EVALS results table."

## Daily routine

Morning: pick tasks, note them in HACKATHON_LOG. Build in small PRs. Evening: Discord office hours for blockers, update log, changelog, spend check.
