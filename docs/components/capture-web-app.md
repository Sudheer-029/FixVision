# Component: Capture web app

**Purpose:** Guide the technician to record the right evidence, step by step, on a phone browser.
**Code:** `frontend/` (Next.js)

## Screens
1. New job: equipment (supported pump), data class (`staged`/`customer`), job token shown large.
2. Symptom: record clip (≤ 30 s) + hold-to-talk voice note.
3. Check: shows the requested diagnostic check with the SAM highlight on a reference frame; record close-up.
4. Guidance: steps with approve / stop buttons; stop conditions shown first.
5a. Post-repair close-up (≤ 10 s): job token in view, then the clean intake.
5. Functional test: checklist overlay (setup with job token in view, power on, run ≥ 20 s, keep the hose and jar in frame until the water passes the fill line, power off), running timer, fields for fill time and conditions. If SAM cannot find a part, show the first frame and ask the technician to tap it.
6. Verdict: Passed / Failed / Inconclusive, reasons, requested actions, evidence frames **with SAM's box drawn on them** (jar, intake), taken from the sampled frame nearest the moment that matters, so the viewer sees what was measured.
7. Trace: per-step model calls, latency, cost (demo and debugging).
8. Manager review: approve / reject with note.

## Not built yet
Hold-to-talk voice (T8; the symptom screen has a text field), the SAM highlight on the check screen, and tap-to-select when SAM cannot find a part. Step approvals are kept in the page only (shortcut until the T9 service record). Runs locally; there is no public hosting.

## Interfaces
REST calls to the API (see `orchestrator.md`) through a Next.js rewrite: the browser calls `/api/*`, and `API_ORIGIN` (default `http://localhost:8000`) says where the API is. Uploads via multipart; MP4 (H.264) recorded with `MediaRecorder` where supported, else file input.

## Failure modes
Upload fails → retry with resume; unsupported codec → server transcodes with ffmpeg; camera permission denied → file upload fallback.

## Tests
Playwright smoke test (`npm run e2e`) for the full flow, against the real API and worker on mocked models (`backend/tests/e2e_app.py`), so it spends no credit.
