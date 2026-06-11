# NEXT CHAT BOOTSTRAP

This file is the canonical remote handoff entry point for a successor chat.
Do not start from chat memory. Read this file first, then follow its boot sequence.

## Current Operational Handoff State

Current verified main/admin HEAD is `e97af5923886ea41e5114bb3755320ba0212d993` (`e97af592`), after `Refresh handoff state after PR1244 (#1245)`.
Last substantive work state is `7f5a3310` (`Enforce operational handoff document freshness (#1244)`).

PR #1245 is an administrative handoff/evidence refresh after PR #1244. It does not replace the substantive safe-state intent.
A successor chat must treat operational documentation freshness as part of handoff freshness: STATUS, CURRENT_HANDOFF, START_NEW_CHAT_PROMPT, NEXT_CHAT_BOOTSTRAP, and the active roadmap must mention current safe/admin markers before they are used as authoritative orientation.
Next safe substantive slice: implement the professional operational documentation projection system from a machine-readable state source, with generated blocks, preservation of curated documentation, rule-registry coverage, and drift gates.

## Canonical chat-switch prompt files

- Start a successor chat with `docs/handoff/START_NEW_CHAT_PROMPT.md`.
- Before leaving a chat, run the closeout routine in `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`.
- A closeout may need to update both prompt files and this bootstrap file.

## Standard successor-chat prompt

Copy this into the next chat:

```text
We work in repo vfi64/agentic-project-kit. Do not start from chat memory.
Read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main completely and execute its boot routine.
After that, verify main, open PRs, CI, STATUS, CURRENT_HANDOFF, handoff_state, compiled_agent_context, rule registry files, document-management rules, and FINAL_SUMMARY_CONTRACT before any mutation.
If continuing after d, f, w, or any other short chat signal, first run agentic-kit evidence inspect locally or inspect equivalent committed remote/repo evidence.
```

## First chat command

1. Read this file completely from remote main.
2. Run or verify `agentic-kit boot check` and `agentic-kit boot prompt` if a local checkout is available.
3. Open every mandatory boot source listed below before repository mutation.
4. Report current main HEAD, open PRs, CI status, last clean evidence, and next smallest safe slice.
5. Before continuing after a chat control signal, use `agentic-kit evidence inspect` or equivalent remote/repo evidence inspection.

## Bootloader output

```text
CHAT_BOOTLOADER

Purpose: bootstrap a successor chat from repository truth.

Mandatory boot sources:
- [present] .agentic/compiled_agent_context.yaml
- [present] .agentic/handoff_state.yaml
- [present] .agentic/rule_mechanism_inventory.yaml
- [present] .agentic/rule_migrations.yaml
- [present] .agentic/rule_preservation.yaml
- [present] docs/STATUS.md
- [present] docs/handoff/CURRENT_HANDOFF.md
- [present] docs/handoff/START_NEW_CHAT_PROMPT.md
- [present] docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- [present] docs/governance/FINAL_SUMMARY_CONTRACT.md
- [present] docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- [present] docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- [present] docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- [present] docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
- [present] docs/planning/WORKFLOW_REDUCTION_FOCUS.md

Mandatory workflow rules:
- Start from repository artifacts instead of chat memory.
- Read mandatory boot sources before repository changes.
- Prefer Python runners for local workflow execution; shell remains a thin adapter.
- Use run_summary_renderer for final summaries in evidence-bearing workflows.
- Evidence-bearing local workflow finalization must use `agentic-kit evidence finalize-log` or a stricter successor. Freehand final PASS footers are not valid closeout evidence.
- Treat d, f, and w as communication signals rather than evidence.
- Run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence before continuing after chat control signals.
- Inspect repo or remote evidence before requesting pasted terminal output.
- Use the supported protected-change planning route before protected YAML, JSON, or Markdown control changes: `./ns protected-change-plan --diff-file <file>` or `python -m agentic_project_kit.protected_change_planner --diff-file <file>`. Do not use `agentic-kit protected-change-plan`; that package CLI command is not registered.
- Before a chat switch, run the closeout prompt and check whether START_NEW_CHAT_PROMPT.md, CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md, and NEXT_CHAT_BOOTSTRAP.md all need updates.

Required first action in a successor chat:
- Read these sources and verify main, open PRs, CI, STATUS, handoff, rule registry, and final-summary contracts before repository changes.
- If continuing after a chat control signal, run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence first.

### RESULT: PASS ###
```

## Next work items

- Finish local sync after the bootloader/summary-runner merge and verify boot write/check plus targeted tests.
- Use boot write to refresh docs/handoff/NEXT_CHAT_BOOTSTRAP.md before chat changes.
- Harden no-op/PASS_ALREADY_DONE handling for already satisfied target states.
- Use `agentic-kit evidence inspect --require-summary` after chat control signals so d/f/w do not rely on chat memory.
- Use `agentic-kit evidence finalize-log` for evidence-bearing local workflow closeout so invalid summary fields cannot still end in a freehand final PASS.
- Automate red CI failed-log diagnosis in the repo workflow path.
- Resume Rule Registry Phase A only in small PRs: typed schema, generated projections, stronger assertions, query/impact analysis, and documentation integration.
- Continue the document-management projection system: move operative truth into machine-readable sources and keep Markdown as generated or verified projection where possible.
- Postpone GUI work until the workflow kernel, no-op handling, evidence inspection, and red-CI diagnosis are stable.

## Final summary requirement

Evidence-bearing workflow outputs must use `agentic_project_kit.run_summary_renderer.SummaryPayload`, the Python workflow summary runner, or `agentic-kit evidence finalize-log`. Do not hand-write legacy final summaries.

### RESULT: PASS ###
