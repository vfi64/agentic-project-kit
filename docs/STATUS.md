Current version: 0.3.35

# Project Status

Status-date: 2026-05-19
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Its core purpose is to move durable project memory out of chat transcripts and into versioned repository files, deterministic gates, evidence logs, and explicit handoff state.

The project treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, rules, and release metadata. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current Goal

The immediate goal after v0.3.29 is to close out v0.3.30 GUI readiness hardening. This is not a Tkinter implementation slice. The release line hardens the machine-readable contracts a later thin Tkinter cockpit will consume: action results, cockpit JSON output, registry-only action selection, command queue state, and evidence state.

## Current State

## v0.3.34 Portable Core Hardening Plan

v0.3.34 is planned as the final pre-GUI portable-core hardening line before starting the thin Tkinter cockpit implementation.

Goal: move the remaining risky release, DOI, evidence, PR-closeout, and typed-work-order control logic out of large shell blocks and into tested Python core functions that can be called by CLI, `./ns`, typed work orders, and the later Tkinter cockpit.

Required v0.3.34 scope:

- Expand systematic unit and contract tests for typed work orders, including valid work orders, missing fields, invalid types, unknown actions, queue cardinality, already-executed guards, evidence requirements, and negative runtime validation.
- Encapsulate release-phase semantics in Python core APIs: before-metadata `release-preflight`, after-metadata `release-check`, after-publication `post-release-check`, and DOI metadata recording.
- Prevent the Zenodo concept DOI from being accepted as a version-specific DOI when `post-release-check` reports WAITING.
- Reduce `./ns` and shell scripts to thin delegation layers for standard workflows; no new large shell control blocks for release, DOI, evidence, or PR-closeout logic.
- Provide machine-readable results or stable action result objects for GUI-relevant actions.
- Keep README release history extracted into `docs/releases/VERIFIED_RELEASES.md` and avoid reintroducing README length pressure.
- Preserve evidence-log consistency guards, including expected in-progress log handling and final-result contradiction checks.

Tkinter remains explicitly deferred until this portable-core hardening baseline is released and post-release verified.

Acceptance criteria for starting the Tkinter cockpit after v0.3.34:

- Typed work order core behavior is covered by systematic unit tests, not only dogfooding logs.
- Release and DOI workflows expose Python-callable, tested actions with clear phase boundaries.
- The concept DOI versus version DOI WAITING case is guarded.
- GUI-facing actions can be invoked without composing fragile multi-step shell scripts.


Current released version: 0.3.32
Previous release compatibility literal for planning-state freshness coverage: Current released version: 0.3.29
Current release tag: v0.3.32
Zenodo concept DOI: `10.5281/zenodo.20101359`
Verified Zenodo version DOI: `10.5281/zenodo.20314341`
Post-release evidence: `docs/reports/terminal/20260520-v0.3.30-post-release-doi.log`

v0.3.30 is the current released and post-release verified line; GitHub Release and Zenodo version DOI verification are complete after post-release closeout. It includes the patch-artifact preflight MVP and the hardened planning-state/no-copy evidence workflow.

The active bridge toward the local GUI is no-copy/evidence governance and communication artifact GC hardening, not hidden automation. Normal PASS/FAIL handoff should rely on committed and pushed reports. Manual paste-output is reserved for hard failures such as authentication problems, network failures, terminal crashes, missing remote evidence, or workflow-level ambiguity.

Communication artifact GC hardening is now part of the pre-GUI baseline: symlinked transient artifacts are rejected, repo evidence and command inbox files are protected, and local /tmp/agentic-project-kit-*.log cleanup is TTL-based and dry-run-first via ./ns artifact-gc --tmp-logs.

## v0.3.32 Release Phase and Evidence Closeout

v0.3.32 is the release-phase-semantics and evidence-closeout hardening line. It does not ship the Tkinter GUI.

Completed v0.3.32 capabilities:

- `release-preflight` validates the before-metadata release phase without requiring target version markers in project files.
- `release-check` remains the after-metadata gate.
- `post-release-check` remains the after-release GitHub and Zenodo verification gate.
- `evidence clean-check` and `./ns evidence-clean-check` allow exactly one expected in-progress terminal log while rejecting every other dirty path.
- Merge verification logs for both v0.3.32 slices are remote evidence under `docs/reports/terminal/`.

Release readiness: v0.3.32 is ready for release metadata preparation after the final local gate and release preflight pass.

## Active Workflow Rules

- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, and documentation.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml` mutually consistent.
- Use project-local interpreter/tooling first. Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv` exist.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or branch-switching/sync workflows that must start from a clean tree.
- Use `./ns terminal-finalize` or command-run reports so PASS and FAIL evidence is remote-readable whenever technically possible.
- Larger terminal workflows must begin with three separator lines and end with `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###`.
- Avoid heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, and shell constructs likely to leave `quote>`, `dquote>`, or `heredoc>` prompts.

## Gate Status

The current required gate set for this planning refresh is:

- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns dev`
- `agentic-kit check-docs` / project-local module equivalent
- `agentic-kit doctor` / project-local module equivalent

## Next Safe Step

Finish v0.3.30 by documenting and gating the GUI readiness hardening baseline, then prepare the v0.3.30 release. Do not start Tkinter in this release line. The first thin Tkinter cockpit belongs after the v0.3.30 contracts are released and verified.

Do not expand Pattern Advisor, release automation, or hidden command selection before the GUI foundation and planning freshness guards are stable.

## Documentation Coverage Notes

`docs/DOCUMENTATION_COVERAGE.yaml` is the documentation coverage source for required terms and state-doc coverage. `agentic-kit check-docs` and `agentic-kit doctor` enforce this coverage through deterministic gates.

Planning-state freshness is now part of the governance contract: current-state documents must not contain stale released-version claims, obsolete next-step instructions, or contradictory active baselines.

## v0.3.31 Pre-GUI Execution Hardening Contract

- v0.3.31 starts with the pre-GUI execution hardening contract.
- The contract is documented in `docs/workflow/PRE_GUI_EXECUTION_HARDENING.md`.
- The first hardened invariants are: no false PASS after failed gate, clean base before log creation, no nested quote patch generator, evidence finalization, and a strict GUI boundary.

## v0.3.31 Pre-GUI Execution Hardening Closeout

v0.3.31 is the current pre-GUI execution hardening line. It does not ship the Tkinter GUI.

Completed v0.3.31 capabilities:

- Pre-GUI Execution Hardening Contract.
- Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.
- Local shortcut `./ns evidence-guard LOGFILE`.
- Expected negative-smoke evidence handling.
- Typed Work Order Evidence Contract.
- Typed Work Order Evidence Runtime Check.

Release readiness: v0.3.31 is ready for release metadata preparation after the final local gate and release preflight pass.

Tkinter remains explicitly deferred until the pre-GUI typed Work Order and evidence contracts are release-stable.

## v0.3.31 Evidence Guard Usage

- `agentic-kit evidence guard LOGFILE` validates terminal evidence logs for contradictory final state.
- `./ns evidence-guard LOGFILE` is the preferred local shortcut before using terminal evidence in closeout work.
- The guard rejects genuine final-PASS-after-failure logs while allowing explicitly expected negative-smoke checks.

## Live Status Commands

Run these from the repository root with project-local tooling:

```bash
git status --short
git branch --show-current
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns dev
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli check-docs
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli doctor
```

The equivalent public command names remain `agentic-kit check-docs`, `agentic-kit doctor`, and `agentic-kit post-release-check`; the project-local module form is preferred when global executables are not guaranteed.

## Compatibility Notes For Existing Coverage

Pattern Advisor remains a read-only catalog. Its current public surface is still `patterns list` and `patterns show`; it is advisory-only and must remain separate from deterministic gates.

The exact phrase policy-pack doctor checks is intentionally present here: policy-pack doctor checks remain active through `agentic-kit doctor`; active policy packs are part of the project contract and must remain visible in current-state documentation.

Release verification remains covered by the post-release Zenodo path and `agentic-kit post-release-check`. Current no-copy/evidence status is the bridge toward the thin local Tkinter cockpit.

## Mandatory Final Summary Contract

The no-copy/evidence workflow now requires a mandatory final SUMMARY block for relevant terminal work. `WORK RESULT`, `EVIDENCE RESULT`, `OVERALL RESULT`, `REMOTE_EVIDENCE`, `terminal_log`, `command_report`, and `NEXT_CHAT_REPLY` must be reported separately. A final PASS requires work success and evidence success; a pushed log can prove a failure without turning that failure into success.

## Quality-First Workflow Lessons

The project now treats repeated assistant/workflow mistakes as product defects. The target is not to get a block through quickly; the target is the best deterministic solution for the recurring problem.

Current lessons: avoid nested triple-quote code generators, quote YAML coverage terms containing colons, compile generated Python before relying on gates, validate final SUMMARY blocks before asking for `p`, and never allow a later evidence push to convert failed work into PASS.

## YAML Governance Integrity Lesson

YAML governance files have been damaged more than once by text-style patching. The project now treats this as a recurring workflow defect. `.agentic/handoff_state.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and similar control files must be mutated through parse-modify-dump or an equivalent structured path, then parsed again before gates.


## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified. This remote-first no-guess rule is mandatory for release, DOI, PR, evidence, and governance work.

## Compiled Agent Context YAML

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.

## No remote-command deadlock

Rule id: no-remote-command-deadlock

Remote command first is a delivery preference, not a blocking rule. If `./ns agent-next` reports `NO-COMMAND`, the next assistant response must either queue a complete command pair remotely or give exactly one minimal fallback command. The user must not be kept in an `ask-agent-to-queue-command` loop. Long ad-hoc terminal blocks are only allowed when the remote command path is unavailable or broken.

- Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and final result marker.

## No executable placeholder summaries

Executable terminal blocks must never print final SUMMARY fields with placeholder alternatives such as `PASS|FAIL`, `p|paste-output`, or ellipsis markers. A copied block must end with one concrete outcome only. Placeholder examples are allowed only in prose documents when clearly marked as non-executable examples.

## v0.3.30 GUI Readiness Hardening Closeout

v0.3.30 is the GUI readiness contract release, not the Tkinter GUI release.

Completed contract slices:

- PR #463: ActionResult core contract exposes PASS, FAIL, PENDING, HARD-FAIL, terminal_log, command_report, dirty_state, safety_class, and next_allowed_actions.
- PR #464: `cockpit run --json` exposes machine-readable action results for read-only and blocked bounded actions.
- PR #465: Cockpit Registry is the only allowed action source and validates action ids, safety classes, commands, labels, categories, and descriptions.
- PR #466: Queue-State contract covers NO_COMMAND, EXACTLY_ONE_COMMAND, MULTIPLE_COMMANDS, ALREADY_EXECUTED_COMMAND, DIRTY_INBOX, MISSING_COMMAND_METADATA, and INCOMPLETE_COMMAND.
- PR #467: Evidence-State contract covers REMOTE_EVIDENCE_PRESENT, LOCAL_TMP_ONLY, MISSING_EVIDENCE, STALE_LATEST_POINTER, and command_report_available.

The release closeout criterion is a clean full gate plus release metadata for v0.3.30. Tkinter remains explicitly deferred until after this contract baseline is released.

## v0.3.30 GUI Readiness Hardening Plan

The v0.3.29 review confirms that GC hardening and release hygiene were the right pre-GUI baseline. The useful planning takeaway is not to start Tkinter immediately, but to make the GUI-consumable contracts deterministic first.

Required v0.3.30 scope:

- Action Registry is the single source of allowed GUI actions.
- Action results expose PASS, FAIL, PENDING, HARD-FAIL, terminal_log, command_report, dirty_state, safety_class, and next_allowed_actions in a machine-readable form.
- Queue contracts cover no command, exactly one command, multiple commands, already executed command, dirty inbox, missing command metadata, and failed postconditions.
- Evidence contracts distinguish remote evidence present, local tmp evidence only, missing evidence, stale latest pointer, and command report availability.
- Shell shortcuts remain adapters; durable behavior belongs in tested Python cores.
- Tkinter is explicitly deferred until these contracts pass gates.


## Typed Work Orders Pre-GUI Execution Path

Typed Work Orders are now the preferred pre-GUI execution path for standard safe workflow actions. The current implementation covers:

- PR #472: minimal typed Work Order Runner core.
- PR #473: CLI entrypoint for typed Work Order execution.
- PR #474: repo-owned read-only typed Work Order example and `./ns typed-run` shortcut.
- PR #475: typed queue status contract for `no_command`, `exactly_one_command`, and `multiple_commands`.
- PR #476: `typed-next` queue execution for exactly one queued YAML Work Order.
- PR #477: `typed-next` already-executed guard with `queue_status=already_executed` and no duplicate execution.

Operational rule: for repeatable safe work, prefer repo-owned typed Work Orders over long chat-generated shell or Python patch blocks. Shell shortcuts such as `./ns typed-run`, `./ns typed-queue-status`, and `./ns typed-next` are adapters only; durable behavior belongs in the tested Python runner and queue contracts.

Current typed queue semantics for GUI readiness:

- `no_command`: block with PENDING and exit code 2.
- `multiple_commands`: block ambiguous execution with FAIL and exit code 2.
- `exactly_one_command`: execute through the typed runner.
- `already_executed`: block duplicate execution with PENDING and exit code 2 while preserving both queued and executed YAML files.

The thin Tkinter cockpit must consume these typed contracts instead of inventing hidden command planning or ad-hoc shell execution.

## v0.3.31 Pre-GUI Execution Hardening Plan

The GUI expansion is intentionally paused before further Tkinter development. The next slice must reduce the two remaining workflow risks before the GUI becomes the primary interface:

1. Shell and quote errors from generated terminal patch blocks.
2. Drift from literal Markdown state checks and scattered current/previous release facts.

Required near-term scope before continuing GUI expansion:

- Add a minimal typed Work Order Runner that can execute repo-backed, schema-checked work orders without chat-generated patch scripts.
- Keep the first runner small: read-only command execution, existing cockpit action execution, evidence/log finalization, deterministic PASS/FAIL/PENDING/HARD-FAIL summaries, and dirty-state blocking.
- Forbid new long chat-generated Python or shell patch scripts for standard work once the runner exists; chat should describe intent and repo tools should execute typed operations.
- Defer the full Patch DSL until after the minimal runner exists. The later DSL should support safe operations such as replace_once, insert_after, append_unique, ensure_line, dry-run, and atomic writes through safe_file_replace.
- Defer the full structured State Source of Truth until after the minimal runner and thin GUI foundation. The later state source should move current release, previous release, DOI, evidence, GUI readiness, and next-slice facts into machine-readable YAML and render or validate Markdown from that state.
- Resume Tkinter only after this pre-GUI hardening plan is recorded and the next work begins with the minimal Work Order Runner. The next GUI must remain a thin presentation layer over registry actions and machine-readable results.

Recommended sequencing:

- v0.3.31 Slice 1: minimal typed Work Order Runner for GUI-safe execution and quote-risk reduction.
- v0.3.31 Slice 2: thin Tkinter MVP over Action Registry and cockpit JSON results.
- v0.3.32: typed Patch DSL to eliminate quote-heavy chat patches for standard file edits.
- v0.3.33: structured State Source of Truth to reduce literal-document drift.

The architectural rule is: chat describes intent; repo-owned tools execute typed operations; Markdown is a projection, not the primary source of truth; shell is a runner, not a patch language.


- v0.3.34 pre-GUI portable-core hardening continued with an explicit `./ns dev-local-feature-gate` routing fix. The shortcut now runs the local feature gate directly before the `tools/next-step.py` fallback and is covered by `tests/test_v034_ns_dev_gate_routing.py`.
- Remote merge evidence for the routing fix is recorded in `docs/reports/terminal/v0.3.34_ns_dev_gate_routing_merge_verification.log`.


- v0.3.34 pre-GUI portable-core hardening continued by extracting local feature gate execution into `src/agentic_project_kit/local_feature_gate.py`. The `./ns dev-local-feature-gate` and `./ns dev` routes now dispatch through this tested Python core instead of embedding the full gate in shell.
- PR #525 initially caused a historical red main CI run because `tests/test_repo_ns_entrypoint.py` still expected the old shell-embedded `NS DEV LOCAL FEATURE GATE` text. PR #526 repaired the stale regression to assert the new dispatcher/core contract, and the latest main CI is green.
- Remote evidence is recorded in `docs/reports/terminal/v0.3.34_local_feature_gate_core_merge_verification.log`.


- v0.3.34 pre-GUI portable-core hardening continued with a pure Python finalize-guard decision core in `src/agentic_project_kit/finalize_guard.py`. This models idempotent completion, noop branches, PR-needed branches, superseded branches, and relevant conflict failures before replacing the shell runner.
- Regression coverage is in `tests/test_v034_finalize_guard_core.py`. Remote evidence is recorded in `docs/reports/terminal/v0.3.34_finalize_guard_core_merge_verification.log`.


- v0.3.34 finalize-guard hardening continued by making the Python decision core contract executable via `python -m agentic_project_kit.finalize_guard` and by making `PASS_SUPERSEDED` reachable for conflicting but already-represented finalization branches.
- Regression coverage remains in `tests/test_v034_finalize_guard_core.py`. Remote evidence is recorded in `docs/reports/terminal/v0.3.34_finalize_guard_core_contract_verification.log`.

- v0.3.34 is published and verified with Zenodo version DOI `10.5281/zenodo.20315568`.

- v0.3.34 release cycle is closed: GitHub release, release assets, Zenodo concept DOI, Zenodo version DOI, DOI metadata, and post-release verification are complete.


## v0.3.35 Pre-GUI Core and CLI Consolidation Plan

v0.3.35 is planned as a consolidation line before starting the Tkinter cockpit MVP. The release should not add the GUI itself. Its purpose is to remove remaining pre-GUI weaknesses that would otherwise become visible or harder to fix once a GUI calls into the project workflows.

Required v0.3.35 scope:

- Expand the unit-test matrix for the new Python core modules, especially `finalize_guard`, `local_feature_gate`, and `release_doi_safety`.
- Continue reducing shell scripts to thin delegators around tested Python cores, prioritizing release, DOI, evidence, and dirty-state paths before comfort wrappers.
- Harden the release and DOI phase as explicit contracts: `release-check` is the pre-publish gate, while `post-release-check` is the post-publish DOI-aware gate.
- Make evidence and dirty-log checks visible as stable action contracts instead of ad-hoc terminal interpretation.
- Make the documented layered CLI usability model visible in practical entry points: Daily, Guided, Maintainer, and Debug.

Acceptance criteria before GUI work resumes:

- The high-risk pre-GUI command paths have Python core tests or explicit documented deferrals.
- `./ns`, `./ns-menu`, Cockpit action metadata, and CLI help do not contradict the layered usability model.
- Release and post-release flows distinguish expected post-publish states from real failures without requiring manual interpretation.
- No GUI slice starts until the remaining shell/Python boundary is intentionally classified.

- v0.3.35 core-test-matrix consolidation started by expanding regression coverage for `finalize_guard`, `local_feature_gate`, and `release_doi_safety` without changing runtime behavior.

- v0.3.35 consolidation continued by wiring `tools/ns_finalize_guard.sh` to the tested Python `agentic_project_kit.finalize_guard` decision core.
- The shell path now acts as a git-state collector and delegates machine-readable finalization classification to the Python core while preserving `STATUS:` lines and `### RESULT:` markers.

- v0.3.35 release-gate core extraction prep evidence is now repo-backed in `docs/reports/terminal/v0.3.35_release_gate_core_extraction_prep.log`; this replaces the earlier chat-only diagnostic and records the grep hygiene rule: prefer `git grep` or exclude `__pycache__` from diagnostics.

- v0.3.35 consolidation continued by extracting `tools/ns_release_gate.sh` behavior into the tested Python core `src/agentic_project_kit/release_gate_core.py`. The shell entry point is now a thin adapter. Release-gate behavior remains pre-publish only: no tag, no release, no DOI mutation, and no GUI work.

- v0.3.35 is published and verified with Zenodo version DOI `10.5281/zenodo.20316280`.

- v0.3.35 release-gate/core consolidation is released and DOI metadata is recorded; v0.3.35 is closed for pre-GUI core consolidation.

- v0.3.36 current-state cleanup started as a documentation-only line: normalize README current-release wording, make the v0.3.35 CHANGELOG entry describe the actual delivered work, clarify GUI/cockpit status, and lock release-phase semantics in tests before any bounded Tkinter MVP work.\n\n- v0.3.36 standard-error hardening started: Remote-log evidence is mandatory for standard-error hardening slices; summaries must include `terminal_log=docs/reports/terminal/...`, `command_report=...`, and `NEXT_CHAT_REPLY`. FAIL without terminal kill uses NEXT_CHAT_REPLY: f so the next step reconstructs from the remote log before asking for pasted terminal output.\n

- v0.3.36 standard-error hardening slice 1 is remote-evidence backed: merge/local-gate output is recorded in `docs/reports/terminal/v0.3.36_merge_standard_error_hardening_1.log`. This explicitly restores the rule that FAIL recovery starts from committed/pushed logs before asking for pasted terminal output.
- v0.3.36 run-summary contract evidence is repo-backed in `docs/reports/terminal/v0.3.36_run_summary_contract_merge_evidence.log`; run summaries must expose `terminal_log`, `REMOTE_EVIDENCE`, `STANDARD_ERROR_REDUCTION`, and `GUI_PREPARATION` so standard-error reduction and GUI readiness stay visible after each slice.
