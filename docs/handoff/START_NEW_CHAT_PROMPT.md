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

If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.\n## Operational documentation refresh state after PR #1272\n\nCurrent administrative handoff refresh state is `58f1fe76` (`Refresh successor handoff after PR1271 (#1272)`). Continue next only after this post-PR1272 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1273\n\nCurrent administrative handoff refresh state is `509d4119` (`Refresh successor handoff after PR1272 (#1273)`). Continue next only after this post-PR1273 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1274\n\nCurrent administrative handoff refresh state is `4d536e2c` (`Refresh successor handoff after PR1273 (#1274)`). Continue next only after this post-PR1274 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1275\n\nCurrent administrative handoff refresh state is `f56fee9b` (`Refresh successor handoff after PR1274 (#1275)`). Continue next only after this post-PR1275 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1276\n\nCurrent administrative handoff refresh state is `22e1e13d` (`Refresh successor handoff after PR1275 (#1276)`). Continue next only after this post-PR1276 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1277\n\nCurrent administrative handoff refresh state is `e3d5cf4a` (`Refresh successor handoff after PR1276 (#1277)`). Continue next only after this post-PR1277 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1278\n\nCurrent administrative handoff refresh state is `de4f1bc7` (`Refresh successor handoff after PR1277 (#1278)`). Continue next only after this post-PR1278 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1279\n\nCurrent administrative handoff refresh state is `79795ae3` (`Refresh successor handoff after PR1278 (#1279)`). Continue next only after this post-PR1279 refresh is committed and merged; the next substantive slice must be created from fresh main.\n\n## Operational documentation refresh state after PR #1281\n\nCurrent administrative handoff refresh state is `dfb22003` (`Skip admin refresh for refresh-only PRs (#1281)`). Continue next only after this post-PR1281 refresh is committed and merged; the next substantive slice must be created from fresh main.\n