# No-Copy Terminal Evidence Policy

Status: active
Decision status: accepted

## Purpose

Routine collaboration must not require terminal copy-and-paste. A user response of d is meaningful only when the terminal action produced repo-backed evidence that can be inspected later.

## Binding rules

- Relevant terminal actions must write durable evidence under docs/reports/terminal or docs/reports/command_runs.
- PASS must not be printed after a failed required command.
- After log-backed PASS, the user may answer d without pasting terminal output.
- Manual terminal output is required only for FAIL, broken logging, aborted process, terminal loss, kill -9, or unavailable pushed evidence.
- Future handoff YAML and generated handoff prompts must include this policy and must not accumulate obsolete workaround rules.
