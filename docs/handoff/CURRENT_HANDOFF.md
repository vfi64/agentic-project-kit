<!-- post-pr714-closeout -->
# Current Handoff

Status-date: 2026-05-24
Project: agentic-project-kit
Branch: main
Base branch: main
Current version: 0.4.1

## Purpose

This file is the concise, curated current handoff pointer. Long-term history belongs in CHANGELOG, release records, governance contracts, and committed terminal evidence.

## Current State

- Current released version: 0.4.1.
- Current release tag: v0.4.1.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
- Main is refreshed after PR #714 at `7d092cb`.
- Evidence: `docs/reports/terminal/pr714-verify-after-test-alignment.log`; remote evidence present.

## Current Repository State

Safe state is main after PR714. PR715 is administrative closeout only. Broad migration, release, tag, DOI mutation, and non-read-only GUI work remain blocked. The repository is the source of truth; chat memory is not a source of truth.

## Current Goal

Repair PR715 closeout drift, merge only after green CI and clean mergeability, then implement structured-summary enforcement before documentation-management work resumes.

## Current Baselines

Documentation registry: `docs/DOCUMENTATION_REGISTRY.yaml`; contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`; summary: `agentic-kit docs-registry`; JSON report: `agentic-kit docs-registry --report PATH`; visible in agentic-kit check-docs, agentic-kit doctor, docs-audit, doc-mesh-audit, doc-lifecycle-audit, handoff, release-check, and post-release-check.

Workflow hardening: direct-path-first GitHub connector use; structured YAML mutation; `.agentic/control_file_preservation.yaml`; no-remote-command-deadlock; remote-first no-guess; command help inspection; Terminal acknowledgement audit; remote inspection evidence contract.

GUI MVP: cockpit-readiness, doctor, and check-docs pass as bounded read-only GUI actions. GUI readiness hardening, not a Tkinter implementation, remains the boundary. Action Registry is the single source of allowed GUI actions. Do not start GUI implementation in this slice.

## Mandatory Successor-Chat Sources

Read before mutation: `.agentic/compiled_agent_context.yaml`, `docs/governance/FINAL_SUMMARY_CONTRACT.md`, `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`, `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `docs/TEST_GATES.md`, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, log, PRs, latest terminal log, handoff state, interpreter state, and gates before patching.
- Do not assume global python, python3, agentic-kit, ruff, pytest, or venv.
- Remote-first no-guess includes command help, known remote paths, PRs, commits, logs, and authoritative repo files before action.
- Remote command first is a delivery preference, not a permission bypass or a reason to skip evidence.
- Preserve PASS and FAIL terminal output remotely under docs/reports/terminal when technically possible.
- `d`, `D`, `f`, or `F` are acknowledgement signals, not evidence; inspect logs before continuing; last terminal output must be checked for contradictions, including a PASS summary after a failed step, not only the final summary block.
- Relevant workflow blocks must render the mandatory final SUMMARY through the canonical renderer route. Legacy handmade WORK RESULT and NEXT_CHAT_REPLY summaries are drift. Example evidence field: terminal_log=docs/reports/terminal/<name>.log.
- Final summary contract anchors: WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE: PASS, NEXT_CHAT_REPLY: p, CHAT_REPLY, terminal_log, command_report.
- No executable placeholder summaries and final-summary-no-executable-placeholders remain active.
- Remote log lookup must direct-fetch the named docs/reports/terminal log path before asking the user to paste output.
- FAIL without terminal kill uses NEXT_CHAT_REPLY: f and must first inspect the repo-backed log before requesting paste-output.
- Typed Work Orders Pre-GUI Execution Path remains preferred: ./ns typed-run <path>; ./ns typed-queue-status --json; ./ns typed-next --json; it uses the minimal typed Work Order Runner as the pre-GUI bridge without chat-generated patch scripts and dirty-state blocking. Required typed-state anchors: no_command, exactly_one_command, multiple_commands, already_executed, dirty worktrees, typed Patch DSL, structured State Source of Truth, Markdown is a projection.
- Recurring workflow problems must become rules, failure patterns, tests, or tooling.

## Required Local Gate

Run state-freshness-check, handoff-check, governance-check, docs-audit, dev, and terminal-remote-preflight where applicable.

## Next Safe Step

Repair PR715 first and verify that the post-PR714 closeout state, handoff state, current handoff, and successor prompt are consistent with PR714 rather than PR712. After PR715 is green and merged, the next immediate hardening slice is structured final-summary enforcement.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through docs/STATUS.md, docs/handoff/CURRENT_HANDOFF.md, .agentic/handoff_state.yaml, docs/TEST_GATES.md, docs/DOCUMENTATION_COVERAGE.yaml, .agentic/project.yaml, sentinel.yaml, governance contracts, and committed terminal evidence.

## Historical Compatibility Anchors

agentic-kit check-docs; agentic-kit doctor; Tkinter cockpit; v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; not the Tkinter cockpit release; PR #463: ActionResult core contract; PR #464: `cockpit run --json`; PR #465: Registry-only; PR #466: Queue-State contract; PR #467: Evidence-State contract; already executed command; dirty-state blocking; dirty worktrees; v0.3.31 Pre-GUI Execution Hardening Plan; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 Evidence Guard Usage; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; Local shortcut `./ns evidence-guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion.; Typed Work Orders Pre-GUI Execution Path; typed Patch DSL; structured State Source of Truth; Markdown is a projection; no_command; exactly_one_command; multiple_commands; already_executed; v0.3.32 Release Phase and Evidence Closeout; Current released version: 0.3.29; Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path; v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; no new large shell control blocks; Tkinter remains explicitly deferred; Do not start GUI implementation in this slice.; GUI expansion is intentionally paused; remote inspection evidence contract; Remote-log evidence is mandatory for standard-error hardening slices; Terminal acknowledgement audit; PR #650 merged; PR #651 merged; PR #652 merged.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml.
