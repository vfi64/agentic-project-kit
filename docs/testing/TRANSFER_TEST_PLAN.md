# Transfer Test Plan

Status: active  
Owner: maintainers  
Target release: v0.4.12  
Planning anchor: `docs/planning/PROJECT_DIRECTION.yaml` milestone `transfer-test-plan`

## Purpose

This file specifies the transfer tests that must govern the three supported
communication paths before further GUI expansion:

1. Remote / PR / CI.
2. File transfer through the `gui-transfer-tasks` task carrier.
3. Copy-and-Paste as recovery fallback only.

The plan is a specification for later implementation slices. It does not add a
new transfer protocol and does not authorize GUI code to bypass existing
`agentic-kit` wrappers.

## Transfer Modes

| Mode | Role | Canonical route | Primary commands |
|---|---|---|---|
| `remote` | GitHub/PR/CI work by a remote-capable assistant | Branch, PR, CI, merge, post-merge handoff | `agentic-kit transfer pr-create-complete`, `agentic-kit transfer post-merge-complete`, `agentic-kit transfer patch-cycle-status --json` |
| `file_transfer` | Default GUI/local dialog path | `gui-transfer-tasks` remote ref plus canonical inbox/outbox files | `agentic-kit transfer submit-user-task --publish --json`, `agentic-kit transfer continue --json`, `agentic-kit transfer state --json` |
| `copy_paste` | Recovery/fallback when remote or file transfer is unavailable | Complete bounded command block plus `LOG=...` and `RC=...` reply | No implicit mutation; use explicit wrapper commands inside bounded blocks |

## Canonical Files And Refs

| Purpose | Canonical location |
|---|---|
| GUI task carrier remote ref | `gui-transfer-tasks` |
| LLM-readable GUI task file | `.agentic/transfer/inbox/current.yaml` on `gui-transfer-tasks` |
| Local transfer inbox | `.agentic/transfer/inbox/current.yaml` |
| Local transfer outbox | `.agentic/transfer/outbox/last_result.txt` |
| Handoff package validation | `docs/reports/handoff-packages/latest/validation_report.json` |
| Latest transfer handoff report | `docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json` |

Rules:

- A bare `g` or `go` is always a command to re-read the canonical GUI task carrier.
- The assistant must read `.agentic/transfer/inbox/current.yaml` from remote ref
  `gui-transfer-tasks`, unless the send result explicitly names another ref.
- Missing carrier means the assistant replies exactly `TASK_NOT_FOUND` and does
  not mutate anything.
- Copy-and-Paste is a fallback path and must not become the default GUI transfer
  route.

## Expected Signals

| Signal | Meaning | Required next behavior |
|---|---|---|
| `result_status=PASS` | The wrapper completed its deterministic contract | Continue to the next safe step |
| `result_status=BLOCKED` | A guard stopped before unsafe work | Preserve evidence and diagnose the blocker |
| `result_status=FAIL` | Command failed outside the normal guard path | Stop and inspect bounded evidence |
| `remote_readable=true` | Published carrier was verified on the advertised remote ref | User may send `g/go` |
| `TASK_NOT_FOUND` | Assistant could not read the canonical task carrier | User or GUI must republish or diagnose send state |
| `RULE_REFRESH_ACK` | Communication rule refresh was verified | Mutation may continue if other gates are green |
| `WAIT_FOR_D2` | Communication rule refresh is pending | No mutating action before ACK |

## Test Cases

### Remote / PR / CI

| ID | Scenario | Command surface | Expected result | Evidence |
|---|---|---|---|---|
| TT-REMOTE-001 | Clean feature branch can enter PR lifecycle | `transfer pr-create-complete --json` | PR created or completed through wrapper, no ad-hoc `gh` path | JSON result with PR number, head SHA, CI status |
| TT-REMOTE-002 | Missing or stale remote head blocks before PR creation | existing remote-head guard or PR wrapper | `BLOCKED`, no PR with wrong head | blocker names remote head/ref mismatch |
| TT-REMOTE-003 | Red CI blocks merge | `transfer pr-wait-ci`, `transfer pr-complete` | `BLOCKED`, no merge | failed check names or bounded CI evidence |
| TT-REMOTE-004 | Post-merge handoff is required and completed | `transfer post-merge-complete --after-pr` | PASS or explicit admin refresh PR | refresh PR number or NOOP report |
| TT-REMOTE-005 | Local main after merge is clean and current | `transfer sync-main`, `post-merge-check`, `repo-status` | PASS/NOOP and clean worktree | compact wrapper summaries |

### File Transfer / SEND-READ

| ID | Scenario | Command surface | Expected result | Evidence |
|---|---|---|---|---|
| TT-FILE-001 | GUI sends a task through the canonical carrier | `transfer submit-user-task --publish --json` | `remote_readable=true` | `published_ref=gui-transfer-tasks`, remote path, blob/content verification |
| TT-FILE-002 | Initial prompt instructs `g/go` to read the canonical ref | `gui initial-llm-prompt --json` | Prompt names `gui-transfer-tasks` and `.agentic/transfer/inbox/current.yaml` | JSON prompt text or rendered prompt fixture |
| TT-FILE-003 | Bare `g/go` never reuses chat memory | prompt/generator tests | Prompt says to re-read current task and compare task identity/hash | deterministic prompt test |
| TT-FILE-004 | Missing remote carrier fails closed | assistant protocol fixture or transfer read path | exact reply `TASK_NOT_FOUND`; no mutation | protocol test or simulated 404 fixture |
| TT-FILE-005 | Local continue consumes the canonical inbox | `transfer continue --json` | PASS/BLOCKED with bounded evidence | local transfer result JSON |
| TT-FILE-006 | Read button uses canonical transfer state | `transfer state --json` | Outbox status reflects `.agentic/transfer/outbox/last_result.txt` | transfer-state JSON |
| TT-FILE-007 | D2 pending blocks send/mutation | GUI gatekeeper/status fixture | WAIT_FOR_D2; send button disabled | GUI/viewmodel test |

### Copy-and-Paste Recovery

| ID | Scenario | Command surface | Expected result | Evidence |
|---|---|---|---|---|
| TT-CP-001 | GUI labels Copy-and-Paste as recovery/fallback | GUI/viewmodel | Mode is visible but not default | viewmodel test |
| TT-CP-002 | Generated fallback block is bounded and logs to file | documented fallback block or wrapper output | User returns only `LOG=...` and `RC=...` | bounded log file |
| TT-CP-003 | Long terminal output is not required in chat | communication contract test | Prompt forbids broad paste output unless explicitly needed | prompt/contract fixture |
| TT-CP-004 | Fallback cannot invent a new transfer protocol | prompt/contract test | Uses existing wrappers or stops with missing-wrapper diagnostic | deterministic text/contract assertion |
| TT-CP-005 | Non-zero `RC` stops mutation-oriented continuation | local result parser or workflow guard | `BLOCKED` or FAIL classification | compact diagnostic JSON |

## Failure Cases And Stop Conditions

Stop immediately when any of these conditions appears:

- Worktree is dirty in an unexplained way before remote mutation.
- `main` is not equal to `origin/main` before starting a new slice.
- `validation_report.json` is missing or not PASS when a successor handoff is required.
- A bare `g/go` cannot read the canonical carrier from `gui-transfer-tasks`.
- A send result lacks `remote_readable=true`.
- A communication rule refresh is pending (`d2`, `WAIT_FOR_D2`) and no ACK has been verified.
- A PR wrapper reports missing/stale remote head, red CI, merge-state conflict, or post-merge refresh required.
- Copy-and-Paste instructions would require broad terminal output, unbounded grep/cat, or an ad-hoc protocol.
- The same patch family fails twice without bounded diagnostic evidence.

## Evidence Formats

Each implemented test should prefer machine-readable evidence:

- JSON command output from `agentic-kit ... --json`.
- Compact wrapper summaries for human-readable terminal output.
- Bounded log files under `tmp/` or governed report paths when long output is unavoidable.
- Explicit PR number, branch, head SHA, base ref, CI status, and handoff refresh status for remote work.
- Explicit `published_ref`, `remote_path`, `remote_readable`, and content/blob verification for GUI task carriers.
- Explicit `LOG=...` and `RC=...` for Copy-and-Paste fallback runs.

Do not use screenshots or chat memory as primary evidence for transfer correctness.

## Implementation Order

1. Add or verify tests for the canonical SEND/READ ref and path.
2. Add or verify tests for `g/go` fail-closed behavior.
3. Add file-transfer state tests that cover inbox, outbox, and missing carrier cases.
4. Add remote PR lifecycle tests for remote-head, CI, merge, and post-merge handoff blockers.
5. Add Copy-and-Paste fallback tests that prove it remains a recovery path.
6. Only then expand GUI behavior that depends on these transfer contracts.

## Non-Goals

- No new transfer command family.
- No GUI mutation path outside existing wrappers.
- No live release or tag behavior.
- No external-project operating-model implementation.
- No broad rewrite of handoff projections or generated reports.
