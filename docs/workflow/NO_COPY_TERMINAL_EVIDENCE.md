Status: active
Status-date: 2026-07-09
Superseded-by: n/a

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


## Fixed remote-next dialog path

For dialog-oriented local work, the preferred target path is `agentic-kit remote-next`. The command synchronizes `main` and executes the next typed work order through the repo-backed typed work-order runner. Chat assistants should prefer queuing a typed work order for this path over pasting long local terminal blocks. The GUI must use the same command path instead of introducing a separate execution model.

`remote-next` reports `expected_closeout_path=` lines when a typed work order creates repo-backed evidence. Those paths are the canonical dirty-state closeout set for the next evidence PR and are intended for future GUI display.

## Full-output transfer requirement

Every local task initiated by the assistant must capture the complete terminal transcript in a repo-backed transfer or evidence file that the assistant can inspect without asking the user to paste output. The captured record must include stdout, stderr, exit code, argv, start time, end time, current branch, HEAD, dirty-state evidence, and the generated terminal-log or command-report path.

Manual paste is an exception, not the normal workflow. It is allowed only when the transfer/evidence file cannot be produced or retrieved, for example after kill -9, terminal loss, machine crash, network failure before push, Python startup failure, filesystem failure, or an explicitly reported broken logging path.

## Remote Python task requirement

Local execution requests must be delivered as repo-backed Python programs, typed work orders, or `agentic-kit` commands. They must run through the repository virtual environment and must not depend on global Python or shell state. For this repository the canonical local runtime is `.venv/bin/python` and `.venv/bin/agentic-kit` with Python 3.13.

Long ad-hoc shell blocks, fragile multi-line `python -c` strings, and raw decoration lines as terminal input are not valid default execution paths. They are recovery-only tools when the repo-backed Python or typed-work-order path is unavailable.

## Safe evidence closeout helper

Use `agentic-kit evidence commit-paths` for explicit evidence path commits. The helper accepts only the expected path set, commits it with a supplied message, and verifies that the worktree is clean after the commit. Closeout scripts must finalize any repo-backed log before invoking this helper and must not write to the committed repo-backed log afterwards. The helper must accept expected tracked deletions and stage them with `git add -A -- <paths>`.

## Remote-next aliases

Use `agentic-kit rn` as the short alias for `agentic-kit remote-next`. Use `agentic-kit rnc` to close out the dirty path set produced by the last successful remote-next run. If no closeout paths are dirty, `rnc` must report `result_status=no_closeout`, render `### RESULT: NO-CLOSEOUT ###`, and exit with code 2 rather than presenting the state as a hard failure. The GUI must expose these as Run Next Work Order and Close Out Last Run.
