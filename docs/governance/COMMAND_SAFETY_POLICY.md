# Command Safety Policy



Document class: governance/system

Status-date: 2026-07-08

Split-from: docs/planning/COMMAND_SAFETY_HARDENING_PLAN.md

Archived-source: docs/archive/COMMAND_SAFETY_HARDENING_PLAN.md

Project: agentic-project-kit



This governance document preserves the normative command-safety rules extracted from the historical hardening plan. Historical implementation slices remain archived in `docs/archive/COMMAND_SAFETY_HARDENING_PLAN.md`.



## Purpose

Before GUI work, Pattern Advisor expansion, or release orchestration, every command currently classified as unsafe or only partially safe must become safe as a standalone production step.  A command is safe only when it fails closed, emits a deterministic summary, preserves or publishes evidence, and does not require the user to reconstruct state from ad-hoc terminal output.

This plan deliberately does not ask for a new full PR-cycle or release-cycle command first.  It hardens the underlying individual commands before composing them into complex workflows.



## Decision

The priority order is:

1. Harden unsafe or partially safe single commands.
2. Add command-level evidence upload and final summary guarantees.
3. Reclassify each command only after tests and a real remote-backed run prove the behavior.
4. Only then resume GUI work or build complex branch/release orchestrators.



## Safety definition for an individual command

A command is safe as an individual production step only if all criteria hold:

- It has a deterministic machine-readable result status: `PASS`, `FAIL`, `BLOCKED`, or a typed lifecycle state that maps to one of those states.
- It prints a concise final summary with next safe action.
- It does not rely on chat interpretation of raw terminal output.
- It writes or can publish a stable evidence report to a repository-readable path.
- It distinguishes product failure, lifecycle transition, local preflight blocker, remote upload failure, and already-completed state.
- It is idempotent where practical, or detects already-completed work without creating duplicate PRs, duplicate reports, or refresh loops.
- It has targeted unit tests for known failure modes and at least one remote-backed validation run before reclassification.



## Current command classification

### Safe as individual steps

These are considered usable as individual steps with normal verification:

- `agentic-kit rules acknowledge`
- `agentic-kit transfer state`
- `agentic-kit transfer repo-status`
- `agentic-kit transfer head-sha`
- `agentic-kit transfer pr-status <PR> --expected-head-sha <SHA>`
- `agentic-kit transfer pr-wait-ci <PR> --expected-head-sha <SHA>`
- `agentic-kit transfer pr-merge-safe <PR> --expected-head-sha <SHA> --merge-method <method>`
- `agentic-kit transfer post-merge-check`

The PR and merge commands still require expected-head protection and explicit verification of the returned state.

### Partially safe but requiring hardening

These commands must not be used as the sole source of production truth until this plan is complete:

- `agentic-kit transfer remote-next`
- typed work-order execution through `.agentic/typed_work_orders/inbox`
- `agentic-kit transfer admin-refresh-pr --after-pr <PR>`
- `agentic-kit transfer post-merge-complete --after-pr <PR>`
- evidence publication/finalization paths used after direct transfer commands

### Not yet safe as complex production workflows

These remain blocked until every underlying step above is safe:

- one-command branch-to-PR-to-merge production cycle
- one-command post-merge lifecycle completion with evidence upload
- one-command release cycle including tag, GitHub Release, DOI/Zenodo, changelog, citation, post-release checks, and final evidence
- GUI write-button workflows that mutate repo state



## GUI gating rule

No GUI write action should be enabled for an unsafe command.  GUI work may continue only for read-only inspection, visualization, or disabled-button planning until all commands it wraps are reclassified as safe individual steps.



## Reclassification process

A command can move from partially safe to safe only after:

1. implementation PR merged,
2. CI green,
3. targeted tests cover the observed failure class,
4. one real remote-backed run demonstrates the behavior,
5. final evidence report is repository-readable,
6. this plan or a successor status file is updated with the reclassification.
