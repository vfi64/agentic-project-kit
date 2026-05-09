# Project Status

Status-date: 2026-05-09
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/prepare-v0.2.3-release
Current version: 0.2.3

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, and handoff files.

The project itself now has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.

Prepared release candidate:

- v0.2.3: release-state validation for local tags, remote tags, and GitHub releases.

Project-level state documentation is present on main:

- docs/STATUS.md
- docs/TEST_GATES.md
- docs/handoff/CURRENT_HANDOFF.md

Project-level state documentation is machine-checkable:

- agentic-kit check-docs checks the state gate documents.
- sentinel.yaml is optional for check-docs, so the kit repository root can be checked directly.
- stale handoff markers are detected in docs/handoff/CURRENT_HANDOFF.md.

Release preparation is CLI-supported:

- agentic-kit release-plan prints a release preparation checklist for the target version.
- The plan includes local gates, package validation, state-file checks, local tag lookup, remote tag lookup, GitHub release lookup, and release verification commands.
- The plan checks for an existing target tag and release before suggesting tag creation.

Release state validation is CLI-supported:

- agentic-kit release-check validates release state for a target version.
- It checks semantic version shape, CHANGELOG version text, STATUS version text, CURRENT_HANDOFF version text, local tag availability, remote tag availability, and GitHub release availability.
- It treats unavailable remote/GitHub tooling as WARN, while existing local tags, remote tags, or GitHub releases are FAIL.
- It exits with code 1 when a required release-state check fails.

Current validated gates before this release-preparation branch:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit release-plan -> passed
- agentic-kit release-check --version 0.2.3 -> failed as expected because state files were not yet prepared for 0.2.3; local tag, remote tag, and GitHub release were free
- agentic-kit release-check --version 0.2.2 -> failed as expected because local tag, remote tag, and GitHub release v0.2.2 already exist and CHANGELOG lacks the exact searched heading text
- python -m build -> wheel and sdist built before v0.2.2 release
- twine check dist/* -> passed before v0.2.2 release
- TestPyPI upload for 0.2.2 -> passed
- TestPyPI installation of 0.2.2 -> passed
- Generated project smoke test with --kit-source testpypi -> passed

## Current Goal

Prepare version 0.2.3 consistently across package metadata, CHANGELOG, STATUS, and CURRENT_HANDOFF, then validate the release state before tagging.

## Current Blockers

- None known.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit release-plan
agentic-kit release-check --version 0.2.3

For package validation, also run:

python -m build
twine check dist/*

## Next Safe Step

Pull feature/prepare-v0.2.3-release locally, run the full local gate, and confirm that agentic-kit release-check --version 0.2.3 passes before merging and tagging.
