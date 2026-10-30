---
description: T12 (stretch) - fine-tune a Muse open model on Fireworks
---
Only run this if T1–T10 are done. Read docs/architecture/adr/ADR-0006-fireworks-fine-tuned-observer.md.
Export dev-split observe_test examples (inputs + labeled observations JSON) to Fireworks' supervised fine-tuning format; never include test-split clips. Add a Fireworks client (OpenAI-compatible, FIREWORKS_BASE_URL), a script to start the job on FIREWORKS_BASE_MODEL, and eval configs `fw-base` and `fw-tuned`. Run both on the test split and add the rows to docs/EVALS.md. Adopt the tuned model only if false passes do not increase.
Run /check, commit `feat: T12 Fireworks fine-tuned observer`.
