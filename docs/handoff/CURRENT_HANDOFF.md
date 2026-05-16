Current version: 0.3.18

# Current Handoff

Status-date: 2026-05-16
Project: agentic-project-kit
Branch: feature/cockpit-action-selection-ux
Base branch: main

## Current Goal

Current released version: 0.3.18
Current development slice: v0.3.19 Cockpit Action Selection UX

v0.3.18 is released and post-release verified with version DOI `10.5281/zenodo.20245754`. Zenodo concept DOI: `10.5281/zenodo.20101359`. The final post-DOI state cleanup is merged on main at `55e37dd Finalize state after v0.3.18 DOI metadata (#254)`.

The active v0.3.19 slice adds an inspect-only cockpit action selection view. `agentic-kit cockpit select` renders a numbered action list from the central cockpit action registry without executing actions. `./ns select` delegates to that command, and `./ns-menu` exposes it as a numbered entry without adding new shell execution logic.

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

Feature branch:

```text
feature/cockpit-action-selection-ux
```

Implemented in this branch:

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

Full pre-PR gates still need to be run after the documentation refresh:

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

Because state and handoff refreshes affect repository source-of-truth wording, `agentic-kit doc-mesh-audit` should be run before opening or merging the PR. `agentic-kit doc-lifecycle-audit` remains useful as a direct smoke check and is also covered by `agentic-kit doctor`.

## Current Branch Work

The v0.3.19 Cockpit Action Selection UX slice is implementation-complete at the feature-branch level. It should now receive full local gates, then a narrow PR.

## Next Safe Step

Next safe step: sync this branch locally, run full gates after the documentation refresh, inspect the diff, and open a PR if all gates pass.
