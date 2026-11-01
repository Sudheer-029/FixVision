<!-- id: guidance.v1 -->
Write repair guidance for fault {fault_id} on a 3–6 V mini submersible pump, using ONLY the approved guide below. Do not add steps, tools or claims that are not in the guide.

- `stop_conditions`: every stop condition that applies, from the safety section and the fault section.
- `steps`: the repair steps in order, each with the `component_concept` it concerns (a short noun phrase such as "white pump") and `requires_approval` true where the guide marks "(requires approval)".
- `cited_sections`: the section ids you used, e.g. "G-F1", "G-SAFETY".

You never decide whether the repair passed; the functional test does.

Approved guide:
{guide}
