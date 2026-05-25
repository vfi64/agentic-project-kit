<!-- v042-post-release-doi-closeout -->
# Current Handoff

Status-date: 2026-05-25
Project: agentic-project-kit
Branch: main
Base branch: main
Current version: 0.4.2

## Purpose

This file is the concise, curated current handoff pointer. Long-term history belongs in CHANGELOG, release records, governance contracts, and committed terminal evidence.

## Current State

- Released version: 0.4.2.
- Release tag: v0.4.2.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.4.2 Zenodo version DOI: `10.5281/zenodo.20376095`.
- GitHub Release publication, release assets, and post-release Zenodo verification are complete for v0.4.2.
- Main is refreshed after PR #769 at `06d6ea30a39e5763283358db8bb93d5566b421cd`.
- Release assets are verified: `agentic_project_kit-0.4.2-py3-none-any.whl` and `agentic_project_kit-0.4.2.tar.gz`.
- Release evidence: `docs/reports/terminal/pr767-v042-release-metadata-prep.log`, `docs/reports/terminal/v042-release-publish.log`, and `docs/reports/terminal/v042-post-release-check.log`.
- PRs #718-#764 established and closed out the governed rule-registry direct-coverage baseline with direct test coverage for all active mechanisms and explicit completion reporting.

## Current Repository State

Safe state is main after PR769 and after v0.4.2 release publication plus post-release DOI verification. The governed rule registry is enforced through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight. It covers twelve active mechanisms: summary-renderer, execution-mode-switch, rule-preservation-guard, workflow-guard, patch-preflight, chat-communication-rules, chat-bootstrap-drift-rules, portable-execution-rules, evidence-guard, typed-work-order-runner, release-state-validation, and post-release-archive-check. `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json` expose explicit direct-coverage completion state. GUI work remains deferred. The repository is the source of truth; chat memory is not a source of truth.

## Current Goal

Complete this v0.4.2 DOI metadata closeout, merge it, and then fix protected control-file preservation before further registry hardening, generated projection work, or documentation-management rebuild work resumes.

## Current Baselines

Documentation registry: `docs/DOCUMENTATION_REGISTRY.yaml`; contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`; summary: `agentic-kit docs-registry`; JSON report: `agentic-kit docs-registry --report PATH`; visible in agentic-kit check-docs, agentic-kit doctor, docs-audit, doc-mesh-audit, doc-lifecycle-audit, handoff, release-check, and post-release-check.

Rule registry: `.agentic/rule_mechanism_inventory.yaml`; migration map: `.agentic/rule_migrations.yaml`; coverage map: `.agentic/rule_test_coverage.yaml`; direct-test plan: `.agentic/rule_direct_test_plan.yaml`; validator: `src/agentic_project_kit/rule_registry_validator.py`; CLI check: `agentic-kit rule-registry check`; CLI report: `agentic-kit rule-registry report`; hard enforcement: workflow-guard and patch-preflight.

Workflow hardening: direct-path-first GitHub connector use; structured YAML mutation; `.agentic/control_file_preservation.yaml`; no-remote-command-deadlock; remote-first no-guess; command help inspection; Terminal acknowledgement audit; remote inspection evidence contract.

GUI MVP: cockpit-readiness, doctor, and check-docs pass as bounded read-only GUI actions. GUI readiness hardening, not a Tkinter implementation, remains the boundary. Action Registry is the single source of allowed GUI actions. Do not start GUI implementation in this slice.

## Mandatory Successor-Chat Sources

Read before mutation: `.agentic/compiled_agent_context.yaml`, `docs/governance/FINAL_SUMMARY_CONTRACT.md`, `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`, `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `docs/TEST_GATES.md`, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `.agentic/rule_mechanism_inventory.yaml`, `.agentic/rule_migrations.yaml`, `.agentic/rule_test_coverage.yaml`, `.agentic/rule_direct_test_plan.yaml`.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, log, PRs, latest terminal log, handoff state, interpreter state, and gates before patching.
- Do not assume global python, python3, agentic-kit, ruff, pytest, or venv.
- Remote-first no-guess includes command help, known remote paths, PRs, commits, logs, and authoritative repo files before action.
- Remote command first is a delivery preference, not a permission bypass or a reason to skip evidence.
- Preserve PASS and FAIL terminal output remotely under docs/reports/terminal when technically possible.
- `d`, `D`, `f`, or `F` are acknowledgement signals, not evidence; inspect logs before continuing.
- Relevant workflow blocks must render the mandatory final SUMMARY through the canonical renderer route.
- Final summary contract anchors: WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE: PASS, NEXT_CHAT_REPLY: p, CHAT_REPLY, terminal_log, command_report.
- Remote log lookup must direct-fetch the named docs/reports/terminal log path before asking the user to paste output.
- Typed Work Orders Pre-GUI Execution Path remains preferred: ./ns typed-run <path>; ./ns typed-queue-status --json; ./ns typed-next --json.
- Recurring workflow problems must become rules, failure patterns, tests, or tooling.
- Governed rule-registry changes must be additive, structured, test-backed, and validated through `rule-registry check`, workflow-guard, and patch-preflight.
- Protected control-file preservation is the first implementation target after this DOI closeout unless a higher-severity release-state inconsistency is discovered.

## Required Local Gate

Run state-freshness-check, handoff-check, governance-check, rule-registry check, patch-preflight, docs-audit, dev, and terminal-remote-preflight where applicable.

## Next Safe Step

Merge and verify this v0.4.2 DOI metadata closeout. After the closeout is on main, fix protected control-file preservation before further registry hardening, generated-projection work, or documentation-management rebuild work.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through docs/STATUS.md, docs/handoff/CURRENT_HANDOFF.md, .agentic/handoff_state.yaml, docs/TEST_GATES.md, docs/DOCUMENTATION_COVERAGE.yaml, .agentic/project.yaml, sentinel.yaml, governance contracts, rule-registry files, and committed terminal evidence.

## Historical Compatibility Anchors

agentic-kit check-docs; agentic-kit doctor; Tkinter cockpit; v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; not the Tkinter cockpit release; PR #463: ActionResult core contract; PR #464: `cockpit run --json`; PR #465: Registry-only; PR #466: Queue-State contract; PR #467: Evidence-State contract; already executed command; dirty-state blocking; dirty worktrees; v0.3.31 Pre-GUI Execution Hardening Plan; v0.3.31 Pre-GUI Execution Hardening Closeout; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`; Local shortcut `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Typed Work Order Evidence Contract; Typed Work Order Evidence Runtime Check; validate_typed_work_order_evidence; Typed Work Orders Pre-GUI Execution Path; typed Patch DSL; structured State Source of Truth; Markdown is a projection; no_command; exactly_one_command; multiple_commands; already_executed; v0.3.32 Release Phase and Evidence Closeout; Current released version: 0.3.29; Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; `release-preflight`; `release-check`; `post-release-check`; `evidence clean-check`; `./ns evidence-clean-check`; v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; Tkinter remains explicitly deferred; remote inspection evidence contract; Remote-log evidence is mandatory for standard-error hardening slices; Terminal acknowledgement audit; PR #650 merged; PR #651 merged; PR #652 merged.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml.
