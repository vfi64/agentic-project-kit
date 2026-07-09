Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Repo Command Runner

`./ns agent-run` is the intended no-copy handoff path for local agent work.

Instead of pasting terminal blocks into the shell, the repository stores the current command in:

- `.agentic/commands/current.yaml`
- `.agentic/commands/current.sh`

The runner:

1. reads the current command metadata,
2. refuses already executed `command_id` values,
3. validates `current.sh` with `sh -n`,
4. executes the script through the terminal log wrapper,
5. writes a report under `docs/reports/command_runs/`,
6. appends `.agentic/commands/executed.jsonl`,
7. commits and pushes the command report and terminal log.

Outcomes:

- `PASS_EXECUTED`
- `FAIL_NO_COMMAND`
- `FAIL_ALREADY_EXECUTED`
- `FAIL_INVALID_COMMAND`
- `FAIL_SHELL_SYNTAX`
- `FAIL_COMMAND`
- `FAIL_UPLOAD`

Safety boundary:

- This is repository-backed local execution.
- Command files must stay small, auditable, and deterministic.
- Mutating/release/merge workflows require explicit command metadata and later confirmation-token hardening.
- Manual copy-and-paste terminal blocks are now a recovery path, not the default workflow.

## Inbox mode

`./ns agent-next` is the preferred command for routine no-copy handoff. It pulls the current branch, expects exactly one complete pending command pair under `.agentic/commands/inbox/`, copies that pair to the transient `current.yaml` and `current.sh` compatibility path, executes it through `agent-run`, then removes the transient current files.

Pending command files use matching names, for example `.agentic/commands/inbox/example.yaml` and `.agentic/commands/inbox/example.sh`. Multiple complete pending commands are refused with `FAIL_AMBIGUOUS_COMMANDS`.

Manual terminal copy-and-paste blocks remain recovery-only.

## Agent-next postconditions

A successful `PASS_EXECUTED` is intended to mean that the command script succeeded and the handoff state was cleaned up. The runner therefore checks postconditions after `agent-next`:

- no transient `.agentic/commands/current.yaml`
- no transient `.agentic/commands/current.sh`
- no complete pending inbox command pair left behind
- no dirty inbox command paths after upload

If any of these checks fail, `agent-next` reports `FAIL_POSTCONDITION`.

## Result handoff pointer

Every `./ns agent-run` or `./ns agent-next` run writes `docs/reports/command_runs/LATEST_COMMAND_RUN.txt`. The file points to the newest command-run report under `docs/reports/command_runs/`. After the user replies `d` for PASS or `f` for normal FAIL, the next agent must read this pointer first, then the referenced report, then the terminal log referenced by that report. Copy-and-paste is reserved for terminal crashes, authentication/network failure, or missing remote evidence.

## Visible agent-next result footer

`./ns agent-next` must end with a visible result footer. `PASS` prints `reply=p` and `### NEXT CHAT REPLY: PASS -> p ###`; a normal command failure prints `reply=f` and `### NEXT CHAT REPLY: FAIL -> f ###`; `NO-COMMAND` prints `reply=ask-agent-to-queue-command`; hard failures such as pull/upload/postcondition problems print `reply=paste-output` and `### NEXT CHAT REPLY: HARD-FAIL -> paste output ###`. This terminal footer is part of the no-copy workflow contract.

## Hard-fail result contract

`./ns agent-next` distinguishes normal command failure from workflow-level hard failures. Pull failures, ambiguous pending commands, upload/postcondition failures, authentication/network problems, and missing remote evidence are hard failures. The visible footer must print `### AGENT-NEXT RESULT: HARD-FAIL ###` and `reply=paste-output` for these cases. A normal command exit failure remains `FAIL` with `reply=f`, and no pending command remains `NO-COMMAND` with `reply=ask-agent-to-queue-command`.

## Command inbox check

`./ns command-inbox-check` validates the repo-backed queue before local execution. It accepts an empty inbox or exactly one complete `.yaml`/`.sh` pair, rejects orphan files, rejects multiple complete pending commands, validates required metadata and safety classes, runs `sh -n`, and blocks known unsafe command-script fragments such as heredocs, branch switches, pull commands, logout, kill, and top-level exec usage.

## Inner fail marker detection

`agent-run` treats a terminal log whose last result marker is `### RESULT: FAIL ###` as `FAIL_COMMAND`, even if the shell process exits with code 0. This prevents evidence finalization or wrapper layers from masking failed command scripts as `PASS_EXECUTED`.

## Missing script report robustness

`agent-run` report creation must not crash if `.agentic/commands/current.sh` is removed during command execution. In that case the script SHA256 field is recorded as `missing` so the runner can still write durable command-run evidence and return a deterministic outcome.

## Completed command inbox guard

`./ns command-inbox-check` rejects a pending inbox pair if its `command_id` already has durable command-run evidence. This prevents completed remote commands from remaining on `main` as stale queue artifacts and causing later `FAIL_AMBIGUOUS_COMMANDS` runs.
