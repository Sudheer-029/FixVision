# Security and data handling

## Secrets
`.env` only (never committed); platform secret stores in deployment; separate keys for dev and demo; rotate if exposed.

## Data
- Demo and eval data are staged rig recordings with no people's faces or voices beyond the author.
- Media retention: `MEDIA_RETENTION_DAYS` (default 7) for raw uploads; records keep sampled evidence frames only.
- `data_class = customer` jobs never use contributor-mode models (their content may be used for training).

## Threat model (summary)
| Threat | Mitigation |
|---|---|
| Prompt injection via transcript or video | No separate scanner (ADR-0011); schema-checked outputs; verdict by rules. Injected text could still distort an observation; not scanned for |
| Fake or reused evidence | Job token in frame; switch-on and running checks; Inconclusive by default |
| Key leakage | No keys in client; server-side calls only |
| Unsafe guidance | Approved guide only, cited sections, stop conditions, technician approval |
| Open API | No login yet: run locally, never on a public URL |
