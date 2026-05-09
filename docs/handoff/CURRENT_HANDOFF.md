# Current Handoff

Status-date: 2026-05-09
Project: agentic-project-kit
Branch: main
Base branch: main
Current version: 0.2.2

## Current Goal

Keep repository state, handoff information, and required evidence current before starting the next functional feature branch.

## Current Repository State

The project has released version 0.2.2.

Important completed work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.2 was tagged, released on GitHub, uploaded to TestPyPI, installed from TestPyPI in a fresh virtual environment, and used to generate a test project.
- Project-level state documentation is present in docs/STATUS.md, docs/TEST_GATES.md, and docs/handoff/CURRENT_HANDOFF.md.
- PR #7 made project-level state documentation machine-checkable through agentic-kit check-docs.
- check-docs can run in the kit repository root without sentinel.yaml.
- PR #9 added agentic-kit release-plan for release preparation.
- release-plan includes local gates, package validation, version checks, local tag lookup, remote tag lookup, GitHub release lookup, and release verification commands.
- PR #11 added agentic-kit release-check for release state validation.
- PR #13 extended release-check and release-plan with remote release state validation.
- release-check validates semantic version shape, CHANGELOG version text, STATUS version text, CURRENT_HANDOFF version text, local tag availability, remote tag availability, and GitHub release availability.
- release-check treats unavailable remote/GitHub tooling as WARN, while existing local tags, remote tags, or GitHub releases are FAIL.
- release-check exits with code 1 when a required release-state check fails.

Current branch work:

- None on main.
- New functional work should start from main on a fresh feature branch.

## Source of Truth

Read in this order:

1. README.md
2. CHANGELOG.md
3. docs/STATUS.md
4. docs/TEST_GATES.md
5. docs/handoff/CURRENT_HANDOFF.md
6. src/agentic_project_kit/
7. tests/

## Required Local Gate

Run:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit release-plan
    agentic-kit release-check --version <target-version>

For package validation, also run:

    rm -rf dist build
    find . -maxdepth 3 -name "*.egg-info" -type d -prune -exec rm -rf {} +
    python -m build
    twine check dist/*
    ls -lh dist/

## Latest Known Evidence

Last known successful checks:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit release-plan -> passed
- agentic-kit release-check --version 0.2.3 -> failed as expected because state files are not prepared for 0.2.3; local tag, remote tag, and GitHub release are free
- agentic-kit release-check --version 0.2.2 -> failed as expected because local tag, remote tag, and GitHub release v0.2.2 already exist and CHANGELOG lacks the exact searched heading text
- python -m build -> passed before v0.2.2 release
- twine check dist/* -> passed before v0.2.2 release
- GitHub CI for v0.2.2 commit -> passed
- GitHub Release workflow for v0.2.2 tag -> passed
- TestPyPI upload of 0.2.2 -> passed
- TestPyPI install of 0.2.2 -> passed
- Generated project smoke test with --kit-source testpypi -> passed

## Current Open Work

- None.

## Next Safe Step

Start a new feature branch from main. Recommended next feature: prepare a real next release candidate by updating CHANGELOG, STATUS, CURRENT_HANDOFF, and version metadata consistently, then validate it with release-check before tagging.
