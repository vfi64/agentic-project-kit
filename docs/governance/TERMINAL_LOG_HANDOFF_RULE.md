Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Terminal Log Handoff Rule

## Quality principle

The terminal-log workflow must optimize for deterministic quality, not speed. Repeated logging, dirty-state, false-PASS, or handoff failures are product defects and must be addressed with helpers, guards, tests, and documentation instead of relying on manual discipline.

Status: active workflow rule.

## Purpose

Long local terminal runs must leave a committed terminal log in the repository so that the next assistant turn can inspect the last run without requiring manual copy-and-paste.

## Rule

- Every larger workflow block must write its complete terminal output to `docs/reports/terminal/*.log`.
- The terminal log must be staged, committed, and pushed together with the code/docs changes from that run.
- After `### RESULT: PASS ###`, a user reply of `d` means the run was seen and the next safe step may continue.
- After `### RESULT: FAIL ###`, the terminal output or the committed log path must be inspected before continuing.
- A log file must not be written again after the commit that is supposed to contain it.
- If a script writes to the log after staging or committing, the final state is not clean and must be repaired before opening or merging a PR.

## Required end state

A successful run should end with:

```text
### RESULT: PASS ###
git status --short
<clean or only intentionally ignored files>
```

If the final `git status --short` shows a modified terminal log, the commit is incomplete.
## Wrapper commands

The terminal-log handoff workflow is supported by:

- `./ns run-logged <name> -- <command...>`: runs a local command while teeing output into `docs/reports/terminal/*.log` and updates `LATEST_TERMINAL_LOG.txt`.
- `./ns terminal-status`: read-only inspection of the latest terminal log pointer.
- `./ns terminal-upload`: failure-handoff helper that commits and pushes only terminal-log artifacts.

For PASS handoff, prefer `run-logged` for larger local runs. For FAIL handoff, run `./ns terminal-upload` and then answer `f` or `fail` in the chat.
## Clean checks inside logged runs

Commands executed through `./ns run-logged` must not use plain `test -z "$(git status --short)"` as a cleanliness gate, because `run-logged` necessarily updates `docs/reports/terminal/LATEST_TERMINAL_LOG.txt` and creates a terminal log.

Use `./ns terminal-clean-check` instead. It returns:

- `PASS_CLEAN` when the working tree is clean.
- `PASS_ONLY_TERMINAL_LOG_DIRTY` when only terminal-log artifacts are dirty.
- `FAIL_DIRTY_NON_LOG_FILES` when any non-terminal-log file is dirty.

## Finalized log rule

Do not commit a repository log file while the current process is still writing to it. Long scripts must tee into a temporary log outside `docs/reports/terminal/`, then finalize the completed log into `docs/reports/terminal/*.log` with `./ns terminal-finalize <tmp-log> <name>` before staging, committing, and pushing. The finalized log must contain an explicit `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###` marker.

This rule exists because committing a log file while `tee` is still appending to it creates a dirty tracked log after commit and can block checkout, merge, or PR closeout.
