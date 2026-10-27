# Component: Perception service (SAM 3.1)

**Purpose:** Turn named components into tracked regions and frame-level signals the verification engine can use.
**Code:** `backend/app/perception/`

## Prompts
Concept prompts (one per request): `pump`, `water stream`, `hose`, `measuring jug`, `intake`. Box prompt on the joint region selected at check time (`<0f>` + box token).

## Signals produced
| Signal | Definition |
|---|---|
| `visible_ratio[component]` | Share of sampled frames with a mask for the component |
| `stream_present[frame]` | Water-stream mask area above a minimum |
| `joint_in_view_s` | Seconds the joint box track is present |
| `intake_occlusion` | Mask overlap of foreign object with intake region (F1 close-up) |

## Settings
Frames sampled at `SAM_SAMPLE_FPS` (default 10) after trimming to the test window; `include_confidence: "true"`; stream responses; parse with `meta-sam-parser`.

## Cost
$0.20 per 1,000 frames (min 50 per request). A 30 s clip at 10 fps ≈ 300 frames ≈ $0.06.

## Failure modes
Empty result for a concept → signal = 0 (not an error); `400` → fix prompt, no retry; out-of-order frames → sort by frame marker.

## Tests
Parser unit tests on saved streams; signal tests on sample clips.
