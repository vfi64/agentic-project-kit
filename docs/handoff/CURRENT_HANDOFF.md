Current version: 0.4.1

# Current Handoff

<!-- CURRENT_HANDOFF_OVERLAY_AFTER_PR709 -->

# Current Handoff Overlay After PR709

Status-date: 2026-05-24
Project: agentic-project-kit
Branch: main
Base branch: main

## Purpose

This overlay records the current state after PR #709 without treating preserved compatibility anchors as the current source-of-truth narrative. `docs/STATUS.md` is the compact live dashboard; `CHANGELOG.md`, release records, governance contracts, and terminal evidence hold long-term history.

## Current State

- Current released version: 0.4.1.
- Current release tag: v0.4.1.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
- PR #692 introduced the first documentation registry schema and guard slice.
- PR #695 added the first read-only registry consumer and operational/artifact classifications.
- PR #696 added the read-only registry JSON report path.
- PR #697 added docs-audit registry visibility.
- PR #698 added doc-mesh registry visibility.
- PR #699 added doc-lifecycle registry visibility.
- PR #700 added handoff check/show registry visibility.
- PR #701 added release-check and post-release-check registry visibility.
- PR #702 refreshed state and handoff artifacts after PR701.
- PR #706 added the warning-based successor handoff prompt freshness guard.
- PR #707 recorded post-guard successor handoff and closeout evidence.
- PR #708 refreshed handoff state after PR707.
- PR #709 exposed `.agentic/communication_artifacts.yaml` through the read-only documentation registry summary and JSON report without changing cleanup behavior.

## Documentation Registry Baseline

- Machine-readable registry: `docs/DOCUMENTATION_REGISTRY.yaml`.
- Registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- Read-only summary command: `agentic-kit docs-registry`.
- Read-only JSON report: `agentic-kit docs-registry --report PATH`.
- Artifact policy source now consumed by the registry summary: `.agentic/communication_artifacts.yaml`.
- The registry is visible in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.
- Broad migration is still forbidden. The current registry guard is structural only and does not prove semantic documentation quality.

## Current GUI Baseline

- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- Headless GUI action execution tests cover the bounded read-only executor.
- `agent-run` and non-read-only GUI actions remain disabled in the GUI MVP.
- The future Tkinter cockpit must remain a thin presentation layer over registry actions and machine-readable results.

## Mandatory Source Order For Next Chat

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

## Active Rules For The Next Slice

- Start from repo state, not chat memory.
- Use the successor handoff freshness guard before treating handoff prose as authoritative.
- A pure administrative handoff refresh merge must not create an endless refresh loop.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Keep documentation registry work additive, reversible, and test-backed.
- Do not start a broad documentation migration, create a tag, publish a release, or perform remote/destructive GUI actions.

## Required Local Gate

Before merge or handoff, run:

```bash
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns docs-audit
./ns dev
agentic-kit check-docs
agentic-kit doctor
agentic-kit post-release-check --version 0.4.1
```

## Mandatory Final Summary Contract

Relevant terminal blocks must end with the mandatory final SUMMARY block. Use `NEXT_CHAT_REPLY: p` only when `OVERALL RESULT: PASS` and `REMOTE_EVIDENCE: PASS`. Use `NEXT_CHAT_REPLY: f` when the work failed but remote evidence is available. Use `NEXT_CHAT_REPLY: paste-output` when remote evidence is missing or incomplete.

## Next Safe Step

Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr709.md` for a chat switch after this closeout lands. Then continue the documentation-management rebuild with one small, additive, reversible, test-backed registry slice, preferably toward machine-readable source/projection planning.

Do not start a broad documentation migration, create a tag, publish a release, or perform remote/destructive GUI actions in the next slice.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage and compatibility: documentation coverage, `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, `agentic-kit doctor`, policy-pack checks, policy packs, post-release Zenodo, `agentic-kit post-release-check`, no-copy/evidence, Tkinter cockpit, curated, Current released version: 0.3.29, Mandatory Final Summary Contract, `NEXT_CHAT_REPLY: p`, `REMOTE_EVIDENCE: PASS`.
