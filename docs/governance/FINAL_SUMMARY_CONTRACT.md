## Final summary contract

Every relevant workflow block must end with the framed SUMMARY contract. This contract is durable and must not disappear across chats, handoffs, or command-generation paths.

Required block:

```text
================================================================
SUMMARY

SLICE
  NAME: <slice-name>
  SCOPE: <short scope>
  BRANCH: <branch-or-NONE>

EXECUTION
  ORIGIN: local|remote|mixed
  STATE_MODE: local|remote|unknown
  MODE_CHECK: pass|fail|not_run
  SWITCH_HINT: ./ns mode-write local|remote && ./ns mode-check local|remote

RESULT
  WORK: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND
  EVIDENCE: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED
  OVERALL: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND

REMOTE
  REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED
  PR: #<number> open|merged|none
  HEAD_SHA: <sha-or-NONE>
  CI: pass|fail|in_progress|not_started|unknown
  MERGE: done|not_done|blocked|not_required

EVIDENCE FILES
  terminal_log: docs/reports/terminal/<file>.log|NONE
  command_report: docs/reports/command_runs/<file>.md|NONE

INTERPRETATION
  <one short sentence explaining what the result really means>

NEXT
  SAFE_STEP: <next concrete action>
  CHAT_REPLY: d|f|w|paste-output|stop

### RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND ###
================================================================
```

This is the preferred end marker for agent-directed terminal blocks, remote command reports, release work, merge verification, and handoff-sensitive work. Short local experiments may use a smaller marker, but any state-changing or evidence-bearing workflow must use the framed SUMMARY.

## Terminal output requirement

The structured SUMMARY must be printed by the terminal block itself and captured in the terminal log. A chat-only summary is not sufficient for a relevant workflow block.

For terminal-directed work, the final visible terminal output must contain the rendered summary block from `./ns summary` or `agentic_project_kit.run_summary_renderer`. The chat response may repeat or interpret the result, but it must not be the only place where the structured summary exists.

A terminal block that ends with only `### RESULT: PASS ###` or `### RESULT: FAIL ###` is incomplete for state-changing, evidence-bearing, recovery, merge, release, CI, documentation-governance, or handoff-sensitive work.

## No executable placeholder summaries

Executable terminal blocks must never print final SUMMARY fields with placeholder alternatives such as `PASS|FAIL`, `p|paste-output`, or ellipsis markers. A copied block must end with one concrete outcome only. Placeholder examples are allowed only in prose documents when clearly marked as non-executable examples.


## Deterministic failure semantics

A final `PASS` is invalid when any required inner work result, required gate, or required verification is `FAIL`.

`REMOTE_EVIDENCE: PASS` requires committed and pushed evidence or an equivalent remote-readable report. A local-only transcript, chat paste, queued CI run, or unpushed temporary log is not remote evidence.

A successful evidence upload can prove a failed run; it must not relabel failed work as `WORK RESULT: PASS`.

## Terminal-log mandate for local mutation blocks

A non-trivial local mutation block must not claim `REMOTE_EVIDENCE: PASS` with `terminal_log=NONE`.

For local mutation work, `terminal_log=docs/reports/terminal/` is the expected repo-readable evidence path. A chat-only transcript can explain a failed local run, but it is not remote evidence.

If a block mutates files, creates commits, pushes branches, opens PRs, or merges PRs, the final summary must either name a repo-readable terminal log or explicitly downgrade evidence to `CHAT_ONLY`, `PARTIAL`, or `FAIL`.

## Logged-block status propagation guard

A log-backed local mutation block must not control final PASS or FAIL through `STATUS` mutations inside a pipeline/subshell logging construct such as `{ ... } | tee "$LOG"`.

Reason: POSIX shells may run the left side of a pipeline in a subshell, so `STATUS=1` set inside the logged block can be lost and a false PASS can be printed.

Allowed routes are a dedicated runner, a command-report path, or direct file-descriptor redirection to a temporary log followed by copying the log into `docs/reports/terminal/` only after gates pass.

If a block detects a failed test, failed gate, failed mode check, or failed remote mutation, the final `RESULT` section must report `WORK: FAIL` and must not be overwritten by logging plumbing.

## Communication summary id contract

Every final summary must include a deterministic communication id header in the form `SUMMARY COMM-xxxxx | YYYY-MM-DD HH:MM:SS +ZZZZ`.

The canonical counter is stored in `.agentic/communication_state.json`. The counter is incremented through `./ns comm-next-summary`; the state is checked through `./ns comm-check`.

The counter provides an audit reference for local, remote, and mixed execution summaries. It must not be silently renumbered after publication.

The header must not repeat branch, origin, or mode; those values belong in the structured `SLICE` and `EXECUTION` blocks.


## \nRequired evidence fields for rendered summaries:\n\n- `terminal_log_remote`: committed/pushed log path, or `NONE` when unavailable.\n- `terminal_log_local`: local temporary log path, or `NONE` when not created.\n- `command_report`: committed command report path, or `NONE`.\n\nDeterministic renderer usage

New local mutation runbooks must render final summaries through `./ns summary`, which delegates to `agentic_project_kit.run_summary_renderer`.
Handwritten multi-line `printf` summary blocks are deprecated for new runbooks because they repeatedly caused drift between WORK, EVIDENCE, OVERALL, remote-log, and next-reply fields.
A local failure may reference a tmp log only as `terminal_log_local`; it must not claim remote evidence unless a `docs/reports/terminal/` log was committed and pushed.
The accepted terminal block pattern is: collect results in variables, persist the remote log when gates pass, then call `./ns summary` once.
## No legacy handwritten summary fallback

All relevant workflow blocks must produce their final framed summary through the deterministic renderer route `./ns summary` or the Python module `agentic_project_kit.run_summary_renderer`. Handwritten multi-line `printf` summary blocks are not an acceptable fallback after the renderer exists. A block that mixes old `WORK RESULT:` / `NEXT_CHAT_REPLY:` output with the newer structured renderer format is a contract failure, even if the final line says `### RESULT: PASS ###`.

Every summary invocation must provide at least `--slice`, `--scope`, `--branch`, `--work`, `--evidence`, `--overall`, and `--terminal-log`. For logged local mutation blocks, both `--terminal-log-remote` and `--terminal-log-local` must be set honestly. If no remote log was committed, the summary must say `REMOTE_EVIDENCE: FAIL` or `CHAT_ONLY` as appropriate and must not claim remote evidence.


## Chat acknowledgement and renderer-terminal-log rule

A short chat acknowledgement such as `d`, `D`, `f`, or `F` only means that the local terminal block has finished. It is not evidence of success or failure. Before continuing, inspect the previous terminal output or available log evidence for contradictions, including earlier FAIL markers, renderer errors, accidental branch creation, missing committed remote logs, PASS-after-failure contradictions, legacy summary formats, and duplicate or conflicting final anchors.

Rendered summaries must provide a real `terminal_log` value. `terminal_log: NONE` is invalid even when `REMOTE_EVIDENCE` is `NOT_REQUIRED` or the evidence class is `CHAT_ONLY`. For read-only or chat-only work, use a truthful local transcript path in `terminal_log` and `terminal_log_local`, and keep `terminal_log_remote: NONE` unless the log has actually been committed and pushed.

After `./ns summary`, do not append a handwritten legacy result footer. The renderer output is the final result anchor. A handmade footer may only appear inside older archived logs, not in new workflow blocks.

## Stop-after-fail and post-release gate separation

A workflow block must not continue into later mutation, PR creation, merge, tag, release, or post-merge verification sections after a blocking gate has failed. The final summary must report the failed gate and the branch actually reached.

`release-check` verifies pre-publication readiness and intentionally fails once the target tag or GitHub Release exists. Post-publication and DOI closeout blocks must use `post-release-check`, release visibility checks, DOI text verification, and normal project gates instead.

A PR state where checks are not yet reported must be represented as `CI: not_reported` or equivalent. It is not `CI: PASS`.

## Terminal log finalization rule

A relevant terminal block must not upload a partial running log before the final state lines are written.
The terminal log uploaded to `docs/reports/terminal/*.log` must include the rendered structured SUMMARY and the FINAL STATE section, or the block must explicitly mark the evidence as partial.
Preferred implementation: write the complete output to a temporary log, append SUMMARY and FINAL STATE, stop writing to that log, then copy the completed log into `docs/reports/terminal/` and commit it.

## Remote log lookup rule

When a workflow summary or terminal block names an expected `docs/reports/terminal/*.log` path, a successor chat must verify that exact path directly before claiming the log is missing.

GitHub code search, commit search, and filename search are advisory only. They may lag behind a recent push and must not be the sole basis for saying remote evidence is unavailable.

Required order: direct fetch of the named path at the expected branch or `main`; then PR/branch metadata; then search fallback only if the path is unknown.

If direct fetch succeeds, the assistant must treat the log as remote evidence even when search does not find it yet.

## GUI visual evidence workflow rule

Manual GUI visual verification must be a two-phase workflow.

Phase A may launch the GUI and record technical launch evidence, but it must not depend on an interactive shell `read` prompt for the final result.

Phase B must record the human PASS or FAIL result non-interactively, render the structured summary with a generated argument list or JSON payload, and upload the completed log.

Long shell-backslash invocations of `./ns summary` are forbidden in GUI visual evidence blocks because a lost dash can corrupt the summary command. Use a generated Python argument list or JSON payload instead.

## Canonical field anchors

The final framed SUMMARY block must preserve these exact field anchors:

- WORK RESULT
- EVIDENCE RESULT
- OVERALL RESULT
- REMOTE_EVIDENCE
- NEXT_CHAT_REPLY

These anchors are machine-checked so summary rendering cannot silently drift back to an older or ambiguous format.
