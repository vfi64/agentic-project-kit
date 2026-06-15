# Remote Transfer State Machine Hardening Plan

Status: proposed
Decision status: proposed

Planned before the remaining `ns` replacement work continues.

This plan is intentionally placed before the remaining `ns` replacement work because the remote file-transfer protocol is the operational substrate used to hand work between local execution, repository state, and LLM-guided follow-up.

## Problem

The transfer workflow already has important safety rules, including the exactly-one-command principle and head/branch checks. The remaining fragility is missing machine-checkable correlation between:

- the active inbox command,
- the active outbox result,
- the repository head and branch at command creation,
- the repository head and branch at command execution,
- the command/result identity,
- and transient remote failures.

Without this correlation, a stale `last_result`, an old transfer file, or a half-completed remote operation can be mistaken for the current state.

## Goals

1. Preserve the exactly-one-command protocol.
2. Make inbox/outbox correlation machine-checkable.
3. Detect stale `last_result` instead of treating it as a valid result.
4. Detect duplicate, obsolete, or unreferenced transfer files.
5. Harden local-vs-remote drift handling using explicit expected heads and observed heads.
6. Represent remote outages as a recoverable state, never as success.
7. Keep all changes compatible with protected-file and evidence rules.
8. Avoid broad rewrites of governance, handoff, planning, YAML, or generated-reference files.

## Non-goals

- Do not relax protected-file rules.
- Do not replace the full transfer mechanism in one large patch.
- Do not proceed with `ns` replacement until the transfer state machine has at least the MVP gates.
- Do not hide network failures behind successful exit codes.
- Do not make local-only assumptions after a failed remote operation.

## Target state model

The transfer layer should expose a small machine-readable state vocabulary:

    STATE=NO_COMMAND
    STATE=COMMAND_READY
    STATE=COMMAND_RUNNING
    STATE=RESULT_READY
    STATE=STALE_RESULT
    STATE=CONFLICT
    STATE=REMOTE_DRIFT
    STATE=REMOTE_UNREACHABLE
    STATE=BLOCKED

Each state must include a deterministic `NEXT` value, for example:

    STATE=RESULT_READY
    NEXT=consume_result

    STATE=STALE_RESULT
    NEXT=ignore_or_archive_stale_result

    STATE=REMOTE_UNREACHABLE
    NEXT=retry_remote_check_later

## Required metadata

Every active transfer command should have machine-readable metadata:

    command_id
    created_at_utc
    command_kind
    expected_branch
    expected_head
    expected_origin_main
    input_hash

Every result should have machine-readable metadata:

    command_id
    finished_at_utc
    result_status
    observed_branch
    observed_head
    observed_origin_main
    output_hash

The result is valid only if it correlates to the active command.

## Validation rules

### Exactly-one-command protocol

- There must be zero or one active inbox command.
- If more than one active command exists, report `STATE=CONFLICT`.
- If no active command exists and no active result exists, report `STATE=NO_COMMAND`.

### Inbox/outbox correlation

- If inbox and outbox both exist, their `command_id` values must match.
- If an outbox result exists without a matching active command, it is either already consumed or stale.
- If `command_id` does not match, report `STATE=STALE_RESULT` or `STATE=CONFLICT`.

### Stale last_result

A `last_result` is stale when any of these are true:

- its `command_id` does not match the current inbox command,
- its observed head is not compatible with the expected command head,
- its finished time predates the active command creation time,
- its result file was produced for a different branch,
- or the input hash does not match the active command.

### Duplicate or old transfer files

- Active inbox/outbox locations may contain only canonical active files.
- Historical files must live in an archive or report directory.
- Unknown `.tmp`, `.bak`, `.old`, or duplicate command/result files in active locations should trigger `STATE=CONFLICT`.

### Remote-vs-local drift

The command may execute only when:

    local_branch == expected_branch
    local_head == expected_head
    origin_main == expected_origin_main

If this fails, report:

    STATE=REMOTE_DRIFT
    NEXT=sync_or_regenerate_command

Allowed exceptions must be explicit and narrow, for example a dedicated sync or refresh command.

### Remote unreachable

SSH/GitHub outages cannot be prevented. They can be made safe:

- classify as `STATE=REMOTE_UNREACHABLE`,
- do not mutate after a failed remote preflight,
- do not report success,
- keep the same `command_id` reusable for a later retry,
- require remote verification after push, PR creation, merge, or fetch-sensitive operations.

## Proposed implementation slices

### Slice A: Transfer metadata schema and parser

Add a small parser/validator for transfer command and result metadata.

Acceptance checks:

- malformed metadata is rejected,
- missing `command_id` is rejected,
- command/result metadata can be parsed without executing the payload.

### Slice B: Inbox/outbox correlation check

Add a status command or internal helper that validates active inbox/outbox correlation.

Acceptance checks:

- matching command/result returns `RESULT_READY`,
- mismatched command/result returns `STALE_RESULT`,
- duplicate active files return `CONFLICT`.

### Slice C: Stale last_result detection

Teach the transfer status layer to distinguish current result from stale historical result.

Acceptance checks:

- old `last_result` after a new inbox command is not accepted,
- stale result includes reason and `NEXT`.

### Slice D: Remote drift preflight

Require expected branch/head/origin-main checks before executing mutable transfer commands.

Acceptance checks:

- mismatched local head blocks execution,
- mismatched origin/main blocks execution,
- sync/regenerate command remains allowed only when explicit.

### Slice E: Remote unreachable classification

Normalize SSH/GitHub failure output into `REMOTE_UNREACHABLE`.

Acceptance checks:

- failed fetch/ls-remote/push is not treated as success,
- no later mutation occurs after a remote preflight failure,
- output says retry is safe.

### Slice F: Roadmap gate before ns replacement

Keep the `ns` replacement blocked until the transfer state-machine MVP is green.

Acceptance checks:

- roadmap names transfer-state hardening as the first dependency,
- `ns` replacement section references this gate,
- no `ns` replacement slice starts before the gate is green.

## Definition of done for the MVP gate

The transfer state-machine MVP is ready when all are true:

- exactly-one-command validation is tested,
- inbox/outbox command-id correlation is tested,
- stale `last_result` is tested,
- duplicate active transfer file detection is tested,
- remote-vs-local drift blocks mutable execution,
- remote-unreachable state is represented distinctly,
- `post-merge-check`, `repo-status`, and transfer status outputs can be consumed without prose parsing,
- protected-diff-plan passes,
- docs-audit passes.

## Work ordering

This work must be completed before the remaining `ns` replacement work because the replacement will increase reliance on wrapper-mediated and remote-file-mediated orchestration. Hardening the transfer state first reduces the risk of loop states, stale command execution, and ambiguous handoffs.
