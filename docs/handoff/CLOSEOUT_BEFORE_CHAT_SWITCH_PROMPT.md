---
schema_version: 2
artifact_type: chat_switch_prompt
role: closeout_before_chat_switch
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
successor_context: docs/reports/handoff-packages/latest/successor_context.yaml
paired_prompt: docs/handoff/START_NEW_CHAT_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - successor_context.yaml
  - source_manifest.json
  - validation_report.json
  - agentic-kit transfer chat-switch-complete
  - protected-diff-plan
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Closeout Before Chat Switch Prompt

Before leaving a chat, run the deterministic successor handoff package command:

```bash
cd /path/to/
./.venv/bin/agentic-kit transfer chat-switch-complete --render-prompt
```

The command must generate the package files, update the three canonical chat-switch prompt files, validate that no stale or accumulative markers remain, and print the copy/paste successor prompt.

Do not start product work in this closeout. If validation fails, repair the handoff projection first.
