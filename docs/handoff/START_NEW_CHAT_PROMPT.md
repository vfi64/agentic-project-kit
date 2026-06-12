---
schema_version: 2
artifact_type: chat_switch_prompt
role: start_new_chat
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
successor_context: docs/reports/handoff-packages/latest/successor_context.yaml
paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - successor_context.yaml
  - source_manifest.json
  - validation_report.json
  - agentic-kit transfer chat-switch-complete
  - AGENTS.md
  - README.md
  - SECURITY.md
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Start New Chat Prompt

Copy `docs/reports/handoff-packages/latest/successor_prompt.md` into the successor chat.

The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.

If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.\n## Operational documentation refresh state after PR #1272\n\nCurrent administrative handoff refresh state is `58f1fe76` (`Refresh successor handoff after PR1271 (#1272)`). Continue next only after this post-PR1272 refresh is committed and merged; the next substantive slice must be created from fresh main.\n