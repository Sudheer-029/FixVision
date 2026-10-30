---
description: T11 - open-weight backend on Baseten
---
Read docs/architecture/adr/ADR-0004-open-weights-and-contributor-mode.md.
Finish `baseten_client.py` for `meta-models/muse-spark-open-1026` (OpenAI-compatible; take the base URL from Baseten's docs or dashboard). Use it for the record summary and as an alternate backend for `observe_test` selected by config (`OBSERVER_BACKEND=meta|baseten`). Add an eval config `open-weights` and run it on the dev split. Make sure the trace view shows which backend ran (needed for the open-weights prize).
Run /check, commit `feat: T11 Muse Spark Open on Baseten`.
