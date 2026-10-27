# Deployment

| Part | Target | Notes |
|---|---|---|
| Web app | Vercel | `NEXT_PUBLIC_API_URL` points to the API |
| API + worker | Modal (or Render) | Secrets from the platform's secret store; persistent volume for SQLite and media |
| Open weights | Baseten | `meta-models/muse-spark-open-1026` |

## Release
1. CI green on `main`.
2. Tag `vX.Y.Z`, update `CHANGELOG.md`.
3. Deploy API, then web app; run `scripts/smoke.py` against production.

## Rollback
Redeploy the previous tag on both platforms; database migrations must be backward compatible (additive only during the hackathon).
