# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/release-v025
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

Current v0.2.5 release-preparation branch includes:

- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks and Remote Work Authorization.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and machine-readable task gates.
- PR #31 activated policy-pack checks in doctor.
- PR #32 defined the semantic quality boundary and added deterministic document-quality heuristics.
- PR #33 improved release visibility and README positioning for v0.2.5.
- This branch raises package and citation metadata to 0.2.5 and finalizes the changelog heading.

Project-level state documentation is present on the release-preparation branch:

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

Current release branch work:

- pyproject.toml version is set to 0.2.5.
- CITATION.cff version is set to 0.2.5.
- CHANGELOG.md has a v0.2.5 section.
- README.md current status describes v0.2.5 as a release candidate and avoids promising a version-specific Zenodo DOI before publication.
- STATUS.md and CURRENT_HANDOFF.md point to feature/release-v025.
- No tag, release artifact, publication artifact, merge, or direct main write is part of this branch.

Latest validated local gates before this branch:

- git branch --show-current -> main
- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.4

## Current Goal

Prepare the v0.2.5 release metadata and state files so a maintainer can review, merge, and then perform the separate tag and publication steps.

## Current Blockers

- Local gate must be rerun after the release-preparation updates on feature/release-v025.
- agentic-kit release-plan --version 0.2.5 and agentic-kit release-check --version 0.2.5 should be run before opening or merging the release PR.
- Maintainer approval is required before merge, tag creation, release artifacts, publication artifacts, or GitHub repository setting changes.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit release-plan --version 0.2.5
agentic-kit release-check --version 0.2.5

## Next Safe Step

Pull feature/release-v025 locally and run the standard local gate plus release-plan and release-check for 0.2.5. If they pass, open a PR for the v0.2.5 release-preparation changes. Do not tag or publish without maintainer approval.
