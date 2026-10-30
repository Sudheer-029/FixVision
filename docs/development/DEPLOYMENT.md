# Deployment

| Part | Target | Notes |
|---|---|---|
| Web app | Vercel | `NEXT_PUBLIC_API_URL` points to the API |
| API + worker | Render (or Fly.io), one instance with a persistent disk | Secrets from the platform's secret store; SQLite and media on the disk. One instance only: SQLite does not share well across machines. Modal only if its credit arrives and a volume is tested |
| Open weights | Baseten | `meta-models/muse-spark-open-1026` |

## Release
1. CI green on `main`.
2. Tag `vX.Y.Z`, update `CHANGELOG.md`.
3. Deploy API, then web app; run `scripts/smoke.py` against production.

## Rollback
Redeploy the previous tag on both platforms; database migrations must be backward compatible (additive only during the hackathon).
