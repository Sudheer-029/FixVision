# Development guide

## Prerequisites
Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 20+, ffmpeg, git. A Meta Model API key (`MODEL_API_KEY`).

## Repository layout (target)
```
backend/            FastAPI app (api, jobs, agents, perception, voice, measurement, verification, records, cases, guard)
frontend/           Next.js web app
evals/              trial runner and reports
config/             rig_baseline.yaml, thresholds
data/guides/        pump_guide.md (written by us)
data/samples/       a few small demo clips (committed)
data/labels.csv     trial labels (committed); raw clips are not committed
docs/               all documentation
```

## Run locally
```bash
cp .env.example .env
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev   # http://localhost:3000
```

## Conventions
- Python: type hints, Pydantic models for every external payload, `ruff` + `pytest`.
- TypeScript: strict mode, `eslint`.
- All model calls go through `backend/app/clients/meta_client.py` (retries, timeouts, caching, cost log). No direct SDK calls elsewhere.
- Prompts live in files, versioned, referenced by id in traces.
- No secrets in code, tests or fixtures.

## Git workflow
- `main` is always demo-able. One feature per branch: `feat/<name>`, `fix/<name>`, `docs/<name>`.
- Conventional commits: `feat: verification engine C2 flow check`.
- Small PRs, merged after CI passes. Update `HACKATHON_LOG.md` daily and `CHANGELOG.md` per merge.
- Any real choice between options → an ADR the same day.

## Working with Claude Code
- One task at a time, with the matching component doc and the spec section in the prompt.
- Ask for tests with every change; review every diff before committing.
- Keep docs in sync: a change to a component updates its doc in the same PR.
- See `docs/BUILD_PLAN.md` for the task prompts.
