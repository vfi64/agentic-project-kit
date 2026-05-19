Current version: 0.3.26

# Current Handoff

Status-date: 2026-05-18
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Stabilize rule governance and terminal/evidence governance before GUI, release automation, or new feature work. The repository must remain the durable memory: rules are durable only when documented, test-backed, and enforced by repo tooling or gates.

## Current Repository State

Current released version: 0.3.26
Current branch after PR #400 merge: main
Open PRs after PR #400 verification: none observed in remote check

Recent main history after v0.3.26 includes:

```text
b09b65e Preserve PR 399 merge verification log (#400)
171bdfc Add remote mutation dirty-state preflight guard (#399)
f978096 Preserve PR 397 merge verification log (#398)
2e1e81c Preserve sync diagnosis for rule evidence governance (#397)
7b59312 Preserve PR 395 merge verification log (#396)
b56eb31 Preserve v0.3.26 publish terminal log (#395)
7b5d105 Prepare v0.3.26 release metadata (#394)
922c50c Preserve clean main verification after local branch cleanup (#393)
aaa1e77 Preserve rule governance verification log (#392)
d86f538 Add test-backed rule governance contract (#391)
3490c15 Add ns interpreter discovery and no-exec guard (#390)
```

## Completed Most Recent Slice

PR #399 added `./ns terminal-remote-preflight`, `remote_mutation_preflight()` in `terminal_logging.py`, tests in `tests/test_terminal_remote_preflight.py`, and documentation in `docs/TEST_GATES.md`. This guard requires a fully clean worktree before remote mutations or merge/sync verification. It intentionally fails even for terminal-log dirtiness because dirty logs can block branch switching, fast-forward pulls, PR merges, and verification.

PR #400 preserved the successful PR #399 merge verification log. The log records that PR #399 checks passed, the new preflight guard passed before merge, PR #399 merged, main synchronized, `./ns terminal-remote-preflight` worked on main, and `./ns dev` passed with 395 tests.

## Latest Verified Gates

- `./ns terminal-remote-preflight`: PASS
- `./ns handoff-check`: PASS
- `./ns governance-check`: PASS
- `./ns dev`: PASS
- pytest: 395 passed
- ruff: PASS
- check-docs: PASS
- doctor: PASS; version drift check reports project state matches version 0.3.26

Latest terminal evidence pointer: `docs/reports/terminal/20260518-210113_pr399-merge-verification.log`.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- First verify branch, status, log, open PRs, latest terminal log, handoff state, interpreter/tooling state, and gates.
- Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv`.
- Use project-local commands and resolved interpreters.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or workflows that need a clean tree.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- If a PASS/FAIL handoff lacks remote-readable evidence, treat that as a workflow bug.
- Do not use heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, or quote-prone shell constructs in chat-pasted terminal blocks.
- Larger terminal blocks must begin with three long separator lines and end with a clear `### RESULT: ... ###` marker.

## Next Safe Step

Merge this STATUS/HANDOFF refresh only after local and CI gates pass. After that, consider a small deterministic guard that detects stale accumulated STATUS/HANDOFF historical fragments. Do not start GUI or release-automation expansion until this state refresh is merged and verified.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `docs/TEST_GATES.md`, `docs/DOCUMENTATION_COVERAGE.yaml`, `.agentic/project.yaml`, `sentinel.yaml`, and committed terminal evidence under `docs/reports/terminal/`.

Documentation coverage is enforced by `agentic-kit check-docs` and `agentic-kit doctor`. The doctor also reports project contract, policy packs, policy-pack checks, document lifecycle, TODO gates, and version drift status.

Release verification remains covered by the post-release Zenodo path and `agentic-kit post-release-check` after publication.

## Required Local Gate

Before merge or handoff, run:

```bash
./ns handoff-check
./ns governance-check
./ns dev
```

Before any remote mutation, merge verification, release publication, tag creation, or clean-tree sync workflow, additionally run `./ns terminal-remote-preflight`.

The exact lowercase phrase `documentation coverage` is intentionally present here because `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, and `agentic-kit doctor` enforce required state-document coverage terms deterministically.

## Current No-Copy / GUI Handoff

Current state after PR #423: `main` contains the hardened repo-backed no-copy workflow. Completed inbox commands are rejected by `./ns command-inbox-check` if their `command_id` already has durable command-run evidence, preventing stale completed commands from causing later `FAIL_AMBIGUOUS_COMMANDS`. The normal local operator path remains `git pull --ff-only origin main` followed by `./ns agent-next`; normal PASS/FAIL should be handled with `p` or `f` by reading remote evidence first. `HARD-FAIL -> paste output` remains reserved for auth/network/push failures, terminal crashes, missing remote evidence, or workflow-level ambiguity.

Immediate sequence: first finalize this status/handoff refresh and final no-copy verification, then cut `v0.3.27`, then start the GUI foundation. The first GUI should be deliberately thin: a local Tkinter cockpit wrapping pull-and-run-next, latest command report/log display, clean-state checks, and gate buttons. Pattern Advisor work is deferred until the GUI foundation is merged and released.
