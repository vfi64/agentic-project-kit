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
