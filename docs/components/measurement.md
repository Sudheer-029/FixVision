# Component: Measurement input

**Purpose:** Capture technician-entered test values and test conditions.
**Code:** `backend/app/measurement/`, test screen in the web app

Fields: `fill_time_s` (500 mL, typed cross-check), `supply` (`fresh_aa_x4`, `used_aa_x4`, `usb_5v`), `head_cm`, `water_level_cm`, notes.
Flow is **not** computed from the typed time. The verification engine computes `flow_lpm` from the video (`fill_mark_t − fill_start_t`, see [ADR-0007](../architecture/adr/ADR-0007-flow-timed-from-video.md)) and uses `fill_time_s` only to detect disagreement (> 15% → C2 insufficient).
Validation: `fill_time_s` between 5 and 600; `head_cm` and `water_level_cm` between 0 and 200; else reject input.
