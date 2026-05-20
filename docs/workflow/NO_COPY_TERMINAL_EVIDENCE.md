# No-Copy Terminal Evidence Policy

Status: active
Decision status: accepted

## Purpose

Routine collaboration must not require terminal copy-and-paste. A user response of d is meaningful only when the terminal action produced repo-backed evidence that can be inspected later.

## Binding rules

- Relevant terminal actions must write durable evidence under docs/reports/terminal or docs/reports/command_runs.
- PASS must not be printed after a failed required command.
- After log-backed PASS, the user may answer d without pasting terminal output.
- Normal FAIL handoff must use f and repo-backed evidence, typically docs/reports/command_runs/LATEST_COMMAND_RUN.txt plus the referenced terminal log. Manual terminal output is required only when FAIL evidence is unavailable, logging is broken, the process aborted, the terminal was lost, kill -9 occurred, pushed evidence is unavailable, or the user explicitly asks for pasted output.
- Future handoff YAML and generated handoff prompts must include this policy and must not accumulate obsolete workaround rules.

## `d`/`f` command-result handoff

For repo-backed agent commands, `docs/reports/command_runs/LATEST_COMMAND_RUN.txt` is the canonical first read after `d` or `f`. The referenced command report records the outcome, exit code, branch, script hash, and terminal-log path. A normal FAIL must still leave remote evidence; otherwise the workflow is broken and must be repaired.
