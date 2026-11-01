# Component: Job orchestrator and API

**Purpose:** Own the job state machine and expose the REST API.
**Code:** `backend/app/api/`, `backend/app/jobs/`

## API (v0)
| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs` | Create job (equipment, data_class) → job id, token |
| POST | `/jobs/{id}/media` | Upload clip or audio with `kind` (`symptom`, `check`, `closeup` (post-repair), `test`, `voice`) |
| POST | `/jobs/{id}/triage` | Run reasoning on symptom → causes + requested check |
| POST | `/jobs/{id}/guidance` | Guidance for the confirmed cause |
| POST | `/jobs/{id}/test` | Submit test measurements and conditions; starts verification |
| GET | `/jobs/{id}` | Job state, verdict, record |
| GET | `/jobs/{id}/trace` | Model calls, latency, cost |
| POST | `/jobs/{id}/review` | Manager approve / reject |

## State machine
See `ARCHITECTURE.md` §4. Transitions are validated; illegal transitions return `409`.

## Failure modes
Model timeout → step marked `error`, user can retry; worker crash → step resumable (idempotent by `job_id + step`).

## Tests
State-transition unit tests; API tests with mocked model clients.
