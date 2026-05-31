# Transfer GitHub Action Coverage

Status-date: 2026-05-31
Status: active
Decision status: accepted
Review policy: Review before Phase 0 closeout, before GUI write-action enablement, and whenever transfer command contracts change.
Project: agentic-project-kit

## Purpose

This document records Phase 0 of `docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md`.

The goal is to verify whether the GitHub-backed transfer path has enough local `agentic-kit transfer` actions to avoid connector-blocked orchestration for the LLM-to-local and local-to-LLM workflow.

The GUI must later dispatch only actions whose contract is explicit, testable, and safe for the current state.

## Classification

- `covered`: action exists and has a specific command contract for the workflow step.
- `partial`: action exists but still needs stronger state typing, JSON contract hardening, or GUI-specific safety rules.
- `missing`: no suitable transfer action exists yet.
- `unsafe-for-gui`: action may exist but must not be directly exposed by GUI without additional gating.

## Coverage Matrix

| Workflow step | Transfer action | Coverage | Notes |
| --- | --- | --- | --- |
| Inspect repository status | `transfer repo-status` | covered | Local status inspection is available. |
| Inspect recent repository log | `transfer repo-log` | covered | Useful for preflight and post-merge evidence. |
| Inspect current HEAD SHA | `transfer head-sha` | covered | Required for pinned PR/merge workflows. |
| Inspect actual diff | `transfer repo-diff` | covered | Required before protected-change planning and commits. |
| Fetch origin | `transfer fetch-origin` | covered | Required before freshness-sensitive operations. |
| Pull current branch | `transfer pull-current` | covered | Required for local main synchronization. |
| Create branch | `transfer branch-create` | covered | Required for local slice setup. |
| Switch branch | `transfer branch-switch` | covered | Required for local slice and main sync workflows. |
| Delete branch | `transfer branch-delete` | partial | Useful cleanup action; unsafe for GUI without stale-branch confirmation. |
| Commit explicit paths | `transfer commit` | partial | Exists, but GUI must require explicit paths and clean pre/post status checks. |
| Push current branch | `transfer push-current` | covered | Required to publish transfer-created branches. |
| Create pull request | `transfer pr-create` | covered | Avoids raw `gh pr create`; should be preferred in transfer workflows. |
| Inspect PR status | `transfer pr-status` | covered | Supports expected head SHA and failed-log diagnostics. |
| Wait for PR CI | `transfer pr-wait-ci` | covered | Supports expected head SHA, timeout, and polling interval. |
| Safe PR merge | `transfer pr-merge-safe` | covered | Requires expected head SHA. |
| Post-merge verification | `transfer post-merge-check` | covered | Required after merge and local sync. |
| Administrative handoff refresh PR | `transfer admin-refresh-pr` | covered | Required when a substantive PR makes handoff refresh necessary. |
| Inspect remote next work | `transfer remote-next` | partial | Useful for LLM-to-local transfer, but GUI needs clearer state mapping. |
| Execute local transfer order | `transfer run-local` | partial | Powerful action; GUI must gate by typed state and expected command class. |
| Inspect transfer state | `transfer state` | partial | Needs integration with rule-refresh states from the handshake plan. |
| Inspect transfer status | `transfer status` | partial | Needs GUI-ready status vocabulary. |
| Inspect transfer artifact | `transfer inspect` | partial | Useful diagnostics; GUI should keep read-only. |
| Apply transfer order | `transfer apply` | unsafe-for-gui | Mutation action; must stay blocked until rule snapshot and transfer state gates exist. |
| Closeout transfer workflow | `transfer closeout` | partial | Needs clear evidence-finalization contract before GUI exposure. |

## Key Findings

The core Branch/PR/Merge path is covered by transfer actions:

1. `branch-create`
2. `branch-switch`
3. `repo-diff`
4. `commit`
5. `push-current`
6. `pr-create`
7. `pr-status`
8. `pr-wait-ci`
9. `pr-merge-safe`
10. `post-merge-check`
11. `admin-refresh-pr`

The previous fallback to raw `gh pr create` was unnecessary for this repository line. The preferred transfer workflow should use `transfer pr-create` when the task is part of the LLM-to-local transfer path.

Several actions are still only partial for GUI readiness because they need typed state contracts, stronger JSON stability, or button-state gating.

## GUI Implications

The GUI may eventually expose the covered actions, but only through state-aware dispatch.

Initial GUI buttons should not directly expose broad mutation actions such as `apply`, `run-local`, or branch deletion until rule-refresh and transfer-state gates are implemented.

The GUI should show a small number of safe next actions derived from transfer state rather than a raw command catalog.

## Required Next Work

1. Add deterministic tests that critical transfer action names remain registered.
2. Verify JSON output contracts for PR status, wait, merge, and admin refresh.
3. Integrate rule-refresh handshake states before exposing write actions in GUI.
4. Promote partial actions to covered only after state and JSON contracts are hardened.

## Relationship To Rule Refresh Handshake

This coverage matrix completes the first planning artifact for Phase 0 of `RULE_REFRESH_HANDSHAKE_PLAN.md`.

The next implementation step should harden the rule-refresh handshake schema and transfer-state integration. The GUI remains downstream of those machine-checked states.
