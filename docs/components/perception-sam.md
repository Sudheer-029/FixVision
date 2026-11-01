# Component: Perception service (SAM 3.1)

**Purpose:** Turn named components into tracked regions and frame-level signals the verification engine can use.
**Code:** `backend/app/perception/`

## Prompts
Concept prompts (one per request), only where a check needs them:

| Concept | Clip / window | Check |
|---|---|---|
| `pump` | Test clip, first 5 s | C0 |
| `jar` | Whole test clip (fill window not yet known) | C0, C2 |
| `hose` | Whole test clip | C0, C3 |
| `water stream` | Whole test clip (run window not yet known) | C1 |
| `intake` | Post-repair close-up | C4 |

If a concept returns no mask in the first 5 s, the capture screen can ask the technician to tap that part on the first frame, and the point is sent as a `<0f>` point prompt.

## Output
Per concept, a presence timeline: sampled times in seconds from clip start where a mask is present, plus the sample interval. A successful request with no match → empty timeline. A request that errors → `None` (no timeline), so the engine treats it as missing evidence, never as zero presence. The engine derives the windowed values in [VERIFICATION_SPEC §4.2](../VERIFICATION_SPEC.md). Runs in parallel with `observe_test`.

## Settings
Frames sampled at `SAM_SAMPLE_FPS` (default 3; enough to see whether water is flowing) after trimming to each window; `include_confidence: "true"`; stream responses; parse with `meta-sam-parser`. Responses cached by content hash.

## Cost
$0.20 per 1,000 frames, minimum 50 frames per request, and **every concept is a separate request billed for all its frames**. A 60 s test clip at 3 fps: `water stream` + `hose` + `jar` ≈ 540 frames, `pump` on 5 s = 50 billed frames, `intake` close-up = 50 → ≈ 640 frames ≈ **$0.13 per job**.

## Failure modes
Empty result for a concept → empty timeline (not an error); request error → no timeline; `400` → fix prompt, no retry; out-of-order frames → sort by frame marker.

## Tests
Parser unit tests on saved streams; timeline tests on sample clips.
