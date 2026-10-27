# Component: Measurement input

**Purpose:** Capture measured test values and test conditions.
**Code:** `backend/app/measurement/`, test screen in the web app

Fields: `fill_time_s` (500 mL), `supply` (`fresh_aa_x4`, `used_aa_x4`, `usb_5v`), `head_cm`, `water_level_cm`, notes.
Derived: `flow_lpm = 0.5 / fill_time_s × 60`.
Cross-check: reasoning agent reports `timer_visible`; if not visible, C2 evidence is insufficient.
Validation: `fill_time_s` between 5 and 600; else reject input.
