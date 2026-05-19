Current version: 0.3.27

# Project Status

Status-date: 2026-05-19
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Its core purpose is to move durable project memory out of chat transcripts and into versioned repository files, deterministic gates, evidence logs, and explicit handoff state.

The project treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, rules, and release metadata. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current Goal

The immediate goal after v0.3.27 is to refresh the planning state and harden documentation freshness guards before GUI, release-automation, or Pattern Advisor expansion. Planning files must be curated current-state documents, not accumulated historical fragments.

## Current State

Current released version: 0.3.27
Current release tag: v0.3.27
Zenodo concept DOI: `10.5281/zenodo.20101359`
Verified Zenodo version DOI: `10.5281/zenodo.20283414`

v0.3.27 is the current released and verified baseline. It preserves the hardened repo-backed no-copy workflow: remote tasks are queued under `.agentic/commands/inbox/`, local execution runs through `./ns agent-next`, durable command evidence is written under `docs/reports/command_runs/`, and terminal evidence is written under `docs/reports/terminal/`.

The active bridge toward the local GUI is no-copy/evidence governance, not hidden automation. Normal PASS/FAIL handoff should rely on committed and pushed reports. Manual paste-output is reserved for hard failures such as authentication problems, network failures, terminal crashes, missing remote evidence, or workflow-level ambiguity.

## Active Workflow Rules

- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, and documentation.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml` mutually consistent.
- Use project-local interpreter/tooling first. Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv` exist.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or branch-switching/sync workflows that must start from a clean tree.
- Use `./ns terminal-finalize` or command-run reports so PASS and FAIL evidence is remote-readable whenever technically possible.
- Larger terminal workflows must begin with three separator lines and end with `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###`.
- Avoid heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, and shell constructs likely to leave `quote>`, `dquote>`, or `heredoc>` prompts.

## Gate Status

The current required gate set for this planning refresh is:

- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns dev`
- `agentic-kit check-docs` / project-local module equivalent
- `agentic-kit doctor` / project-local module equivalent

## Next Safe Step

Finish the planning-state refresh and documentation-freshness guard hardening. After that is merged and verified, start the first thin local Tkinter cockpit slice over the existing safe action layer: pull-and-run-next, status display, latest command-run report, latest terminal log, clean-state checks, and gate buttons.

Do not expand Pattern Advisor, release automation, or hidden command selection before the GUI foundation and planning freshness guards are stable.

## Documentation Coverage Notes

`docs/DOCUMENTATION_COVERAGE.yaml` is the documentation coverage source for required terms and state-doc coverage. `agentic-kit check-docs` and `agentic-kit doctor` enforce this coverage through deterministic gates.

Planning-state freshness is now part of the governance contract: current-state documents must not contain stale released-version claims, obsolete next-step instructions, or contradictory active baselines.

## Live Status Commands

Run these from the repository root with project-local tooling:

```bash
git status --short
git branch --show-current
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns dev
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli check-docs
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli doctor
```

The equivalent public command names remain `agentic-kit check-docs`, `agentic-kit doctor`, and `agentic-kit post-release-check`; the project-local module form is preferred when global executables are not guaranteed.

## Compatibility Notes For Existing Coverage

Pattern Advisor remains a read-only catalog. Its current public surface is still `patterns list` and `patterns show`; it is advisory-only and must remain separate from deterministic gates.

The exact phrase policy-pack doctor checks is intentionally present here: policy-pack doctor checks remain active through `agentic-kit doctor`; active policy packs are part of the project contract and must remain visible in current-state documentation.

Release verification remains covered by the post-release Zenodo path and `agentic-kit post-release-check`. Current no-copy/evidence status is the bridge toward the thin local Tkinter cockpit.

## Mandatory Final Summary Contract

The no-copy/evidence workflow now requires a mandatory final SUMMARY block for relevant terminal work. `WORK RESULT`, `EVIDENCE RESULT`, `OVERALL RESULT`, `REMOTE_EVIDENCE`, `terminal_log`, `command_report`, and `NEXT_CHAT_REPLY` must be reported separately. A final PASS requires work success and evidence success; a pushed log can prove a failure without turning that failure into success.
