# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/add-zenodo-doi
Current version: 0.2.4

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, handoff files, release-state validation, citation metadata, and Zenodo-backed archival.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4: added Zenodo-backed citation and archival metadata.

v0.2.4 release evidence:

- Git tag v0.2.4 was pushed.
- GitHub Release v0.2.4 exists.
- Release workflow for v0.2.4 passed.
- CI workflow for v0.2.4 passed.
- Release assets are attached: wheel and source distribution.
- Zenodo archived v0.2.4.
- Zenodo all-versions DOI: 10.5281/zenodo.20101359.
- Zenodo v0.2.4 version DOI: 10.5281/zenodo.20101360.

Citation and archival state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- CITATION.cff provides citation metadata and the all-versions Zenodo DOI.
- .zenodo.json provides Zenodo deposit metadata.
- README.md includes the Zenodo DOI badge and citation guidance.

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

Current validated gates before this branch:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- python -m build -> built wheel and source distribution for v0.2.4
- twine check dist/* -> passed for v0.2.4 artifacts
- GitHub Release workflow for v0.2.4 -> passed
- GitHub CI workflow for v0.2.4 -> passed
- Zenodo archival for v0.2.4 -> completed

## Current Goal

Record the assigned Zenodo DOI in README.md, CITATION.cff, STATUS, and CURRENT_HANDOFF.

## Current Blockers

- None known.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs

## Next Safe Step

Pull docs/add-zenodo-doi locally and run the local gate. If it passes, merge the branch. After merge, the next functional development block should likely be agentic-kit doctor.
