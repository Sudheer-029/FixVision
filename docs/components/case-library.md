# Component: Case library

**Purpose:** Store approved records and retrieve similar cases as context for triage.
**Code:** `backend/app/cases/`

- Only `REVIEWED/approved` records are added, with consent flag.
- Retrieval: filter by equipment and symptom keywords, then rank by similarity of transcript and triage summary (simple embedding or keyword score; no claims of learning).
- Retrieved text passes the guard layer.
- Export of approved cases feeds the eval dataset (dev split only).
