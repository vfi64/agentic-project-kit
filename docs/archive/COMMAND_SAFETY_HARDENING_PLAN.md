# Command Safety Hardening Plan

Document class: historical archive
Status-date: 2026-07-08
Archived-from: docs/planning/COMMAND_SAFETY_HARDENING_PLAN.md
Superseded-by: docs/governance/COMMAND_SAFETY_POLICY.md and docs/planning/PROJECT_DIRECTION.yaml

Status: active
Decision status: accepted
Review policy: Review before GUI work, release orchestration work, or any change to transfer, remote-next, post-merge, PR, evidence, or release command behavior.
Project: agentic-project-kit

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

## Required hardening slices

### Slice 1: post-merge-complete finalization and evidence

Problem observed after PR1084/PR1085/PR1086:

- `post-merge-complete` created or used admin refresh PR1086.
- PR1086 was actually merged remotely.
- The command still returned `ADMIN_REFRESH_MERGE_BLOCKED` and `FINAL_SIGNAL=f`.
- A subsequent `post-merge-check` returned `NOOP` on main.
- The command did not produce a correct final summary or remote evidence upload.

Required behavior:

- Treat already-merged or successfully merged admin refresh PR as a valid transition.
- Re-read or synchronize main after admin refresh merge.
- Run a final `post-merge-check`.
- If final state is `NOOP`, return `PASS` / `COMPLETE`.
- If final state is still `REFRESH_REQUIRED`, return `BLOCKED` / `REFRESH_LOOP_DETECTED`.
- Emit a concise final summary that includes after PR, refresh PR, lifecycle state, final post-merge state, report path, and next safe action.
- Publish or hand off a stable evidence report, not just terminal text.

Acceptance tests:

- merge succeeds and final `NOOP` returns `COMPLETE`.
- admin refresh PR is already merged and final `NOOP` returns `COMPLETE`.
- admin refresh merge command reports failure but remote PR state is merged; command recovers by final check.
- final `REFRESH_REQUIRED` returns `REFRESH_LOOP_DETECTED` without creating a second refresh PR.
- report publication failure is reported as `BLOCKED` without hiding successful product state.

### Slice 2: remote-next block-tolerant execution

Problem observed repeatedly:

- `remote-next` blocked on dirty local transfer/report artifacts.
- It could run on a stale or wrong branch.
- It sometimes published a BLOCKED report but did not execute the intended current order.
- The user still had to paste local reports when the remote report was stale or missing.

Required behavior:

- Classify dirty paths into product changes, protected governance changes, allowed transient transfer artifacts, and unknown files.
- Never clean or discard unknown/product changes automatically.
- For allowed transient transfer artifacts, emit a typed recovery path or optionally stage them into a bounded diagnostic report.
- Explicitly report expected branch, actual branch, current head, upstream head, rule ack state, dirty classification, order id, and report freshness.
- Detect stale orders and stale reports.
- Refuse to claim progress from an old report.
- Keep the canonical user command stable: `./.venv/bin/agentic-kit transfer remote-next`.

Acceptance tests:

- dirty transient report artifacts produce a stable `BLOCKED` report with concrete next safe action.
- wrong branch produces `BLOCKED` with expected/actual branch fields.
- stale rule ack produces `BLOCKED` with rule ack fields.
- no order produces `BLOCKED` with missing-order reason.
- successful order execution publishes a fresh report and marks the order executed.

### Slice 3: typed work-order lifecycle

Required behavior:

- Every work order has a unique id, target branch, expected state, log path, and publish behavior.
- Executed orders move or are recorded in an executed state without losing evidence.
- Stale or duplicate orders are detected before execution.
- Order labels must match their actual target PR or command; old `post-pr1082` labels must not silently execute during `post-pr1084` workflows.

Acceptance tests:

- single valid order executes once.
- stale order blocks.
- duplicate active orders block.
- executed order is not rerun accidentally.
- report path matches order id.

### Slice 4: admin-refresh-pr idempotence

Required behavior:

- Creating an admin refresh PR must be idempotent.
- If a matching refresh PR already exists, return its PR number and head SHA.
- If it is already merged, return a typed `ALREADY_MERGED` state instead of failure.
- Do not create a second admin refresh PR for the same lifecycle round unless explicitly requested after a loop diagnosis.

Acceptance tests:

- new PR created.
- existing open PR recovered.
- existing merged PR detected.
- duplicate candidate detection blocks safely.

### Slice 5: evidence publication and final summaries

Required behavior:

- Every production command that mutates or completes lifecycle state must have a report path or publish hook.
- Direct command invocations must either publish evidence or clearly state that they are local-only and provide the exact publish command.
- Final summary must include result status, lifecycle state, evidence path, upload status, branch/head, and next safe action.
- `f` or `d` is not evidence by itself; it only reflects the command's printed final signal.

Acceptance tests:

- successful command publishes report.
- failed command publishes diagnostic report.
- upload failure is represented as `BLOCKED` with local report path.
- stale report cannot be interpreted as current success.

### Slice 6: release command safety gate

Release orchestration remains blocked until slices 1-5 are complete.

Before release work resumes, verify:

- PR cycle commands are safe individually.
- post-merge lifecycle commands are safe individually.
- evidence upload and final summaries are safe individually.
- release checks can publish final evidence and do not depend on manual terminal reconstruction.

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

## Next smallest safe slice

Implement Slice 1 first: harden `agentic-kit transfer post-merge-complete --after-pr <PR>` so that an actually merged admin refresh PR leads to final main synchronization, final `post-merge-check`, correct `COMPLETE` summary on `NOOP`, and stable evidence publication or an explicit upload-blocked report.
