## Post-PR811 Current-State Override

Safe state is main at `f9cf80513eaa89e7d0e8b4dc060e83621058fe62` (`f9cf805`), after PR #811.

PR #811 is merged and hardens `src/agentic_project_kit/handoff_freshness.py` so successor-handoff discovery includes Markdown, YAML, and YML files. The PR810 stale-Markdown plus valid-YAML override case is covered by `tests/test_handoff_freshness.py`.

Evidence path for this closeout: `docs/reports/terminal/pr811-merge-finalize.log`.

Next safe step: finish the PR811 closeout evidence and then continue only with a small deterministic workflow-kernel hardening slice, such as PR/CI status or protected-diff checking. Do not start broad documentation migration, GUI expansion, release tagging, or publication work from this handoff.


## Post-PR809 Current-State Override

Safe state is main at `ee87fa57ed9372c758e68770478b5783878b506d` (`ee87fa5`), after PR #809 and recovery evidence commit. PR #809 is merged at `02bacce54bdc9fd9936fd381d40a7db82bf12924`.

The current protection baseline includes the finalize-log addendum `docs/governance/FINAL_SUMMARY_CONTRACT_FINALIZE_LOG_ADDENDUM.md`, the protected-change planner broad-rewrite guard, and direct tests in `tests/test_protected_change_planner.py` plus registry integration through the `patch-preflight` mechanism.

Evidence: `docs/reports/terminal/pr809-merge-finalize-summary-recovery.log`. The earlier ambiguous PR809 closeout log is superseded and must not be used as success evidence.

Next safe step: continue with guarded status/handoff refresh closeout and then generate a successor-chat handoff only after evidence inspection passes.


<!-- v042-safety-release-prep -->
# Current Handoff

Status-date: 2026-05-25
Project: agentic-project-kit
Branch: main
Base branch: main
Current version: 0.4.2

## Purpose

This file is the concise, curated current handoff pointer. Long-term history belongs in CHANGELOG, release records, governance contracts, and committed terminal evidence.

## Current State

- Prepared release: 0.4.2.
- Prepared release tag: v0.4.2.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Previous verified Zenodo version DOI: `10.5281/zenodo.20357657`; v0.4.2 Zenodo verification is pending until post-release closeout.
- Main is refreshed after PR #766 at `cf75340`.
- PRs #718-#764 established and closed out the governed rule-registry direct-coverage baseline: mechanism inventory, migration map, validator, CLI command, workflow-guard integration, patch-preflight integration, deterministic metadata/conflict/completeness checks, direct test coverage for all active mechanisms, an empty direct-test follow-up plan, and explicit machine-readable plus human-readable completion reporting.
- Evidence: `docs/reports/terminal/pr737-rule-registry-release-evidence.log`, `docs/reports/terminal/pr739-rule-registry-source-evidence-validation.log`, `docs/reports/terminal/pr740-rule-registry-surfaces-tests-inventory.log`, `docs/reports/terminal/pr741-rule-registry-surfaces-tests-inventory-recovery.log`, `docs/reports/terminal/pr742-rule-registry-surfaces-tests-validation.log`, `docs/reports/terminal/pr761-chat-communication-direct-coverage.log`, `docs/reports/terminal/pr762-chat-bootstrap-drift-direct-coverage.log`, and `docs/reports/terminal/pr764-rule-registry-completion-reporting.log`.

## Current Repository State

Safe state is main after PR766 and before v0.4.2 release publication. The governed rule registry is enforced through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight. It currently covers twelve active mechanisms with category, priority, enforcement_phase, owner, conflict_domains, surfaces, tests, coverage classification, migration-map completeness, and direct-test coverage for all active mechanisms: summary-renderer, execution-mode-switch, rule-preservation-guard, workflow-guard, patch-preflight, chat-communication-rules, chat-bootstrap-drift-rules, portable-execution-rules, evidence-guard, typed-work-order-runner, release-state-validation, and post-release-archive-check. `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json` now expose explicit direct-coverage completion state. Broad documentation migration, release, tag, DOI mutation, and non-read-only GUI work remain blocked unless a new slice explicitly scopes them. GUI work remains deferred. The repository is the source of truth; chat memory is not a source of truth.

## A1 State Refresh Addendum

Protected Change Planner A1 is complete on remote main.

- Verified main HEAD: `c07f8ece568501771849bd922aefd1f8ed169ff6`.
- PR #791 is merged.
- `./ns protected-change-plan --diff-file <file>` routes to `agentic_project_kit.protected_change_planner`.
- Verification log: `docs/reports/terminal/protected-change-planner-a1-merge-verify.log`.
- Immediate next slice: fix expected-negative-smoke and final-summary ambiguity before product work.

## Current Goal

Prepare and publish the v0.4.2 safety release, then start a successor chat before resuming documentation-management rebuild work.

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
- `d`, `D`, `f`, or `F` are acknowledgement signals, not evidence; inspect logs before continuing; last terminal output must be checked for contradictions, including a PASS summary after a failed step, not only the final summary block.
- Relevant workflow blocks must render the mandatory final SUMMARY through the canonical renderer route. Legacy handmade WORK RESULT and NEXT_CHAT_REPLY summaries are drift. Example evidence field: terminal_log=docs/reports/terminal/<name>.log.
- Final summary contract anchors: WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE: PASS, NEXT_CHAT_REPLY: p, CHAT_REPLY, terminal_log, command_report.
- No executable placeholder summaries and final-summary-no-executable-placeholders remain active.
- Remote log lookup must direct-fetch the named docs/reports/terminal log path before asking the user to paste output.
- FAIL without terminal kill uses NEXT_CHAT_REPLY: f and must first inspect the repo-backed log before requesting paste-output.
- Typed Work Orders Pre-GUI Execution Path remains preferred: ./ns typed-run <path>; ./ns typed-queue-status --json; ./ns typed-next --json; it uses the minimal typed Work Order Runner as the pre-GUI bridge without chat-generated patch scripts and dirty-state blocking. Required typed-state anchors: no_command, exactly_one_command, multiple_commands, already_executed, dirty worktrees, typed Patch DSL, structured State Source of Truth, Markdown is a projection.
- Recurring workflow problems must become rules, failure patterns, tests, or tooling.
- Governed rule-registry changes must be additive, structured, test-backed, and validated through `rule-registry check`, workflow-guard, and patch-preflight.
- Documentation-management rebuild work may resume only as small additive documentation-registry or projection slices after this closeout is merged and verified.

## Required Local Gate

Run state-freshness-check, handoff-check, governance-check, rule-registry check, patch-preflight, docs-audit, dev, and terminal-remote-preflight where applicable.

## Next Safe Step

Merge and verify v0.4.2 release metadata, publish the v0.4.2 tag/release, run post-release checks, and then prepare a detailed successor-chat handoff.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through docs/STATUS.md, docs/handoff/CURRENT_HANDOFF.md, .agentic/handoff_state.yaml, docs/TEST_GATES.md, docs/DOCUMENTATION_COVERAGE.yaml, .agentic/project.yaml, sentinel.yaml, governance contracts, rule-registry files, and committed terminal evidence.

## Historical Compatibility Anchors

agentic-kit check-docs; agentic-kit doctor; Tkinter cockpit; v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; not the Tkinter cockpit release; PR #463: ActionResult core contract; PR #464: `cockpit run --json`; PR #465: Registry-only; PR #466: Queue-State contract; PR #467: Evidence-State contract; already executed command; dirty-state blocking; dirty worktrees; v0.3.31 Pre-GUI Execution Hardening Plan; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 Evidence Guard Usage; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; Local shortcut `./ns evidence-guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion.; Typed Work Orders Pre-GUI Execution Path; typed Patch DSL; structured State Source of Truth; Markdown is a projection; no_command; exactly_one_command; multiple_commands; already_executed; v0.3.32 Release Phase and Evidence Closeout; Current released version: 0.3.29; Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path; v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; no new large shell control blocks; Tkinter remains explicitly deferred; Do not start GUI implementation in this slice.; GUI expansion is intentionally paused; remote inspection evidence contract; Remote-log evidence is mandatory for standard-error hardening slices; Terminal acknowledgement audit; PR #650 merged; PR #651 merged; PR #652 merged.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml.
