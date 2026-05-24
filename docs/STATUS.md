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
`docs/STATUS.md` is the compact live dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

Planning-state freshness is a hard drift signal. The state files must distinguish current release facts, compatibility anchors, and preserved historical test anchors. `Current released version: 0.3.29` remains here only as a compatibility anchor for planning-state freshness coverage, not as the current release.

## Current Goal
Continue the documentation-management rebuild through small, reversible, test-backed registry slices. The registry baseline exists, has a read-only CLI summary, has a JSON report path, is visible in audit/handoff/release surfaces, and now consumes the machine-readable communication artifact policy. Do not start a broad documentation migration, create a release tag, publish a release, or perform destructive GUI/remote actions in the next slice.

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
- PR #695 added the read-only `agentic-kit docs-registry` summary command and a narrow operational/artifact classification set.
- PR #696 added `agentic-kit docs-registry --report PATH` as a read-only JSON handoff for later GUI, doc-mesh, lifecycle, and artifact consumers.
- PR #697 surfaced registry summary data in `agentic-kit docs-audit`.
- PR #698 surfaced registry summary data in `agentic-kit doc-mesh-audit`.
- PR #699 surfaced registry summary data in `agentic-kit doc-lifecycle-audit`.
- PR #700 surfaced registry summary data in `agentic-kit handoff check` and `agentic-kit handoff show`.
- PR #701 surfaced registry summary data in `agentic-kit release-check` and `agentic-kit post-release-check`.
- PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.
- PR #706 added the warning-based successor handoff prompt freshness guard.
- PR #707 recorded post-guard successor handoff and closeout evidence.
- PR #708 refreshed handoff state after PR707.
- PR #709 exposed `.agentic/communication_artifacts.yaml` through the read-only documentation registry summary and JSON report without changing cleanup behavior.

The registry guard is intentionally structural only. It checks schema, allowed classes, required rule fields, duplicate paths, and registered path existence. It does not prove semantic documentation quality and does not authorize broad migration.

## Current GUI Baseline
- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- Headless GUI action execution tests cover the bounded read-only executor without opening a Tkinter window.
- The Tkinter cockpit remains a thin future presentation layer over registry actions and machine-readable results.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.

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

Documentation registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md` governs additive registry slices. The machine-readable source is `docs/DOCUMENTATION_REGISTRY.yaml`.

Mandatory Final Summary Contract: relevant workflow blocks must end with the framed summary fields, including WORK RESULT and REMOTE_EVIDENCE. Use the canonical summary renderer; do not append handwritten legacy summary footers.

## Live Status Commands
Use project-local commands first: `./ns state`, `./ns check-docs`, `./ns doctor`, `./ns docs-audit`, `./ns handoff-check`, `./ns governance-check`, and `agentic-kit handoff prompt` when installed through the active project environment.

The registry can be inspected through `agentic-kit docs-registry` and exported with `agentic-kit docs-registry --report PATH`. Registry summary data is visible in `agentic-kit docs-audit`, `agentic-kit doc-mesh-audit`, `agentic-kit doc-lifecycle-audit`, `agentic-kit handoff check`, `agentic-kit handoff show`, `agentic-kit release-check`, and `agentic-kit post-release-check`.

## Active Workflow Rules
- Read mandatory successor-chat sources before mutation.
- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, or repo-backed rules.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Keep documentation registry changes additive, modular, reversible, and test-backed.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.
- Generated terminal blocks must avoid heredocs, risky multiline `python -c` snippets, and quote-prone constructs.
- Recent CHANGELOG release entries from v0.3.36 onward are guarded structurally; the guard must not be reduced to a naive bullet-count rule.

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

This remote chat environment cannot run local Python 3.13 gates. Merge readiness requires equivalent CI evidence.

## Current Evidence Anchors
- `docs/reports/terminal/v041-final-main-verify-after-pr689.log`
- `docs/reports/terminal/v041-successor-chat-handoff-after-pr701.md`
- `docs/reports/terminal/v041-handoff-after-pr701.log`
- PR #706 CI evidence for successor handoff freshness guard coverage.
- PR #707 evidence for post-guard successor handoff and closeout.
- PR #708 evidence for post-PR707 state refresh.
- PR #709 CI evidence for the artifact policy registry consumer.

## Next Safe Step
Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr709.md` for a chat switch after this closeout lands. Then continue with one additional small documentation registry slice, preferably toward machine-readable source/projection planning. Do not start a broad migration.

## Compatibility Coverage Anchors
These compact anchors are intentionally retained for deterministic coverage, not as current narrative: documentation coverage, `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, `agentic-kit doctor`, policy-pack doctor checks, policy-pack checks, policy packs, Pattern Advisor, read-only catalog, patterns list, patterns show, advisory-only, post-release Zenodo, `agentic-kit post-release-check`, no-copy/evidence, Tkinter cockpit, Mandatory Final Summary Contract, WORK RESULT, REMOTE_EVIDENCE, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`.
