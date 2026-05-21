Current version: 0.3.35

# Current Handoff

Status-date: 2026-05-21
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Finalize the v0.3.36 direct `ns` shell-adapter removal state, then harden remaining workflow rules deterministically before GUI or release work.

This is not a Tkinter implementation slice and not a release slice.

## Current Repository State

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

The detailed remaining workplan is `docs/workflow/V0.3.36_REMAINING_WORKPLAN.md`.

## Remaining Workplan

Next bounded sequence:

1. Finish this status/handoff refresh.
2. Harden false-PASS, remote-evidence, stale-shell-test, and mode-guard rules as deterministic tests or validators.
3. Audit portability and reduce hard global-tool assumptions.
4. Expand the typed Work Order unit-test matrix.
5. Prepare v0.3.36 only after state docs and gates are consistent.

Open work categories:

- Typed Work Order Unit-Test Matrix.
- Release and DOI Python-Core Encapsulation audit.
- Shell command inventory and direct `ns -> tools/ns_*.sh` reintroduction guard.
- Evidence and dirty-log checks as action contracts.
- Status and handoff consistency.
- Deterministic rule hardening.
- Portability audit.
- Shell inventory.
- v0.3.36 release preparation.

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, log, open PRs, latest terminal log, handoff state, interpreter/tooling state, and gates before patching.
- Keep state documents curated. Do not append new current-state fragments below obsolete ones.
- Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv`.
- Use `./ns mode-check local` or `./ns mode-check remote` before workflows that depend on local/remote execution mode.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or workflows that need a clean tree.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` or command-run reports whenever technically possible.
- Do not use heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, or quote-prone shell constructs in chat-pasted terminal blocks.
- Larger terminal blocks must begin with three long separator lines and end with a clear `### RESULT: ... ###` marker.
- A final PASS is invalid when any required inner work result is FAIL.
- `REMOTE_EVIDENCE: PASS` requires committed and pushed evidence or an equivalent remote-readable report.

## Required Local Gate

Before merge or handoff, run or verify equivalent CI/local gates:

```bash
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns dev
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli check-docs
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli doctor
```

Before any remote mutation, merge verification, release publication, tag creation, or clean-tree sync workflow, additionally run `./ns terminal-remote-preflight`.

The exact phrases policy-pack checks, policy packs, post-release Zenodo, agentic-kit post-release-check, documentation coverage, and no-copy/evidence are intentionally present because deterministic coverage gates enforce them.

## Next Safe Step

Merge this status/handoff refresh, then start the deterministic rule-hardening slice. Do not start Tkinter, Pattern Advisor expansion, hidden command planning, or v0.3.36 release metadata until the remaining workplan and handoff state are consistent.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `docs/workflow/V0.3.36_REMAINING_WORKPLAN.md`, `docs/TEST_GATES.md`, `docs/DOCUMENTATION_COVERAGE.yaml`, `.agentic/project.yaml`, `sentinel.yaml`, and committed terminal evidence under `docs/reports/terminal/`.

## Mandatory Final Summary Contract

Relevant terminal blocks must end with the mandatory final SUMMARY block. Use `NEXT_CHAT_REPLY: d` only when `OVERALL RESULT: PASS`. Use `NEXT_CHAT_REPLY: f` when the work failed and remote evidence is available. Use `NEXT_CHAT_REPLY: paste-output` when remote evidence is missing or incomplete.

A pushed log can prove a failure without turning that failed work into success.

## Quality-First Workflow Lessons

Use the best deterministic fix, not the shortest patch. New recurring problems must be recorded as rules, failure patterns, tests, or tooling. Specifically: no nested triple-quote code generators, no unquoted YAML coverage terms with colons, no uncompiled generated Python, no stale shell-file test expectations after shell-adapter removal, and no final PASS after an inner FAIL.

## YAML Governance Integrity Lesson

Do not patch YAML governance files by injecting unquoted text. Use structured YAML mutation and parse checks before gate runs.

## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified.

## Compiled Agent Context YAML

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.

## Typed Work Orders Pre-GUI Execution Path

The active pre-GUI path is typed Work Orders, not long chat-generated shell patch blocks. Use repo-owned YAML Work Orders and the tested Python runner wherever possible.

Available path:

- `./ns typed-run <path>` executes a specific typed Work Order.
- `./ns typed-queue-status --json` reports queue state.
- `./ns typed-next --json` executes exactly one queued Work Order from `.agentic/typed_work_orders/inbox`.

Queue contracts must continue to cover no command, exactly one command, multiple commands, and already executed work orders.

## GUI Status

Tkinter remains deferred. GUI preparation is high, but the GUI must wait until deterministic rule hardening and portability audit complete.
