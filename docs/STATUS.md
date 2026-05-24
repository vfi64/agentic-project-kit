<!-- post-pr714-closeout -->
# Project Status

Status-date: 2026-05-24
Project: agentic-project-kit
Primary branch: main
Current work branch: main
Current version: 0.4.1

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Durable project memory belongs in versioned repository files, deterministic gates, evidence logs, and explicit handoff state rather than chat transcripts.

The repository is the source of truth; chat memory is not a source of truth. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current-State Boundary

`docs/STATUS.md` is the live current-state dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

This document is a concise pointer, not a duplicate rule book. Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary and fails if `docs/STATUS.md` exceeds the configured word limit. This is a hard drift signal.

## Current State

Current released version: 0.4.1.
Current release tag: v0.4.1.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
Post-release Zenodo verification is covered by `agentic-kit post-release-check --version 0.4.1`.

Post-PR714 closeout target:
- Main is refreshed after PR #714 at `7d092cb` (`Add workflow guard diagnostics (#714)`).
- PR #714 completed the workflow-guard diagnostics slice, integrated the guard into patch preflight, restored protected-control-file preservation coverage, and removed hard word limits from protected control files.
- Evidence: `docs/reports/terminal/pr714-verify-after-test-alignment.log`; remote evidence present.
- The next immediate hardening task is canonical structured SUMMARY enforcement before resuming documentation-management registry or projection work.

Documentation registry baseline:
- `docs/DOCUMENTATION_REGISTRY.yaml` is the additive machine-readable registry.
- `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md` is the human contract.
- `agentic-kit docs-registry` shows the read-only summary.
- `agentic-kit docs-registry --report PATH` writes the JSON report.
- The registry is visible in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.
- `.agentic/communication_artifacts.yaml` is consumed as read-only artifact-policy input.
- Broad documentation migration remains forbidden. The registry guard is structural only and does not prove semantic documentation quality.

Workflow hardening baseline:
- GitHub connector direct-path-first is the required remote route for known repository paths, refs, PRs, and commits.
- Governance YAML mutation must use parse-modify-dump or an equivalent structured mutation path, then parse again.
- `.agentic/control_file_preservation.yaml` protects active rules from lossy shortening.
- Information preservation outranks compactness for protected control files. Hard length-limit trimming is forbidden; large protected files must be split, referenced, or generated instead of losing active rules.

GUI MVP baseline:
- `cockpit-readiness`, `doctor`, and `check-docs` visually pass as bounded read-only GUI actions.
- Action Registry is the single source of allowed GUI actions.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.
- Headless GUI action execution tests cover the bounded read-only action executor.

## Current Goal

Repair PR715 closeout drift without product changes, merge PR715 only after CI and mergeability are green, then harden canonical structured SUMMARY enforcement before resuming documentation-management work.

## Active Workflow Rules

- Read mandatory successor-chat sources before mutation.
- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, or repo-backed rules.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Relevant terminal blocks must render the structured Final summary contract in terminal output before log upload; example evidence field: terminal_log=docs/reports/terminal/<name>.log.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.
- Remote-first no-guess: do not guess repository state; inspect known remote paths, PRs, commits, logs, and command help first.
- Remote command first is a delivery preference, not a permission bypass or a reason to skip evidence.
- Remote-log evidence is mandatory for standard-error hardening slices.
- FAIL without terminal kill uses NEXT_CHAT_REPLY: f and must first inspect the repo-backed log before requesting paste-output.
- Remote inspection evidence contract: logs and command reports that matter for later reasoning must be committed, pushed, and registered for later GC.
- no-remote-command-deadlock applies: remote command output must not depend on manual paste when remote or local evidence exists.
- Ruff must run only on Python sources or Python files; shell files use shell checks, not Ruff.
- Generated terminal blocks must avoid heredocs, risky multiline `python -c` snippets, and quote-prone constructs.
- Recent CHANGELOG release entries from v0.3.36 onward are guarded structurally.
- Typed Work Orders Pre-GUI Execution Path remains the preferred pre-GUI execution path, with the minimal typed Work Order Runner as the pre-GUI bridge without chat-generated patch scripts.
- Documentation registry changes must remain additive, modular, reversible, and test-backed.
- Remote repo inspection should use the GitHub connector direct-path-first workflow when path, commit, PR, or branch is known.
- Governance YAML must be changed through parse-modify-dump and validated after mutation.
- Protected control files must preserve active rules unless an explicit successor migration is recorded and tested.
- Structured SUMMARY drift is blocking drift: missing, malformed, contradictory, or legacy summaries must be fixed before product or documentation-management work continues.
- v0.3.30 GUI Readiness Hardening Closeout was not the Tkinter GUI release.
- GUI readiness hardening, not a Tkinter implementation, remains the pre-GUI boundary before any bounded Tkinter MVP work.
- GUI expansion is intentionally paused until the current hardening slice is green.

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

Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, CHAT_REPLY, and the final result marker. No executable placeholder summaries and final-summary-no-executable-placeholders remain active.

No-copy/evidence contract: `d` means a log-backed block appears finished; evidence must still be inspected. `f` means failure was reported; first inspect remote or local evidence and request pasted output only when evidence is unavailable or unusable.

## Live Status Commands

Use project-local commands first: `./ns state`, `./ns check-docs`, `./ns doctor`, `./ns docs-audit`, `./ns handoff-check`, `./ns governance-check`, `agentic-kit check-docs`, `agentic-kit doctor`, and `agentic-kit handoff prompt` when installed through the active project environment.

The registry can be inspected through `agentic-kit docs-registry` and exported with `agentic-kit docs-registry --report PATH`.

## Gate Status

Required gate set for current-state, handoff, or governance-summary changes:
- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns docs-audit`
- `./ns dev`
- `agentic-kit check-docs`
- `agentic-kit doctor`
- `agentic-kit post-release-check --version 0.4.1`

This remote chat environment cannot run the local Python gates directly. Merge readiness requires equivalent CI evidence.

## Next Safe Step

First repair PR715 and verify that the post-PR714 closeout state, handoff state, current handoff, and successor prompt are consistent with PR714 rather than PR712.

Then perform the dedicated hardening slice: enforce structured final summaries across the renderer, tests, workflow guard or patch preflight, generated handoff prompts, terminal logs, command reports, and chat/workflow contracts. Do not return to the documentation-management rebuild until this drift is closed.

## Historical Compatibility Anchors

These anchors keep older regression tests attached to their migrated contracts without turning STATUS into the long-term history: read-only catalog; advisory-only; Pattern Advisor; `patterns list`; `patterns show`; Planning-state freshness; Tkinter cockpit; v0.3.30 GUI Readiness Hardening Plan; v0.3.30 GUI Readiness Hardening Closeout; PR #463: ActionResult core contract; PR #464: `cockpit run --json`; PR #465: Registry-only; PR #466: Queue-State contract; PR #467: Evidence-State contract; already executed command; dirty-state blocking; dirty worktrees; v0.3.31 Pre-GUI Execution Hardening Plan; v0.3.31 Pre-GUI Execution Hardening Closeout; v0.3.31 Evidence Guard Usage; v0.3.31 is the current pre-GUI execution hardening line.; It does not ship the Tkinter GUI.; Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.; Local shortcut `./ns evidence-guard LOGFILE`.; `agentic-kit evidence guard LOGFILE`; `./ns evidence-guard LOGFILE`; contradictory final state; final-PASS-after-failure; Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.; Typed Work Order Evidence Contract.; Typed Work Order Evidence Runtime Check.; validate_typed_work_order_evidence; Next safe step: prepare and release v0.3.31.; Do not start Tkinter before v0.3.31 is released and post-release verified.; Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion.; Typed Work Orders Pre-GUI Execution Path; typed Patch DSL; structured State Source of Truth; Markdown is a projection; no_command; exactly_one_command; multiple_commands; already_executed; v0.3.32 Release Phase and Evidence Closeout; Current released version: 0.3.29; Current released version: 0.3.32; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; `release-preflight` validates the before-metadata release phase; `release-check` remains the after-metadata gate; `post-release-check` remains the after-release GitHub and Zenodo verification gate; `evidence clean-check`; `./ns evidence-clean-check`; expected in-progress log may be the only dirty path; v0.3.34 Portable Core Hardening Plan; Typed work order unit-test matrix; Release and DOI core action extraction; Concept-DOI versus version-DOI WAITING guard; no new large shell control blocks; Tkinter remains explicitly deferred; Do not start GUI implementation in this slice.; GUI expansion is intentionally paused; remote inspection evidence contract; Remote-log evidence is mandatory for standard-error hardening slices; PR #650 merged; PR #651 merged; PR #652 merged.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml.
