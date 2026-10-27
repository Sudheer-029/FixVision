# Component: Guard layer

**Purpose:** Keep untrusted text from steering the agents, and enforce scope and safety limits.
**Code:** `backend/app/guard/`

## Behaviour
- Scan transcripts, technician free text and retrieved case text with LlamaFirewall `PROMPT_GUARD` (+ `HIDDEN_ASCII`) before prompts are built.
- Block → step returns `INCONCLUSIVE`-style refusal with reason; never silently drop content.
- Scope rules: unsupported equipment, mains voltage, gas, pressure vessels → refuse guidance and recommend escalation.
- Guidance must include stop conditions; missing → regenerate once, then refuse.

## Config
`GUARD_ENABLED`, model download via `llamafirewall configure` (Hugging Face).

## Failure modes
Guard model unavailable → fail closed for guidance (refuse), fail open with warning for transcripts in `staged` jobs only.

## Tests
Red-team set of 20 injection strings in transcripts; expect block rate and log false positives.
