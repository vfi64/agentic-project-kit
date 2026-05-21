Current version: 0.3.35

# Project Status

Status-date: 2026-05-21
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Its core purpose is to move durable project memory out of chat transcripts and into versioned repository files, deterministic gates, evidence logs, explicit handoff state, and typed work execution contracts.

The repository, not the chat transcript, is the durable source of truth for current state, gates, handoff, evidence, rules, and release metadata. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current Goal

The immediate goal after the v0.3.36 direct shell-adapter removal round is to finalize repository state, harden remaining workflow rules deterministically, audit portability, and only then prepare the next release.

Current priorities:

1. Keep the known direct `ns -> tools/ns_*.sh` workflow-adapter count at zero.
2. Keep the remaining workplan in repo-owned documents.
3. Harden recurring workflow mistakes as tests, validators, or action contracts.
4. Audit portability and typed Work Order coverage.
5. Prepare v0.3.36 only after state docs and gates are consistent.

The detailed remaining workplan is `docs/workflow/V0.3.36_REMAINING_WORKPLAN.md`.

## Current State

## v0.3.36 Direct `ns` Shell-Adapter Removal Baseline

The known direct `./ns` workflow routes to tracked `tools/ns_*.sh` adapters have been removed and replaced by Python module or CLI routes.

Removed direct adapters:

- `tools/ns_clean_evidence.sh`
- `tools/ns_commit_pr_guard.sh`
- `tools/ns_pr_cleanup.sh`
- `tools/ns_slice_runner.sh`
- `tools/ns_release_gate.sh`
- `tools/ns_release_verify.sh`
- `tools/ns_release_prep.sh`
- `tools/ns_release_publish.sh`
- `tools/ns_up_pr_completion.sh`

Current invariant: `./ns` may remain a small POSIX bootstrap/dispatcher, but durable workflow behavior belongs in tested Python modules or CLI commands. New direct `ns -> tools/ns_*.sh` workflow adapters are not allowed without an explicit migration exception, tests, and a removal plan.

Direct `ns` shell-adapter count for the known workflow adapter class: 0.

## Remaining v0.3.36 Work

The remaining work is intentionally bounded. No GUI and no release should start before these state and rule-hardening tasks are closed or explicitly deferred.

Open items:

1. Typed Work Order Unit-Test Matrix: audit and expand tests for schema, queue cardinality, already-executed guards, evidence metadata, and dirty-state behavior.
2. Release and DOI Python-Core Encapsulation: audit release/DOI phase boundaries and keep the Zenodo concept DOI versus version DOI WAITING case guarded.
3. Shell Commands Reduced To Delegation: maintain inventory tests that block reintroduction of direct `ns -> tools/ns_*.sh` routes.
4. Evidence and Dirty-Log Checks As Action Contracts: audit `clean-evidence`, `evidence-clean-check`, `evidence-guard`, `terminal-clean-check`, `terminal-remote-preflight`, `patch-preflight`, `mode-check`, and `mode-write`.
5. Status and Handoff Update: keep this file, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml` mutually consistent.
6. Deterministic Rule Hardening: enforce no false PASS after inner FAIL, remote-evidence truthfulness, stale shell-test prevention, and mode-guard requirements.
7. Portability: remove or document global tool assumptions and prefer project-local Python/module routes.
8. Shell Inventory: classify any remaining shell as bootstrap, CI shell, test fixture, documentation example, or legacy adapter.
9. v0.3.36 Release: prepare only after the state docs and gates are green.

## Active Workflow Rules

- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, and documentation.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml` mutually consistent.
- Use project-local interpreter/tooling first. Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv` exist.
- Use `./ns mode-check local` or `./ns mode-check remote` before workflows that depend on local/remote execution mode.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or branch-switching/sync workflows that must start from a clean tree.
- Use `./ns terminal-finalize` or command-run reports so PASS and FAIL evidence is remote-readable whenever technically possible.
- Larger terminal workflows must begin with three separator lines and end with `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###`.
- Avoid heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, and shell constructs likely to leave `quote>`, `dquote>`, or `heredoc>` prompts.
- A final PASS is invalid when any required inner work result is FAIL.
- `REMOTE_EVIDENCE: PASS` requires committed and pushed evidence or an equivalent remote-readable report.

## Gate Status

The current required gate set for this planning refresh is:

- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns dev`
- `agentic-kit check-docs` / project-local module equivalent
- `agentic-kit doctor` / project-local module equivalent

## Next Safe Step

Finish this status/handoff refresh, merge it, and then start the deterministic rule-hardening slice. Do not start Tkinter or release v0.3.36 until the remaining workplan and handoff state are consistent.

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

## Documentation Coverage Notes

`docs/DOCUMENTATION_COVERAGE.yaml` is the documentation coverage source for required terms and state-doc coverage. `agentic-kit check-docs` and `agentic-kit doctor` enforce this coverage through deterministic gates.

Planning-state freshness is part of the governance contract: current-state documents must not contain stale released-version claims, obsolete next-step instructions, or contradictory active baselines.

The exact phrases policy-pack doctor checks, policy-pack checks, policy packs, post-release Zenodo, agentic-kit post-release-check, documentation coverage, and no-copy/evidence are intentionally present because deterministic coverage gates enforce required state-document coverage terms.

## Current Release Metadata

Current released version: 0.3.35
Current release tag: v0.3.35
Zenodo concept DOI: `10.5281/zenodo.20101359`

v0.3.36 is not released yet. The current v0.3.36 work is hardening and state refresh work after the direct `ns` shell-adapter removal baseline.

## Mandatory Final Summary Contract

Relevant workflow blocks must end with the framed SUMMARY contract containing `WORK RESULT`, `EVIDENCE RESULT`, `OVERALL RESULT`, `REMOTE_EVIDENCE`, `terminal_log`, `command_report`, `NEXT_CHAT_REPLY`, and a final result marker.

A final PASS requires work success and evidence success. A pushed log can prove a failure without turning that failed work into success.

## Quality-First Workflow Lessons

The project treats repeated assistant/workflow mistakes as product defects. The target is not to get a block through quickly; the target is the best deterministic solution for the recurring problem.

Current lessons: avoid nested triple-quote code generators, quote YAML coverage terms containing colons, compile generated Python before relying on gates, validate final SUMMARY blocks before asking for `p` or `d`, and never allow a later evidence push to convert failed work into PASS.

## YAML Governance Integrity Lesson

YAML governance files must be mutated through parse-modify-dump or an equivalent structured path, then parsed again before gates. Text injection into YAML is forbidden for complex values.

## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified.

## Compiled Agent Context YAML

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.

## Typed Work Orders Pre-GUI Execution Path

Typed Work Orders remain the preferred pre-GUI execution path for standard safe workflow actions. Use repo-owned YAML Work Orders and the tested Python runner wherever possible.

Available path:

- `./ns typed-run <path>` executes a specific typed Work Order.
- `./ns typed-queue-status --json` reports queue state.
- `./ns typed-next --json` executes exactly one queued Work Order from `.agentic/typed_work_orders/inbox`.

The thin Tkinter cockpit must consume typed contracts, action registry metadata, and machine-readable results instead of inventing hidden command planning or ad-hoc shell execution.

## GUI Status

Tkinter remains deferred. GUI preparation is high because the action registry, cockpit JSON, typed Work Orders, evidence state, mode guard, and direct shell-adapter removals are in place, but the GUI must wait until deterministic rule hardening and portability audit complete.
