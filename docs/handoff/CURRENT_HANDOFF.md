Current version: 0.3.27

# Current Handoff

Status-date: 2026-05-19
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Refresh the planning state after v0.3.27 and harden documentation freshness guards. The repository must remain the durable memory: rules are durable only when documented, test-backed, and enforced by repo tooling or gates.

## Current Repository State

Current released version: 0.3.27
Current release tag: v0.3.27
Verified Zenodo version DOI: `10.5281/zenodo.20283414`
Current branch after v0.3.27: main

v0.3.27 is the current verified no-copy/evidence baseline. The normal operator path is `git pull --ff-only origin main` followed by `./ns agent-next`. Normal command PASS/FAIL should be handled through remote-readable command reports and terminal logs, not manual copy-and-paste.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, log, open PRs, latest terminal log, handoff state, interpreter/tooling state, and gates before patching.
- Keep state documents curated. Do not append new current-state fragments below obsolete ones.
- Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv`.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or workflows that need a clean tree.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Do not use heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, or quote-prone shell constructs in chat-pasted terminal blocks.
- Larger terminal blocks must begin with three long separator lines and end with a clear `### RESULT: ... ###` marker.

## Next Safe Step

Complete this planning-state refresh and guard-hardening slice. After merge and verification, begin the thin local Tkinter cockpit foundation. The first GUI must remain a presentation layer over explicit safe action metadata and must show command output, return codes, safety class, latest command-run report, and latest terminal log.

Pattern Advisor expansion, release-automation expansion, and hidden command planning are intentionally deferred.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `docs/TEST_GATES.md`, `docs/DOCUMENTATION_COVERAGE.yaml`, `.agentic/project.yaml`, `sentinel.yaml`, and committed terminal evidence under `docs/reports/terminal/`.

The exact lowercase phrase `documentation coverage` is intentionally present here because `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, and `agentic-kit doctor` enforce required state-document coverage terms deterministically.

## Required Local Gate

Before merge or handoff, run:

```bash
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns dev
```

Before any remote mutation, merge verification, release publication, tag creation, or clean-tree sync workflow, additionally run `./ns terminal-remote-preflight`.

The exact phrases `policy-pack checks`, `policy packs`, `post-release Zenodo`, `agentic-kit post-release-check`, `documentation coverage`, and no-copy/evidence are intentionally present because deterministic coverage gates enforce them.
