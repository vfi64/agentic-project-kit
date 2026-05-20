Current version: 0.3.30

# Project Status

Status-date: 2026-05-19
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Its core purpose is to move durable project memory out of chat transcripts and into versioned repository files, deterministic gates, evidence logs, and explicit handoff state.

The project treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, rules, and release metadata. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current Goal

The immediate goal after v0.3.29 is to close out v0.3.30 GUI readiness hardening. This is not a Tkinter implementation slice. The release line hardens the machine-readable contracts a later thin Tkinter cockpit will consume: action results, cockpit JSON output, registry-only action selection, command queue state, and evidence state.

## Current State

Current released version: 0.3.30
Previous release compatibility literal for planning-state freshness coverage: Current released version: 0.3.29
Current release tag: v0.3.30
Zenodo concept DOI: `10.5281/zenodo.20101359`
Verified Zenodo version DOI: pending for v0.3.30; previous v0.3.29 DOI `10.5281/zenodo.20303218`
Post-release evidence: pending for v0.3.30; previous evidence `docs/reports/terminal/20260520-v0.3.29-post-release-discovery-v2.log`

v0.3.30 is the current prepared release line; GitHub Release and Zenodo version DOI verification are pending until post-release closeout. It includes the patch-artifact preflight MVP and the hardened planning-state/no-copy evidence workflow.

The active bridge toward the local GUI is no-copy/evidence governance and communication artifact GC hardening, not hidden automation. Normal PASS/FAIL handoff should rely on committed and pushed reports. Manual paste-output is reserved for hard failures such as authentication problems, network failures, terminal crashes, missing remote evidence, or workflow-level ambiguity.

Communication artifact GC hardening is now part of the pre-GUI baseline: symlinked transient artifacts are rejected, repo evidence and command inbox files are protected, and local /tmp/agentic-project-kit-*.log cleanup is TTL-based and dry-run-first via ./ns artifact-gc --tmp-logs.

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

Finish v0.3.30 by documenting and gating the GUI readiness hardening baseline, then prepare the v0.3.30 release. Do not start Tkinter in this release line. The first thin Tkinter cockpit belongs after the v0.3.30 contracts are released and verified.

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

## Quality-First Workflow Lessons

The project now treats repeated assistant/workflow mistakes as product defects. The target is not to get a block through quickly; the target is the best deterministic solution for the recurring problem.

Current lessons: avoid nested triple-quote code generators, quote YAML coverage terms containing colons, compile generated Python before relying on gates, validate final SUMMARY blocks before asking for `p`, and never allow a later evidence push to convert failed work into PASS.

## YAML Governance Integrity Lesson

YAML governance files have been damaged more than once by text-style patching. The project now treats this as a recurring workflow defect. `.agentic/handoff_state.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and similar control files must be mutated through parse-modify-dump or an equivalent structured path, then parsed again before gates.


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

## v0.3.30 GUI Readiness Hardening Closeout

v0.3.30 is the GUI readiness contract release, not the Tkinter GUI release.

Completed contract slices:

- PR #463: ActionResult core contract exposes PASS, FAIL, PENDING, HARD-FAIL, terminal_log, command_report, dirty_state, safety_class, and next_allowed_actions.
- PR #464: `cockpit run --json` exposes machine-readable action results for read-only and blocked bounded actions.
- PR #465: Cockpit Registry is the only allowed action source and validates action ids, safety classes, commands, labels, categories, and descriptions.
- PR #466: Queue-State contract covers NO_COMMAND, EXACTLY_ONE_COMMAND, MULTIPLE_COMMANDS, ALREADY_EXECUTED_COMMAND, DIRTY_INBOX, MISSING_COMMAND_METADATA, and INCOMPLETE_COMMAND.
- PR #467: Evidence-State contract covers REMOTE_EVIDENCE_PRESENT, LOCAL_TMP_ONLY, MISSING_EVIDENCE, STALE_LATEST_POINTER, and command_report_available.

The release closeout criterion is a clean full gate plus release metadata for v0.3.30. Tkinter remains explicitly deferred until after this contract baseline is released.

## v0.3.30 GUI Readiness Hardening Plan

The v0.3.29 review confirms that GC hardening and release hygiene were the right pre-GUI baseline. The useful planning takeaway is not to start Tkinter immediately, but to make the GUI-consumable contracts deterministic first.

Required v0.3.30 scope:

- Action Registry is the single source of allowed GUI actions.
- Action results expose PASS, FAIL, PENDING, HARD-FAIL, terminal_log, command_report, dirty_state, safety_class, and next_allowed_actions in a machine-readable form.
- Queue contracts cover no command, exactly one command, multiple commands, already executed command, dirty inbox, missing command metadata, and failed postconditions.
- Evidence contracts distinguish remote evidence present, local tmp evidence only, missing evidence, stale latest pointer, and command report availability.
- Shell shortcuts remain adapters; durable behavior belongs in tested Python cores.
- Tkinter is explicitly deferred until these contracts pass gates.
