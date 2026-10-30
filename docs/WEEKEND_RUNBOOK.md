# Weekend runbook (Oct 30 – Nov 4, IST)

How to build FixVision with Claude Code, one step at a time. Each step = one slash command in a **fresh Claude Code session**, then review → `/check` → commit → push.

## One-time setup (Fri, 15 min)
1. Open the `FixVision` folder in Claude Code (desktop app → open folder).
2. Local `.env`: `cp .env.example .env`, fill `MODEL_API_KEY`, `BASETEN_API_KEY`, `FIREWORKS_API_KEY`. Claude cannot read `.env` (blocked in `.claude/settings.json`); programs still load it.
3. Install tools on the Mac: `brew install uv ffmpeg node` (skip what you have).
4. If Claude Code offers `/init` (it creates CLAUDE.md), skip it. Project context lives in `.claude/skills/` and `docs/`.
5. Optional: `npx skills add tt-a1i/archify -g` for diagrams.

## Order of work

| # | When | Command | Done when | Needs |
|---|---|---|---|---|
| 1 | Fri | `/t1-scaffold` | pytest, ruff, `npm run build` pass | — |
| 2 | Fri | `/t2-meta-client` | `scripts/smoke.py` OK for every model; video tokens noted | `.env` keys, one short MP4 in `data/samples/` |
| 3 | Fri | `/t3-verification` | 100% branch coverage on verification | — |
| — | Fri 9:30 PM | Fireworks livestream | Base model id noted in `.env` | — |
| 4 | Sat AM | Build rig, record baseline (RIG.md) | `config/rig_baseline.yaml` filled; 2–3 clips per fault | Pump parts |
| 5 | Sat | `/t4-perception` | `scripts/perceive.py` prints signals for a real clip | Clips |
| 6 | Sat | `/t5-reasoning` | `scripts/run_clip.py` gives correct verdicts for F1–F3 repaired and faulty | — |
| 7 | Sat PM | `/t6-api` | API tests pass, happy + Inconclusive paths | — |
| 8 | Sun | `/t7-web-app` | Full flow on your phone | Laptop and phone on same Wi-Fi, or deploy |
| 9 | Sun | `/t8-guard-voice-measure` | Red-team test passes | — |
| 10 | Sun | `/t9-records` | Record view + approval work | — |
| 11 | Sun PM | Deploy (DEPLOYMENT.md) + record the 3 demo cases | Live URL works | — |
| 12 | Mon | Record ~50 labeled trials, `/t10-evals` | EVALS table filled from test split | Rig |
| 13 | Mon | `/t11-baseten` | Open-weights eval config runs | Baseten key |
| 14 | Mon (stretch) | `/t12-fireworks` | Base vs tuned rows in EVALS | Fireworks key |
| 15 | Tue | `demo-director` subagent → record and edit video | ≤ 3:00, all checklist items | — |
| 16 | Wed | Final checks, submit, post on X | Submitted before evening IST | — |

Daily: `/next` to see where you are, `/log-day` at night.
After any change to verification, agents, prompts or perception: ask "use the spec-reviewer subagent on my changes".

## Session tips
- One task per session; start with the slash command, then answer its questions.
- Ask Claude to show the plan before writing code for T3–T7.
- If a step stalls for more than 45 minutes, cut scope (cut order in BUILD_PLAN.md) rather than push through.
- Keep the spend check: the cost ledger total vs DAILY_SPEND_LIMIT_USD.

## Git per step
```bash
git checkout -b feat/t3-verification
# ... Claude Code works, /check passes ...
git add -A && git commit -m "feat: T3 verification engine with adversarial tests"
git checkout main && git merge --no-ff feat/t3-verification && git push origin main
```
Working alone and short on time? Committing straight to `main` is fine; keep commits small.
