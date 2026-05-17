Current version: 0.3.21

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
