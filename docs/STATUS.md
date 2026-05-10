# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/release-visibility-v025
Current version: 0.2.4

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

Merged post-v0.2.4 work on main includes:

- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks and Remote Work Authorization.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and machine-readable task gates.
- PR #31 activated policy-pack checks in doctor.
- PR #32 defined the semantic quality boundary and added deterministic document-quality heuristics.

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

Current release visibility branch work:

- CHANGELOG.md has an Unreleased section preparing the v0.2.5 release narrative without raising the package version.
- README.md now foregrounds the purpose, the difference from a simple skeleton generator, the doctor/check-docs workflow, project scope boundary, and GitHub discovery suggestions.
- STATUS.md and CURRENT_HANDOFF.md now point to feature/release-visibility-v025 instead of the old semantic-boundary branch.
- No tag, release artifact, publication artifact, version bump, merge, or direct main write is part of this branch.

Latest validated local gates at branch creation:

- git branch --show-current -> feature/release-visibility-v025
- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.4

## Current Goal

Prepare a small release-visibility and positioning cut for a maintainer-owned v0.2.5 release decision. The branch should make the post-v0.2.4 health-check, policy-pack, documentation-coverage, machine-readable task-gate, and semantic-boundary work visible without performing release-owned actions.

## Current Blockers

- Local gate must be rerun after the documentation updates on feature/release-visibility-v025.
- Maintainer approval is required before merge, version bump, tag creation, release artifacts, publication artifacts, or GitHub repository setting changes.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor

Optional release-preparation smoke command before a later release branch or release PR:

agentic-kit release-plan --version 0.2.5

## Next Safe Step

Pull feature/release-visibility-v025 locally and run the standard local gate. If it passes, open a PR for README, CHANGELOG, STATUS, and handoff visibility updates. Do not merge or release without maintainer approval.
