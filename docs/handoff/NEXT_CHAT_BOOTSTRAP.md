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
