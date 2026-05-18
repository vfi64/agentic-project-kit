# Terminal Log Handoff Rule

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
