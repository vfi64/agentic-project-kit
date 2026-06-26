# Chat Communication Contract

Status-date: 2026-05-22
Status: normative governance contract
Scope: LLM-to-user, user-to-LLM, LLM-to-terminal, and terminal-to-LLM communication for agentic-project-kit work

## Purpose

This contract removes ambiguity from chat-assisted development. Communication shortcuts, terminal blocks, failure handling, and follow-up behavior must be interpreted from repository evidence, not from memory or good intentions.

Large LLMs must have less freedom, not more prose. The durable pattern is: read the required sources, verify current state, run deterministic checks, produce honest evidence, then continue.

## Required startup behavior for successor chats

A successor chat must not start with a terminal block, mutation, merge, release, or GUI feature patch. It must first read the mandatory source list from `.agentic/compiled_agent_context.yaml` and then the human governance documents named there.

Minimum first-read set:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. relevant source and test files for the requested slice

If any of these sources are missing, contradictory, stale, or unreachable, the chat must report drift and avoid mutation until the drift is resolved or a handoff prompt is produced.

## User acknowledgements

Short user replies are control signals, not evidence.

- `d` or `D`: the previous local block appears finished from the user's perspective. The assistant must still inspect terminal output, remote log, command report, PR state, branch, dirty state, and summary before treating it as success.
- `f` or `F`: the previous block failed or the user reports failure. The assistant must first look for local or remote evidence paths and propose log upload/recovery before asking for pasted output.
- `w` or `W`: continue, but only within the current governance and evidence rules.
- `paste-output`: manual output is needed because repo-backed or local evidence is unavailable, broken, or insufficient.
- `stop`: no further mutation or terminal instructions.

A suggested next chat reply for a failed workflow should normally be `f`, not `d`, when remote evidence exists but the work failed. Remote evidence can prove failure; it does not convert failure into success.

## LLM-to-user rules

The assistant must:

- state the current source of truth and evidence basis for any next action,
- separate product progress from workflow/evidence progress,
- report when a failure is caused by tooling, shell environment, summary rendering, CI, docs, tests, or product code,
- avoid asking for full pasted output when a local or remote log path exists,
- prefer a minimal evidence-recovery step over a large new patch after failure,
- never treat a user's `d` as proof that the work passed,
- never hide that a block was only partially executed,
- explicitly say when remote evidence is unavailable.

## LLM-to-terminal rules

Canonical workflow execution must not depend on long ad-hoc shell blocks. When terminal execution is unavoidable, the block must be bounded, copy-safe, and evidence-aware.

Forbidden as canonical control mechanisms:

- heredocs,
- risky multi-line `python -c` strings,
- raw decoration lines that execute as shell commands,
- implicit POSIX tools as correctness dependencies,
- status variables mutated inside `{ ... } | tee "$LOG"` pipeline/subshell constructs,
- handwritten legacy summary footers after `./ns summary`,
- `REMOTE_EVIDENCE: PENDING` in final summaries,
- continuing to PR creation, merge, release, or tagging after a blocking gate failure.

Allowed routes:

- repository-owned Python runners,
- `agentic-kit` CLI commands backed by Python core logic,
- `./ns` as a thin convenience adapter when the local shell is healthy,
- generated command reports and terminal logs stored under the documented evidence paths.

## Terminal-to-LLM rules

Every non-trivial terminal or remote command workflow must end in evidence that the assistant can inspect:

- a rendered final summary printed in the terminal output,
- the same rendered final summary captured in the terminal log or command report,
- a terminal log path or command report path,
- branch and dirty-state evidence when mutation occurred,
- PR/CI/merge state when remote mutation occurred,
- explicit downgrade when evidence is partial, chat-only, or failed.

A chat-only structured summary is not enough for terminal-directed work. The terminal block must render the structured summary itself, normally through `./ns summary`, so the evidence remains inspectable after chat handoff.

A terminal log upload is evidence transport. It does not change the result of failed work.

If a terminal summary names a concrete remote log path, verify that exact path directly before using search results. Search lag is not evidence that a pushed log is missing.

## Failure communication

On failure, the next assistant response must choose the least lossy recovery path:

1. inspect remote evidence if available,
2. inspect local log path if the user pasted it,
3. propose a minimal log-upload or status-recovery step,
4. ask for pasted output only when evidence cannot be retrieved or uploaded.

A blocking gate failure must stop later mutation sections. The final result must identify the first blocking failure and the actual state reached.

## PASS communication

A final PASS claim requires all of the following:

- required work passed,
- required gates passed or were honestly marked not run/not required,
- evidence exists and matches the claim,
- remote evidence is PASS when the workflow requires no-copy continuation,
- no earlier required inner FAIL was overwritten,
- the final summary is rendered through the canonical renderer route,
- terminal-directed work printed the structured summary in the terminal output and captured it in the terminal log.

## Optimization requirement

For every future rule or workflow step, prefer the option that reduces LLM discretion, reduces duplicated wording, improves portability, and makes drift machine-detectable. If a rule cannot yet be machine-checked, it must name the review-only exception and the evidence a reviewer must inspect.

Manual GUI verification must not hide the final result behind an interactive terminal read prompt. Use a two-phase record: GUI launch first, then a non-interactive PASS or FAIL evidence record with a generated summary invocation.

## Mandatory no-copy transfer rules

For assistant-initiated local work, complete terminal output must be captured in a repo-backed transfer or evidence file. The record must contain stdout, stderr, exit code, argv, start time, end time, current branch, HEAD, dirty-state evidence, and a concrete log or command-report path. A normal FAIL must still produce inspectable evidence; the assistant must not ask for pasted output when the transfer file exists or can be pushed.

Local tasks must normally be provided as repo-backed Python programs, typed work orders, or `agentic-kit` commands and must run through the repository virtual environment. Global Python, global shell state, long ad-hoc shell blocks, risky multi-line `python -c`, and raw visual separator lines as terminal commands are forbidden as default control paths.

Manual copy-and-paste of terminal output is allowed only after a hard local failure that prevents evidence creation or transfer, including kill -9, process startup failure, terminal loss, machine crash, filesystem failure, network failure before push, or explicitly broken logging.

## Preferred dialog signals

The preferred dialog signals are `d` for done, `f` for fail, and `g` for go. `g` replaces the former German `w` signal for continuing with the next safe planned step. `w` remains accepted as a legacy alias for `g` during transition, but new tooling and generated instructions should prefer `g`.

The local command aliases are `agentic-kit rn` for run-next/remote-next and `agentic-kit rnc` for remote-next closeout. GUI controls must use these aliases rather than introducing a separate execution model.

### Communication rule refresh handshake

`d2` is a mandatory rule-loading dialog state, not a normal continuation signal.

`agentic-kit rules communication-refresh --publish --json` writes the communication rule capsule metadata and a local pending state with `required_next_reply=d2`. A normal `g` continuation must not bypass that pending state.

The refresh file is not magical LLM memory. The assistant must read the remote rule capsule at `docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md`, verify the expected blob hash, and provide a machine-readable `RULE_REFRESH_ACK` before mutating workflows continue.

`agentic-kit rules acknowledge-communication-refresh --ack-file <path> --json` validates that ACK. `agentic-kit rules require-current-communication-context --json` blocks when a `d2` pending state exists without a matching ACK.

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
