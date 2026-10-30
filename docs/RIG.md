# Demonstration rig and staged faults

**Status:** v0.1 (2026-10-27)

## Bill of materials

| Item | Example source | Approx. price (INR) |
|---|---|---|
| Mini submersible pump, 3–6 V DC, 80–120 L/h (×2, one spare) | [Probots PRO919](https://probots.co.in/3-6v-mini-water-pump-submersible-for-diy-hobby-projects-120l-h.html) | 69 each |
| Silicone / PVC tube, 5 mm inner diameter, 1 m | Local hardware or online | 30–60 |
| 4×AA battery holder **with switch** (or USB cable with bare leads + power bank) | Local electronics or online | 30–60 |
| Fresh and partly used AA batteries | — | — |
| Clear plastic tub or bucket | Home | 0 |
| Measuring jug with 500 mL mark | Home | 0 |
| Phone stand, a cloth or sponge (for blockage), tape | Home | 0 |

Avoid aquarium fountain pumps that run on 230 V mains.

## Layout

Tub with water → pump submerged → hose up to a fixed head height (record cm) → hose joint midway (taped connector) → outlet over the measuring jug. Phone on a stand framing pump, joint and jug. On-screen timer visible (second phone or the capture screen timer).

## Baseline (Day 1)

Run the healthy rig 5 times with fresh batteries; record the 500 mL fill time; store the median as `baseline_lpm` in `config/rig_baseline.yaml` with head height and water level, then set `measured: true` and bump `version` (until then every verdict is Inconclusive, "No rig baseline").

## Staged faults

| ID | How to stage | How to repair |
|---|---|---|
| F1 blocked inlet | Wrap cloth or sponge over the intake | Remove blockage, show clean intake close-up |
| F2 leaking joint | Loosen the hose joint or make a small cut before the joint tape | Re-seat or re-tape the joint, show close-up |
| F3 weak supply | Use partly drained batteries | Replace with fresh batteries, record in conditions |

## Recording plan for evaluation

- Per fault: ≥ 8 faulty runs and ≥ 8 repaired runs, varied lighting and angle.
- Adversarial (one group per row of VERIFICATION_SPEC §7): ≥ 5 "never switched on", ≥ 5 "joint hidden", ≥ 3 "switched on, no flow" (inlet fully blocked with the pump still submerged; switch off after ~25 s; never run the pump dry), ≥ 3 "typed time too fast", ≥ 3 "fill cut / jug out of frame", ≥ 3 reused test clips, ≥ 3 reused close-ups.
- Healthy controls: ≥ 5.
- Label every clip at recording time in `data/labels.csv` (clip id, fault, state, expected verdict, notes). Labels come from how the clip was staged, not from the model.
- Split by recording session: dev (tuning) and test (held out, untouched until final report).

## Safety

- Low voltage only (≤ 6 V). Never connect to mains.
- Run the pump under water only; dry running damages it.
- Keep batteries and holder away from water.
- All faults are staged and disclosed as staged in the demo and docs.
