# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/post-release-v025
Current version: 0.2.5

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, and deterministic document-quality heuristics.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4: added Zenodo-backed citation and archival metadata.
- v0.2.5: released the post-v0.2.4 repository-health and visibility work, including project contracts, profiles, policy packs, policy-pack doctor checks, documentation coverage drift checks, machine-readable task gates, and the semantic quality boundary.

v0.2.5 release evidence:

- PR #33 improved release visibility and README positioning for v0.2.5.
- PR #34 raised package and citation metadata to 0.2.5 and finalized the changelog heading.
- Tag v0.2.5 was pushed.
- GitHub Release v0.2.5 was created successfully by the Release workflow.
- Release assets were attached: `agentic_project_kit-0.2.5-py3-none-any.whl` and `agentic_project_kit-0.2.5.tar.gz`.
- `agentic-kit release-check --version 0.2.5` now fails as expected because the local tag, remote tag, and GitHub release already exist. That command is a pre-release gate, not a post-release success check.

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

Project-level state documentation is machine-checkable:

- agentic-kit check-docs checks the state gate documents.
- docs/architecture/ARCHITECTURE_CONTRACT.md is a required state gate document.
- docs/DOCUMENTATION_COVERAGE.yaml is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, and semantic quality boundary language remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own machine-readable task gate configuration.

Project health diagnostics are CLI-supported:

- agentic-kit doctor checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift.
- agentic-kit check-docs checks documentation coverage and deterministic document-quality heuristics.
- agentic-kit release-plan and agentic-kit release-check support release-state validation before maintainer-owned tagging and publication.

Current post-release branch work:

- STATUS.md marks v0.2.5 as released.
- CURRENT_HANDOFF.md marks v0.2.5 as released.
- README.md and CITATION.cff are not changed on this branch because the v0.2.5 version-specific Zenodo DOI has not been verified in this branch.
- No tag, release artifact, publication artifact, merge, or direct main write is part of this branch.

Latest validated release gates:

- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.5
- agentic-kit release-check --version 0.2.5 -> PASS before tag creation
- python -m build -> successfully built the 0.2.5 wheel and sdist
- twine check dist/* -> passed for the 0.2.5 wheel and sdist
- Release workflow for v0.2.5 -> success
- gh release view v0.2.5 -> release exists with wheel and sdist assets

## Current Goal

Update the repository state files after the v0.2.5 GitHub release so future agents no longer treat the release as pending.

## Current Blockers

- Local gate must be rerun after the post-release status updates on docs/post-release-v025.
- The v0.2.5 version-specific Zenodo DOI has not been verified in this branch. Do not add it to README.md or CITATION.cff by guessing.
- Maintainer approval is required before merge, publication changes, or GitHub repository setting changes.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
gh release view v0.2.5

Expected note:

agentic-kit release-check --version 0.2.5 is expected to fail after publication because it verifies that the target tag and GitHub release are still unused.

## Next Safe Step

Pull docs/post-release-v025 locally and run the standard local gate. If it passes, open a PR for the post-release state update. After that, verify Zenodo separately and only then decide whether README.md or CITATION.cff need a DOI follow-up.
