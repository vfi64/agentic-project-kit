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

Command manifest entrypoint:
- MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json (manifest_sha: 799be87e8212). Every reply containing commands MUST start with: COMMAND_MANIFEST_ACK 799be87e8212. Consult `agentic-kit command-for` before proposing commands and choose the most specific available Kit workflow command.
- Before proposing ANY command run/consult `agentic-kit command-for` and choose the most specific available Kit workflow command.
- raw git/gh commands with a mapped wrapper are rejected by instruction lint.

Command reference contract:
- Read `docs/reference/agentic-kit-commands.json` before composing agentic-kit commands.
- Read `docs/reference/AGENTIC_KIT_COMMANDS.md` before composing agentic-kit commands.
- `must_not_reconstruct_commands_from_memory: true`.
- Treat `source_hashes` as freshness evidence.
source_hashes:
- docs/reference/AGENTIC_KIT_COMMANDS.md: e8ab7fa796fae23f6304daf40ea2a238c72706c2761d3efec04015781275fd78
- docs/reference/agentic-kit-commands.json: 9843a0ce0694924b0cb64b6a9d30de7c0c61e69de20ed81708deb3b9f739eea2
