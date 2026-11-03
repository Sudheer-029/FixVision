# Component: Service record

**Purpose:** Produce the evidence-backed record a manager can review.
**Code:** `backend/app/records/record.py`, `frontend/app/jobs/[id]/record/`, `GET /jobs/{id}/record`

Contents: job id and token, equipment, fault hypothesis, symptom transcript, verdict and reasons, each check, measurements (fill time from video and typed, run time), test conditions, uncertainties, requested actions, evidence frames, guide sections used, model ids, thresholds version, timestamps, reviewer decision.

Formats: page in the app (print or save as PDF from the browser) and JSON. Every fact comes from structured fields; no model writes any part of the record.
