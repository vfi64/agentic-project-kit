Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Persistent Handoff State

Quality rule: choose the technically deterministic solution over the quickest workaround. Standard errors must be converted into guards, tests, and documented contracts; do not rely on memory, speed, or manual discipline when a deterministic check can prevent recurrence.

Status: active
Decision status: accepted

## Purpose

`.agentic/handoff_state.yaml` is the structured, repo-backed source for handoff state. It prevents future chats and agents from reconstructing current state only from conversation memory.

## Commands

- `./ns handoff-show` prints a compact summary.
- `./ns handoff-check` validates required fields, active rule ids, superseded rule metadata, and failure-pattern prevention notes.
- `./ns handoff-prompt` renders a copy-ready handoff prompt from YAML.

## Rule lifecycle hygiene

Rules use `active`, `superseded`, or `historical` status. Generated handoff prompts include active rules by default and must not present superseded or historical rules as binding instructions.

## No-copy integration

The handoff state references `.agentic/no_copy_terminal_policy.yaml`. A normal PASS handoff should therefore rely on committed/pushed logs and reports; manual terminal paste is reserved for failure or unavailable evidence.

## Environment bootstrap rule

A new chat or workflow must not assume that global `agentic-kit`, `python`, `ruff`, or `.venv` already exist. First verify the local environment. Prefer project-local commands such as `.venv/bin/python -m agentic_project_kit.cli ...` after `.venv` has been created. If global `agentic-kit` is missing or `.venv` is absent, classify this as bootstrap/environment state, not as a product failure.

## Interactive terminal safety rule

Terminal blocks pasted into an interactive shell must never terminate that shell. Do not use `exit`, `logout`, `kill`, or top-level `exec` in chat-pasted blocks. A pasted block must report `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###` and then return to the prompt. Use exit codes only inside saved scripts executed as child processes.

## Communication artifact cleanup rule

Temporary communication files must be centrally classified before cleanup. Use `.agentic/communication_artifacts.yaml` as the allowlist and policy source. Do not use ad-hoc `rm` on `docs/reports`, `.agentic/commands`, handoff files, terminal logs, command-run reports, or pointer files. A garbage collector must start with dry-run behavior and must write a cleanup report before any deletion.

## Communication artifact garbage collection

Temporary communication artifacts must be centrally recognizable and removable only through registered safe paths. Use `agentic-kit artifact-gc` for a dry-run plan and `agentic-kit artifact-gc --execute` only after reviewing the plan. The collector must not delete arbitrary `docs/reports` files, release evidence, handoff state, source files, or unregistered paths.

## Commit Semantics

`safe_state.commit` records the last substantive work state by default, not necessarily the newest administrative refresh merge on `main`.

This prevents endless refresh loops: a PR that only refreshes `.agentic/handoff_state.yaml` does not require another refresh PR just because it produced a newer merge commit.

Use `safe_state.semantics: last_substantive_work_state` for this mode. Administrative refresh PR numbers may be recorded under `safe_state.administrative_refresh_prs`.

## Planning-state freshness rule

Current planning files must be curated, not accumulated. `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml` must agree on the active release, next safe step, evidence policy, and blocked work. Historical fragments may remain only in explicitly historical documents or clearly marked strategy retrospectives.

`./ns state-freshness-check` must reject stale current-state fragments such as obsolete released-version claims, outdated next-step instructions, or a handoff YAML version that disagrees with current status documents. This rule exists because stale planning files caused repeated wrong-command, wrong-path, and wrong-priority drift.
Supported state freshness check: `agentic-kit state-freshness-check`.
