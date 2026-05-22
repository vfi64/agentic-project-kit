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
