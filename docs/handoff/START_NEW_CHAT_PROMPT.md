---
schema_version: 2
artifact_type: chat_switch_prompt
role: start_new_chat
current_handoff_marker: eba9247c
current_branch_at_generation: codex/harden-gui-initial-prompt-and-task-editor
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

Current handoff marker: `1becc4a7`.

Copy `docs/reports/handoff-packages/latest/successor_prompt.md` into the successor chat.

The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.

If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.## Operational documentation refresh state after PR #1303

Current administrative handoff refresh state is `794ceff0` (`Fix operational handoff refresh newlines (#1303)`). Continue next only after this post-PR1303 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1307

Current administrative handoff refresh state is `e88a5591` (`Harden successor package freshness gates (#1307)`). Continue next only after this post-PR1307 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1311

Current administrative handoff refresh state is `afc21ade` (`Project bootstrap gate into successor package (#1311)`). Continue next only after this post-PR1311 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1317

Current administrative handoff refresh state is `23c913f9` (`Refresh successor package after PR1316 (#1317)`). Continue next only after this post-PR1317 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1324

Current administrative handoff refresh state is `75d7a3d3` (`Refresh successor package during admin handoff refresh (#1324)`). Continue next only after this post-PR1324 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1330

Current administrative handoff refresh state is `a7a0b6a2` (`Audit ns to agentic-kit migration before GUI (#1330)`). Continue next only after this post-PR1330 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1334

Current administrative handoff refresh state is `c6ab40da` (`Classify ns migration docs before GUI (#1334)`). Continue next only after this post-PR1334 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1338

Current administrative handoff refresh state is `979825da` (`Remove ns dev go up shortcuts (#1338)`). Continue next only after this post-PR1338 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1839

Current administrative handoff refresh state is `dfe1c970` (`Add GUI project root selection (#1839)`). Continue next only after this post-PR1839 refresh is committed and merged; the next substantive slice must be created from fresh main.
