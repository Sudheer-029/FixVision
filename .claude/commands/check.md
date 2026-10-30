---
description: Pre-commit check for tests, lint, secrets, docs and hackathon rules
---
Run and report (fix what you can, list what you could not):
1. `cd backend && uv run ruff check . && uv run pytest -q` ; if frontend changed: `cd frontend && npm run lint && npm run build`.
2. Secrets: `git diff --cached` and the working tree contain no API keys, no `.env`, no tokens (search for `MODEL_API_KEY=`, `sk-`, `Bearer `). `.env` must be git-ignored.
3. No raw media or copyrighted material staged (only files under data/samples/ are allowed).
4. Docs in sync: if a component changed, its docs/components/*.md is updated; any real design choice has an ADR.
5. Rules: all in-product AI calls go through backend/app/clients/ to Meta models (or Baseten/Fireworks open weights); verdicts come only from backend/app/verification/.
6. No CLAUDE.md file was created.
Finish with a one-line PASS / FAIL summary and a suggested conventional commit message.
