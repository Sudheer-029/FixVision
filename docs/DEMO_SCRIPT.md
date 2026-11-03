# Demo script (3:00)

Say and show on screen: "Faults are staged on a low-voltage demo rig. Everything shown was built during the hackathon, on Meta's models." Hindi speech is subtitled in English. Slow steps are sped up and labelled with the real speed-up factor.

| Time | Scene | What the viewer sees |
|---|---|---|
| 0:00–0:15 | Hook | The same pump, three outcomes: **Failed**, **Inconclusive**, and a trick clip refused. "The models report what they see. Fixed rules decide." |
| 0:15–0:35 | Problem and product | "A half-blocked pump still hums and still pumps, just slowly." One line on each Meta model's job: Muse Spark observes, SAM 3.1 tracks, Voice Transcribe hears |
| 0:35–1:05 | Before the repair | New job with the big code → Hindi voice note, transcript on screen → likely cause and one check → guidance with stop conditions and step approval |
| 1:05–1:25 | Faulty pump | `F1_faulty_01` → **Failed**: 51% of healthy speed, with the evidence frame and SAM's box on the jar |
| 1:25–1:50 | After the repair | Close-up with SAM's box on the pump → `f1_repaired_01` → **Inconclusive**: just under the 80% line (79% on this run), on a fading battery. "It will not sign off on almost." |
| 1:50–2:15 | Trick clips | Pump never switched on (`adv_never_on_01`), pump hidden at the start (`adv_pump_hidden_01`), old video under another job's code (`adv_reused_01`): each **Inconclusive** with the reason |
| 2:15–2:35 | Proof | Service record and manager review; trace of model calls and cost; results table from EVALS.md, stated as a small exploratory sample |
| 2:35–2:50 | What we built | Ours vs third-party; verification tests; the Passed path is covered by automated tests, no real clip reached it |
| 2:50–3:00 | Close | "A system that refuses to close a repair without sufficient evidence." Repo link |

Model results vary between fresh runs: the faulty clip usually gives Failed but gave Inconclusive in the eval run, and the repaired clip measured 76–79%. Show the results table with that miss, and say so if the on-screen run replays recorded model answers.

Do not show or imply a real Passed, and say "box", not "mask", for what appears on the evidence frames.
