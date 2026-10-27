# Security and data handling

## Secrets
`.env` only (never committed); platform secret stores in deployment; separate keys for dev and demo; rotate if exposed.

## Data
- Demo and eval data are staged rig recordings with no people's faces or voices beyond the author.
- Media retention: `MEDIA_RETENTION_DAYS` (default 7) for raw uploads; records keep sampled evidence frames only.
- `data_class = customer` jobs never use contributor-mode models (their content may be used for training).
- Case library entries require a consent flag.

## Threat model (summary)
| Threat | Mitigation |
|---|---|
| Prompt injection via transcript or case text | Guard layer before prompts; structured outputs; verdict by rules |
| Fake or reused evidence | Job token in frame; switch-on and running checks; Inconclusive by default |
| Key leakage | No keys in client; server-side calls only |
| Unsafe guidance | Approved guide only, stop conditions, scope refusal, technician approval |
