Current version: 0.4.1
# Project Status
Status-date: 2026-05-24
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose
agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Durable project memory belongs in versioned repository files, deterministic gates, evidence logs, and explicit handoff state rather than chat transcripts.

The repository is the source of truth; chat memory is not a source of truth. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current-State Boundary
`docs/STATUS.md` is the live current-state dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary and fails if `docs/STATUS.md` exceeds the configured word limit. This is a hard drift signal, not a stylistic preference.

## Current Goal
Continue the documentation-management rebuild through small, reversible, test-backed registry slices. The registry baseline exists, has a read-only CLI summary, has a JSON report path, and is connected to the current read-only audit, handoff, release-check, post-release-check, and communication-artifact policy surfaces. Do not start a broad documentation migration, create a release tag, publish a release, or perform destructive GUI/remote actions in the next slice.

## Current State
Current released version: 0.4.1.
Current release tag: v0.4.1.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
Post-release Zenodo verification is covered by `agentic-kit post-release-check --version 0.4.1`.

Documentation registry baseline on `main`:
- PR #692 added `docs/DOCUMENTATION_REGISTRY.yaml` as the first additive documentation and artifact classification registry.
- PR #692 documented the registry contract in `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- PR #692 wired the structural registry guard into `agentic-kit check-docs`, and therefore into `agentic-kit docs-audit`.
- PR #692 added targeted registry tests and YAML governance parse coverage.
- PR #694 refreshed `docs/STATUS.md` after the registry baseline while leaving the handoff file unchanged.
- PR #695 classified a narrow operational/artifact set and added the read-only `agentic-kit docs-registry` summary command.
- PR #696 added `agentic-kit docs-registry --report PATH` as a read-only JSON handoff for later GUI, doc-mesh, lifecycle, and artifact-GC consumers.
- PR #697 surfaced registry summary data in `agentic-kit docs-audit` as a read-only audit dimension.
- PR #698 surfaced registry summary data in `agentic-kit doc-mesh-audit` as read-only mesh context.
- PR #699 surfaced registry summary data in `agentic-kit doc-lifecycle-audit` as read-only lifecycle context.
- PR #700 surfaced registry summary data in `agentic-kit handoff check` and `agentic-kit handoff show` without changing generated handoff prompts.
- PR #701 surfaced registry summary data in `agentic-kit release-check` and `agentic-kit post-release-check` as read-only release context.
- PR #709 exposed `.agentic/communication_artifacts.yaml` through the read-only documentation registry summary and JSON report without changing cleanup behavior.
- The registry guard is intentionally structural only. It checks schema, allowed classes, required rule fields, duplicate paths, and registered path existence. It does not prove semantic documentation quality and does not authorize broad migration.

GUI MVP baseline on `main`:
- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.
- Headless GUI action execution tests now cover the bounded read-only action executor without opening a Tkinter window.
- Tk runtime for manual judgement must import `tkinter`, `yaml`, `typer`, `rich`, and `pydantic`.

Current GUI, release, documentation registry, and governance evidence:
- `docs/reports/terminal/v040-record-check-docs-gui-visual-pass.log`
- `docs/reports/terminal/v040-repair-tk-venv-deps-zsh-safe-check-docs-visual.log`
- `docs/reports/terminal/v040-record-doctor-gui-manual-launch-visual-result.log`
- `docs/reports/terminal/v040-final-release-readiness-and-successor-handoff.log`
- `docs/reports/terminal/v040-doi-metadata-remote-closeout.log`
- `docs/reports/terminal/gui-action-execution-headless-remote.log`
- `docs/reports/terminal/changelog-quality-guard-remote.log`
- `docs/reports/terminal/v041-handoff-after-pr709.log`
- PR #692 CI evidence for Ruff, tests, and CLI smoke.
- PR #694 CI evidence for Ruff, tests, and CLI smoke.
- PR #695 CI evidence for Ruff, tests, and CLI smoke.
- PR #696 CI evidence for Ruff, tests, and CLI smoke.
- PR #697 CI evidence for Ruff, tests, and CLI smoke.
- PR #698 CI evidence for Ruff, tests, and CLI smoke.
- PR #699 CI evidence for Ruff, tests, and CLI smoke.
- PR #700 CI evidence for Ruff, tests, and CLI smoke.
- PR #701 CI evidence for Ruff, tests, and CLI smoke.
- PR #709 CI evidence for Ruff, tests, and CLI smoke.

Recent closeout anchors:
- PR #656 closed out the GUI MVP three read-only actions.
- PR #657 modeled administrative evidence state in generated handoff prompts.
- PR #670 guarded Ruff scope and terminal quote safety after release publication.
- PR #671 closed v0.4.0 DOI metadata on main.
- PR #680 added headless GUI action execution tests.
- PR #681 added deterministic recent-release CHANGELOG quality checks to `check-docs`.
- PR #689 closed the v0.4.1 DOI metadata state on main.
- PR #690 recorded final main verification after the v0.4.1 DOI metadata closeout.
- PR #691 refreshed handoff state and the successor handoff prompt after final v0.4.1 verification.
- PR #692 introduced the first documentation registry schema and guard slice.
- PR #694 refreshed the live status after the registry baseline.
- PR #695 added the first read-only registry consumer and operational/artifact classifications.
- PR #696 added the read-only registry JSON report path.
- PR #697 added docs-audit registry visibility.
- PR #698 added doc-mesh registry visibility.
- PR #699 added doc-lifecycle registry visibility.
- PR #700 added handoff check/show registry visibility.
- PR #701 added release-check and post-release-check registry visibility.
- PR #709 added the artifact policy registry consumer.
- v0.4.1 is tagged, published, post-release checked, and has verified Zenodo version DOI `10.5281/zenodo.20357657`.

## Active Workflow Rules
- Read mandatory successor-chat sources before mutation.
- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, or repo-backed rules.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Relevant terminal blocks must render the structured Final summary contract in terminal output before log upload.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.
- Ruff must run only on Python sources or Python files; shell files use shell checks, not Ruff.
- Generated terminal blocks must avoid heredocs, risky multiline `python -c` snippets, and quote-prone constructs.
- Recent CHANGELOG release entries from v0.3.36 onward are guarded structurally; the guard must not be reduced to a naive bullet-count rule.
- Documentation registry changes must remain additive, modular, reversible, and test-backed. The registry guard is structural and must not be used as a broad migration trigger.

## Documentation and Communication Contracts
Mandatory successor-chat source order is defined by `.agentic/compiled_agent_context.yaml` and checked by `agentic-kit docs-audit`:
1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

Documentation registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md` governs the additive registry slices. The machine-readable source is `docs/DOCUMENTATION_REGISTRY.yaml`.

Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and the final result marker.

## Live Status Commands
Use project-local commands first: `./ns state`, `./ns check-docs`, `./ns doctor`, `./ns docs-audit`, `./ns handoff-check`, `./ns governance-check`, and `agentic-kit handoff prompt` when installed through the active project environment. Planning-state freshness, documentation coverage, policy-pack checks, Pattern Advisor, `patterns list`, `patterns show`, read-only catalog, advisory-only, post-release Zenodo, `docs/DOCUMENTATION_COVERAGE.yaml`, and `docs/DOCUMENTATION_REGISTRY.yaml` are compact live-state anchors here; detailed history belongs in `CHANGELOG.md`.

The registry can be inspected through `agentic-kit docs-registry` and exported with `agentic-kit docs-registry --report PATH`. Registry summary data is visible in `agentic-kit docs-audit`, `agentic-kit doc-mesh-audit`, `agentic-kit doc-lifecycle-audit`, `agentic-kit handoff check`, `agentic-kit handoff show`, `agentic-kit release-check`, and `agentic-kit post-release-check`.

## Gate Status
Required gate set for current-state or handoff changes:
- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns docs-audit`
- `./ns dev`
- `agentic-kit check-docs`
- `agentic-kit doctor`
- `agentic-kit post-release-check --version 0.4.1`

This remote chat environment could not run the local Python 3.13 gates. Merge readiness requires equivalent CI evidence.

## Compact Regression Anchors
These compact anchors are intentionally retained to keep existing deterministic gates stable while preserving the current-state boundary. They are pointers, not long-term narrative history.

- No executable placeholder summaries / final-summary-no-executable-placeholders.
- no-remote-command-deadlock; remote-first no-guess; remote inspection evidence contract.
- Typed Work Orders Pre-GUI Execution Path; preferred pre-GUI execution path; already executed command; dirty worktrees; remote evidence present.
- v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; GUI readiness hardening, not a Tkinter implementation; not the Tkinter GUI release; Tkinter is explicitly deferred until these contracts pass gates.
- v0.3.31 Evidence Guard Usage; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; Local shortcut `./ns evidence-guard LOGFILE`.; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.
- Current released version: 0.3.29; Current released version: 0.3.32; v0.3.32 Release Phase and Evidence Closeout; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path.
- v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; no new large shell control blocks; Tkinter remains explicitly deferred.
- v0.3.36 current-state cleanup started as a documentation-only line.
- PR #649 merged; PR #650 merged; PR #651 merged; PR #652 merged.
- Remote-log evidence is mandatory for standard-error hardening slices.

## Compact Legacy Test Anchors
These anchors are deliberately compact compatibility pointers. Long narrative history belongs in `CHANGELOG.md`.

- no-remote-command-deadlock: Remote command first is a delivery preference, not a requirement when it would create deadlock.
- remote-first no-guess: inspect command help before inventing command names; command help must be checked before remote-only assumptions.
- Typed Work Orders Pre-GUI Execution Path: preferred pre-GUI execution path; long chat-generated shell or Python patch blocks are deprecated; thin Tkinter cockpit must consume these typed contracts.
- Historic release anchor: Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`.
- v0.3.36 current-state cleanup started as a documentation-only line before any bounded Tkinter MVP work.
- remote inspection evidence contract: failed or diagnostic logs must be uploaded and registered for later GC.

## Next Safe Step
Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr709.md` for a chat switch after PR710 lands, then continue with one additional small registry consumer or machine-readable source/projection planning slice. Do not start a broad migration.

## Compatibility Coverage Anchors
These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, v0.3.31 is the current pre-GUI execution hardening line., Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`.
