# Test Gates

Status-date: 2026-05-09
Project: agentic-project-kit

## Purpose

This file defines the required evidence before claiming that a change is complete.

The repository must not rely on memory, chat history, or informal claims. Relevant checks must be run and reported explicitly.

## Gate Matrix

| Change type | Required evidence |
|---|---|
| Documentation only | git diff, content review, and if possible agentic-kit check-docs on a generated project |
| Python code | python -m pytest -q and ruff check . |
| CLI behavior | Unit tests plus CLI smoke command |
| Generator behavior | Generator test plus generated-project file inspection |
| GitHub workflow change | Local workflow review plus GitHub Actions run |
| Packaging/release change | python -m build, twine check dist/*, release workflow result |
| Release planning change | Unit tests plus agentic-kit release-plan CLI smoke command |
| Release state validation change | Unit tests plus agentic-kit release-check CLI smoke command |
| Project health check change | Unit tests plus agentic-kit doctor CLI smoke command |
| Citation metadata health change | Unit tests plus agentic-kit doctor CLI smoke command |
| TestPyPI validation | TestPyPI upload, fresh venv install, CLI smoke command |
| Handoff/state change | Update docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md |

## Standard Local Gate

Run these commands:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs

## Doctor Gate

Run this command when changing project health diagnostics:

    agentic-kit doctor

Expected evidence: required project files, documentation/TODO gates, version drift, and citation metadata drift are reported as PASS, WARN, or FAIL with an overall status.

Citation metadata is optional for young or generated projects. Missing DOI/Zenodo metadata must produce WARN, not FAIL. Once any DOI/Zenodo metadata is present, partial or inconsistent metadata must produce FAIL.

## Packaging Gate

Run these commands:

    rm -rf dist build
    find . -maxdepth 3 -name "*.egg-info" -type d -prune -exec rm -rf {} +
    python -m build
    twine check dist/*
    ls -lh dist/

## Release Gate

Plan first:

    agentic-kit release-plan

Validate release state before tagging:

    agentic-kit release-check --version <version>

Before tagging:

    git status --short
    git log --oneline -5
    git show HEAD:pyproject.toml | grep '^version'

After tagging:

    gh run list --workflow Release --limit 5
    gh run watch $(gh run list --workflow Release --limit 1 --json databaseId --jq '.[0].databaseId')
    gh release view <tag>

## Outcome Reporting

Use this shape:

    - Intended outcome:
    - Required evidence:
    - Outcome achieved: yes / no / partial
    - Changed files:
    - Tests run:
    - Tests not run:
    - Remaining risks:
    - Next safe step:

## Maintenance Rule

Whenever the current branch, version, release state, test status, or next safe step changes, update docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md.
