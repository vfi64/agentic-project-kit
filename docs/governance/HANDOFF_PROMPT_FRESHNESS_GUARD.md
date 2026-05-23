# Handoff Prompt Freshness Guard

Status-date: 2026-05-23
Status: normative governance contract
Scope: successor chat handoff prompts, closeout refreshes, and stale handoff detection

## Purpose

A successor handoff prompt must not be treated as authoritative merely because it exists in `docs/reports/terminal/`. The prompt must represent the current repository state or must prominently warn that it may be stale.

This rule addresses the observed failure pattern where a successor handoff prompt generated after one PR remained apparently current after later substantive main merges.

## Required freshness sources

Before a successor handoff prompt is presented as authoritative, the prompt path must check at least:

- `docs/STATUS.md`,
- `.agentic/handoff_state.yaml`,
- `docs/handoff/CURRENT_HANDOFF.md`,
- the latest successor handoff prompt under `docs/reports/terminal/`.

## Required behavior

The guard must warn prominently when the current git HEAD is not represented by `handoff_state.yaml` safe/admin state or when the configured/latest successor handoff prompt does not mention the current handoff commit marker.

The guard may be warning-based rather than fail-closed. A drifted repository still needs to render a repairable prompt. The forbidden outcome is a silent stale prompt.

## Closeout rule

When a user asks for a handoff prompt, the system must first check whether status, handoff state, current handoff, and the latest successor prompt are current against main. If not, the correct next action is a small closeout/handoff-refresh slice before the prompt is used as authoritative.

## Deterministic enforcement

The canonical prompt path is `agentic-kit handoff prompt`. It must surface the freshness guard result before the rendered handoff prompt.

Regression coverage must include the old failure class: a later current HEAD with an older successor prompt that only mentions the earlier commit.
