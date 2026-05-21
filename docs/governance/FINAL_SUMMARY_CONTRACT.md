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
