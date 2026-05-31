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

## Canonical Rule Source Contract

The hardened rule-refresh workflow must not create a second manually maintained rule system.

The existing repository-backed rule sources remain the only canonical rule source of truth. They include the existing `.agentic/*.yaml` rule and handoff files, governance documents, handoff documents, planning documents, and the existing rule-refresh source lists.

Snapshots are derived artifacts. They must be generated from canonical sources and must never require manual rule duplication.

Markdown refresh files are human-readable projections. They may help the LLM and maintainer understand the current rules, but they are not the authoritative machine state.

The optimized architecture is:

- Canonical rule sources
- read-only validation
- derived snapshot with hashes, freshness, and validity
- human-readable projection
- LLM acknowledgement against snapshot identity
- transfer-state gate
- GUI button state

A future implementation must preserve this single-source model. If a proposed slice adds a manually edited snapshot, a separate GUI rule table, or a chat-only rule copy, the slice must be blocked or redesigned.

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
- Do not introduce double-maintained rule or snapshot state.
- Treat generated snapshots and Markdown refresh files as derived artifacts, not canonical sources.

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

Phase 0 artifact: `docs/planning/TRANSFER_GITHUB_ACTION_COVERAGE.md`.

Rule-source validator JSON contract: `docs/planning/RULE_SOURCE_VALIDATOR_JSON_CONTRACT.md`.

## Phase 1: Canonical Rule Source Hardening And Derived Snapshot Schema

Goal: harden the existing canonical rule sources and define the derived snapshot schema without creating a second manually maintained rule system.

Required work:

- document the canonical source set used by rule refresh;
- add read-only validation expectations for existing YAML and governance sources;
- define required source presence, parseability, and role metadata;
- define per-source content hashing for derived snapshots;
- define a combined snapshot identity derived from canonical sources;
- define missing-source and stale-state validity fields;
- define intended next LLM action and allowed next transfer state;
- specify that Markdown refresh files are projections, not canonical state.

Acceptance:

- the canonical source contract is documented;
- schema work is framed as a generated derivative of canonical sources;
- generated snapshots are deterministic except for timestamp;
- missing mandatory sources make the derived snapshot invalid;
- tests reject double-maintained rule-state language;
- tests protect the no-parallel-rule-system decision.

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
2. Harden and validate canonical sources before adding generated snapshot behavior broadly.
3. Add acknowledgement validation before treating a generated rule file as sufficient.
4. Integrate transfer-state gating before adding GUI write actions.
5. Only after this foundation is green should GUI implementation expand.

## Explicit Non-Goals

- no release, tag, DOI, or publication work;
- no broad rewrite of the rule registry;
- no GUI implementation in the planning PR;
- no claim that deterministic validation proves semantic perfection;
- no chat-only rule additions without repo-backed anchors;
- no parallel manually maintained snapshot or GUI rule table.

## Review Rule

Any future slice in this line must answer:

- Does this reduce reliance on chat memory?
- Does this make drift detectable earlier?
- Does this fail closed?
- Does this improve local-to-LLM or LLM-to-local transfer reliability?
- Does this keep GUI behavior downstream of machine-checked state?
- Does this preserve one canonical rule source model?
