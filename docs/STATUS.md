Current version: 0.3.21

# Project Status

Status-date: 2026-05-16
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, documentation-mesh drift auditing, document lifecycle auditing, and local cockpit action inspection.

The project itself has a current state layer so work can be continued from the repository state files. Its development model treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, and release metadata.

## Current Goal

v0.3.19 Cockpit Action Selection UX is merged on main via PR #255. v0.3.19 is released, post-release verified, and DOI metadata is recorded on main.

The slice must stay inspect-only: it may improve action discovery through `agentic-kit cockpit select`, `./ns select`, and a numbered `./ns-menu` entry, but it must not add a new execution path or loosen bounded/destructive action blocking.

## Current State

Current released version: 0.3.19
Completed slice: v0.3.19 Cockpit Action Selection UX

v0.3.19 is released and post-release verified with version DOI `10.5281/zenodo.20246121`. The release covers the `./ns-menu` cockpit JSON consumer update: the menu no longer clears the terminal by default, `NS_MENU_CLEAR=1` restores clearing when desired, and a numbered `./ns actions --json` entry exposes the schema-versioned cockpit action inventory. Cockpit action execution remains unchanged: read-only actions may run through `cockpit run`, bounded actions remain blocked without explicit allow, and destructive actions remain blocked. Zenodo concept DOI: `10.5281/zenodo.20101359`. The post-release Zenodo verification for v0.3.19 is complete.

PR #255 added an inspect-only cockpit action selection view. `agentic-kit cockpit select` renders a numbered action list from the central cockpit action registry without executing actions. `./ns select` delegates to that command, and `./ns-menu` exposes it as a numbered entry without adding new shell execution logic.

## Recent completed work since v0.3.14

- PR #232 added the Local Cockpit Foundation with `agentic-kit cockpit status`, `agentic-kit cockpit actions`, `./ns cockpit`, `./ns actions`, and a read-only structured action inventory.
- PR #236 added the Local Cockpit Action Layer with `agentic-kit cockpit run <action-id>`, structured action results, read-only action execution, bounded-action blocking without explicit allow, and destructive-action blocking.
- PR #240 added `./ns cockpit-run <action-id>` as a repo-local adapter shortcut and exposed only the read-only `./ns cockpit-run git.status` path in `./ns-menu`, raising the suite to 212 tests.
- PR #245 added `agentic-kit cockpit actions --json` as schema-versioned machine-readable cockpit action inventory output while keeping human output unchanged, raising the suite to 215 tests.
- PR #250 updated `./ns-menu` so it no longer clears the terminal by default, added the `NS_MENU_CLEAR=1` opt-in path, and exposed `./ns actions --json` as a numbered menu entry, raising the suite to 217 tests.
- PR #254 finalized repository state after v0.3.18 DOI metadata, leaving main clean at `55e37dd`.
- PR #255 added `agentic-kit cockpit select`, `./ns select`, a numbered `./ns-menu` entry, and regression coverage for the inspect-only action selection UX.

## Local Cockpit state

Local Cockpit Foundation is now extended by the v0.3.15 action-layer line, the v0.3.16 adapter-hardening line, the v0.3.17 JSON-inventory line, the v0.3.18 menu-consumer line, and the current v0.3.19 action-selection UX line for reducing copy-and-paste through a shared action API.

The cockpit action registry remains the central source of truth. `cockpit actions --json` exposes machine-readable metadata without executing actions. `cockpit select` exposes a human numbered selection view without executing actions. `cockpit run` remains the execution path and allows registered read-only actions by default. Bounded or destructive Git, release, tag, merge, cleanup, or remote operations remain blocked by default.

## Workflow request state

- `.agentic/workflow_state` is expected to be `IDLE`.
- `.agentic/current_work.yaml` may remain present with `state: READY`.
- A normal `ns` run in `IDLE` plus `READY` is intentionally a no-op.
- A workflow starts only by explicit request.
- `tools/next-step.py` remains a compatibility bridge and should not grow into the long-term public API surface.

## Idea-note state

The repository has five related non-binding architecture idea notes:

- `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
- `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
- `docs/ideas/LAYERED_CLI_USABILITY.md`
- `docs/ideas/PATTERN_ADVISOR.md`
- `docs/ideas/DIDACTIC_GUIDANCE.md`

These documents preserve architecture options without making them automatic implementation requirements.

Pattern Advisor remains optional and advisory-only. The current read-only catalog exposes `patterns list` and `patterns show`; it remains a read-only catalog, not an autopilot, a gate, or an automatic architecture decision layer.

## Documentation-mesh audit state

- `agentic-kit doc-mesh-audit` exists and currently checks machine-readable drift classes: version mismatch, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- `agentic-kit doc-lifecycle-audit` checks bounded lifecycle metadata for idea, planning, roadmap, and strategy documents and is included in `agentic-kit doctor`.
- These audits are deterministic and bounded. They do not claim semantic proof of documentation quality.

## AI-assisted development assessment

The project is strongest as a governed AI-assisted software development layer, not as an autonomous coding agent. Its main design choice is to move durable project state out of the model context and into version-controlled repository files.

Repository files act as the durable source of truth for status, handoff, architecture constraints, test gates, workflow state, and release evidence. Deterministic gates (`pytest`, `ruff`, `check-docs`, `doctor`, `doc-mesh-audit`, and release checks) remain separate from model-generated advice. Semantic quality review remains advisory and human-owned unless converted into deterministic checks.

## Project-level state documentation

Project-level state documentation is present on main:

- `.agentic/project.yaml`
- `sentinel.yaml`
- `.agentic/todo.yaml`
- `docs/STATUS.md`
- `docs/TEST_GATES.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/architecture/ARCHITECTURE_CONTRACT.md`
- `docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md`
- `docs/architecture/LOCAL_COCKPIT_FOUNDATION.md`
- `docs/DOCUMENTATION_COVERAGE.yaml`
- `docs/WORKFLOW_OUTPUT_CYCLE.md`
- `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
- `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
- `docs/ideas/LAYERED_CLI_USABILITY.md`
- `docs/ideas/PATTERN_ADVISOR.md`
- `docs/ideas/DIDACTIC_GUIDANCE.md`

Project-level state documentation is machine-checkable:

- `agentic-kit check-docs` checks the state gate documents.
- `agentic-kit doc-mesh-audit` checks bounded cross-document drift classes for targeted documentation-mesh changes.
- `docs/architecture/ARCHITECTURE_CONTRACT.md` is a required state gate document.
- `docs/DOCUMENTATION_COVERAGE.yaml` is a documentation coverage matrix.

## Project health diagnostics

- `agentic-kit doctor` checks required project files, project contract status, policy-pack checks, documentation gates, document lifecycle metadata, machine-readable task gates, and version drift including package `__version__` drift.
- `agentic-kit check-docs` checks documentation coverage and deterministic document-quality heuristics.
- `agentic-kit doc-mesh-audit` checks targeted documentation-mesh drift classes.
- `agentic-kit doc-lifecycle-audit` checks bounded lifecycle metadata and is covered by `agentic-kit doctor`.
- `agentic-kit release-plan` and `agentic-kit release-check` support release-state validation before maintainer-owned tagging and publication.
- `agentic-kit post-release-check` verifies GitHub release and Zenodo archive state after publication.

## Current Blockers

No current blockers are known after PR #255.

## Live Status Commands

Run:

```bash
git status --short
git branch --show-current
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
.venv/bin/agentic-kit doc-lifecycle-audit
```

## Next Safe Step

Current slice: document GUI i18n, localized tooltips, and Instruction Bridge roadmap. This planning slice records a future i18n system for GUI labels/help/tooltips and a safe human-to-terminal-or-GUI-to-LLM instruction file mechanism. Next safe step: run documentation gates, open the roadmap PR, and then choose the first implementation slice.

## Latest completed implementation slice: PR hygiene guard

PR #277 added the read-only `agentic-kit pr-hygiene` diagnostic command, optional JSON output, shared cockpit read-only action `audit.pr-hygiene`, and tests for deterministic PR and branch hygiene analysis. The command performs no GitHub or Git mutations.

Next safe step: choose the next implementation slice from the GUI/i18n, planning-doc scaffolding, or instruction-bridge roadmap.

## Latest completed implementation slice: planning document scaffold

The merged planning-doc scaffold slice added `agentic-kit scaffold planning-doc`, a deterministic command for creating lifecycle-valid governed planning documents with `Status`, `Decision status`, `Scope`, and `Review policy` metadata. The slice also recorded the terminal result marker rule in `AGENTS.md`.

Next safe step: choose the next implementation slice from GUI i18n foundation, localized tooltips, or Instruction Bridge.

## Latest completed implementation slice: no-copy ns workflow control

PR #281 added `./ns dev` as a local feature-branch gate without `git pull --ff-only`, added a guard for risky `./ns go` use on dirty feature branches, and recorded the design in `docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md`.

Next safe step: choose the next GUI-compatible cockpit/i18n or instruction-bridge implementation slice.

## Latest completed implementation slice: ns up safety hardening

PR #285 hardened the ./ns up PR completion workflow. The command now refuses unsafe main or dirty-branch use, checks mergeability before merge, updates main only after a successful merge, keeps separator output portable, and preserves the GUI-compatible no-copy workflow direction.

Next safe step: choose the next GUI-compatible cockpit/i18n or instruction-bridge implementation slice.

## Latest completed release slice: v0.3.21 DOI metadata

v0.3.21 is released and post-release DOI metadata has been recorded. The GitHub release exists, the release verification command passes, and the verified Zenodo version DOI is 10.5281/zenodo.20258057.

## Latest completed implementation slice: deterministic release cycle hardening

PR #293 hardened the release cycle by removing recurring false failures: release-gate now cleans stale build artifacts before building, release-publish waits for the asynchronous GitHub Release workflow and verifies the completed release state, and release verification is available as a dedicated no-copy command.

## Latest completed implementation slice: ns up idempotence hardening

PR #295 hardened `./ns up` so pending PR checks are treated as a wait state and already merged PRs are handled idempotently instead of causing false FAIL states. This removes another recurring release/development-cycle friction point.

## Latest completed implementation slice: ns up no-op branch idempotence

PR #297 hardened `./ns up` so branches without a current PR and without commits ahead of main are treated as an idempotent no-op state instead of causing a spurious failure. This removes another recurring release/finalization workflow irritant.



## Next prioritized work step: deterministic ns slice runner

The next implementation priority is a deterministic `./ns` slice runner that can execute recurring patch and release-cycle subtasks as a bounded batch workflow. The runner should advance automatically from one step to the next on PASS, stop or enter a defined repair path on FAIL, and treat already-reached target states idempotently instead of producing artificial failures.

Target behavior:

- `PASS` means the requested target state was reached or was safely detected as already reached.
- `FAIL` means the requested target state was not reached and no safe idempotent interpretation or repair path is available.
- Pending CI checks, existing PRs, already-merged PRs, no-op branches, empty commits, stale `dist/` artifacts, delayed GitHub releases, delayed Zenodo DOI visibility, and previously completed documentation finalization must be handled deterministically.
- Shell scripts must be checked with shell syntax checks such as `sh -n`; Python linters must not be run on shell scripts.
- Longer patch operations should be implemented through robust generated script files, not heredocs, fragile inline `python -c`, or complex shell quoting.

Candidate command shape:

- `./ns slice <name>` for named, bounded workflows.
- Initial target workflow: `./ns slice ns-up-noop-branch-idempotence` or an equivalent first hardening slice.

This work is prioritized because repeated non-semantic FAIL states have been slowing down the development and release cycle. The goal is to remove these recurring standard errors deterministically and elegantly before adding larger GUI/Cockpit capabilities.


## Latest completed implementation slice: no direct main commit guard

The repository workflow now has an explicit ./ns commit-guard path that refuses commit/PR workflow on main and instructs the user to create a feature or docs branch first. This closes the recurring accidental direct-main commit failure mode and supports the upcoming deterministic ns slice runner.



## Latest completed implementation slice: deterministic ns slice runner

The deterministic `./ns` slice runner is now implemented and documented as the next workflow automation layer. It supports bounded multi-step execution, advances automatically after PASS states, stops on FAIL states, and records the intended direction toward less copy-and-paste and fewer non-semantic workflow failures.


## Latest completed implementation slice: idempotent PR create guard

PR #297 added an idempotent PR creation guard. The finalization path now treats already-completed documentation branches as a completed no-op instead of attempting to create an empty PR. This removes a recurring false FAIL in the release and finalization cycle.
