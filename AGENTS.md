# Agent Instructions

This repository uses explicit project-state and architecture governance. Do not rely on chat history or memory as the source of truth.

## Required Reading Order

Before making non-trivial changes, read these files in order:

1. `docs/architecture/ARCHITECTURE_CONTRACT.md`
2. `docs/STATUS.md`
3. `docs/TEST_GATES.md`
4. `docs/handoff/CURRENT_HANDOFF.md`
5. relevant source and test files

## Architecture Contract Rule

`docs/architecture/ARCHITECTURE_CONTRACT.md` is a required project gate document.

You must check it before changes that affect any of the following:

- project purpose or product boundary;
- CLI command behavior;
- generated project structure;
- profiles or policy packs;
- `doctor`, `check-docs`, `check-todo`, release checks, or other gates;
- repository state files or handoff conventions;
- agent instructions, PR templates, evidence staging, or review workflow;
- automation boundaries, GitHub integration, or future multiuser assumptions.

If a change conflicts with the architecture contract, do not silently implement it. Instead:

1. state the conflict;
2. propose either a smaller implementation or an architecture-contract update;
3. make the contract update explicit and reviewable.

## Responsibility Split

Use this responsibility model from the architecture contract:

```text
LLM / coding agent      -> propose, explain, draft, inspect, and prepare changes
agentic-kit doctor      -> check contracts, drift, evidence, gates, and repository health
human / maintainer      -> decide, approve, reject, merge, and own architectural judgment
```

## Required Local Gate

Before claiming completion, run or request evidence for:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

If a command was not run, say so explicitly and explain why.
