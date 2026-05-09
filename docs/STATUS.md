# Project Status

Status-date: 2026-05-09
Project: agentic-project-kit
Primary branch: main
Current work branch: main
Current version: 0.2.2

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, and handoff files.

The project itself now has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.

Project-level state documentation is present on main:

- docs/STATUS.md
- docs/TEST_GATES.md
- docs/handoff/CURRENT_HANDOFF.md

Current validated gates:

- python -m pytest -q -> 11 passed
- ruff check . -> passed
- python -m build -> wheel and sdist built
- twine check dist/* -> passed
- TestPyPI upload for 0.2.2 -> passed
- TestPyPI installation of 0.2.2 -> passed
- Generated project smoke test with --kit-source testpypi -> passed

## Current Goal

Keep repository state, handoff information, and required evidence current before starting the next functional feature branch.

## Current Blockers

- None known.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
python -m build
twine check dist/*

## Next Safe Step

Start the next functional change from main on a fresh feature branch. The most useful next feature is to make the documentation state gates machine-checkable through the CLI and tests.
