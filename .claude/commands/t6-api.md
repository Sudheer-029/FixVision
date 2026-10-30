---
description: T6 - job orchestrator, REST API, worker, SQLite
---
Read docs/components/orchestrator.md and docs/architecture/ARCHITECTURE.md §4.

Implement the job state machine (illegal transition → 409), SQLModel/SQLAlchemy tables (jobs, media, observations, verdicts, records, cost ledger), the endpoints in orchestrator.md, an async worker (simple in-process queue is fine) so model calls run off the request path, idempotent steps keyed by job_id + step, and `GET /jobs/{id}/trace` (calls, latency, cost per step). Job creation returns a random 4-character job token.
API tests with mocked clients covering the full happy path and an Inconclusive path.
Run /check, commit `feat: T6 orchestrator and API`.
