# FixVision slash commands

Project setup for Claude Code. Commands live in `commands/` (type `/` to run), skills in `skills/`, subagents in `agents/`. Order of work: docs/WEEKEND_RUNBOOK.md.

Skills: `meta-model-api` (how to call Meta models), `fixvision-rules` (non-negotiable rules). Subagents: `spec-reviewer` (review diffs against the spec), `demo-director` (video and submission).

`settings.json` blocks Claude from reading `.env` and from force-push and `rm -rf`.

| Command | What it does |
|---|---|
| /next | Shows the next unfinished task and its checklist |
| /t1-scaffold … /t12-fireworks | One build task each (see BUILD_PLAN.md) |
| /check | Pre-commit check: tests, lint, secrets, docs in sync, rules |
| /log-day | Updates HACKATHON_LOG.md and CHANGELOG.md from today's commits |
| /adr <title> | Creates a new ADR from the template |
