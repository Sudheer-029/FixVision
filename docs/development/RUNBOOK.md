# Runbook

| Symptom | Likely cause | Action |
|---|---|---|
| Many `429` from Model API | Rate limit | Backoff is automatic; reduce eval concurrency |
| `404 model_not_found` | Wrong model id or no access | Check `GET /v1/models`; fix env |
| `400` from SAM | Bad prompt or media format | Check prompt is one noun phrase; transcode to H.264 MP4 |
| Verdicts mostly Inconclusive | Capture guidance unclear or thresholds too strict | Review traces; tune on dev split only |
| Spend rising fast | Eval loop on standard mode | Switch eval to contributor / open weights; check cost ledger |
| Upload fails on phone | Codec / size | Use file input fallback; server transcodes |

Daily checks during the hackathon: Billing page spend vs plan, error rate in traces, CI status.
