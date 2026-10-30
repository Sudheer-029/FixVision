---
description: T1 - create backend and frontend skeletons with CI
---
Read README.md, docs/development/DEVELOPMENT.md, docs/development/TESTING.md and docs/architecture/ARCHITECTURE.md.

Create:
- `backend/`: Python 3.12 project managed by uv (`pyproject.toml`), FastAPI app at `backend/app/main.py` with `GET /health`, package folders matching DEVELOPMENT.md (api, jobs, clients, agents, perception, voice, measurement, verification, records, cases, guard) each with `__init__.py`, settings loaded from `.env` via pydantic-settings using the variables in `.env.example`, pytest + ruff configured, one passing test for /health.
- `frontend/`: Next.js (App Router, TypeScript strict, ESLint), a placeholder home page "FixVision", `NEXT_PUBLIC_API_URL` read from env.
- `config/rig_baseline.yaml` with placeholder values and comments, `data/guides/`, `data/samples/`, `data/labels.csv` header (`clip_id,session,split,fault,state,expected_verdict,notes`).
- `.github/workflows/ci.yml`: ruff + pytest for backend, lint + build for frontend.

Rules: no business logic yet; no secrets; do not create CLAUDE.md.
Done when: `cd backend && uv run pytest` passes, `uv run ruff check .` is clean, `cd frontend && npm run build` succeeds.
Then run /check and commit: `feat: T1 project scaffold`.
