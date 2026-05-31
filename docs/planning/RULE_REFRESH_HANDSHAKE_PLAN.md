# Rule Refresh Handshake Plan

Status-date: 2026-05-31
Status: active
Decision status: accepted
Review policy: Review before Phase 0 closeout, before adding rule-snapshot schema implementation, and before expanding GUI write actions.
Project: agentic-project-kit

## Purpose

This plan defines the hardened rule-refresh handshake between the local repository, GitHub-backed transfer artifacts, and the LLM.

The goal is to reduce chat drift, stale-rule execution, connector-blocked orchestration, and instruction loss by moving rule freshness into a machine-checkable workflow state instead of relying on chat memory or informal reminders.

## Problem

The current rule refresh mechanism can generate repo-backed rule snapshots through `agentic-kit rules communication-refresh` and `agentic-kit rules handoff-refresh`.

That is necessary but not sufficient.

The current mechanism is still trigger-based: the assistant is instructed to read generated files after user replies such as `d2` or `d3`. This improves reproducibility, but it does not yet provide a fail-closed handshake proving that the LLM has consumed the correct current rule snapshot before product work continues.

## Target Outcome

Every relevant local-to-LLM and LLM-to-local transfer cycle must have a machine-checkable rule state.

A correct workflow should be able to answer:

- which rule snapshot is current,
- which source files were used,
- which source commit and safe-state commit were used,
- whether any mandatory source was missing,
- whether the snapshot is stale relative to current `main`,
- whether the LLM has acknowledged the exact snapshot identity,
- whether product work is allowed or blocked.

The GUI must later display this state; it must not invent or infer it.

## Non-Negotiable Requirements

- Fail closed when a mandatory rule source is missing.
- Fail closed when the rule snapshot is stale relative to the required repo head.
- Fail closed when the LLM has not acknowledged the exact snapshot identity.
- Fail closed when the transfer state and rule snapshot disagree.
- Do not rely on chat memory as evidence of rule freshness.
- Do not use freehand PASS summaries as evidence.
- Keep all rule-refresh state repo-readable and auditable.
- Prefer explicit project-local Python entry points when wrapper contracts are unclear.
- Keep GUI behavior downstream of the machine-checked state.

## Phase 0: Transfer GitHub Action Coverage

Goal: prove that the GitHub-backed transfer path has local `agentic-kit transfer` actions for the commands needed to avoid connector-blocked orchestration.

Inventory at minimum:

- repository status,
- repository log,
- current HEAD SHA,
- actual diff,
- fetch origin,
- pull current branch,
- create branch,
- switch branch,
- commit explicit paths,
- push current branch,
- create PR,
- inspect PR status,
- wait for PR CI with expected head SHA,
- safe PR merge with expected head SHA,
- post-merge handoff-refresh status,
- administrative handoff-refresh PR,
- transfer-state inspection,
- local transfer-order execution,
- remote transfer-order execution.

Acceptance:

- produce a coverage matrix with `covered`, `partial`, `missing`, and `unsafe-for-gui` classifications;
- identify actions that still shell out to `git` or `gh`;
- identify actions that are safe enough for GUI dispatch;
- add deterministic test anchors for the critical action names.

## Phase 1: Rule Snapshot Schema

Goal: define a machine-readable rule snapshot schema.

Required fields:

- schema version,
- generated timestamp,
- generating command,
- repository name,
- current main commit,
- handoff safe-state commit,
- source file list,
- per-source content hash,
- combined snapshot hash,
- missing source list,
- stale-state indicators,
- intended next LLM action,
- allowed next transfer state.

Acceptance:

- schema is documented;
- generated snapshots are deterministic except for timestamp;
- missing mandatory sources make the snapshot invalid;
- tests reject malformed snapshots.

## Phase 2: Rule Snapshot Generator

Goal: replace loose generated Markdown-only rule refreshes with a structured snapshot plus human projection.

Acceptance:

- `communication-refresh` and `handoff-refresh` emit or reference structured snapshot data;
- Markdown projections remain readable but are not the only source of truth;
- tests verify source hashes and missing-source behavior.

## Phase 3: LLM Acknowledgement Contract

Goal: define and validate an acknowledgement that proves the LLM has read the exact current snapshot.

Required acknowledgement fields:

- snapshot id,
- snapshot hash,
- repo head,
- source count,
- missing source count,
- declared next allowed action.

Acceptance:

- product work remains blocked without a matching acknowledgement;
- stale or mismatched acknowledgement is rejected;
- acknowledgement is repo-readable or transfer-state-readable.

## Phase 4: Transfer-State Integration

Goal: integrate rule freshness into transfer state.

Required states:

- `RULE_REFRESH_REQUIRED`,
- `RULE_SNAPSHOT_READY`,
- `WAITING_FOR_LLM_RULE_ACK`,
- `RULES_CONFIRMED`,
- `RULE_REFRESH_BLOCKED`.

Acceptance:

- transfer state exposes these states as JSON;
- next action is deterministic;
- unsafe actions are blocked unless rules are confirmed.

## Phase 5: GUI Gate Integration

Goal: make the GUI a control surface over the hardened rule state.

Acceptance:

- GUI buttons are enabled only when transfer state allows them;
- blocked states show the exact missing prerequisite;
- no GUI path bypasses the rule-refresh gate.

## Execution Order

1. Complete Phase 0 before expanding GUI implementation.
2. Implement the snapshot schema before changing rule-refresh behavior broadly.
3. Add acknowledgement validation before treating a generated rule file as sufficient.
4. Integrate transfer-state gating before adding GUI write actions.
5. Only after this foundation is green should GUI implementation expand.

## Explicit Non-Goals

- no release, tag, DOI, or publication work;
- no broad rewrite of the rule registry;
- no GUI implementation in the planning PR;
- no claim that deterministic validation proves semantic perfection;
- no chat-only rule additions without repo-backed anchors.

## Review Rule

Any future slice in this line must answer:

- Does this reduce reliance on chat memory?
- Does this make drift detectable earlier?
- Does this fail closed?
- Does this improve local-to-LLM or LLM-to-local transfer reliability?
- Does this keep GUI behavior downstream of machine-checked state?
