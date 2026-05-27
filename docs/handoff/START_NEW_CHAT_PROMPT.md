---
schema_version: 1
artifact_type: chat_switch_prompt
role: start_new_chat
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - evidence inspect
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Start New Chat Prompt

This file is the canonical prompt for starting a successor chat. It is paired with `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md` and `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`.

If this prompt changes, the closeout prompt and `NEXT_CHAT_BOOTSTRAP.md` may also need to be updated. A closeout slice must check all three files before a chat switch.

Current administrative handoff state after PR #838: main contains `777d957474318fdf797ca23625e52046c3fb7df0` (`Refresh post-PR837 administrative handoff state (#838)`). The substantive safe-state may intentionally remain at the last substantive work commit when `safe_state.semantics: last_substantive_work_state` is set; later handoff-only refreshes belong in `administrative_evidence_state`.

## Prompt to copy into the successor chat

```text
We work in repo vfi64/agentic-project-kit.

Do not start from chat memory. Source of truth is the remote repository: main, PRs, CI, tags, releases, issues, and repo artifacts.

First read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main completely and execute its boot routine.

Before any repository mutation, verify:

- current main HEAD
- open PRs and CI status
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/handoff/NEXT_CHAT_BOOTSTRAP.md
- .agentic/handoff_state.yaml
- .agentic/compiled_agent_context.yaml
- .agentic/rule_mechanism_inventory.yaml
- .agentic/rule_migrations.yaml
- .agentic/rule_preservation.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
- docs/planning/WORKFLOW_REDUCTION_FOCUS.md

Report briefly:

1. current main HEAD,
2. open PRs and CI status,
3. whether NEXT_CHAT_BOOTSTRAP.md is current enough,
4. whether STATUS, CURRENT_HANDOFF, and handoff_state are consistent,
5. last clean verified state,
6. next smallest safe slice.

Important:

- d, f, and w are communication signals, not evidence.
- After d, f, w, or any other short chat control signal, run `agentic-kit evidence inspect` locally or inspect equivalent committed remote/repo evidence before continuing.
- Do not ask for pasted terminal output before checking available repo or remote evidence.
- Do not mutate product state before full boot verification.
- Protected YAML, JSON, and Markdown control files require protected change planning.
- Evidence-bearing workflows must use the structured summary renderer or Python workflow summary runner.
- Before the next chat switch, run a closeout slice using docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md. That closeout may need to update this prompt, the closeout prompt, and docs/handoff/NEXT_CHAT_BOOTSTRAP.md.
```
