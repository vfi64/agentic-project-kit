Current version: 0.3.3

# Project Status

Status-date: 2026-05-13
Project: agentic-project-kit
Primary branch: main
Current work branch: release/prepare-v0.3.3

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, and workflow evidence capture.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions through v0.3.2 are complete. The current branch prepares v0.3.3 as a patch release for workflow usability and drift hardening.

Recent completed work since v0.3.2:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` so package-version drift is detected.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running local workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage for it.

v0.3.3 release scope:

- Package-version drift detection.
- `ns` / `next-step.py` workflow usability.
- Project-local workflow environment bootstrap.
- Explicit `FAILED` workflow-state handling.

Release discipline:

- Do not add a v0.3.3 version-specific DOI before the GitHub release exists and Zenodo has archived it.
- Use the Zenodo concept DOI `10.5281/zenodo.20101359` during release preparation.
- Run `agentic-kit post-release-check --version 0.3.3` only after the GitHub Release is published.

Project-level state documentation is present on main:

- .agentic/project.yaml
- sentinel.yaml
- .agentic/todo.yaml
- docs/STATUS.md
- docs/TEST_GATES.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/architecture/ARCHITECTURE_CONTRACT.md
- docs/architecture/AGENTIC_CODING_RESEARCH_INPUTS.md
- docs/architecture/references.bib
- docs/DOCUMENTATION_COVERAGE.yaml
- docs/WORKFLOW_OUTPUT_CYCLE.md

Project-level state documentation is machine-checkable:

- `agentic-kit check-docs` checks the state gate documents.
- `docs/architecture/ARCHITECTURE_CONTRACT.md` is a required state gate document.
- `docs/DOCUMENTATION_COVERAGE.yaml` is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, semantic quality boundary language, next-step workflow behavior, environment bootstrap, and `FAILED` handling remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own machine-readable task gate configuration.

Project health diagnostics are CLI-supported:

- `agentic-kit doctor` checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift including package `__version__` drift.
- `agentic-kit check-docs` checks documentation coverage and deterministic document-quality heuristics.
- `agentic-kit release-plan` and `agentic-kit release-check` support release-state validation before maintainer-owned tagging and publication.
- `agentic-kit post-release-check` verifies GitHub release and Zenodo archive state after publication.

## Current Goal

Prepare the v0.3.3 release metadata and state files, then validate the release candidate before tagging.

## Current Blockers

- Local release-preparation gates must pass on `release/prepare-v0.3.3`.
- Maintainer approval is required before merge, tag creation, GitHub release publication, or post-release DOI metadata changes.

## Live Status Commands

Run:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit release-plan --version 0.3.3
agentic-kit release-check --version 0.3.3
```

Expected release-check state before tagging:

- pyproject, CHANGELOG, README, CITATION, STATUS, and CURRENT_HANDOFF mention 0.3.3.
- Local tag `v0.3.3`, remote tag `v0.3.3`, and GitHub Release `v0.3.3` are absent.

## Next Safe Step

Run the standard local gate plus `agentic-kit release-check --version 0.3.3` on `release/prepare-v0.3.3`. If green, open and merge the release-preparation PR. After merge, tag `v0.3.3` and wait for the GitHub Release workflow before running `agentic-kit post-release-check --version 0.3.3`.
