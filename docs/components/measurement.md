# Component: Measurement input

**Purpose:** Capture technician-entered test values and test conditions.
**Code:** `backend/app/measurement/`, test screen in the web app

Fields: `fill_time_s` (to the fill line, typed cross-check), `supply` (`battery_9v`, `usb_5v`), `head_cm`, `water_level_cm`, notes.
Flow is **not** computed from the typed time. The verification engine computes speed relative to the healthy baseline from the video (`fill_line_t − fill_start_t`, see [ADR-0007](../architecture/adr/ADR-0007-flow-timed-from-video.md)) and uses `fill_time_s` only to detect disagreement (> 15% → C2 insufficient).
Validation: `fill_time_s` between 5 and 600; `head_cm` and `water_level_cm` between 0 and 200; else reject input.
