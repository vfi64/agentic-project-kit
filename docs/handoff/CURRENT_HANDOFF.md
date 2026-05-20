Current version: 0.3.28

# Current Handoff

Status-date: 2026-05-19
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Refresh the planning state after v0.3.27 and harden documentation freshness guards. The repository must remain the durable memory: rules are durable only when documented, test-backed, and enforced by repo tooling or gates.

## Current Repository State

Current released version: 0.3.28
Current release tag: v0.3.28
Verified Zenodo version DOI: `10.5281/zenodo.20286394`
Post-release evidence: `docs/reports/terminal/20260519-141830_verify-v0.3.28-post-release-doi-source.log`
Current branch after v0.3.28: main

v0.3.28 is the current verified no-copy/evidence baseline. It includes patch-artifact preflight, mandatory final-summary validation, and post-release DOI evidence.

Communication artifact GC hardening is now part of the pre-GUI baseline: symlinked transient artifacts are rejected, repo evidence and command inbox files are protected, and local /tmp/agentic-project-kit-*.log cleanup is TTL-based and dry-run-first via ./ns artifact-gc --tmp-logs.

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

## Mandatory Final Summary Contract

Relevant terminal blocks must end with the mandatory final SUMMARY block. Use `NEXT_CHAT_REPLY: p` only when `OVERALL RESULT: PASS` and `REMOTE_EVIDENCE: PASS`. Use `NEXT_CHAT_REPLY: f` when the work failed but remote evidence is available. Use `NEXT_CHAT_REPLY: paste-output` when remote evidence is missing or incomplete.

## Quality-First Workflow Lessons

Use the best deterministic fix, not the shortest patch. New recurring problems must be recorded as rules, failure patterns, tests, or tooling. Specifically: no nested triple-quote code generators, no unquoted YAML coverage terms with colons, no uncompiled generated Python, and no final PASS after an inner FAIL.

## YAML Governance Integrity Lesson

Do not patch YAML governance files by injecting unquoted text. Use structured YAML mutation and parse checks before gate runs. Repeated YAML corruption is tracked as `repeated-yaml-governance-file-corruption` and the active rule is `yaml-structured-mutation-only`.


## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified. This remote-first no-guess rule is mandatory for release, DOI, PR, evidence, and governance work.

## Compiled Agent Context YAML

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.

## No remote-command deadlock

Rule id: no-remote-command-deadlock

Remote command first is a delivery preference, not a blocking rule. If `./ns agent-next` reports `NO-COMMAND`, the next assistant response must either queue a complete command pair remotely or give exactly one minimal fallback command. The user must not be kept in an `ask-agent-to-queue-command` loop. Long ad-hoc terminal blocks are only allowed when the remote command path is unavailable or broken.

- Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and final result marker.

## No executable placeholder summaries

Executable terminal blocks must never print final SUMMARY fields with placeholder alternatives such as `PASS|FAIL`, `p|paste-output`, or ellipsis markers. A copied block must end with one concrete outcome only. Placeholder examples are allowed only in prose documents when clearly marked as non-executable examples.

