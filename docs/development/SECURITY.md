# Security and data handling

## Secrets
`.env` only (never committed); rotate if exposed.

## Data
- Demo and eval data are staged rig recordings with no people's faces or voices beyond the author.
- Uploads and evidence frames stay in `data/private/` on the local machine until you delete them; nothing deletes them automatically.

## Threat model (summary)
| Threat | Mitigation |
|---|---|
| Prompt injection via transcript or video | No separate scanner (ADR-0011); schema-checked outputs; verdict by rules. Injected text could still distort an observation; not scanned for |
| Fake or reused evidence | Job token in frame; switch-on and running checks; Inconclusive by default |
| Key leakage | No keys in client; server-side calls only |
| Unsafe guidance | Approved guide only, cited sections, stop conditions, technician approval |
| Open API | No login yet: run locally, never on a public URL |
