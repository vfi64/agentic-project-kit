# First-Chat Onboarding

Status: active  
Date: 2026-08-23  
Audience: first-time users, maintainers, and LLM coding agents

## Purpose

Use this page at the start of a new chat or first repository session. It chooses
one route, then points to the existing Kit commands and docs. It is not a second
planner, rulebook, workflow taxonomy, or release authority.

The generated command manifest remains the command source of truth. Re-check
command names with `agentic-kit command-for` before turning guidance into a
terminal command.

## One Decision

Choose exactly one first route.

### Create a new governed project

Use this route when the Kit should create the repository skeleton, project
contract, starter docs, and local gates.

Core commands:

```bash
agentic-kit init NAME
agentic-kit check
agentic-kit doctor
```

### Add the Kit operating layer to an existing repository

Use this route when project-owned source files already exist and the Kit should
wrap the repository with governance, evidence, and handoff files.

Inspect before writing:

```bash
agentic-kit workspace adopt --root PATH
agentic-kit workspace init --root PATH
```

Write only after reviewing the plan:

```bash
agentic-kit workspace init --root PATH --execute
agentic-kit check --root PATH
agentic-kit doctor --root PATH
```

The shortest brownfield walkthrough is
`docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md`.

### Work on this Kit repository

Use this route when changing `vfi64/agentic-project-kit` itself.

Start by reading the active agent instructions and the command manifest. Before
starting a branch or proposing commands, resolve the specific Kit command with:

```bash
agentic-kit command-for --task work
```

Then use the governed work lifecycle rather than raw branch, PR, or handoff
steps.

## Non-Workspace Message Binding

The canonical non-workspace next-step wording comes from
`agentic_project_kit.workspace_detection.NON_WORKSPACE_NEXT_STEP`.

Current source-bound snippets:

```text
agentic-kit init NAME
agentic-kit workspace init --root PATH
```

If that source message changes, this document and the onboarding measurement
must change in the same slice.

## Minimal Glossary

- governed project: a repository with Kit project contracts, docs, gates, and
  handoff state.
- operating layer: the `.agentic/` governance layer added around an existing
  repository without taking ownership of product source.
- command manifest: the generated command reference in
  `docs/reference/agentic-kit-commands.json`.
- gate: a deterministic check that reports pass, fail, warn, or blocked state.
- handoff: repo-backed context for continuing work without relying on chat
  memory.

## Repeatable Measurement

Run the onboarding measurement before claiming first-chat guidance is current:

```bash
agentic-kit onboarding measure --json
```

The measurement checks this document, README anchors, required command-manifest
entries, glossary terms, and the workspace-detection next-step snippets. It
records counts so future onboarding edits can be compared instead of guessed.
