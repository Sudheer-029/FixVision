# ADR-0010: Fill times from time-labelled jar frames, cropped with SAM's jar box

- **Status:** Accepted
- **Date:** 2026-11-01
- **Pillars affected:** Reliability

## Context
C2 needs `fill_start_t` and `fill_line_t` (ADR-0007). Asked to time them from the test video, Muse Spark 1.3 read the code, switch on/off and the start of the flow well, but returned `fill_line_t = null` at 720p and 1080p, and also on a video cropped to the jar. Asked once for "the first frame at the line" from labelled stills, it answered 25 s where the frames show about 27 s.

## Decision
1. SAM 3.1 finds the jar (`glass jar`); its median box, padded 15%, crops the test clip.
2. ffmpeg extracts one cropped frame per second; frame *i* is at *i* seconds.
3. Muse Spark labels **every** frame `not_filling`, `below_line` or `at_line` (`observe_fill`); a wrong number of labels gets the repair retry.
4. Code turns labels into times: `fill_start_t` = first frame past `not_filling`, `fill_line_t` = first `at_line` frame. Labels that ever step back (e.g. `at_line` then `below_line`) get confidence 0.5, below the 0.7 threshold, so a muddled reading is missing evidence, not a time.
5. The healthy baseline is measured by the same pipeline, so any constant bias in where the model sees "at the line" cancels out in the relative speed.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Times from the video (ADR-0007 as written) | One call | Returned null for the fill line |
| One "first frame at the line" question | Cheaper | 2 s early on a 27 s fill |
| Pixel measurement of the water surface | No model | Fragile on clear water and glass; not observation by a model |
| Per-frame labels, times from frame index (chosen) | Times are exact frame times; steps back are detectable | 1 s resolution; one extra call (≈ $0.04 per clip) |

## Guards against a made-up fill
On `adv_never_on_01` (pump never switched on, jar empty throughout) the v1 prompt labelled the string ring around the empty jar as water at the line: a 4 s "fill". A made-up fast fill is the false-PASS risk, so:
- the prompt (v2) uses frame 0 as the empty-jar reference and warns that the string on an empty jar is not water;
- C2 trusts fill times only when the scene observation `water_flowing` is true with a time, and the fill line comes after it;
- C2 treats a speed above 150% of the healthy rig as untrusted (`insufficient_evidence`);
- run-window comparisons allow one frame (1 s), which can only lengthen the measured fill.

## Consequences
- Fill times are quantised to 1 s (±1 s on a ~26 s fill, about 4%); finer frames cost proportionally more.
- SAM's role grows: without a jar box there are no fill times, so C2 is `insufficient_evidence`.
- The cropped frames are an inspectable artifact for the record and the demo.
