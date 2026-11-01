# Changelog

All notable changes. Format: [Keep a Changelog](https://keepachangelog.com/). Dates in IST.

## [Unreleased]

### Added
- 2026-10-27: Project documentation set, verification spec, rig protocol, build plan.
- 2026-10-28: Fireworks fine-tuning plan (ADR-0006, build task T12), budgets for Baseten and Fireworks credits.
- 2026-10-30: Claude Code project kit (.claude commands, skills, subagents, settings) and weekend runbook.
- 2026-10-30: ADR-0007, flow timed from the test clip.
- 2026-10-30: T1 scaffold (FastAPI backend, Next.js frontend, CI).
- 2026-11-01: T2 Meta API client (retries, cache, cost ledger, spend limit), Baseten client, `scripts/smoke.py`.
- 2026-11-01: T4 SAM 3.1 perception (`backend/app/perception/`: ffmpeg sampling, `glass jar` and `white pump` prompts, presence timelines), recorded SAM fixtures, `scripts/perceive.py`; ADR-0009 (C1 water flow from Muse Spark).
- 2026-11-01: T3 verification engine (`backend/app/verification/`) with boundary, adversarial and property tests at 100% branch coverage (enforced in CI); `scripts/verify_json.py`.

### Changed
- 2026-11-01: Fixed `count_video_frames` failing on MP4s where ffprobe prints a trailing comma.
- 2026-11-01: Scope narrowed to F1 blocked inlet on the rig as built (9 V battery, jar with a fill line); flow judged as speed relative to the healthy baseline; spec v0.3, ADR-0008; healthy baseline and clip labels from the first recording session.
- 2026-11-01: Verification spec clarified after T3 spec review: evidence validation at load (NaN, duplicate observations, token format), bounded thresholds, conservative "seconds with a mask", timelines keyed by clip, `run_s` in the verdict.
- 2026-10-30: Verification spec v0.2 after audit: one canonical observation list, per-clip timeline in seconds, job token on test clip and post-repair close-up, ordered verdict steps (scope → preconditions → observed failure → evidence → passed), fill-window integrity checks, F3 evidence, SAM presence timelines at 3 fps (error ≠ zero) with realistic cost, build plan re-dated, trials recorded Saturday, deployment on Render.
