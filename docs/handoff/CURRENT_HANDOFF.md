Current version: 0.3.22

# Current Handoff

Status-date: 2026-05-16
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Current released version: 0.3.19
Current completed slice: GUI Tk setup documentation

v0.3.19 is released and post-release verified with version DOI `10.5281/zenodo.20246121`. Zenodo concept DOI: `10.5281/zenodo.20101359`. The v0.3.19 DOI metadata is recorded on main via PR #259 after `agentic-kit post-release-check --version 0.3.19` passed. The post-release Zenodo verification path remains covered by `agentic-kit post-release-check`.

PR #255 added an inspect-only cockpit action selection view. `agentic-kit cockpit select` renders a numbered action list from the central cockpit action registry without executing actions. `./ns select` delegates to that command, and `./ns-menu` exposes it as a numbered entry without adding new shell execution logic.

## Current Repository State

Current main head before this feature branch:

```text
55e37dd Finalize state after v0.3.18 DOI metadata (#254)
d86491b Record v0.3.18 DOI metadata (#253)
da14f8b tag: v0.3.18, Prepare v0.3.18 release metadata (#252)
9f05474 Refresh state after ns-menu cockpit JSON consumer (#251)
844501e Expose cockpit JSON inventory in ns-menu (#250)
85bd859 Finalize state after v0.3.17 DOI metadata (#249)
76d4af8 Record v0.3.17 DOI metadata (#248)
1e4bae9 tag: v0.3.17, Prepare v0.3.17 release metadata (#247)
```

Merged PR:

```text
#255 Add cockpit action selection UX
```

Implemented by PR #255:

- `render_action_selection(...)` in the cockpit domain layer.
- `agentic-kit cockpit select` as an inspect-only numbered action-selection command.
- `./ns select` as a thin repo-local adapter.
- `./ns-menu` entry `15) ./ns select`.
- Regression coverage for the selection renderer, CLI command, and `ns` / `ns-menu` adapter wiring.
- CHANGELOG, STATUS, and handoff refresh for the unreleased v0.3.19 slice.

## Safety Contract

The action registry remains the source of truth.

`cockpit select` and `./ns select` are inspect-only. They must not execute actions and must not introduce a second execution path.

`cockpit run` remains the execution path. Read-only actions may run through the existing safety logic. Bounded actions remain blocked unless `cockpit run` receives an explicit allow flag. Destructive actions remain blocked.

No release, tag, merge, push, cleanup, or remote mutation actions are added by this slice.

## Latest verified local gates for this slice

The user locally reported `d` after the sync/test blocks for:

- `agentic-kit cockpit select`
- `./ns select`
- targeted tests: `tests/test_cockpit.py`, `tests/test_repo_ns_entrypoint.py`, `tests/test_cli.py`
- `ruff check .`

A later full local gate run showed `221 passed` and `ruff check .` passed. The documentation gates then failed because the STATUS/HANDOFF refresh removed deterministic documentation coverage phrases. This branch now restores the required coverage phrases for policy packs, policy-pack checks, documentation coverage, post-release Zenodo verification, `agentic-kit post-release-check`, and Pattern Advisor coverage in STATUS.

Full pre-PR gates still need to be rerun after this repair:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
.venv/bin/agentic-kit doc-lifecycle-audit
```

## Workflow State

Expected state:

- `.agentic/workflow_state` = `IDLE`
- `.agentic/current_work.yaml` may remain present with `state: READY`
- no active workflow request
- no remaining `temp/workflow-evidence-*` branches from recent slices

Normal `ns` behavior in `IDLE` plus `READY` is a no-op. A workflow starts only by explicit request.

## Source of Truth

Read in this order:

1. `.agentic/project.yaml`
2. `sentinel.yaml`
3. `docs/architecture/ARCHITECTURE_CONTRACT.md`
4. `docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md`
5. `docs/architecture/LOCAL_COCKPIT_FOUNDATION.md`
6. `docs/DOCUMENTATION_COVERAGE.yaml`
7. `AGENTS.md`
8. `README.md`
9. `docs/STATUS.md`
10. `docs/TEST_GATES.md`
11. `docs/WORKFLOW_OUTPUT_CYCLE.md`
12. `docs/handoff/CURRENT_HANDOFF.md`
13. `src/agentic_project_kit/cockpit.py`
14. `src/agentic_project_kit/cli_commands/cockpit.py`
15. `ns`
16. `ns-menu`
17. `tests/test_cockpit.py`
18. `tests/test_repo_ns_entrypoint.py`
19. `tests/`

## Required Local Gate

For this branch, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
.venv/bin/agentic-kit doc-lifecycle-audit
```

Because state and handoff refreshes affect repository source-of-truth wording and documentation coverage, `agentic-kit doc-mesh-audit` should be run before opening or merging the PR. `agentic-kit doc-lifecycle-audit` remains useful as a direct smoke check and is also covered by `agentic-kit doctor`.

`agentic-kit doctor` must continue to report active policy packs and policy-pack checks for the repository contract.

## Current Branch Work

The v0.3.19 Cockpit Action Selection UX slice is released, post-release verified, and DOI metadata is recorded on main.

## Next Safe Step

Current slice: document GUI i18n, localized tooltips, and Instruction Bridge roadmap. This planning slice records a future i18n system for GUI labels/help/tooltips and a safe human-to-terminal-or-GUI-to-LLM instruction file mechanism. Next safe step: run documentation gates, open the roadmap PR, and then choose the first implementation slice.

## Latest completed implementation slice: PR hygiene guard

PR #277 is merged on `main`. It added a read-only PR hygiene model, CLI command `agentic-kit pr-hygiene`, `--json` output, cockpit registry action `audit.pr-hygiene`, and regression tests. The command intentionally performs no GitHub or Git mutations.

Important local workflow note: prefer `./ns` over bare `ns`, and prefer `.venv/bin/python -m pytest`, `.venv/bin/ruff`, and `PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli ...` over bare `python`, `ruff`, or `agentic-kit`.

Next safe step: choose the next implementation slice. Good candidates are planning-doc scaffolding, GUI i18n foundation, or the Instruction Bridge.

## Latest completed implementation slice: planning document scaffold

The merged planning-doc scaffold slice added `agentic-kit scaffold planning-doc`, lifecycle-valid planning document rendering, overwrite protection, CLI tests, and the terminal result marker rule in `AGENTS.md`.

Important local workflow note: do not repurpose `.agentic/current_work.yaml` as a free-form scratch file; it is covered by workflow tests and documentation coverage. Use branch-specific docs or temporary files under `tmp/` for transient coordination.

Next safe step: choose the next implementation slice. Good candidates are GUI i18n foundation, localized tooltips, or Instruction Bridge.

## Latest completed implementation slice: no-copy ns workflow control

Merged PR: #281

Implemented on main: governed planning document `docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md`, `./ns dev` for local feature gates, and a protective `./ns go` guard for dirty feature branches when `.agentic/current_work.yaml` includes `git_pull_ff_only`.

Important workflow note: prefer `./ns dev` for active feature-branch local gates. Use `./ns go` for the governed workflow path only when the branch state is clean and suitable for the default workflow. Long chat-to-terminal blocks remain fallback only and must start with three separator lines and end with PASS/FAIL markers.

Next safe step: choose the next GUI-compatible cockpit/i18n or instruction-bridge implementation slice.

## Latest completed implementation slice: ns up safety hardening

Merged PR: #285

The ./ns up PR completion workflow is now hardened for safer no-copy operation. It refuses main or dirty-branch use, checks mergeability before merge, updates main only after a successful merge, uses portable separator printing, and remains compatible with the future GUI Cockpit action model.

Next safe step: choose the next GUI-compatible cockpit/i18n or instruction-bridge implementation slice.

## Latest completed release slice: v0.3.21 DOI metadata

Merged release DOI metadata for v0.3.21.

Verified state:
- GitHub release v0.3.21 exists.
- Zenodo concept DOI: 10.5281/zenodo.20101359.
- Zenodo version DOI for v0.3.21: 10.5281/zenodo.20258057.
- `./ns release-verify 0.3.21` passes.

## Latest completed implementation slice: deterministic release cycle hardening

Merged PR: #293

The release workflow has been hardened against recurring deterministic failures. The important fixes are: stale dist artifacts are removed before release builds, publish waits for the asynchronous GitHub Release workflow instead of failing immediately, completed releases are verified through ./ns release-verify VERSION, and repeated release checks should no longer treat an already published version as a normal release-gate target.

Next priority: continue reducing repeated workflow friction by making already-completed release/finalization states idempotent rather than producing artificial FAIL results.

## Latest completed implementation slice: ns up idempotence hardening

Merged PR: #295

`./ns up` now handles two recurring workflow edge cases more deterministically: pending checks are waited on instead of causing an immediate false failure, and already merged PRs are accepted as an idempotent completion state.

## Latest completed implementation slice: ns up no-op branch idempotence

Merged PR: #297

`./ns up` now handles no-op branches idempotently: if no PR exists and the branch has no commits ahead of main, the command reports a clean completion state instead of failing. This is part of the deterministic cleanup of recurring workflow false failures.



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

Merged slice: no direct main commit guard.

The ./ns workflow now includes a commit-guard helper that prevents accidental direct commits and PR attempts from main. If invoked on main, it stops with an instructional failure instead of allowing a non-PR direct-main path. This is part of the current standard-error cleanup before larger GUI/Cockpit work.



## Latest completed implementation slice: deterministic ns slice runner

The deterministic `./ns` slice runner is now implemented and documented as the next workflow automation layer. It supports bounded multi-step execution, advances automatically after PASS states, stops on FAIL states, and records the intended direction toward less copy-and-paste and fewer non-semantic workflow failures.


## Latest completed implementation slice: idempotent PR create guard

The workflow now avoids failing when a finalization branch contains no commits beyond main because the intended state is already present. Treat this as a completed idempotent state, not as an error requiring another PR.

## Latest completed implementation slice: idempotent finalization branch guard command

`./ns finalize-guard <branch> [marker-text]` is now available to inspect finalization branches before attempting PR creation or cleanup. Use it when a docs finalization branch may already be merged, superseded, conflicting, or effectively represented on main. This is part of the standard-error cleanup path before larger GUI/Cockpit work.


## Latest completed implementation slice: safe diagnostic cleanup guard

The workflow now includes a safe cleanup path for diagnostic evidence files. Use it before PR completion when temporary reports or copied evidence files appear in the working tree. This prevents accidental tracked deletions and avoids another recurring non-semantic FAIL state.

## Latest completed release slice: v0.3.22 DOI metadata

Completed release state:

- v0.3.22 is published.
- GitHub release v0.3.22 exists.
- Zenodo concept DOI remains 10.5281/zenodo.20101359.
- Zenodo version DOI for v0.3.22: 10.5281/zenodo.20258186.
- `./ns release-verify 0.3.22` passes.

v0.3.23 control workflow consolidation is complete and merged on main. The important completed fixes are: shared `control_state` model, stop-on-fail Python slice-runner core, documented workflow control contract, target-state-aware `./ns slice-runner`, early-stop `./ns release-gate` when release metadata is missing, and automated `./ns release-prep` metadata updates for pyproject, package `__version__`, CITATION, CHANGELOG, README, STATUS, and CURRENT_HANDOFF. Next safe direction: use the new control model to harden dirty-evidence cleanup, finalize-guard machine-readable outcomes, and stale PR cleanup classification before any GUI/Cockpit expansion.

Evidence-cleanup guard is merged on main via PR #316. `./ns clean-evidence` is available and `./ns up` now gives a concrete repair hint for workflow-evidence dirtiness. Next safe standard-error hardening target: make `./ns finalize-guard` return clear machine-readable outcomes such as PASS_ALREADY_ON_MAIN, PASS_NOOP_BRANCH, PASS_SUPERSEDED, FAIL_CONFLICT_RELEVANT, and FAIL_NEEDS_HUMAN_REVIEW.

Finalize-guard outcome classification is merged on main via PR #318. ./ns finalize-guard now reports machine-readable target states: PASS_ALREADY_ON_MAIN, PASS_NOOP_BRANCH, PASS_SUPERSEDED, PASS_NEEDS_PR, FAIL_CONFLICT_RELEVANT, and FAIL_NEEDS_HUMAN_REVIEW. Next safe standard-error hardening target: classify stale open PRs deterministically before any GUI/Cockpit expansion.
