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
agentic-kit transfer chat-switch-complete --render-prompt
```

The command must generate the package files, update the three canonical chat-switch prompt files, validate that no stale or accumulative markers remain, and print the copy/paste successor prompt.

Do not start product work in this closeout. If validation fails, repair the handoff projection first.

Command manifest entrypoint:
- MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json (manifest_sha: 8c79745610b0). Every reply containing commands MUST start with: COMMAND_MANIFEST_ACK 8c79745610b0. Consult `agentic-kit command-for` before proposing commands and choose the most specific available Kit workflow command.
- Before proposing ANY command run/consult `agentic-kit command-for` and choose the most specific available Kit workflow command.
- raw git/gh commands with a mapped wrapper are rejected by instruction lint.

Command reference contract:
- Read `docs/reference/agentic-kit-commands.json` before composing agentic-kit commands.
- Read `docs/reference/AGENTIC_KIT_COMMANDS.md` before composing agentic-kit commands.
- `must_not_reconstruct_commands_from_memory: true`.
- Treat `source_hashes` as freshness evidence.
source_hashes:
- docs/reference/AGENTIC_KIT_COMMANDS.md: d4158b36ba2650219780747758ca4c281433bcc7dab3ea1733b69c0d9b01cb61
- docs/reference/agentic-kit-commands.json: a99e6eb2d327d46084140fdf73b2b868a0f798b80ccd3287120daabcccd1e575
