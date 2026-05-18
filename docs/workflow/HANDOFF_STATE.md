# Persistent Handoff State

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

## Commit Semantics

`safe_state.commit` records the last substantive work state by default, not necessarily the newest administrative refresh merge on `main`.

This prevents endless refresh loops: a PR that only refreshes `.agentic/handoff_state.yaml` does not require another refresh PR just because it produced a newer merge commit.

Use `safe_state.semantics: last_substantive_work_state` for this mode. Administrative refresh PR numbers may be recorded under `safe_state.administrative_refresh_prs`.
