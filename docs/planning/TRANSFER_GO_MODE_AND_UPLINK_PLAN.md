# Transfer Go Mode and Remote Uplink Plan

Status-date: 2026-06-01
Status: active
Decision status: accepted-for-B11-follow-up
Project: agentic-project-kit

## Problem

The current terminal workflow still exposes too much low-level output to the human operator. It is possible for a multi-command paste to show an earlier `f` and a later `d`, which is technically explainable per-command but confusing for a human. The workflow is not good enough if the user must scan long JSON or copied terminal logs to know whether the next chat turn should continue.

The current run-and-log/uplink layer is also not yet sufficient as the sole communication path between the local machine and the LLM. Until the report is reliably written and uploaded to the remote repository at the end of the local command sequence, copy-and-paste remains the safety fallback.

## User-facing target

The normal successful human-visible terminal ending should be small and stable:

```text
TRANSFER_UPLOAD=done
REMOTE_REPORT=docs/reports/transfer_runs/<timestamp>-<label>.json
CHAT_REPLY=g
```

`g` means: the local sequence reached a terminal report state and the next assistant turn should read the remote report, derive `d`/`f`/wait internally, and provide the next safe action. The user should not have to decide between `d`, `f`, and `w` from raw terminal output in the normal path.

## Failure target

Only exceptional failure classes should require manual copy-and-paste:

- the local process is killed before the report writer runs;
- the report is written locally but cannot be committed or pushed because of network, authentication, branch, or worktree safety failure;
- the wrapper itself crashes before emitting the upload status.

In these cases the terminal ending must say explicitly that upload failed and must give the local report path or instruct the user to paste the terminal output.

## Sequence-level rule

For a command sequence, the final visible status is sequence-level, not last-command-level:

- any failed step makes the sequence status failed unless the command was explicitly classified as allowed/transient and then successfully recovered;
- a later successful command must not hide an earlier failed command;
- CI-pending is not a failure and not a success; the local runner must wait for the CI terminal result when the requested action depends on CI;
- network failures during verification are recoverable evidence failures and must be represented as such, not as green continuation.

## CI waiting rule

Commands that depend on CI readiness must wait locally until GitHub reports a terminal CI state or until a configured timeout is reached. While waiting, the terminal should show a lightweight progress signal so the user knows that the command is alive.

The GUI should expose this as a progress state or spinner/progress bar. The user should not need to poll manually unless the configured wait times out.

## Report contents

The remote transfer report should include at least:

- timestamp and run id;
- branch and HEAD at start and end;
- command sequence label;
- every command with return code, stdout, stderr, duration, and classified signal;
- aggregate sequence signal;
- remote upload status;
- next safe action for tools/GUI;
- short user-facing `CHAT_REPLY=g` when the report is successfully uploaded.

## GUI implication

The GUI should eventually need only one primary Go action for the normal workflow. A secondary button may open the last transfer report for inspection. The raw report should be available for debugging and evidence, not required for ordinary operation.

## Implementation slices

1. Add/finish a sequence-level transfer runner that captures all command outputs and computes one aggregate signal.
2. Add a remote-uplink closeout step that writes the report under `docs/reports/transfer_runs/`, commits it safely on a dedicated report branch or through the selected transfer mechanism, and pushes it.
3. Replace normal human-visible output for the go path with `TRANSFER_UPLOAD`, `REMOTE_REPORT`, and `CHAT_REPLY=g`.
4. Add a `show last-transfer-report` style command for local inspection and GUI use.
5. Harden CI-wait actions so progress is visible and the command waits to a terminal CI result or timeout.
6. Add tests for sequence failure masking, upload success/failure, missing report, CI wait timeout, and compact terminal output.

## Non-goals

- no GUI feature implementation before the transfer/uplink contract is test-backed;
- no broad protected-file rewrite;
- no hidden success if the remote report was not uploaded;
- no reliance on chat-only interpretation as proof of state.
