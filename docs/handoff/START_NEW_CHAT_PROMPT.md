## Post-PR1245 Administrative Handoff Refresh State

Current main/admin HEAD: `e97af592` (`Refresh handoff state after PR1244 (#1245)`).
Last substantive work marker: `7f5a331` / PR #1244 (`Enforce operational handoff document freshness`).

This is an administrative handoff/evidence refresh after PR #1244. It does not replace the substantive safe-state intent. It exists so operational handoff freshness no longer points at stale PR1011-era prompts.

Next safe substantive slice: implement the professional operational documentation projection system from a machine-readable state source, with generated blocks, preservation of curated documentation, rule-registry coverage, and drift gates.

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

Current operational handoff state after PR #1243: main contains `88e01f46f4928174ea241039e0a863f28570130a` (`88e01f46`), `Refresh handoff state after PR1242 (#1243)`. Last substantive work state is `4bf3da29` (`Render transfer payload commands as compact summaries (#1242)`). Successor chats must verify STATUS, CURRENT_HANDOFF, this prompt, NEXT_CHAT_BOOTSTRAP, and the active roadmap against these current safe/admin markers before product work.

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

## Operational documentation projection state after PR #1249

Current operational documentation projection state is `dfb7c2ba` (`Introduce operational handoff projection source (#1249)`). PR #1249 introduced `.agentic/operational_handoff_state.yaml` as the first machine-readable operational handoff state source and projects the current operational bootstrap block from that source. Continue next with Slice 2: generated-block markers and targeted block updates while preserving curated documentation.

## Operational documentation refresh state after PR #1250

Current administrative handoff refresh state is `9d24918d` (`Refresh operational state after PR1249 (#1250)`). PR #1250 refreshed the post-PR1249 operational handoff state and registered the operational handoff state projection source for Protected Planner coverage. Continue next only after this post-PR1250 refresh is committed and merged; the next substantive documentation step remains Slice 2: generated-block markers and targeted generated-block updates while preserving curated documentation.

## Operational documentation refresh state after PR #1253

Current administrative handoff refresh state is `d23c9a9f` (`Add generated operational handoff markers (#1253)`). PR #1253 added generated-block markers around the projected operational handoff block. Continue next only after this post-PR1253 refresh is committed and merged; the next substantive documentation step is Slice 2b from fresh main.

## Operational documentation refresh state after PR #1255

Current administrative handoff refresh state is `3f111f1d` (`Add generated operational handoff block replacement (#1255)`). PR #1255 added targeted replacement of the marked generated operational handoff block while preserving curated surrounding documentation. Continue next only after this post-PR1255 refresh is committed and merged; the next substantive documentation slice must be created from fresh main.
