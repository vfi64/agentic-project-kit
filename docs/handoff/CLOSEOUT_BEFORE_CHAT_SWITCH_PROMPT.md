---
schema_version: 1
artifact_type: chat_switch_prompt
role: closeout_before_chat_switch
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
paired_prompt: docs/handoff/START_NEW_CHAT_PROMPT.md
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
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Closeout Before Chat Switch Prompt

This file is the canonical closeout prompt for the current chat before starting a successor chat. It is paired with `docs/handoff/START_NEW_CHAT_PROMPT.md` and `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`.

If this prompt changes, the start prompt and `NEXT_CHAT_BOOTSTRAP.md` may also need to be updated. A closeout slice must check all three files before a chat switch.

## Prompt to run before leaving the current chat

```text
Create a final follow-up / closeout slice for the next chat.

Goal: A successor chat must be able to reconstruct all current workflow rules, bootloader rules, open work, last verified state, and next safe slice from docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main.

Scope: no product work. This is a handoff/bootstrap closeout only.

Steps:

1. Inspect remote truth first:
   - main HEAD
   - open PRs
   - CI status
   - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
   - docs/handoff/START_NEW_CHAT_PROMPT.md
   - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
   - docs/STATUS.md
   - docs/handoff/CURRENT_HANDOFF.md
   - .agentic/handoff_state.yaml
   - .agentic/compiled_agent_context.yaml
   - Rule Registry files
   - relevant planning documents

2. Check whether NEXT_CHAT_BOOTSTRAP.md and both chat-switch prompt files include the current state:
   - last main HEAD or last verified state,
   - open PRs,
   - next work items,
   - known standard failures,
   - boot commands,
   - mandatory boot sources,
   - final-summary rules,
   - Rule Registry and document-management work,
   - GUI deferral,
   - no-op / PASS_ALREADY_DONE,
   - d/f semantics,
   - red CI failed-log diagnosis.

3. If any file is stale:
   - build a small PR that only updates bootstrap/handoff prompt state,
   - use agentic-kit boot write or write_next_chat_bootstrap() where applicable,
   - update docs/handoff/START_NEW_CHAT_PROMPT.md and docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md if their contracts or prompt wording changed,
   - run targeted tests for chat boot, workflow summary runner, run summary renderer, and any affected handoff/governance tests,
   - wait for CI,
   - if CI is red, fetch failed job logs in the same diagnostic path,
   - merge only after green CI.

4. If all files are current:
   - state that explicitly with remote evidence,
   - name main HEAD,
   - name docs/handoff/NEXT_CHAT_BOOTSTRAP.md as the canonical successor-chat entry point.

5. Final answer must contain only:
   - Status: BOOTSTRAP_CURRENT or BOOTSTRAP_REFRESHED,
   - main HEAD,
   - open PRs,
   - last verified state,
   - next safe slice,
   - the short start prompt from docs/handoff/START_NEW_CHAT_PROMPT.md.

Do not start new product work in this closeout slice.
```
