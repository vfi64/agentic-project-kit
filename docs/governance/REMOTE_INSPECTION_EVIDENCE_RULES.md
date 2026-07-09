Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Remote inspection evidence rules

Status: active contract.

## Purpose

Inspection and classification blocks may produce long diagnostic output. These outputs must not force chat paste-output when the same evidence can be captured as a bounded remote evidence artifact.

## Contract

- Inspection and classification blocks should write their complete output to a terminal log.
- The preferred temporary path class is `docs/reports/terminal/tmp-inspection/` on a temporary evidence branch, not an untracked local-only file.
- The final summary must expose `terminal_log`, `REMOTE_EVIDENCE`, `STANDARD_ERROR_REDUCTION`, and `GUI_PREPARATION`.
- When the block passes and the remote evidence path is available, the human acknowledgement may be `d` or `done`; the next agent must reconstruct state from the remote evidence instead of requesting pasted output.
- When the block fails, the final summary must use `NEXT_CHAT_REPLY: f` unless the remote evidence is explicitly missing or unusable.
- Temporary remote inspection evidence must be registered for later cleanup by the evidence garbage-collection workflow.
- Garbage collection must remove obsolete temporary inspection evidence only after the corresponding state is represented by a durable main-branch log, status entry, or handoff entry.
- The GC must not delete release logs, merge verification logs, DOI logs, or permanent audit evidence.

## Failure handling

A visible inner `FAIL` from an expected diagnostic gate is allowed only when the surrounding block marks it explicitly as expected, explains why it is expected, and still reports the outer result honestly.

## GUI relevance

The future local GUI should read these remote evidence summaries instead of depending on copied terminal output. The same contract is therefore part of GUI readiness.
