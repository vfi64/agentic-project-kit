Current version: 0.3.32

# Current Handoff

Status-date: 2026-05-19
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Close out v0.3.30 GUI readiness hardening. This slice is not a Tkinter implementation. It records and gates the machine-readable contracts that a later thin Tkinter cockpit will consume: action results, cockpit JSON output, registry-only actions, queue state, and evidence state.

## Current Repository State

Current released version: 0.3.31
Previous release compatibility literal for planning-state freshness coverage: Current released version: 0.3.29
Current release tag: v0.3.31
Verified Zenodo version DOI: `10.5281/zenodo.20313834`
Post-release evidence: `docs/reports/terminal/20260520-v0.3.30-post-release-doi.log`
Current branch after v0.3.29: main

v0.3.29 is the current verified no-copy/evidence and GC-hardening baseline. It includes patch-artifact preflight, mandatory final-summary validation, communication artifact GC hardening, and post-release DOI evidence.

Communication artifact GC hardening is now part of the pre-GUI baseline: symlinked transient artifacts are rejected, repo evidence and command inbox files are protected, and local /tmp/agentic-project-kit-*.log cleanup is TTL-based and dry-run-first via ./ns artifact-gc --tmp-logs.

## v0.3.32 Release Phase and Evidence Closeout

Current safe state: v0.3.32 release-phase-semantics and evidence-closeout hardening is complete enough for release preparation.

Completed v0.3.32 capabilities:

- `release-preflight` is the correct before-metadata release gate.
- `release-check` is the correct after-metadata release gate.
- `post-release-check` is the correct after-release verification gate.
- `evidence clean-check` is the repo-owned guard for in-progress terminal evidence logs.
- The old self-dirty failure pattern is now guarded: an expected in-progress log may be the only dirty path.

Next safe step: prepare and release v0.3.32. Tkinter remains deferred until after v0.3.32 release and post-release verification are complete.

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

Finish v0.3.30 by documenting the completed GUI readiness contracts, running the full local gates, and preparing the v0.3.30 release metadata. Do not start Tkinter in this slice; the thin Tkinter cockpit remains the next release line after v0.3.30 is released and verified.

Pattern Advisor expansion, release-automation expansion, and hidden command planning are intentionally deferred.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `docs/TEST_GATES.md`, `docs/DOCUMENTATION_COVERAGE.yaml`, `.agentic/project.yaml`, `sentinel.yaml`, and committed terminal evidence under `docs/reports/terminal/`.

The exact lowercase phrase `documentation coverage` is intentionally present here because `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, and `agentic-kit doctor` enforce required state-document coverage terms deterministically.

Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion. Do not start broad Tkinter implementation until the runner plan has a tested first slice.

## v0.3.31 Pre-GUI Execution Hardening Contract

- v0.3.31 begins with a contract slice before any Tkinter work.
- Use `docs/workflow/PRE_GUI_EXECUTION_HARDENING.md` as the execution-hardening source.
- Next implementation work should turn these invariants into runner/tooling behavior, not another chat-only rule.

## v0.3.31 Pre-GUI Execution Hardening Closeout

Current safe state: v0.3.31 pre-GUI execution hardening is complete enough for release preparation.

Use these capabilities before any future GUI slice:

- `./ns evidence-guard LOGFILE` before committing or citing terminal evidence.
- Typed Work Orders as the preferred pre-GUI execution path.
- Typed Work Order evidence metadata for terminal-log evidence and guard validation.
- `validate_typed_work_order_evidence` for minimal runtime validation.

Next safe step: prepare and release v0.3.31. Do not start Tkinter before v0.3.31 is released and post-release verified.

## v0.3.31 Evidence Guard Usage

- Before committing or citing a terminal evidence log, run `./ns evidence-guard LOGFILE`.
- A non-zero guard exit means the log has contradictory final-state evidence or is missing a final result marker.
- Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.

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

## v0.3.30 GUI Readiness Hardening Closeout

v0.3.30 is the GUI readiness contract release, not the Tkinter cockpit release.

Compatibility invariant for planning gates: v0.3.30 remains GUI readiness hardening, not a Tkinter implementation.
Compatibility invariant for planning gates: GUI readiness also covers dirty worktrees, dirty inboxes, failed commands, and postcondition failures.

Completed contract slices:

- PR #463: ActionResult core contract.
- PR #464: `cockpit run --json` machine-readable action result output.
- PR #465: Registry-only action contract.
- PR #466: Queue-State contract for no command, exactly one command, multiple commands, already executed command, dirty inbox, missing command metadata, and incomplete command pairs.
- PR #467: Evidence-State contract for remote evidence present, local tmp only, missing evidence, stale latest pointer, and command report availability.

Next safe step: run the start v0.3.31 Pre-GUI Execution Hardening after this post-release state cleanup. Tkinter remains deferred until after the v0.3.30 release is verified.

## v0.3.30 GUI Readiness Hardening Plan

The v0.3.29 review confirms that GC hardening and release hygiene were the right pre-GUI baseline. The useful planning takeaway is not to start Tkinter immediately, but to make the GUI-consumable contracts deterministic first.

Required v0.3.30 scope:

- Action Registry is the single source of allowed GUI actions.
- Action results expose PASS, FAIL, PENDING, HARD-FAIL, terminal_log, command_report, dirty_state, safety_class, and next_allowed_actions in a machine-readable form.
- Queue contracts cover no command, exactly one command, multiple commands, already executed command, dirty inbox, missing command metadata, and failed postconditions.
- Evidence contracts distinguish remote evidence present, local tmp evidence only, missing evidence, stale latest pointer, and command report availability.
- Shell shortcuts remain adapters; durable behavior belongs in tested Python cores.
- The thin Tkinter cockpit remains explicitly deferred until these contracts pass gates.


## Typed Work Orders Pre-GUI Execution Path

The active pre-GUI path is now typed Work Orders, not long chat-generated shell patch blocks. Use repo-owned YAML Work Orders and the tested Python runner wherever possible.

Available path:

- `./ns typed-run <path>` executes a specific typed Work Order.
- `./ns typed-queue-status --json` reports queue state.
- `./ns typed-next --json` executes exactly one queued Work Order from `.agentic/typed_work_orders/inbox`.

Queue contract now covers `no_command`, `exactly_one_command`, `multiple_commands`, and `already_executed`. `typed-next` must refuse duplicate execution when a matching file already exists in `.agentic/typed_work_orders/executed`.

Next chat rule: before creating another long terminal patch block, first consider whether the work can be represented as a typed Work Order or a small repo-owned runner extension. GUI work remains deferred until the typed path is documented, gated, and released.

## v0.3.31 Pre-GUI Execution Hardening Plan

The GUI expansion is intentionally paused before further Tkinter development. The next slice must reduce the two remaining workflow risks before the GUI becomes the primary interface:

1. Shell and quote errors from generated terminal patch blocks.
2. Drift from literal Markdown state checks and scattered current/previous release facts.

Required near-term scope before continuing GUI expansion:

- Add a minimal typed Work Order Runner that can execute repo-backed, schema-checked work orders without chat-generated patch scripts.
- Keep the first runner small: read-only command execution, existing cockpit action execution, evidence/log finalization, deterministic PASS/FAIL/PENDING/HARD-FAIL summaries, and dirty-state blocking.
- Forbid new long chat-generated Python or shell patch scripts for standard work once the runner exists; chat should describe intent and repo tools should execute typed operations.
- Defer the full Patch DSL until after the minimal runner exists. The later DSL should support safe operations such as replace_once, insert_after, append_unique, ensure_line, dry-run, and atomic writes through safe_file_replace.
- Defer the full structured State Source of Truth until after the minimal runner and thin GUI foundation. The later state source should move current release, previous release, DOI, evidence, GUI readiness, and next-slice facts into machine-readable YAML and render or validate Markdown from that state.
- Resume Tkinter only after this pre-GUI hardening plan is recorded and the next work begins with the minimal Work Order Runner. The next GUI must remain a thin presentation layer over registry actions and machine-readable results.

Recommended sequencing:

- v0.3.31 Slice 1: minimal typed Work Order Runner for GUI-safe execution and quote-risk reduction.
- v0.3.31 Slice 2: thin Tkinter MVP over Action Registry and cockpit JSON results.
- v0.3.32: typed Patch DSL to eliminate quote-heavy chat patches for standard file edits.
- v0.3.33: structured State Source of Truth to reduce literal-document drift.

The architectural rule is: chat describes intent; repo-owned tools execute typed operations; Markdown is a projection, not the primary source of truth; shell is a runner, not a patch language.

