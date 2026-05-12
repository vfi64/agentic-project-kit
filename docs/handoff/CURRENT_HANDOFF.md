Current version: 0.3.0

# Current Handoff

Status-date: 2026-05-12
Project: agentic-project-kit
Branch: feature/declarative-workflow-runner
Base branch: main

## Current Goal

Add a declarative, allowlisted local workflow runner that reduces manual terminal Copy-and-Paste while preserving bounded evidence, state safety, documentation coverage, and the existing `agentic-kit check-docs` / `agentic-kit doctor` gates.

## Current Repository State

The project has released version 0.3.0. The current post-release workflow work is focused on reducing manual terminal Copy-and-Paste while keeping local execution bounded and auditable.

Recent completed workflow work:

- PR #122 added `tools/next-step.py` as the initial TEST/UPLOAD/CLEANUP evidence cycle.
- PR #123 added `IDLE` as the safe no-op state so accidental `python tools/next-step.py` calls do not start a new run.
- PR #124 documented `done` and `d` as the terminal acknowledgement wording.

Current implementation direction:

- Prefer a declarative workflow request file over executable ad-hoc local scripts.
- Use `.agentic/current_work.yaml` for the current local task.
- Use `tools/workflow_runner.py` as the allowlisted local runner.
- Keep the old TEST/UPLOAD/CLEANUP states compatible while introducing REQUESTED/RUNNING/UPLOADED/FAILED.
- Never use `shell=True` for workflow steps.
- Preserve evidence on FAILED and do not automatically cleanup failed runs.

Release and governance context:

- The project remains governed by `.agentic/project.yaml`, `sentinel.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and the architecture contract.
- Active profiles include generic Git repository, Markdown docs, Python CLI, Git/GitHub, and release-managed workflows.
- Active policy packs include solo-maintainer, agentic-development, release-managed, and documentation-governed.
- `agentic-kit doctor` must continue to report policy-pack checks and policy packs.
- `agentic-kit check-docs` must continue to enforce documentation coverage.
- The post-release Zenodo workflow remains active; use `agentic-kit post-release-check --version X.Y.Z` before updating DOI metadata.

Planned CLI follow-up to propose at a suitable point:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

Do not let `tools/next-step.py` grow indefinitely. Once the declarative workflow runner is stable, move the workflow operations into first-class `agentic-kit workflow ...` commands.

## Source of Truth

Read in this order:

1. .agentic/project.yaml
2. sentinel.yaml
3. docs/architecture/ARCHITECTURE_CONTRACT.md
4. docs/DOCUMENTATION_COVERAGE.yaml
5. AGENTS.md
6. README.md
7. docs/STATUS.md
8. docs/TEST_GATES.md
9. docs/WORKFLOW_OUTPUT_CYCLE.md
10. docs/handoff/CURRENT_HANDOFF.md
11. src/agentic_project_kit/
12. tests/

## Required Local Gate

For the declarative workflow runner branch, run targeted syntax/tests first, then full gates:

```bash
python -m py_compile tools/next-step.py tools/workflow_runner.py tests/test_workflow_state.py
python -m pytest tests/test_workflow_state.py -q
ruff check tools/next-step.py tools/workflow_runner.py tests/test_workflow_state.py
./tools/screen_control_gate.sh
```

The full screen-control gate must include:

```bash
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

## Current v0.3.0 DOI Work

Zenodo shows the v0.3.0 version DOI as `10.5281/zenodo.20140467`. A DOI metadata patch should update `CITATION.cff`, `CHANGELOG.md`, and, if done carefully, README/status/handoff visibility files.

## Terminal Workflow Rule

When no terminal output is needed, the user may reply `done` or the short form `d`. When terminal output is needed, ask for a bounded Begin/End Copy Terminal block.

## Next

- Pull the latest `feature/declarative-workflow-runner` branch.
- Run the targeted syntax/test/ruff checks.
- Run `./tools/screen_control_gate.sh`.
- If gates pass, inspect PR #126 and decide whether to merge or split the large handoff/documentation change.
- After this first declarative runner lands, do not immediately remove TEST/UPLOAD/CLEANUP; keep compatibility until the new path has been smoke-tested.

## Next Safe Step

Run the required local gate on `feature/declarative-workflow-runner`. If green, test the declarative path with `.agentic/current_work.yaml` and `REQUESTED` in a controlled smoke run before using it as the default workflow.

