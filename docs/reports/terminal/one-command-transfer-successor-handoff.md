# One-Command Transfer Successor Handoff

Status: handoff only, not a PASS closeout
Date: 2026-06-03
Branch: `feature/harden-release-publish-head-guards`
Base observed: `main` at `e4714010eee0dc499e7f010dea67f14b7fb43d2b`

## Stop condition

Do not continue release-publish product work in the successor chat.
Do not merge this branch as-is.
Do not rewrite protected governance, handoff, YAML, or Markdown control files before running the protected-change workflow.

## Current remote state

Open PRs observed before this handoff: none.

Feature branch `feature/harden-release-publish-head-guards` is ahead of `main` and contains mixed WIP:

- partial release-publish core and CLI work,
- branchless remote-next bootstrap work,
- transfer reports and outbox evidence,
- a machine-readable one-command transfer protocol,
- a known syntax error in `tests/test_transfer_remote_next.py`,
- a queued payload for fixing that syntax error.

The branch is not clean enough to merge.

## Known failing evidence

Latest published transfer report before this handoff showed:

- label: `one-command-transfer-rule-bootstrap-plan`
- result: FAIL/BLOCK
- failing step: pytest collection
- file: `tests/test_transfer_remote_next.py`
- reason: `SyntaxError: unterminated string literal`

The broken local/remote file has a split string around the dirty worktree test. The queued payload file is:

```text
.agentic/transfer/payloads/fix-remote-next-test-syntax.py
```

The intended transfer order file was attempted at:

```text
.agentic/transfer/inbox/current.yaml
```

but the file was not found remotely during handoff inspection after the attempt. The next chat must verify whether it exists locally or remotely before using it.

## Machine-readable protocol artifact

The requested one-command transfer protocol is recorded in English at:

```text
.agentic/transfer/one_command_transfer_protocol.yaml
```

It says the user command must permanently be:

```zsh
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
./.venv/bin/agentic-kit transfer remote-next
```

The user replies only:

```text
g
```

`g` means the assistant must read newest remote-backed evidence, or treat missing/stale remote evidence as BLOCK/TRANSFER_UPLINK_PROBLEM.

## User-approved protocol requirement

The next implementation slice must focus only on making `agentic-kit transfer remote-next` a block-tolerant one-command wrapper.

Required properties:

1. `remote-next` must not require a branch argument.
2. The branch must come from a transfer order or derived remote-next configuration.
3. The local checkout may be blocked before remote-next runs.
4. The wrapper must still emit a stable diagnostic report on blocked state.
5. The wrapper must capture current branch, HEAD, rule-ack status, dirty state, untracked files, staged and unstaged files, branch-switch safety, pull safety, report creation capability, and remote publication capability.
6. If work can proceed, it must execute the transfer order, publish the report, commit report files if possible, refresh rule ack after commit if needed, and push if possible.
7. All of that must be captured in one execution report.
8. The assistant must not ask the user to run several local transfer commands in fallback mode after this is implemented.
9. Every local-to-LLM transfer file must carry the machine-readable protocol header to reduce LLM drift.

## Recommended next safe slice

One isolated slice only:

```text
Harden `agentic-kit transfer remote-next` as a block-tolerant one-command transfer wrapper.
```

Do not touch release-publish until this slice is green and merged.

## Minimal successor chat prompt

Use this prompt in the next chat:

```text
We work in repo vfi64/agentic-project-kit.

Do not start from chat memory. Read remote repository truth first.

Primary goal of this chat only:
Finish the one-command transfer protocol. Do not continue release-publish product work.

Start by reading, in this order:

- docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main
- docs/handoff/START_NEW_CHAT_PROMPT.md
- docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- .agentic/compiled_agent_context.yaml
- .agentic/handoff_state.yaml
- .agentic/transfer/one_command_transfer_protocol.yaml on branch feature/harden-release-publish-head-guards
- docs/reports/terminal/one-command-transfer-successor-handoff.md on branch feature/harden-release-publish-head-guards

Important:

- There are no open PRs expected at handoff creation, but verify this remotely.
- Branch feature/harden-release-publish-head-guards is WIP and must not be merged as-is.
- The branch contains a known test syntax error in tests/test_transfer_remote_next.py.
- The next safe slice is to harden transfer remote-next as a block-tolerant one-command wrapper.
- The permanent user command must be exactly:

cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
./.venv/bin/agentic-kit transfer remote-next

- The user replies only with g.
- After g, inspect latest remote evidence yourself and infer PASS/FAIL/BLOCK/WAIT.
- Do not ask for long terminal output while repo-backed or local diagnostic paths exist.
- Do not give the user multi-command local sequences once the remote-next wrapper is the target mechanism; if bootstrap exceptions are necessary, label them explicitly and keep them minimal.
- Repo files must be in English.
```

## Not done

- No protected-change plan was run for governance/handoff prompt updates.
- No CI was run on a PR for this branch.
- No merge was performed.
- No release-publish completion was achieved.
- No final PASS is claimed.
