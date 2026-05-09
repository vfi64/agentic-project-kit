# Project Status

Status-date: 2026-05-09
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/documentation-state-gates
Current version: 0.2.2

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, and handoff files.

The project itself also needs a current state layer so work can be continued safely in a new chat or by another agent without relying on memory.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.

Current validated gates:

- python -m pytest -q -> 11 passed
- ruff check . -> passed
- python -m build -> wheel and sdist built
- twine check dist/* -> passed
- TestPyPI upload for 0.2.2 -> passed
- TestPyPI installation of 0.2.2 -> passed
- Generated project smoke test with --kit-source testpypi -> passed

## Current Goal

Add project-level documentation state gates so repository state, handoff information, and required evidence stay current.

## Current Blockers

- Project-level docs were missing before this branch:
  - docs/STATUS.md
  - docs/TEST_GATES.md
  - docs/handoff/CURRENT_HANDOFF.md
- Generated project templates already contain similar files, but the root project itself did not.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
python -m build
twine check dist/*

## Next Safe Step

Create project-level docs, add checks/tests if useful, run all gates, commit the documentation-state update, and open a pull request into main.
