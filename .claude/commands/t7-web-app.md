---
description: T7 - mobile web app (guided capture, verdict, trace, review)
---
Read docs/components/capture-web-app.md.

Build in `frontend/` the 8 screens listed there against the API. Priorities: (1) new job with big job token, (2) functional-test screen with the on-screen checklist and running timer, measurement fields, upload, (3) verdict screen with Passed / Failed / Inconclusive colour, reasons, requested actions and evidence frames, (4) trace view, (5) symptom + check + guidance, (6) manager review.
Mobile first, works in Safari on iPhone and Chrome on Android; file-input fallback when MediaRecorder is unavailable. Clean, readable, no external UI kit required.
Add one Playwright smoke test with a sample clip. Run /check, commit `feat: T7 web app`.
