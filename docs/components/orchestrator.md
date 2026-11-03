# Component: Job orchestrator and API

**Purpose:** Own the job state machine and expose the REST API.
**Code:** `backend/app/api/`, `backend/app/jobs/`

## API (v0)
| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs` | Create job (equipment, data_class; a staged job may pass the `token` its recorded clip shows, a customer job never can) → job id, token |
| POST | `/jobs/{id}/media` | Upload clip or audio with `kind` (`symptom`, `check`, `closeup` (post-repair), `test`, `voice`) |
| POST | `/jobs/{id}/triage` | Run reasoning on symptom → causes + requested check |
| POST | `/jobs/{id}/guidance` | Guidance for the confirmed cause |
| POST | `/jobs/{id}/test` | Submit test measurements and conditions; starts verification |
| GET | `/jobs/{id}` | Job state, verdict, record |
| GET | `/jobs/{id}/evidence/{jar\|intake}` | Frame with SAM's box from the latest verdict |
| GET | `/jobs/{id}/trace` | Model calls, latency, cost |
| POST | `/jobs/{id}/review` | Manager approve / reject |

## State machine
See `ARCHITECTURE.md` §4. Transitions are validated; illegal transitions return `409`.

Uploading the post-repair close-up from `GUIDANCE_ISSUED` also records `REPAIR_REPORTED`. Re-uploading a clip in the state it produced replaces it (the latest clip of each kind is used).

## Worker and steps
`triage`, `guidance:<fault>` and `verify:<test media id>` run on one in-process worker thread, so `POST` returns `202` and the client polls `GET /jobs/{id}`. Each step is a row keyed by `job_id + step`; a queued, running or done step is never started again. Model calls hold no database session, and a step's result, rows and state change commit together. Each new test recording is its own `verify` attempt.

The trace reads `cost_ledger` (written by `MetaClient`, a separate SQLite file) and places each call under the step whose time window contains it.

## Failure modes
Model timeout or any step exception → step marked `error`, the job stays in its state and the same `POST` retries it. API clients see only the exception type; details stay in the server log. A restart marks unfinished steps `error`, so they can be retried (assumes one API process). No verdict is written unless verification ran.

## Storage
Tables in `app/jobs/models.py`: jobs, media, steps, observations, verdicts, records. Database and uploads live under `data/private/` (git-ignored). Upload limits: 300 MB, refused from `Content-Length` before the body is parsed; `.mp4 .mov .webm .m4a .wav`; the client's file name is never used on disk.

## Known limits
No authentication yet: the job id is the only access control and anyone holding it can approve a review, so the API must stay private until login and a manager role exist.

## Tests
State-transition unit tests; API tests with mocked model clients.
