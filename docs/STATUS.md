# Project Status

Status-date: 2026-05-09
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/zenodo-metadata
Current version: 0.2.3

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, handoff files, release-state validation, and citation/archiving metadata.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.

v0.2.3 release evidence:

- Git tag v0.2.3 was pushed.
- GitHub Release v0.2.3 exists.
- Release workflow for v0.2.3 passed.
- CI workflow for v0.2.3 passed.
- Release assets are attached: wheel and source distribution.

Zenodo preparation:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- v0.2.3 was released before Zenodo integration was enabled, so the next release is expected to be the first automatically archived Zenodo release.
- CITATION.cff is being added for citation metadata.
- .zenodo.json is being added for Zenodo deposit metadata.
- README documents the citation and archiving setup without a DOI badge yet.

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

Current validated gates before this Zenodo metadata branch:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit release-plan -> target v0.2.3 before tagging
- agentic-kit release-check --version 0.2.3 -> PASS before tagging
- python -m build -> built wheel and source distribution for v0.2.3
- twine check dist/* -> passed for v0.2.3 artifacts
- GitHub Release workflow for v0.2.3 -> passed
- GitHub CI workflow for v0.2.3 -> passed

## Current Goal

Add citation and Zenodo metadata, then validate the branch locally before merging. The next release after this branch should be used to trigger Zenodo archival and DOI assignment.

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

For package validation, also run:

python -m build
twine check dist/*

## Next Safe Step

Pull feature/zenodo-metadata locally and run the local gate. If it passes, merge the branch. Then prepare the next small release to trigger Zenodo archival.
