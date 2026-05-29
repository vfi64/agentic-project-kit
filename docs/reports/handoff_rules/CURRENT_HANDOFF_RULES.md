# Current handoff rules refresh

Status: generated
Generated at: 2026-05-29T19:59:58+00:00
Next reply trigger: `d3`

## Assistant instruction

On user reply d3, read this generated file before continuing and start the documented handoff mechanism from the repo-backed source snapshots.

## Source files

- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `.agentic/handoff_state.yaml`
- `.agentic/compiled_agent_context.yaml`

## Source snapshots

### `docs/handoff/CURRENT_HANDOFF.md`

```text
## Post-PR897 Handoff Refresh State

Current verified main HEAD is `a766ce92bbd4fc6cebfbb3ce3762bfa56e79c60c` (`a766ce9`).
Commit subject: `Harden standard summary log classification (#897)`.

PR #897 is merged. This is an administrative post-merge handoff/status refresh before chat handoff.

The post-merge handoff refresh status gate is the canonical decision point after merges: `agentic-kit handoff post-merge-refresh-status`.

Next safe step after this refresh is merged and verified: start the successor chat from the fresh prompt and continue only if the machine-readable refresh status is `result=NOOP`.

## Post-PR894 Handoff Refresh State

Current verified main HEAD is `87407ac463b46638f340fc757ec452c46e803096` (`87407ac`).
Commit subject: `Merge pull request #894 from vfi64/docs/post-merge-gate-bootstrap-visibility`.

PR #894 is merged. This is an administrative post-merge handoff/status refresh before chat handoff.

The post-merge handoff refresh status gate is the canonical decision point after merges: `agentic-kit handoff post-merge-refresh-status`.

Next safe step after this refresh is merged and verified: start the successor chat from the fresh prompt and continue only if the machine-readable refresh status is `result=NOOP`.

## Post-Merge Handoff Refresh Status Gate Visibility

The post-merge handoff refresh status gate is now documented for bootstrap visibility. After any PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status. Continue only on result=NOOP; create an administrative handoff refresh slice on result=REFRESH_REQUIRED before product work.

## Post-PR892 Handoff Refresh State

Current verified main HEAD is `64f5c4d49e4012e42170b47e6bcf48bf383e8a94` (`64f5c4d`).
Commit subject: `Merge pull request #892 from vfi64/feature/post-merge-gate-visibility-inventory`.

PR #892 is merged. It recorded a read-only inventory of where the post-merge handoff refresh status gate is visible.

Current verified release remains v0.4.4.
Verified Zenodo version DOI remains `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: move the post-merge refresh status gate into a more visible kit/ns workflow path without broad product-code changes.

## Post-PR888 Patch Preflight Slice-Gate State

Current verified main HEAD is `508f3dfa2be50d4f369f31e270cc930c24873015` (`508f3df`).
Commit subject: `Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean`.

PR #888 is merged. It hardens patch preflight with an optional required slice gate, preventing helper-local PASS from being confused with slice readiness when the worktree is dirty or slice governance gates fail.

This is an administrative post-PR888 handoff/status refresh only. No product-code change belongs in this slice.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, with slice-gate evidence and patch-preflight evidence rather than helper-local PASS claims.

## Post-PR886 Workflow Evidence Hygiene State

Current verified main HEAD is `d77d5804d7eead98ff65b52e38c6d73bc640051c` (`d77d580`).
Commit subject: `Merge pull request #886 from vfi64/codex/fix-workflow-evidence-hygiene`.

PR #886 is merged. It removes the recurring dirty-worktree failure caused by ordinary next-turn/work-order runs writing directly to `docs/reports/terminal/next-turn-latest.log`. The fixed repo-backed slot is now produced by explicit upload/promotion, and upload checks `repo_root` to avoid stale evidence from another checkout.

This is an administrative post-PR886 handoff/status refresh only. No product-code change belongs in this slice.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, with slice-gate evidence rather than helper-local PASS claims.

## Post-PR883 GUI Gatekeeper Inventory State

Current verified main HEAD is `1ec13cb5283d9b796b667526791eaa94a04073ff` (`1ec13cb`).
Commit subject: `Merge pull request #883 from vfi64/feature/gui-gatekeeper-inventory-helper`.

PR #883 is merged. It added the GUI gatekeeper implementation inventory and records the implementation surface for result/log classification, summary validation, upload/evidence preflight, work-order routing, action registry, GUI display, handoff freshness, PR/merge readiness, and shell-adapter migration.

This is an administrative post-PR883 handoff/status refresh only. No GUI product-code change belongs in this slice.

Next safe step after this refresh is merged and verified: implement the smallest temporary Python slice-gate command for planning/documentation slices. The gate must distinguish helper-local PASS from slice PASS and block missing repository governance gates.

## Post-PR881 Bootstrap Refresh State

Current verified main HEAD is `1bb1c0d4b1f0d937314f245217cda9266ed0d106` (`1bb1c0d`).
Commit subject: `Refresh bootstrap handoff after PR880`.

PR #881 merged the post-PR880 bootstrap/handoff refresh. This follow-up records the actual post-PR881 main HEAD because the PR #881 merge commit used a custom subject that is not represented by the prior handoff state.

Current verified release remains v0.4.4.
Verified Zenodo version DOI remains `10.5281/zenodo.20431326`.

No GUI product work belongs in this refresh. Next safe step after merge and verification is the GUI deterministic gatekeeper read-only inspection/inventory slice.

## Post-PR880 Bootstrap Refresh State

Current verified main HEAD is `f853ccf770e5f692ca2815912b252e453259fc69` (`f853ccf`).
Commit subject: `Merge pull request #880 from vfi64/fix/handoff-freshness-admin-merge-chain`.

PR #880 is merged. It hardens the handoff freshness guard by accepting direct administrative merge commits and bounded first-parent administrative merge chains, while still blocking product merges inside such chains.

Current verified release remains v0.4.4.
Verified Zenodo version DOI remains `10.5281/zenodo.20431326`.

This is an administrative bootstrap/handoff/status refresh only. No GUI product work belongs in this slice.

Next safe step after this refresh is merged and verified: begin the GUI deterministic gatekeeper migration with a read-only inspection/inventory slice only.

## Post-PR873 GUI Gatekeeper Planning State

Current verified main HEAD is `5b30fe30ed9b813255fb9a89d85a6f7bf1ab70ab` (`5b30fe3`).
Commit subject: `Record PR873 final main closeout evidence`.

PR #873 baseline is `Add GUI work order upload strip (#873)`, commit `23532a0`. Final closeout evidence: `docs/reports/terminal/pr873-final-main-closeout.log`.

Planning document: `docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md`.

PR #874 is planning/state-refresh only. It records the GUI deterministic gatekeeper migration plan and refreshes state pointers. It must not include product-code changes.

Required sequence:
1. Finish planning-only PR #874.
2. Prepare and publish safety release v0.4.4.
3. Generate fresh successor-chat handoff.
4. Start the gatekeeper migration PR series in small reversible PRs.

Next safe step: finish this planning/state-refresh PR; do not start gatekeeper implementation or further GUI feature work before v0.4.4 is released and post-release verified.

## Post-PR838 Administrative Handoff Refresh State

Current administrative main HEAD is `777d957474318fdf797ca23625e52046c3fb7df0` (`777d957`), after PR #838 refreshed post-PR837 administrative handoff state.

PR #837 `Record post-PR836 successor handoff` is merged at `71ba85b5322e26c52680b0dbfe38d81957bb1160` (`71ba85b`). PR #838 `Refresh post-PR837 administrative handoff state` is merged at `777d957474318fdf797ca23625e52046c3fb7df0` (`777d957`).

The substantive safe-state remains `c0ac933a29b71c6660ae7e436386414f08ff9e7b` (`c0ac933`) under `safe_state.semantics: last_substantive_work_state`; later handoff-only refreshes belong in `administrative_evidence_state`.

Next safe step: finish this post-PR838 handoff/status freshness refresh, then continue only with the smallest planned GUI or failure-mode automation slice.


## Post-PR834 Successor-Handoff Freshness Closeout State

Current verified main HEAD is `fd1e631312723166982fb1e0d9ecb76397e97559` (`fd1e631`), after PR #834 repaired generator-backed handoff freshness.

Generated handoff safe-state anchor is `fd1e631312723166982fb1e0d9ecb76397e97559` (`fd1e631`).

PR #835 added `docs/reports/terminal/post-pr836-successor-handoff.md` and `docs/reports/terminal/post-pr836-successor-handoff.log` as the successor/evidence anchors.

v0.4.4 is published and post-release verified. Verified Zenodo version DOI: `10.5281/zenodo.20431326`. Release verification evidence: `docs/reports/terminal/v044-post-release-verify.log`.

Next safe step: continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears.


## Post-PR809 Current-State Override

Safe state is main at `ee87fa57ed9372c758e68770478b5783878b506d` (`ee87fa5`), after PR #809 and recovery evidence commit. PR #809 is merged at `02bacce54bdc9fd9936fd381d40a7db82bf12924`.

The current protection baseline includes the finalize-log addendum `docs/governance/FINAL_SUMMARY_CONTRACT_FINALIZE_LOG_ADDENDUM.md`, the protected-change planner broad-rewrite guard, and direct tests in `tests/test_protected_change_planner.py` plus registry integration through the `patch-preflight` mechanism.

Evidence: `docs/reports/terminal/pr809-merge-finalize-summary-recovery.log`. The earlier ambiguous PR809 closeout log is superseded and must not be used as success evidence.

Next safe step: continue with guarded status/handoff refresh closeout and then generate a successor-chat handoff only after evidence inspection passes.


<!-- v042-safety-release-prep -->
# Current Handoff

Status-date: 2026-05-27
Project: agentic-project-kit
Branch: codex/refresh-post-pr835-next-step-state
Base branch: main
Current version: 0.4.4

## Purpose

This file is the concise, curated current handoff pointer. Long-term history belongs in CHANGELOG, release records, governance contracts, and committed terminal evidence.

## Current State

- Current verified release: 0.4.4.
- Current release tag: v0.4.4.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20431326`.
- Main contains PR #834 at `fd1e631`.
- PR #835 added PR834 closeout evidence at `docs/reports/terminal/post-pr836-successor-handoff.log`.
- Generated handoff safe-state now anchors to PR #834 via `docs/reports/terminal/post-pr836-successor-handoff.md`.
- PR #833 recorded the corrected post-PR831 successor handoff at `docs/reports/terminal/post-pr831-successor-handoff.md`.
- PR #831 recorded PR #830 closeout evidence at `docs/reports/terminal/pr830-merge-finalize.log`.
- PR #825 hardened active handoff freshness checks so already-recorded closeout evidence and stale release-version instructions are blocking drift.
- PR #824 recorded PR #823 closeout evidence at `docs/reports/terminal/pr823-merge-finalize.log`.
- PR #823 hardened `merge-if-green` so the merge command validates the target base branch, requires a PR head SHA, passes `--match-head-commit <sha>` to GitHub, and renders checked base/head refs.
- PR #821 hardened `merge-if-green` so post-merge main-CI verification is required before the command reports clean success.
- PR #819 hardened PR status failed-log diagnostics so red CI carries check names, Actions run ids, exact failed-log commands, bounded log-fetch status, and `no-checks` classification.
- PR #817 hardened PASS_ALREADY_DONE target-state classification so generic already-exists output is not sufficient success evidence.
- PR #815 hardened release-prep atomicity and remote release readiness so inconclusive remote checks no longer permit a release PASS.
- PR #812 includes the PR811 closeout evidence log, successor-handoff YAML freshness baseline, protected-change planner YAML anchor hardening, handoff-state preservation, and the explicit opt-in Tk window-smoke guard.
- PRs #718-#764 established and closed out the governed rule-registry direct-coverage baseline: mechanism inventory, migration map, validator, CLI command, workflow-guard integration, patch-preflight integration, deterministic metadata/conflict/completeness checks, direct test coverage for all active mechanisms, an empty direct-test follow-up plan, and explicit machine-readable plus human-readable completion reporting.
- Evidence: `docs/reports/terminal/pr737-rule-registry-release-evidence.log`, `docs/reports/terminal/pr739-rule-registry-source-evidence-validation.log`, `docs/reports/terminal/pr740-rule-registry-surfaces-tests-inventory.log`, `docs/reports/terminal/pr741-rule-registry-surfaces-tests-inventory-recovery.log`, `docs/reports/terminal/pr742-rule-registry-surfaces-tests-validation.log`, `docs/reports/terminal/pr761-chat-communication-direct-coverage.log`, `docs/reports/terminal/pr762-chat-bootstrap-drift-direct-coverage.log`, and `docs/reports/terminal/pr764-rule-registry-completion-reporting.log`.

## Current Repository State

Generated handoff safe state is main after PR834 freshness repair, with this closeout as administrative evidence on top. The governed rule registry is enforced through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight. It currently covers twelve active mechanisms with category, priority, enforcement_phase, owner, conflict_domains, surfaces, tests, coverage classification, migration-map completeness, and direct-test coverage for all active mechanisms: summary-renderer, execution-mode-switch, rule-preservation-guard, workflow-guard, patch-preflight, chat-communication-rules, chat-bootstrap-drift-rules, portable-execution-rules, evidence-guard, typed-work-order-runner, release-state-validation, and post-release-archive-check. `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json` now expose explicit direct-coverage completion state. Release/evidence-kernel hardening continues only in small slices. Broad documentation migration, release, tag, DOI mutation, and non-read-only GUI work remain blocked unless a new slice explicitly scopes them. GUI work remains deferred until handoff freshness is clean. The repository is the source of truth; chat memory is not a source of truth.

## A1 State Refresh Addendum

Protected Change Planner A1 is complete on remote main.

- Verified main HEAD: `c07f8ece568501771849bd922aefd1f8ed169ff6`.
- PR #791 is merged.
- `./ns protected-change-plan --diff-file <file>` routes to `agentic_project_kit.protected_change_planner`.
- Verification log: `docs/reports/terminal/protected-change-planner-a1-merge-verify.log`.
- Immediate next slice: fix expected-negative-smoke and final-summary ambiguity before product work.

## Current Goal

Continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears.

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

Continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears. Documentation-management rebuild work remains deferred.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through docs/STATUS.md, docs/handoff/CURRENT_HANDOFF.md, .agentic/handoff_state.yaml, docs/TEST_GATES.md, docs/DOCUMENTATION_COVERAGE.yaml, .agentic/project.yaml, sentinel.yaml, governance contracts, rule-registry files, and committed terminal evidence.

## Historical Compatibility Anchors

agentic-kit check-docs; agentic-kit doctor; Tkinter cockpit; v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; not the Tkinter cockpit release; PR #463: ActionResult core contract; PR #464: `cockpit run --json`; PR #465: Registry-only; PR #466: Queue-State contract; PR #467: Evidence-State contract; already executed command; dirty-state blocking; dirty worktrees; v0.3.31 Pre-GUI Execution Hardening Plan; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 Evidence Guard Usage; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; Local shortcut `./ns evidence-guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion.; Typed Work Orders Pre-GUI Execution Path; typed Patch DSL; structured State Source of Truth; Markdown is a projection; no_command; exactly_one_command; multiple_commands; already_executed; v0.3.32 Release Phase and Evidence Closeout; Current released version: 0.3.29; Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path; v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; no new large shell control blocks; Tkinter remains explicitly deferred; Do not start GUI implementation in this slice.; GUI expansion is intentionally paused; remote inspection evidence contract; Remote-log evidence is mandatory for standard-error hardening slices; Terminal acknowledgement audit; PR #650 merged; PR #651 merged; PR #652 merged.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml.
```

### `docs/handoff/START_NEW_CHAT_PROMPT.md`

```text
---
schema_version: 1
artifact_type: chat_switch_prompt
role: start_new_chat
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - evidence inspect
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Start New Chat Prompt

This file is the canonical prompt for starting a successor chat. It is paired with `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md` and `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`.

If this prompt changes, the closeout prompt and `NEXT_CHAT_BOOTSTRAP.md` may also need to be updated. A closeout slice must check all three files before a chat switch.

Current administrative handoff state after PR #880: main contains `f853ccf770e5f692ca2815912b252e453259fc69` (`f853ccf`), `Merge pull request #880 from vfi64/fix/handoff-freshness-admin-merge-chain`. PR #880 is administrative handoff-freshness hardening; verified release remains v0.4.4, Zenodo version DOI `10.5281/zenodo.20431326`. Successor chats must verify this state before GUI product work. The next safe product slice is GUI deterministic gatekeeper migration as read-only inspection/inventory only.

Historical administrative handoff state after PR #838: main contains `777d957474318fdf797ca23625e52046c3fb7df0` (`Refresh post-PR837 administrative handoff state (#838)`). The substantive safe-state may intentionally remain at the last substantive work commit when `safe_state.semantics: last_substantive_work_state` is set; later handoff-only refreshes belong in `administrative_evidence_state`.

## Post-Merge Handoff Refresh Status Gate

After every PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status before product work.

Interpretation is machine-derived:

- result=NOOP: continue without an administrative handoff refresh.
- result=REFRESH_REQUIRED: create an administrative handoff refresh slice before product work.

This is not a chat-judgement step. The kit decides whether a post-merge handoff refresh is required; d, f, and w remain communication signals only.

## Prompt to copy into the successor chat

```text
We work in repo vfi64/agentic-project-kit.

Do not start from chat memory. Source of truth is the remote repository: main, PRs, CI, tags, releases, issues, and repo artifacts.

First read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main completely and execute its boot routine.

Before any repository mutation, verify:

- current main HEAD
- open PRs and CI status
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/handoff/NEXT_CHAT_BOOTSTRAP.md
- .agentic/handoff_state.yaml
- .agentic/compiled_agent_context.yaml
- .agentic/rule_mechanism_inventory.yaml
- .agentic/rule_migrations.yaml
- .agentic/rule_preservation.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
- docs/planning/WORKFLOW_REDUCTION_FOCUS.md

Report briefly:

1. current main HEAD,
2. open PRs and CI status,
3. whether NEXT_CHAT_BOOTSTRAP.md is current enough,
4. whether STATUS, CURRENT_HANDOFF, and handoff_state are consistent,
5. last clean verified state,
6. next smallest safe slice.

Important:

- d, f, and w are communication signals, not evidence.
- After d, f, w, or any other short chat control signal, run `agentic-kit evidence inspect` locally or inspect equivalent committed remote/repo evidence before continuing.
- Do not ask for pasted terminal output before checking available repo or remote evidence.
- Do not mutate product state before full boot verification.
- Protected YAML, JSON, and Markdown control files require protected change planning.
- Evidence-bearing workflows must use the structured summary renderer or Python workflow summary runner.
- Before the next chat switch, run a closeout slice using docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md. That closeout may need to update this prompt, the closeout prompt, and docs/handoff/NEXT_CHAT_BOOTSTRAP.md.
```
```

### `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`

```text
---
schema_version: 1
artifact_type: chat_switch_prompt
role: closeout_before_chat_switch
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
paired_prompt: docs/handoff/START_NEW_CHAT_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - evidence inspect
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Closeout Before Chat Switch Prompt

This file is the canonical closeout prompt for the current chat before starting a successor chat. It is paired with `docs/handoff/START_NEW_CHAT_PROMPT.md` and `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`.

If this prompt changes, the start prompt and `NEXT_CHAT_BOOTSTRAP.md` may also need to be updated. A closeout slice must check all three files before a chat switch.

Current administrative handoff state after PR #880: main contains `f853ccf770e5f692ca2815912b252e453259fc69` (`f853ccf`), `Merge pull request #880 from vfi64/fix/handoff-freshness-admin-merge-chain`. PR #880 is administrative handoff-freshness hardening; verified release remains v0.4.4, Zenodo version DOI `10.5281/zenodo.20431326`. Successor chats must verify this state before GUI product work. The next safe product slice is GUI deterministic gatekeeper migration as read-only inspection/inventory only.

Historical administrative handoff state after PR #838: main contains `777d957474318fdf797ca23625e52046c3fb7df0` (`Refresh post-PR837 administrative handoff state (#838)`). The substantive safe-state may intentionally remain at the last substantive work commit when `safe_state.semantics: last_substantive_work_state` is set; later handoff-only refreshes belong in `administrative_evidence_state`.

## Post-Merge Handoff Refresh Status Gate

After every PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status before product work.

Interpretation is machine-derived:

- result=NOOP: continue without an administrative handoff refresh.
- result=REFRESH_REQUIRED: create an administrative handoff refresh slice before product work.

This is not a chat-judgement step. The kit decides whether a post-merge handoff refresh is required; d, f, and w remain communication signals only.

## Prompt to run before leaving the current chat

```text
Create a final follow-up / closeout slice for the next chat.

Goal: A successor chat must be able to reconstruct all current workflow rules, bootloader rules, open work, last verified state, and next safe slice from docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main.

Scope: no product work. This is a handoff/bootstrap closeout only.

Steps:

1. Inspect remote truth first:
   - main HEAD
   - open PRs
   - CI status
   - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
   - docs/handoff/START_NEW_CHAT_PROMPT.md
   - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
   - docs/STATUS.md
   - docs/handoff/CURRENT_HANDOFF.md
   - .agentic/handoff_state.yaml
   - .agentic/compiled_agent_context.yaml
   - Rule Registry files
   - relevant planning documents

2. Check whether NEXT_CHAT_BOOTSTRAP.md and both chat-switch prompt files include the current state:
   - last main HEAD or last verified state,
   - open PRs,
   - next work items,
   - known standard failures,
   - boot commands,
   - mandatory boot sources,
   - final-summary rules,
   - Rule Registry and document-management work,
   - GUI deferral,
   - no-op / PASS_ALREADY_DONE,
   - evidence inspect after d/f/w or any short chat control signal,
   - red CI failed-log diagnosis.

3. If any file is stale:
   - build a small PR that only updates bootstrap/handoff prompt state,
   - use agentic-kit boot write or write_next_chat_bootstrap() where applicable,
   - update docs/handoff/START_NEW_CHAT_PROMPT.md and docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md if their contracts or prompt wording changed,
   - run targeted tests for chat boot, evidence inspector, workflow summary runner, run summary renderer, and any affected handoff/governance tests,
   - wait for CI,
   - if CI is red, fetch failed job logs in the same diagnostic path,
   - merge only after green CI.

4. If all files are current:
   - state that explicitly with remote evidence,
   - name main HEAD,
   - name docs/handoff/NEXT_CHAT_BOOTSTRAP.md as the canonical successor-chat entry point.

5. Final answer must contain only:
   - Status: BOOTSTRAP_CURRENT or BOOTSTRAP_REFRESHED,
   - main HEAD,
   - open PRs,
   - last verified state,
   - next safe slice,
   - the short start prompt from docs/handoff/START_NEW_CHAT_PROMPT.md.

Do not start new product work in this closeout slice.
```
```

### `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`

```text
# Chat Bootstrap and Drift Contract

Status-date: 2026-05-24
Status: normative governance contract
Scope: mandatory startup sequence, drift classes, drift response, and successor-chat handoff behavior

## Purpose

This contract makes chat handoffs reproducible. A new chat must be able to continue without trusting previous-chat memory. It must fetch the current rules, detect contradictions, and stop before mutation when drift is present.

## Mandatory startup sequence

A successor chat must perform this sequence before proposing any mutation block:

1. Identify the repository and remote.
2. Read `.agentic/compiled_agent_context.yaml`.
3. Read every mandatory source named by the compiled context.
4. Read `docs/governance/FINAL_SUMMARY_CONTRACT.md`.
5. Read `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`.
6. Read `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`.
7. Read `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`.
8. Read `docs/TEST_GATES.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md`.
9. Inspect relevant source files and tests for the requested slice.
10. State any drift or uncertainty before acting.

A chat may summarize these sources compactly, but it must not replace the source-reading step with memory.

## Remote repository connector route

For remote-only work on GitHub repositories, use the GitHub connector direct-path-first workflow before falling back to search, guessed URLs, or local shell commands.

Required first route:

1. call `get_repo` for the exact `repository_full_name`;
2. call `fetch_file` for known paths instead of searching for them;
3. call `fetch_commit`, `get_pr_info`, `fetch_commit_workflow_runs`, or `compare_commits` for known commits, pull requests, runs, or branch comparisons;
4. use repository search only when the path or symbol is genuinely unknown;
5. fall back to raw URLs or local commands only after connector access is unavailable or insufficient.

This route is a token- and drift-control rule. Repeatedly trying raw URLs, branch guesses, or unrelated searches while a known connector path exists is drift.

## Drift classes

The system must treat the following as drift:

- compiled context names sources that are missing,
- human governance documents and compiled context disagree,
- final summary vocabulary differs between docs, renderer, and tests,
- `REMOTE_EVIDENCE` accepts forbidden final values such as `PENDING`, `NONE`, or `CHAT_ONLY`,
- `NO-COMMAND` is declared in docs but unsupported by the renderer or tests,
- status or handoff documents point to stale next steps,
- communication rules are absent from coverage or handoff,
- portable execution rules are absent from coverage or tests,
- a workflow claims no-copy completion without remote-readable evidence,
- a workflow asks for pasted output although usable local or remote evidence exists,
- shell-only snippets are presented as canonical cross-platform execution,
- local work starts while `main` is behind `origin/main`, the worktree is dirty, or the branch does not match the intended base,
- remote repository inspection ignores the GitHub connector direct-path-first workflow,
- governance YAML is mutated without a parse-modify-dump workflow and post-mutation parse validation.

## Drift response

On drift detection, the assistant or tool must:

1. warn that drift exists,
2. identify the source files involved,
3. avoid mutation-oriented work unless the mutation is the drift fix itself,
4. offer a comprehensive handoff prompt when chat length, ambiguity, or contradictory state makes continuation unsafe,
5. prefer a small deterministic fix slice over broad product work.

Drift must not be hidden behind a final PASS. If drift was found and not fixed, the final summary must report it honestly.

## Governance YAML mutation rule

Governance YAML includes `.agentic/handoff_state.yaml`, `.agentic/compiled_agent_context.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and `docs/DOCUMENTATION_REGISTRY.yaml`.

The only allowed mutation workflow for these files is parse-modify-dump:

1. parse the original YAML with `yaml.safe_load`;
2. mutate typed Python data structures;
3. write with `yaml.safe_dump` or an equivalent structured emitter;
4. parse the written file again;
5. run the relevant YAML integrity, coverage, and governance tests before claiming success.

Free-text insertion, regex insertion, manual indentation patches, and unparsed string concatenation are forbidden for governance YAML. Quoting a colon after the fact is not enough; the workflow must prevent malformed YAML from being created.

## Handoff prompt requirements

A drift handoff prompt must include:

- repository path and remote identity,
- current branch and commit if available,
- mandatory first-read source list,
- current summary contract vocabulary,
- communication rules including `d`, `f`, `w`, `paste-output`, and `stop`,
- portable execution rule,
- known drift findings,
- forbidden patterns,
- last safe state,
- next safe step,
- instruction not to mutate before reading the mandatory sources.

## Local repository freshness precondition

Before any local mutation, the operator must verify the local repository against the intended remote base. For work based on `main`, the local branch must be `main`, `origin/main` must be fetched, the local HEAD must match `origin/main`, and the worktree must be clean except for explicitly preserved local diagnostics.

If the local repository is behind, the workflow must update it before mutation. If local changes exist, they must be stashed, committed to an evidence branch, or explicitly stopped for review. Continuing product or governance mutation from a stale or contaminated local tree is drift.

## Machine-readable companion

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion for this contract. It must list the mandatory bootstrap sources and the drift reaction rules. Human documents remain authoritative, but the compiled context is the fastest startup map for LLMs.

## Deterministic check direction

`agentic-kit comm-rules-check` must become the deterministic check for this contract. It should fail closed when required anchors are missing or contradictory. Until that command exists, reviewers must inspect this document, the compiled context, the final summary contract, and renderer tests together.

## Optimization requirement

Do not solve drift by adding more overlapping prose to every document. Prefer one canonical document per concept, compact cross-references elsewhere, compiled machine-readable anchors, and tests that catch known regressions.

## Administrative Evidence State für Handoff-Prompts

Ein Handoff-Prompt unterscheidet zwischen `safe_state` und `administrative_evidence_state`. `safe_state` beschreibt den letzten fachlich/substanziellen Arbeitsstand. Reine Log-, Summary-, Handoff- oder Evidence-Commits nach diesem Stand dürfen als `administrative_evidence_state` geführt werden und machen den fachlichen Safe-State nicht automatisch stale.

Ein Nachfolge-Chat muss prüfen, ob spätere Commits nur administrative Evidence betreffen. Fachliche Änderungen nach dem Safe-State sind Drift und müssen vor Produktarbeit geklärt werden.

Dieses Modell verhindert die Endlosschleife, bei der ein finaler Log-Commit den gerade erzeugten Handoff-Prompt sofort wieder formal veralten lässt.
```

### `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`

```text
# Portable Chat Execution Contract

Status-date: 2026-05-24
Status: normative governance contract
Scope: operating-system-independent execution rules for chat-assisted workflows

## Purpose

The kit must work across macOS, Linux, and Windows assumptions. Canonical workflow correctness must not depend on POSIX-only shell utilities, a healthy inherited `PATH`, or long copy-pasted shell scripts.

The observed failure mode was simple and severe: a generated block could not find required tools. A governance system that cannot preserve evidence when the command environment is degraded is not robust enough for large-LLM operation.

## Canonical rule

Durable workflow behavior belongs in Python modules, tests, and CLI commands. Shell commands are adapters only (`shell commands are adapters only`).

Canonical implementation must prefer:

- `pathlib.Path` for paths,
- `shutil` for file operations and tool discovery,
- `platform` for platform inspection,
- `subprocess.run([...], shell=False)` when external commands are unavoidable,
- explicit return objects or structured text reports,
- direct log writing through Python file APIs,
- one summary renderer and one validation vocabulary.

Canonical implementation must not require:

- `cp`, `tail`, `grep`, `sed`, `head`, `tee`, `find`, or `sh`,
- hard-coded Unix paths such as `/usr/bin/git`, `/bin/cp`, or `/tmp` as normative rules,
- shell pipelines for correctness,
- shell-specific quoting behavior,
- shell activation of a virtual environment as the only path to execution.

## Bootstrap principle

The portable bootstrap path is a Python entry point, not a shell recovery script.

Required direction:

- `agentic-kit bootstrap-check` verifies Python, repo root, package importability, required governance files, summary renderer importability, and optional Git availability through portable Python APIs.
- `agentic-kit comm-rules-check` verifies communication, summary, bootstrap, and drift contracts.
- `agentic-kit handoff-prompt --reason drift` emits a successor-chat prompt when drift is detected.

`./ns` may expose shortcuts for local convenience, but it must not be the only canonical route.

## Local repository freshness rule

Local repository work must start from a verified fresh base. The workflow must fetch the remote, compare the intended local base with its upstream, and stop or synchronize before any mutation. A local branch that is behind `origin/main`, a dirty worktree, or untracked command artifacts are preflight findings, not details to ignore.

For local `main`-based work, the safe precondition is: `git fetch origin`, clean or preserved local changes, `git switch main`, local HEAD equal to `origin/main`, then feature branch creation. Mutation before that precondition is forbidden.

## Remote connector route rule

When a GitHub connector is available, remote repository inspection must start with the direct connector route: `get_repo` for repository identity, `fetch_file` for known file paths, `fetch_commit` for known commits, `get_pr_info` for known pull requests, `fetch_commit_workflow_runs` for CI evidence, and `compare_commits` for branch comparisons.

Search is for unknown paths or symbols. Raw URLs and local fallbacks come after connector access is unavailable or insufficient.

## Governance YAML mutation rule

Governance YAML mutation must use parse-modify-dump. Tools and command scripts must load YAML through a parser, mutate typed data, write it through a structured emitter, parse the result again, and then run YAML integrity tests.

Manual indentation patches, regex insertion into YAML lists, unparsed string concatenation, and late quote repair after a failed test are forbidden. A YAML parse error in CI is a workflow defect, not a harmless iteration.

## External command rule

When Python code must call an external command, it must use an argument list and `shell=False`. The code must capture stdout, stderr, return code, and command identity in a reportable structure. It must handle command-not-found as a normal diagnostic result, not as an unhandled crash.

## Evidence rule

Evidence generation must be possible without POSIX file-copy utilities. Python code must be able to create log directories, write logs, copy or move report files, and name local and remote evidence paths using portable path handling.

## Chat block rule

A chat-generated terminal block is allowed only as a bounded fallback or adapter. It must not be the authoritative expression of a reusable workflow. If a shell block is used because the portable runner is missing or broken, the summary must say so and must not claim the portable workflow is healthy.

## OS independence rule

Documentation and tests must not define macOS-only, Linux-only, or Windows-only paths as canonical. OS-specific examples may appear only when labeled as examples or local recovery snippets, not as normative kit behavior.

## Optimization requirement

Whenever a workflow is converted from shell to Python, the implementation must remove assumptions instead of merely translating shell commands. Prefer file parsing, imports, and deterministic checks over external process execution whenever possible.
```

### `.agentic/handoff_state.yaml`

```text
schema_version: 1
updated:
  date: '2026-05-29'
  reason: Refresh handoff state to last substantive work commit
  source: agentic-kit handoff refresh
repo:
  name: agentic-project-kit
  local_path: agentic-project-kit
  remote: github.com:vfi64/agentic-project-kit
  default_branch: main
safe_state:
  branch: main
  commit: e1cac6c
  commit_subject: Integrate GUI gatekeeper into Tkinter shell (#911)
  semantics: current_main_head
  working_tree_expected_clean: true
  administrative_refresh_prs:
  - 656
  - 657
  - 659
  - 660
  - 661
  - 663
  - 665
  - 666
  - 671
  - 672
  - 680
  - 681
  - 688
  - 689
  - 690
  - 691
  - 694
  - 702
  - 705
  - 707
  - 708
  - 710
  - 715
  - 716
  - 718
  - 719
  - 720
  - 721
  - 722
  - 723
  - 724
  - 725
  - 726
  - 727
  - 728
  - 729
  - 730
  - 731
  - 732
  - 733
  - 734
  - 735
  - 736
  - 737
  - 738
  - 739
  - 740
  - 741
  - 742
  - 761
  - 762
  - 763
  - 764
  - 766
  - 831
  - 833
  - 835
  - 836
  - 837
  - 838
  - 878
  - 879
  - 880
  - 881
  - 883
  - 886
  - 888
  - 892
  - 894
  - 897
release:
  current_version: 0.4.4
  previous_version: 0.4.3
  tag: v0.4.4
  github_release_exists: true
  zenodo_concept_doi: 10.5281/zenodo.20101359
  zenodo_version_doi: 10.5281/zenodo.20431326
  post_release_check: PASS
  post_release_evidence: docs/reports/terminal/v044-post-release-verify.log
open_items:
  prs: []
  next_expected_chat_action: Continue after PR892 with post-merge gate visibility
    follow-up work only after the post-merge refresh status gate reports NOOP.
completed_since_previous_handoff:
- 'PR #897 merged standard summary validator hardening before this administrative
  handoff refresh.'
- 'PR #894 merged post-merge gate bootstrap visibility documentation before this administrative
  handoff refresh.'
- 'PR #892 recorded the post-merge handoff refresh status gate visibility inventory
  so the workflow can move the gate into more visible kit/ns paths.'
- 'PR #888 added optional patch-preflight slice-gate enforcement so planning-document
  preflight can require deterministic slice readiness and a clean worktree.'
- 'PR #886 fixed workflow evidence hygiene by moving active next-turn/work-order results
  out of the repo-backed fixed slot until explicit upload/promotion.'
- 'PR #883 added the GUI gatekeeper implementation inventory and recorded that helper-local
  PASS is not slice PASS without matching repository governance gates.'
- 'PR #881 refreshed bootstrap/handoff state after PR #880; this post-PR881 refresh
  records the resulting custom-subject administrative merge commit as current main.'
- 'PR #880 accepted bounded administrative merge chains in the handoff freshness guard
  while preserving blocking behavior for product merges inside such chains.'
- 'PR #877 fixed the handoff freshness self-reference loop by checking freshly rendered
  prompt text before warning.'
- 'PR #876 recorded v0.4.4 DOI metadata and post-release evidence at docs/reports/terminal/v044-post-release-verify.log.'
- 'PR #875 prepared v0.4.4 release metadata, after which v0.4.4 was tagged and post-release
  verified with Zenodo version DOI 10.5281/zenodo.20431326.'
- 'PR #874 records the GUI deterministic gatekeeper migration plan in docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md
  as planning-only work.'
- 'PR #873 added the GUI work order upload strip and was verified by docs/reports/terminal/pr873-final-main-closeout.log.'
- 'PR #838 refreshed post-PR837 administrative handoff state and preserved the last
  substantive safe-state distinction.'
- 'PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.'
- 'PR #838 refreshed post-PR837 administrative handoff state and preserved the last
  substantive safe-state distinction.'
- 'PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.'
- 'PR #836 refreshed post-PR835 next-step state and is the current successor-handoff
  safe-state anchor.'
- 'PR #835 recorded PR #834 closeout evidence at docs/reports/terminal/pr834-merge-finalize.log
  and added docs/reports/terminal/post-pr834-successor-handoff.md as the successor
  anchor.'
- 'PR #834 repaired generator-backed handoff freshness state so the generated successor
  prompt anchors to the post-PR834 safe state.'
- 'PR #833 recorded the corrected post-PR831 successor handoff at docs/reports/terminal/post-pr831-successor-handoff.md
  and superseded the rejected PR825-era stale generated prompt.'
- 'PR #831 recorded PR #830 closeout evidence at docs/reports/terminal/pr830-merge-finalize.log
  and verified main 011b6dc24829be44c7693c468a90694981cd40ce for the successor handoff
  anchor.'
- 'PR #825 hardened active handoff freshness checks: state-freshness-check now fails
  active next-step instructions that point to already-recorded closeout evidence or
  stale release versions.'
- 'PR #824 recorded PR #823 closeout evidence at docs/reports/terminal/pr823-merge-finalize.log
  and refreshed STATUS, CURRENT_HANDOFF, and persistent handoff state.'
- 'PR #823 hardened merge-if-green head/base pinning: the command validates the target
  base branch, requires a PR head SHA, passes --match-head-commit to GitHub, and renders
  checked base/head refs in the command output.'
- 'PR #821 hardened merge-if-green postconditions: after a successful merge, the command
  verifies the merge commit on main, waits for main CI, and fails the command result
  unless main CI is green.'
- 'PR #819 hardened next-turn PR status failed-log diagnostics: red CI now exposes
  failed check names, GitHub Actions run ids, exact gh run view --log-failed commands,
  bounded log-fetch status, and no-checks classification for empty rollups.'
- 'PR #817 hardened PASS_ALREADY_DONE target-state classification: generic already-exists
  output is no longer sufficient success evidence; target-specific classes and hard-failure
  precedence are test-backed.'
- 'PR #815 hardened release-prep atomicity and remote release readiness: release-prep
  stops before metadata patching on main/branch failures; release-check and release-preflight
  block release readiness on remote WARN; release-publish blocks inconclusive remote
  lookups before tagging.'
- 'PR #813 published v0.4.3 and post-release verification found Zenodo version DOI
  10.5281/zenodo.20393329; evidence: docs/reports/terminal/20260526-120216_v043-release-verify.log.'
- 'PR #791 merged Protected Change Planner A1 and verified it via docs/reports/terminal/protected-change-planner-a1-merge-verify.log.'
- 'PR #763 refreshed status and handoff after the PR762 direct-coverage closeout.'
- 'PR #764 added explicit rule-registry direct coverage completion reporting for JSON
  and human CLI reports.'
- 'PR #766 recorded the accepted rule-registry improvement backlog before the v0.4.2
  safety release.'
current_capabilities:
  ns_actions:
  - agent-next
  - agent-run
  - command-inbox-check
  - state-freshness-check
  - terminal-remote-preflight
  - terminal-finalize
  - handoff-show
  - handoff-check
  - governance-check
  - rule-registry check
  - rule-registry report
  - patch-preflight
  - dev
  artifact_dirs:
    terminal_logs: docs/reports/terminal
    command_runs: docs/reports/command_runs
  rule_preservation:
    registry: .agentic/rule_preservation.yaml
    guard: src/agentic_project_kit/rule_preservation.py
    workflow_guard_pattern: rule-preservation-drift
    status: baseline-active
  documentation_registry:
    registry: docs/DOCUMENTATION_REGISTRY.yaml
    contract: docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md
    cli_summary: agentic-kit docs-registry
    cli_report: agentic-kit docs-registry --report PATH
    artifact_policy_source: .agentic/communication_artifacts.yaml
    broad_migration_allowed: false
  governed_rule_registry:
    mechanism_inventory: .agentic/rule_mechanism_inventory.yaml
    migration_map: .agentic/rule_migrations.yaml
    test_coverage: .agentic/rule_test_coverage.yaml
    direct_test_plan: .agentic/rule_direct_test_plan.yaml
    validator: src/agentic_project_kit/rule_registry_validator.py
    cli: agentic-kit rule-registry check
    report_cli: agentic-kit rule-registry report
    report_completion_field: summary.direct_coverage_complete
    workflow_guard_pattern: rule-registry-drift
    patch_preflight: true
    status: completion-reporting-closed
    mechanisms:
    - summary-renderer
    - execution-mode-switch
    - rule-preservation-guard
    - workflow-guard
    - patch-preflight
    - chat-communication-rules
    - chat-bootstrap-drift-rules
    - portable-execution-rules
    - evidence-guard
    - typed-work-order-runner
    - release-state-validation
    - post-release-archive-check
    required_fields:
    - category
    - priority
    - enforcement_phase
    - owner
    - conflict_domains
    - surfaces
    - tests
    compatibility_checks:
    - category/enforcement_phase matrix
    - ambiguous category/priority/enforcement_phase rejection
    completeness_checks:
    - known_legacy_rule_ids index
    - migration entry for every known legacy rule
    - every migration entry indexed
    - migrated/archived/rejected disposition statuses
    coverage_checks:
    - test coverage classification for every active mechanism
    - direct-test path validation
    - empty direct-test follow-up plan after PR762
    reporting_checks:
    - explicit JSON direct_coverage_complete field after PR764
    - explicit human completion_status line after PR764
  workflow_hardening:
    remote_route_rule: GitHub connector direct-path-first for known paths, refs, PRs,
      and commits.
    yaml_mutation_rule: Use structured YAML mutation and parse validation.
    control_file_preservation: .agentic/control_file_preservation.yaml protects active
      rules from lossy shortening.
  gui_mvp:
    status: closed_out_on_main
    verified_read_only_actions:
    - cockpit-readiness
    - doctor
    - check-docs
    disabled_actions:
    - agent-run
    - remote_mutation
    - destructive_actions
policies:
  no_copy_terminal_policy: .agentic/no_copy_terminal_policy.yaml
  control_file_preservation: .agentic/control_file_preservation.yaml
rules:
- id: remote-first-no-guess
  status: active
  text: Do not guess repository state, command syntax, file locations, release phase,
    GitHub JSON fields, or available evidence. Inspect the remote repository, command
    help, known paths, PRs, commits, logs, and authoritative repo files before acting.
- id: quality-first-no-shortcuts
  status: active
  text: Prefer deterministic, test-backed, maintainable fixes over quick patches.
    No shortcuts, workaround-only fixes, or chat-only promises for recurring workflow
    defects.
- id: patch-artifact-preflight-before-application
  status: active
  text: Before applying generated patch artifacts, run patch-artifact preflight diagnostics
    and fail on unsafe quoting, ambiguous YAML terms, or control-file weakening.
- id: generated-code-syntax-first
  status: active
  text: Generated shell and Python artifacts must be syntax-checked before execution
    or commit; generated code cannot be trusted because it looks plausible.
- id: coverage-yaml-terms-must-be-strings
  status: active
  text: Coverage YAML required terms must stay strings; colon-containing terms must
    be quoted or written through structured YAML writers.
- id: final-summary-self-validation
  status: active
  text: Final summaries must be self-validated against preceding output before treating
    a block as successful.
- id: no-copy-terminal-evidence
  status: active
  text: Routine PASS and normal FAIL handoffs must be backed by repo evidence; use
    d for log-backed PASS and f for log-backed FAIL. Manual terminal paste is only
    for hard failure, broken logging, unavailable evidence, unusable evidence, or
    explicit user request.
- id: remote-log-lookup-first
  status: active
  text: Remote evidence must be inspected first for FAIL or uncertain handoffs; direct-fetch
    docs/reports/terminal logs before asking for paste-output unless logging is broken
    or unavailable. The phrase remote evidence is intentionally preserved for rule-preservation
    coverage.
- id: rules-must-be-test-backed
  status: active
  text: Durable workflow rules need a stable repository home, documentation, and deterministic
    tests or guards that fail when the rule disappears or is weakened.
- id: yaml-structured-mutation-only
  status: active
  text: YAML governance files must be changed through parse-modify-dump or equivalent
    structured mutation, then parsed again before gates.
- id: github-connector-direct-path-first
  status: active
  text: For remote GitHub work with known paths, refs, or commits, use direct fetch,
    update, and PR APIs before search.
- id: control-file-preservation
  status: active
  text: Protected control files must preserve active rules and required anchors. Information
    preservation outranks compactness; hard length-limit trimming is forbidden.
- id: structured-summary-must-be-enforced
  status: active
  text: Relevant local or remote work blocks must end with the canonical structured
    SUMMARY from FINAL_SUMMARY_CONTRACT.md. Missing, malformed, contradictory, or
    legacy summaries are workflow drift.
- id: governed-rule-registry-before-documentation-rebuild
  status: active
  text: A governed modular rule registry must become the canonical source of truth
    before documentation-management rebuild work resumes.
recent_failure_patterns:
- id: guessing-before-inspection
  prevention: Before choosing commands, paths, JSON fields, release checks, or DOI
    sources, inspect the remote repository and command help. Treat memory and chat
    summaries as hypotheses until verified.
- id: interpreter-discovery-before-python
  prevention: Discover the active interpreter and project environment before invoking
    python, python3, pytest, ruff, or agentic-kit; prefer .venv/bin/python when the
    project venv exists; avoid naked python; when wrapping shell commands, avoid assuming
    set -e behavior unless explicitly set and logged.
- id: global-cli-or-venv-assumption
  prevention: Do not assume global CLIs or an existing venv; use project-local discovery
    and documented bootstrap paths.
- id: nested-triple-quote-code-generator
  prevention: Avoid nested quote-based code generation, nested shell/Python quote
    layers, nested triple-quoted string literals, and nested triple quotes in generated
    patch scripts; prefer line-list generation, existing helper scripts, simple file
    writes, or structured update APIs.
- id: yaml-colon-term-reinterpreted-as-mapping
  prevention: Quote colon-containing YAML terms or use structured YAML writers so
    plain scalars are not reinterpreted as mappings.
- id: standard-error-guards
  prevention: Recurring workflow errors must become deterministic guards, tests, or
    documented failure patterns.
- id: interactive-terminal-exit
  prevention: Chat-pasted terminal blocks must not end by closing the user terminal;
    avoid top-level exit and exec unless explicitly requested.
- id: stale-successor-handoff-prompt-after-main-merge
  prevention: Refresh STATUS, handoff_state, CURRENT_HANDOFF, and successor prompt
    before treating handoff prose as authoritative.
- id: repeated-yaml-governance-file-corruption
  prevention: Parse YAML before and after mutation and use a structured writer.
- id: final-pass-after-inner-fail
  prevention: Final summaries must distinguish work result from evidence result; evidence
    upload must not relabel failed work as PASS.
- id: lossy-control-file-shortening
  prevention: Do not shorten protected control files by deleting active rules; use
    successors, generated projections, or split/reference patterns.
- id: structured-summary-drift
  prevention: Verify canonical SUMMARY fields and consistency across WORK, EVIDENCE,
    OVERALL, REMOTE_EVIDENCE, terminal_log, command_report, CHAT_REPLY, and RESULT
    marker.
next_allowed_tasks:
- id: tkinter-workbench-gui-slice-1
  title: Continue with the smallest Tkinter workbench GUI slice from docs/planning/TKINTER_WORKBENCH_GUI_PLAN.md
    after PR834 closeout evidence is inspected.
  priority: 1
- id: failure-mode-review-automation-slice-1
  title: Continue with the smallest failure-mode review automation slice from docs/planning/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md
    after PR834 closeout evidence is inspected.
  priority: 2
- id: release-evidence-kernel-hardening-follow-up
  title: Use only a small release/evidence-kernel hardening follow-up if freshness
    or evidence drift reappears.
  priority: 3
blocked_until_closeout:
- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap
- Broad documentation migration during release/evidence-kernel hardening closeouts
- Release, tag, or DOI mutation
- GUI product work before post-PR880 bootstrap refresh is merged and verified
- Broad GUI implementation before the deterministic gatekeeper read-only inspection
  slice
- Gatekeeper product work before post-PR883 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS before repository governance gates pass
- Gatekeeper product work before post-PR886 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without slice-gate evidence
- Gatekeeper product work before post-PR888 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without patch-preflight slice-gate evidence
first_instruction: Start the next chat from the fresh post-PR911 successor handoff
  prompt and obey agentic-kit handoff post-merge-refresh-status before product work.
handoff_maintenance:
  principle: curated-not-accumulated
  update_required_at_chat_end: true
  no_redundant_rules: true
  no_contradictory_rules: true
  remove_obsolete_rules_when_system_changes: true
  latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr911.md
# preservation-anchor: use d for log-backed PASS and f for log-backed FAIL
# preservation-anchor: nested shell/Python quote layers
```

### `.agentic/compiled_agent_context.yaml`

```text
schema_version: 1
updated:
  date: '2026-05-24'
  reason: remote connector route, YAML mutation workflow, and control file preservation hardening
purpose: Fast, redundant-free, machine-readable companion to the human governance docs.
source_policy:
  remote_first_no_guess: true
  human_docs_remain_authoritative: true
  compiled_yaml_must_match_docs: true
  new_rules_need_docs_yaml_tests: true
  local_repo_freshness_before_local_work: true
  github_connector_direct_path_first: true
  yaml_governance_mutation_requires_parse_modify_dump: true
  control_file_preservation_required: true
priority_order:
- .agentic/compiled_agent_context.yaml
- .agentic/control_file_preservation.yaml
- .agentic/handoff_state.yaml
- .agentic/no_copy_terminal_policy.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md
- docs/DOCUMENTATION_REGISTRY.yaml
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/TEST_GATES.md
- docs/DOCUMENTATION_COVERAGE.yaml
mandatory_successor_chat_sources:
- .agentic/compiled_agent_context.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/TEST_GATES.md
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- .agentic/handoff_state.yaml
- AGENTS.md
- CHANGELOG.md
- README.md
- CITATION.cff
- docs/releases/VERIFIED_RELEASES.md
- relevant source files and tests for the requested slice
stable_test_anchors:
- "direct-fetch that path before relying on search results"
- "do not use interactive read prompts or shell-backslash summary invocations"
- "GitHub connector direct-path-first workflow"
- "parse-modify-dump is the only allowed governance YAML mutation workflow"
- "Information preservation outranks compactness"
hard_rules:
- id: remote-first-no-guess
  rule: Inspect remote repo files, authoritative docs, and command help before acting.
- id: no-long-manual-command-blocks
  rule: Queue repo-backed commands or use portable Python core commands instead of returning long local shell blocks.
- id: final-summary-contract
  summary: Preserve the framed SUMMARY contract in every final block.
  rule: Use the mandatory SUMMARY block and never relabel inner failures as PASS.
- id: chat-communication-contract
  rule: Interpret d/f/w/paste-output/stop as communication signals only; verify outcomes from evidence before continuing.
- id: portable-chat-execution-contract
  rule: Canonical workflow correctness must be Python-core-first and operating-system independent; shell is an adapter only.
- id: chat-bootstrap-and-drift-contract
  rule: Successor chats must read mandatory sources first, detect drift, warn, and avoid mutation except for drift fixes.
- id: successor-handoff-freshness-guard
  rule: Before presenting a successor handoff prompt as authoritative, run the freshness guard against STATUS, handoff_state, CURRENT_HANDOFF, and the latest successor prompt.
- id: documentation-registry-first-slice
  summary: Classify documentation and artifacts through an additive, reversible registry before broad migration.
  rule: Documentation registry changes must keep the first slice structural, test-backed, and non-destructive; broad migration, deletion, or taxonomy-driven rewrites require later explicit slices.
- id: patch-artifact-preflight
  rule: Generated patch artifacts must pass syntax, YAML, coverage-term, and final-summary checks before use.
- id: rules-must-be-test-backed
  rule: Durable rules require human docs, compiled YAML, and deterministic tests or a documented review-only exception.
- id: remote-log-direct-path-first
  rule: If a concrete docs/reports/terminal log path is known, direct-fetch that path before relying on search results or declaring evidence missing.
- id: github-connector-direct-path-first
  rule: For remote repo work, first use the installed GitHub connector with repository_full_name and fetch_file/fetch_commit/get_pr_info/fetch_commit_workflow_runs/compare_commits before trying raw URLs, search, or local shell fallbacks.
- id: yaml-governance-parse-modify-dump-only
  rule: parse-modify-dump is the only allowed governance YAML mutation workflow; never patch YAML with free-text injection, regex insertion, or unparsed string concatenation.
- id: control-file-preservation
  summary: Preserve critical control-file information; compactness must not delete active rules.
  rule: Critical control files must be additive or use explicit migration records with successor anchors, rationale, and deterministic tests. Hard length-limit trimming is forbidden; if files grow too large, split, reference, or generate them.
- id: gui-visual-two-phase-evidence
  rule: GUI visual checks must separate manual window launch from non-interactive PASS/FAIL evidence recording; do not use interactive read prompts or shell-backslash summary invocations.
- id: local-main-freshness-before-local-work
  rule: Before local repository mutation, fetch the remote, verify the intended local base equals its remote upstream, preserve or stop on dirty state, and only then create the feature branch.
final_summary_contract:
  work_values:
  - PASS
  - FAIL
  - PENDING
  - HARD-FAIL
  - NO-COMMAND
  evidence_values:
  - PASS
  - FAIL
  - PARTIAL
  - CHAT_ONLY
  - NOT_REQUIRED
  overall_values:
  - PASS
  - FAIL
  - PENDING
  - HARD-FAIL
  - NO-COMMAND
  remote_evidence_values:
  - PASS
  - FAIL
  - PARTIAL
  - NOT_REQUIRED
  forbidden_remote_evidence_values:
  - PENDING
  - NONE
  - CHAT_ONLY
communication_rules:
  d: local block appears finished; inspect evidence before treating as success
  f: failure reported; inspect or upload evidence before asking for pasted output
  w: continue within current governance and evidence rules
  paste-output: manual paste only when repo-backed or local evidence is unavailable or unusable
  stop: no further mutation or terminal instructions
portable_execution_rules:
  canonical_core: Python modules and CLI commands
  shell_role: adapter only
  python_apis:
  - pathlib.Path
  - shutil
  - platform
  - subprocess.run with shell=False
  forbidden_canonical_dependencies:
  - cp
  - tail
  - grep
  - sed
  - head
  - tee
  - find
  - sh
  - hard-coded Unix tool paths
  - shell pipelines for correctness
drift_detection:
  fail_closed: true
  on_drift:
  - warn
  - identify affected sources
  - avoid mutation unless fixing drift
  - offer comprehensive handoff prompt when continuation is unsafe
  drift_classes:
  - contract-vs-renderer value drift
  - contract-vs-test drift
  - missing mandatory bootstrap source
  - stale status or handoff state
  - stale successor handoff prompt after newer main merge
  - forbidden final summary value
  - no-copy claim without remote-readable evidence
  - shell-only canonical workflow example
  - local work starts from stale or dirty repository state
  - remote work ignores the GitHub connector direct-path-first workflow
  - governance YAML is mutated without parse-modify-dump validation
  - protected control file loses an active rule without an explicit successor migration
normal_operator_path:
- use GitHub connector direct-path-first workflow for remote repo inspection
- verify local repository freshness before local mutation
- read mandatory successor chat sources
- inspect current remote state
- run handoff prompt freshness guard before presenting a successor prompt
- run or inspect deterministic checks
- mutate governance YAML only through parse-modify-dump helpers and validate parseability afterward
- preserve protected control-file anchors or record explicit successor migrations
- use portable Python core where available
- render final summary through canonical renderer
quality_goal: Prefer deterministic, portable, test-backed solutions over prompt-only conventions.
workflow_friction_rules:
- id: no-remote-command-deadlock
  priority: high
  rule: Remote command first is preferred, but NO-COMMAND must trigger queuing a complete command pair or exactly one minimal fallback command. Do not loop on ask-agent-to-queue-command.
- id: final-summary-no-executable-placeholders
  summary: Executable terminal blocks must print only concrete final SUMMARY outcomes; never placeholder alternatives like PASS|FAIL or p|paste-output.
```
