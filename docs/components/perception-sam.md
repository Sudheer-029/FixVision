# Component: Perception service (SAM 3.1)

**Purpose:** Turn named components into tracked regions and frame-level signals the verification engine can use.
**Code:** `backend/app/perception/`

## Prompts
Concept prompts (one per request), only where a check needs them:

| Engine key | Prompt sent | Clip | Check |
|---|---|---|---|
| `jar` | `glass jar` | Whole test clip (fill window not yet known) | C0, C2 |
| `intake` | `white pump` | Whole post-repair close-up | C4 |

Prompts are the phrasings SAM matched on the real rig (2026-11-01, `Healthy_01` and the close-up). `jar`, `pump`, `water stream`, `hose`, `tube` and `bowl` returned no masks, even at 1080p: the stream and hose are thin clear plastic and water, and the pump sits behind the glass bowl. Those are observed by Muse Spark instead ([ADR-0009](../architecture/adr/ADR-0009-sam-only-where-it-sees.md)).

If a concept returns no mask in the first 5 s, the capture screen can ask the technician to tap that part on the first frame, and the point is sent as a `<0f>` point prompt.

## Output
Per concept, a presence timeline: sampled times in seconds from clip start where a mask is present, plus the sample interval. A successful request with no match → empty timeline. A request that errors → `None` (no timeline), so the engine treats it as missing evidence, never as zero presence. The engine derives the windowed values in [VERIFICATION_SPEC §4.2](../VERIFICATION_SPEC.md). Runs in parallel with `observe_test`.

## Settings
Frames sampled at `SAM_SAMPLE_FPS` (default 3) at full resolution (`frames.py`, H.264 MP4, no audio); `include_confidence: "true"`; stream responses; parse with `meta-sam-parser`. Responses cached by content hash.

## Cost
$0.20 per 1,000 frames, minimum 50 frames per request, and **every concept is a separate request billed for all its frames**. A 60 s test clip at 3 fps: `jar` ≈ 180 frames, close-up `intake` ≈ 50–70 frames → ≈ 250 frames ≈ **$0.05 per job**.

## Failure modes
Empty result for a concept → empty timeline (not an error); request error → no timeline; `400` → fix prompt, no retry; out-of-order frames → sort by frame marker.

## Tests
`tests/test_perception.py`: real SAM responses saved in `tests/fixtures/sam/` (trimmed to a few frames), no-match = empty timeline, garbled stream or request error = no timeline, ffmpeg sampling (skipped where ffmpeg is missing). `scripts/perceive.py <clip> [--closeup clip]` prints timelines and cost.
