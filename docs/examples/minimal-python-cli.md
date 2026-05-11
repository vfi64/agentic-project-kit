# Minimal Python CLI Demo

## Purpose

This example shows how `agentic-project-kit` turns a new Python CLI idea into a repository with explicit project state, agent instructions, documentation gates, task gates, and local health checks.

## Create the project

Run:

    agentic-kit init demo-cli --type python-cli --description "Small demo CLI" --license MIT --github-actions --pre-commit --agent-docs --logging-evidence

This creates a new `demo-cli` directory with a Python package skeleton and agentic repository governance files.

## Inspect generated state

The generated project includes `.agentic/project.yaml`, `.agentic/todo.yaml`, `AGENTS.md`, `docs/STATUS.md`, `docs/TEST_GATES.md`, `docs/handoff/CURRENT_HANDOFF.md`, `sentinel.yaml`, and `.github/workflows/ci.yml`.

These files make the repository state explicit for future human and AI contributors.

## Run the local gate

Run inside the generated project:

    cd demo-cli
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor

## What this demonstrates

The generated repository does not rely on chat memory alone. It gives future contributors stable files for project identity, agent instructions, current status, handoff, test gates, task tracking, documentation drift checks, and local health diagnostics.

This helps reduce context drift when a human and an AI assistant work across multiple sessions.

## Boundary

Passing these checks does not prove semantic perfection. The checks verify known structural and documentation requirements. They are useful gates, not a substitute for human review.
