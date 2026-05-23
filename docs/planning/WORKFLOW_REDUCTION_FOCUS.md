# Workflow Reduction Focus

Status-date: 2026-05-23
Status: planning focus
Project: agentic-project-kit

## Purpose

This document records the near-term product focus for `agentic-project-kit` after the v0.4.1 documentation-registry baseline.

The next maturity step is not to add more advisory intelligence. The next maturity step is to reduce manual orchestration while preserving safety, evidence, and deterministic governance.

## Strategic Focus

The kit should increasingly answer these questions from repository state instead of chat memory:

- What is the current state?
- What is the next safe action?
- What is forbidden?
- What is stale?
- What evidence exists?
- Which documents are live state, governance, release history, generated artifacts, temporary artifacts, or evidence?

The goal is to move from a powerful expert tool toward a robust working instrument.

## Priority Order

1. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
2. Use the registry to make status, handoff, evidence, artifacts, and retention/GC behavior visible and machine-checkable.
3. Build the GUI as a control surface over already-hardened read-only or bounded actions.
4. Defer Pattern Advisor expansion until the document and evidence substrate is stable.

## Work Model Direction

Future work should prefer small machine-readable work orders over long chat-orchestrated execution. A work order should state:

- slice name,
- goal,
- allowed files,
- required tests or checks,
- forbidden actions,
- closeout requirements.

Chat should describe intent. Repo-owned tools should execute typed operations. Markdown should increasingly be a curated projection of machine-readable state, not the primary state source.

## Handoff and Status Direction

Handoff prompts should be generated from state files, Git state, PR state, registry data, and gate evidence wherever possible. Manual free prose should be a curated supplement, not the source of truth.

`docs/STATUS.md` should remain a compact dashboard. Long history belongs in `CHANGELOG.md`, release records, evidence logs, or dedicated planning documents such as this file.

## Sequencing Decision

This focus must be recorded before completing the documentation-management phase so that the remaining registry slices and the later GUI are shaped by it.

Implementation should not interrupt the current documentation-management line. The practical sequence is:

1. record the focus now;
2. continue the handoff/status freshness guard and documentation-registry work;
3. complete the documentation-management foundation enough for artifact and evidence visibility;
4. then make the GUI expose this reduced-orchestration model;
5. only after that, resume Pattern Advisor expansion.

## Non-Goals For The Current Line

- no broad documentation migration,
- no release or tag work,
- no destructive GUI or remote-GUI actions,
- no expansion of Pattern Advisor before the registry and GUI foundations are ready,
- no new chat-only rules without a repository home and, where appropriate, deterministic checks.

## Review Rule

When a future slice adds complexity, reviewers should ask whether it reduces manual orchestration or only adds another surface area. Prefer the smallest change that makes state, evidence, next action, or drift more explicit.
