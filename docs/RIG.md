# Demonstration rig and staged faults

**Status:** v0.2 (2026-11-01, the rig as built; see [ADR-0008](architecture/adr/ADR-0008-f1-only-relative-flow.md))

## Bill of materials

| Item | Source | Approx. price (INR) |
|---|---|---|
| Mini submersible pump, 3–6 V DC, 80–120 L/h | [Probots PRO919](https://probots.co.in/3-6v-mini-water-pump-submersible-for-diy-hobby-projects-120l-h.html) | 69 |
| Clear hose, about 5 mm inner diameter | Local hardware | 30 |
| 9 V battery with snap connector and a rocker switch | Local electronics | 40 |
| Glass bowl (source), raised on a box | Home | 0 |
| Tall clear jar with a string tied round it as the fill line (receiver) | Home | 0 |
| Second phone running a stopwatch, phone stand, sticky notes, marker | Home | 0 |

Avoid aquarium fountain pumps that run on 230 V mains.

## Layout

Source bowl with the pump submerged, raised on a box → hose over the rim, out of the water → hose end above the jar, so the falling stream is visible. Battery and switch on the box. Phone in landscape on a stand, framing (left to right) the stopwatch phone, the box with the job code on a sticky note, and the jar with its fill line. The water level in the source bowl is the same at the start of every run; the jar is emptied back into it between runs.

## Baseline

Fill time = first water entering the empty jar → water reaching the line. The median of the healthy clips recorded in the same session is stored as `baseline_fill_s` in `config/rig_baseline.yaml`. The 9 V battery weakens with use (healthy fills went from about 26 s to about 34 s within an hour), so the baseline is only valid for clips recorded in the same session.

## Staged fault

| ID | How to stage | How to repair |
|---|---|---|
| F1 blocked inlet | Cover most of the intake hole with tape or tissue until the fill takes about twice as long | Remove the blockage; record a close-up of the clean intake with the job code in shot |

## Recorded clips (2026-11-01, raw files in `data/raw/`, not committed)

| Clip | Code | What it shows |
|---|---|---|
| `Healthy_01` | K7M4 | Healthy fill, about 25.5 s |
| `Healthy_2` | K7M5 | Healthy fill, about 27 s |
| `F1_faulty_01` | P4T9 | Blocked intake, fill about 52 s |
| `f1_repaired_01_closeup` | R2C6 | Clean intake close-up |
| `f1_repaired_01` | R2C6 | Repaired, fill about 33 s (battery fading) |
| `adv_never_on_01` | T4M6 | Pump never switched on |
| `adv_hidden_01` (label `adv_pump_hidden_01`) | S2I3 | Pump covered by the code note at the start |

Times are estimates from frames; T4 measures them from the video. Labels live in `data/labels.csv` and come from how each clip was staged, not from a model.

## Safety

- Low voltage only. The 9 V battery is above the pump's 3–6 V rating, so runs are kept under about a minute. Never connect to mains.
- Run the pump under water only; dry running damages it.
- Keep the battery and switch away from water.
- All faults are staged and disclosed as staged in the demo and docs.
