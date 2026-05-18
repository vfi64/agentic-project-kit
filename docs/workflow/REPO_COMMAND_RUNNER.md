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
