# Planner-Kit-Executor Contract

Status: active  
Date: 2026-08-23  
Scope: governed executor intents, Kit command authority, and the first Hermes adapter boundary

## Purpose

Planner-Kit-Executor integration lets an external planner or executor describe
work as a typed intent while `agentic-kit` remains the authority for command
selection, safety classification, evidence, state, release, and handoff.

Hermes is the first named executor/browser adapter, but Hermes is not a new
workflow taxonomy and is not a repository authority. A Hermes-backed intent must
still resolve each runnable step through the generated command manifest or the
local cockpit/action registry.

## Contract

A planner intent is YAML with `schema_version: 1`, an `id`, a `title`, an
`executor_adapter`, and ordered `steps`.

Supported adapters are:

- `hermes`: external executor/browser adapter name; repository execution still
  passes through Kit-owned command or cockpit surfaces.
- `kit-local`: local adapter for deterministic tests and non-browser operation.

Supported step kinds are:

- `command`: an argv list that starts with `agentic-kit` and resolves to the
  generated command manifest.
- `cockpit_action`: an action ID that resolves to the local cockpit registry.

The command manifest and cockpit registry are the only durable authorities for
step resolution. Raw `git`, `gh`, browser, shell, or Hermes commands are not
valid intent steps.

## Safety

`agentic-kit executor plan INTENT` is read-only. It resolves steps, reports
safety, reports dirty-worktree state, and returns blockers without executing
work.

`agentic-kit executor run INTENT` is dry-run by default. It writes a bounded JSON
result under `tmp/` unless an explicit `--report` path under `docs/reports/` or
`tmp/` is supplied.

Execution rules:

- read-only command-manifest steps may run with `--execute`;
- read-only cockpit actions may run with `--execute`;
- bounded cockpit actions require both step-level `allow_bounded: true` and CLI
  `--allow-bounded`;
- direct non-read-only command-manifest execution is blocked until a narrower
  action surface exists;
- destructive steps are always blocked;
- dirty worktrees block by default when `block_dirty_worktree` is true;
- external credentials, browser sessions, and GUI transports are outside the
  durable intent and must be represented as explicit capability boundaries
  before they affect repository state.

## Evidence And Failure States

Planner-executor run results use the same result vocabulary as cockpit and typed
work-order execution: `PASS`, `FAIL`, `PENDING`, and `HARD-FAIL`.

The JSON result records:

- intent ID and executor adapter;
- dirty-worktree state;
- whether execution happened;
- bounded evidence path;
- blockers;
- per-step command/action results.

This result is evidence that the Kit authorized and ran a bounded set of steps.
It is not evidence that an LLM independently judged its own semantic quality.

## H1-H3 Closeout

The H0 inventory is recorded in
`docs/reports/HERMES_EXECUTOR_H0_INVENTORY_20260823.md`.

This contract closes H1 by defining the proof-of-concept schema and resolution
rules. The `agentic-kit executor plan` command closes H2 as the minimal
read-only adapter surface. The dry-run-by-default `agentic-kit executor run`
command closes the first H3 bounded action surface by permitting only
manifest/cockpit-governed execution with explicit bounded-action gates and
tests.
