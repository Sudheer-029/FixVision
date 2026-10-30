---
description: T9 - service record, manager review, case library
---
Read docs/components/service-record.md and case-library.md.
Service record: HTML view + JSON export with every field listed; facts only from structured data. Optional short summary from Muse Spark Open via the Baseten client (label it "AI summary").
Manager review: approve / reject with note; only approved records with consent flag enter the case library.
Case library: keyword + equipment retrieval of approved cases, passed through the guard, fed to triage as context.
Tests for record completeness and the approval gate. Run /check, commit `feat: T9 records and case library`.
