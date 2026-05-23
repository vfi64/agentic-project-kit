Current version: 0.4.1

# Current Handoff

Status-date: 2026-05-23
Project: agentic-project-kit
Branch: main
Base branch: main

## Purpose

This file is a concise current-state handoff pointer, not a long historical log. It intentionally keeps compact compatibility anchors for deterministic gates, but the current source-of-truth narrative is the active state below.

The repository is the source of truth, not chat memory. This document states the concise-pointer boundary and keeps docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md as concise pointers, not duplicate rule books. Long narrative history belongs in CHANGELOG.md, docs/releases/VERIFIED_RELEASES.md, architecture/governance contracts, planning documents, or committed terminal evidence logs.

## Current State

- Current released version: 0.4.1.
- Current release tag: v0.4.1.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
- Post-release Zenodo verification is covered by `agentic-kit post-release-check --version 0.4.1`.
- v0.4.1 is tagged, published, post-release checked, and DOI metadata is recorded on main.

## Current Documentation-Management Baseline

- PR #692 introduced the first documentation registry schema and guard slice.
- PR #694 refreshed the live status after the registry baseline.
- PR #695 added the first read-only registry consumer and operational/artifact classifications.
- PR #696 added the read-only registry JSON report path.
- PR #697 added docs-audit registry visibility.
- PR #698 added doc-mesh registry visibility.
- PR #699 added doc-lifecycle registry visibility.
- PR #700 added handoff check/show registry visibility.
- PR #701 added release-check and post-release-check registry visibility.
- PR #703 added the workflow-reduction planning focus.
- PR #704 added the machine-readable operational source direction.

Machine-readable registry: `docs/DOCUMENTATION_REGISTRY.yaml`.
Registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
Read-only summary command: `agentic-kit docs-registry`.
Read-only JSON report: `agentic-kit docs-registry --report PATH`.
Registry summary data is visible in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.

Broad migration is still forbidden. The current registry guard is structural only and does not prove semantic documentation quality.

## Planning Focus

The active planning direction is recorded in `docs/planning/WORKFLOW_REDUCTION_FOCUS.md`.

Priority order:

1. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
2. Use the registry to make status, handoff, evidence, artifacts, and retention/GC behavior visible and machine-checkable.
3. Build the GUI as a control surface over already-hardened read-only or bounded actions.
4. Defer Pattern Advisor expansion until the document and evidence substrate is stable.

Machine-readable source direction: operational truth should move into machine-readable sources or machine-checkable anchors. Human-facing Markdown, GUI dashboards, handbooks, and LLM prose should explain, summarize, or project structured state. The LLM may translate structured sources into clear human prose, but it must not be the only place where operational truth exists.

## Current GUI Baseline

- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- Headless GUI action execution tests cover the bounded read-only executor.
- `agent-run` and non-read-only GUI actions remain disabled in the GUI MVP.
- Tkinter remains explicitly deferred until the documentation-management and handoff foundations are stable enough for the GUI to consume structured state.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, recent commits, open PRs, latest terminal log, handoff state, interpreter/tooling state, and gates before patching.
- Keep state documents curated. Do not append new current-state fragments below obsolete ones.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Use `agentic-kit handoff prompt` or `python -m agentic_project_kit.cli handoff prompt` as the canonical successor prompt generator when local tooling is available.
- Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv`.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Final summaries must appear in terminal output and terminal logs for relevant workflow blocks.
- Short replies such as `d`, `D`, `f`, `F`, `w`, `W`, and `p` are communication signals, not evidence.
- Ruff must run only on Python sources or Python files; shell files use shell checks, not Ruff.
- Do not use heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, or quote-prone shell constructs in chat-pasted terminal blocks.
- Larger terminal blocks must begin with three long separator lines and end with a clear `### RESULT: ... ###` marker.
- New operative documents must not be free prose only. Operational state, next actions, evidence, release state, handoff state, registry entries, work orders, artifact-retention rules, and automation behavior need machine-readable sources or machine-checkable anchors.

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

Before any remote mutation, merge verification, release publication, tag creation, or clean-tree sync workflow, additionally run `./ns terminal-remote-preflight`.

This remote chat environment cannot run local Python 3.13 gates. Merge readiness requires equivalent CI evidence.

## Mandatory Successor-Chat Sources

Mandatory successor-chat source order is defined by `.agentic/compiled_agent_context.yaml` and checked by `agentic-kit docs-audit`:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. `.agentic/handoff_state.yaml`
10. `AGENTS.md`
11. `CHANGELOG.md`
12. `README.md`
13. `CITATION.cff`
14. `docs/releases/VERIFIED_RELEASES.md`
15. relevant source files and tests for the requested slice

## Next Safe Step

Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr704.md` for a chat switch.

The next substantive slice should implement the handoff-prompt freshness guard so a stale successor handoff prompt cannot silently remain authoritative after later main merges. After that, continue the documentation-management rebuild with one small registry consumer such as Artifact-GC planning. Do not start a broad migration, create a tag, publish a release, or perform remote/destructive GUI actions in the next slice.

## Mandatory Final Summary Contract

Relevant terminal blocks must end with the mandatory final SUMMARY block. Use concrete values, not placeholder alternatives.

Required fields:

- `WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED`
- `OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED`
- `terminal_log=<repo-path-or-NONE>`
- `command_report=<repo-path-or-NONE>`
- `NEXT_CHAT_REPLY: p|f|paste-output|continue|stop`
- final marker: `### RESULT: PASS|FAIL|PENDING|HARD-FAIL ###`

## Compact Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, policy-pack doctor checks, Pattern Advisor, `patterns list`, `patterns show`, read-only catalog, advisory-only, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, v0.3.31 is the current pre-GUI execution hardening line., Mandatory Final Summary Contract, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`.

Additional legacy anchors for current gates: Current released version: 0.3.29; Current released version: 0.3.32; Version `0.3.9`; v0.3.3; 10.5281/zenodo.20151924; GUI readiness hardening, not a Tkinter implementation; GUI readiness also covers dirty worktrees, dirty inboxes, failed commands, and postcondition failures; v0.3.30 is the GUI readiness contract release, not the Tkinter cockpit release; Typed Work Orders Pre-GUI Execution Path; preferred pre-GUI execution path; already executed command; dirty worktrees; remote evidence present; no-remote-command-deadlock; remote-first no-guess; remote inspection evidence contract; final-summary-no-executable-placeholders; The short acknowledgement `d` is also valid.
