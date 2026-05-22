Current version: 0.4.0
# Project Status
Status-date: 2026-05-22
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/repair-v040-status-drift-after-pr657

## Purpose
agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Durable project memory belongs in versioned repository files, deterministic gates, evidence logs, and explicit handoff state rather than chat transcripts.

The repository is the source of truth; chat memory is not a source of truth. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current-State Boundary
`docs/STATUS.md` is the live current-state dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary and fails if `docs/STATUS.md` exceeds the configured word limit. This is a hard drift signal, not a stylistic preference.

## Current Goal
Keep the v0.4.0 GUI MVP baseline ready for the next readiness slice by repairing current-state drift after PR #657. This is a documentation-state repair only; it does not start release work or change GUI behavior.

## Current State
Current released version: 0.3.37.
Current release tag: v0.3.37.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Verified Zenodo version DOI: `10.5281/zenodo.20329450`.
Post-release Zenodo verification remains covered by `agentic-kit post-release-check`.

GUI MVP baseline on `main`:
- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.
- Tk runtime for manual judgement must import `tkinter`, `yaml`, `typer`, `rich`, and `pydantic`.

Current GUI evidence:
- `docs/reports/terminal/v040-record-check-docs-gui-visual-pass.log`
- `docs/reports/terminal/v040-repair-tk-venv-deps-zsh-safe-check-docs-visual.log`
- `docs/reports/terminal/v040-record-doctor-gui-manual-launch-visual-result.log`
- `docs/reports/terminal/v040-final-release-readiness-and-successor-handoff.log`

Recent closeout anchors:
- PR #656 closed out the GUI MVP three read-only actions.
- PR #657 modeled administrative evidence state in generated handoff prompts.
- Historical open PRs #562, #564, and #568 still need explicit classification or closure before a final v0.4.0 release-readiness conclusion.

## Active Workflow Rules
- Read mandatory successor-chat sources before mutation.
- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, or repo-backed rules.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Relevant terminal blocks must render the structured final SUMMARY in terminal output before log upload.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.

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

Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and the final result marker.

## Live Status Commands
Use project-local commands first: `./ns state`, `./ns check-docs`, `./ns doctor`, `./ns docs-audit`, `./ns handoff-check`, `./ns governance-check`, and `agentic-kit handoff prompt` when installed through the active project environment. Planning-state freshness, documentation coverage, policy-pack checks, Pattern Advisor, `patterns list`, `patterns show`, read-only catalog, advisory-only, post-release Zenodo, and `docs/DOCUMENTATION_COVERAGE.yaml` are compact live-state anchors here; detailed history belongs in `CHANGELOG.md`.

## Gate Status
Required gate set for current-state or handoff changes:
- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns docs-audit`
- `./ns dev`
- `agentic-kit check-docs`
- `agentic-kit doctor`

## Compact Regression Anchors
These compact anchors are intentionally retained to keep existing deterministic gates stable while preserving the current-state boundary. They are pointers, not long-term narrative history.

- No executable placeholder summaries / final-summary-no-executable-placeholders.
- no-remote-command-deadlock; remote-first no-guess; remote inspection evidence contract.
- Typed Work Orders Pre-GUI Execution Path; preferred pre-GUI execution path; already executed command; dirty worktrees; remote evidence present.
- v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; GUI readiness hardening, not a Tkinter implementation; not the Tkinter GUI release; Tkinter is explicitly deferred until these contracts pass gates.
- v0.3.31 Evidence Guard Usage; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; Local shortcut `./ns evidence-guard LOGFILE`.; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.
- Current released version: 0.3.29; Current released version: 0.3.32; v0.3.32 Release Phase and Evidence Closeout; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path.
- v0.3.34 portable core hardening plan; Tkinter remains explicitly deferred.
- v0.3.36 current-state cleanup started as a documentation-only line.
- PR #649 merged; PR #650 merged; PR #651 merged; PR #652 merged.

## Compact Legacy Test Anchors
These anchors are deliberately compact compatibility pointers. Long narrative history belongs in `CHANGELOG.md`.

- no-remote-command-deadlock: Remote command first is a delivery preference, not a requirement when it would create deadlock.
- remote-first no-guess: inspect command help before inventing command names; command help must be checked before remote-only assumptions.
- Typed Work Orders Pre-GUI Execution Path: preferred pre-GUI execution path; long chat-generated shell or Python patch blocks are deprecated; thin Tkinter cockpit must consume these typed contracts.
- Historic release anchor: Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`.
- v0.3.36 current-state cleanup started as a documentation-only line before any bounded Tkinter MVP work.
- remote inspection evidence contract: failed or diagnostic logs must be uploaded and registered for later GC.

## Next Safe Step
Finish this non-destructive current-state repair slice, verify the gates, and then handle the remaining drift separately: `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and historical PRs #562, #564, and #568 must be classified or closed without removing test-bound compatibility anchors.

After the state repair is merged and verified on `main`, generate the next-chat handoff through `agentic-kit handoff prompt` before any v0.4.0 release-readiness conclusion.

## Compatibility Coverage Anchors
These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, v0.3.31 is the current pre-GUI execution hardening line., Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`.
