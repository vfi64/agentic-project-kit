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

Current administrative handoff state after PR #880: main contains `f853ccf770e5f692ca2815912b252e453259fc69` (`f853ccf`), `Merge pull request #880 from vfi64/fix/handoff-freshness-admin-merge-chain`. PR #880 is administrative handoff-freshness hardening; verified release remains v0.4.4, Zenodo version DOI `10.5281/zenodo.20431326`. Successor chats must verify this state before GUI product work. The next safe product slice is GUI deterministic gatekeeper migration as read-only inspection/inventory only.

Historical administrative handoff state after PR #838: main contains `777d957474318fdf797ca23625e52046c3fb7df0` (`Refresh post-PR837 administrative handoff state (#838)`). The substantive safe-state may intentionally remain at the last substantive work commit when `safe_state.semantics: last_substantive_work_state` is set; later handoff-only refreshes belong in `administrative_evidence_state`.

## Post-Merge Handoff Refresh Status Gate

After every PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status before product work.

Interpretation is machine-derived:

- result=NOOP: continue without an administrative handoff refresh.
- result=REFRESH_REQUIRED: create an administrative handoff refresh slice before product work.

This is not a chat-judgement step. The kit decides whether a post-merge handoff refresh is required; d, f, and w remain communication signals only.

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
\n\n## Canonical transfer communication command\n\nFor successor-chat starts, transfer retries, and short control signals, prefer the single communication wrapper:\n\n```text\n./.venv/bin/agentic-kit transfer continue\n```\n\nThis wrapper must run before falling back to lower-level `remote-next`, `restore-known-volatile`, or manual command sequences. A chat may continue after `g` only after inspecting the fresh remote report produced by this wrapper.\n

<!-- agentic-kit:command-reference-lifecycle-discipline:start -->
## Non-optional command-reference and lifecycle discipline

This section is normative for successor-chat handoff, transfer-file workflows, and local execution guidance.

### Command Reference is the source of truth

A chat must not reconstruct `agentic-kit` or `agentic-kit transfer` commands from memory, prior examples, or guessed parameter names.

Before writing a transfer file, giving a copy/paste command, or choosing a local execution path, the chat must treat these files as required sources of truth:

- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`

If a command or option is unclear, the chat must inspect the Command Reference or run the corresponding `--help` locally through an appropriate repo-backed transfer. Guessing command options is a process error.

### Wrapper-first rule

When planning local control, the chat must prefer existing complex `agentic-kit` wrappers over hand-built shell sequences.

Priority order:

1. Existing `agentic-kit` or `agentic-kit transfer` wrapper.
2. Canonical transfer file that invokes the wrapper.
3. Copy/paste shell sequence only when no suitable wrapper exists or the wrapper is proven blocked.

### Canonical PR lifecycle

After a checked patch, do not manually merge as the primary path.

For a new PR, use:

    ./.venv/bin/agentic-kit transfer pr-create-complete --title "<PR title>" --body "<PR body>" --base main --head current --merge-method squash

For an existing PR, use:

    ./.venv/bin/agentic-kit transfer pr-complete <PR_NUMBER> --expected-head-sha current --merge-method squash

If `current` is not accepted or if the branch has to be pinned explicitly, resolve the exact head SHA with `git rev-parse HEAD` and pass that SHA. Do not guess unsupported options.

### Canonical post-merge closeout and remote report

After a successful merge, the required closeout is:

    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-complete --after-pr <PR_NUMBER>
    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-check
    ./.venv/bin/agentic-kit transfer repo-status

`post-merge-complete --after-pr <PR_NUMBER>` is the canonical wrapper that creates post-merge evidence and publishes the transfer report into the remote repository.

`run-and-log` is useful for diagnostics and fallback evidence, but it is not a substitute for `post-merge-complete` after a merge.

### Volatile transfer-output hygiene

Before branch switches, PR completion, or merge-safe operations, known volatile transfer outputs must not be allowed to block the lifecycle.

At minimum, clean these local-only volatile paths when they are dirty and not the target of the current slice:

    git restore -- .agentic/transfer/outbox/last_result.txt
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log

This cleanup is a workaround for volatile report files. It must not be used to discard substantive source, governance, planning, or handoff changes.
<!-- agentic-kit:command-reference-lifecycle-discipline:end -->

