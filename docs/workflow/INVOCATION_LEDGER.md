Status: active
Status-date: 2026-10-16
Superseded-by: n/a

# Local invocation ledger

## Purpose

The ledger records which Kit commands actually run, so decomplexification and drift work can use real counts. The command usage audit of 2026-10-15 (finding F5) could only bound usage from static analysis, tests and simulation. Plan step: `kit-control-effectiveness-measurement` / `local-invocation-ledger` in `docs/planning/PROJECT_DIRECTION.yaml`.

## What is recorded

One JSON line per invocation in `.agentic/tmp/invocation-ledger/ledger.jsonl`:

| Field | Meaning |
|---|---|
| `command` | canonical name from registered command names only, e.g. `agentic-kit work finish`; never arguments or option values |
| `kind` | `cli` for a process start, `internal` for an in-process call an orchestrator reports |
| `invocation_id`, `parent_id`, `root_id`, `depth` | call tree; a Kit command started as a subprocess of another records it as parent |
| `started_at`, `duration_ms`, `returncode` | UTC start (seconds), wall time, exit code |
| `kit_version`, `branch` | installed Kit version and current branch |

No arguments, file contents, environment values or credentials are recorded.

## Scope and retention

- `.agentic/tmp/` is git-ignored, so the ledger is never committed.
- The ledger is on in the Kit's own repository and off in other repositories unless enabled:
  - opt in with `AGENTIC_KIT_INVOCATION_LEDGER=1`, or with an empty file `.agentic/tmp/invocation-ledger/ENABLED`;
  - `AGENTIC_KIT_INVOCATION_LEDGER=0` turns it off everywhere.
- When the ledger passes 4 MB, records older than 90 days are dropped and at most the newest 20,000 are kept.
- A ledger failure never fails a command or changes its return code. The stage and exception type, never the message, go to `.agentic/tmp/invocation-ledger/errors.log`, and the report counts them.

## Report

`agentic-kit ledger report [--days N] [--json]` is read-only. Per command it shows:

- total, outer, nested and internal invocations;
- failures;
- median duration.

It also shows the number of root invocations and the invocations per root, which give a denominator per work cycle. Drift classification is a separate plan step.

## Repeated failures and finding drafts

The report lists repeated failures: the same command failing on the same branch with the same return code at least three times in a row. A success of that command on that branch ends the run. The fingerprint is a hash of command, return code and branch.

`agentic-kit ledger report --write-finding-drafts` writes one local draft per new fingerprint to `.agentic/tmp/invocation-ledger/finding-drafts/`. An existing draft is never overwritten, so a human's edits survive. A draft records evidence and open questions. It is not a filed finding, and repairs follow the plan's graded rule: a patch only on a work branch and only up to a green PR, while merges and architecture changes need human approval.

## Drift signals

`agentic-kit audit-drift-signals [--consumer-ledger PATH] [--json]` measures the three drift classes of the self-hosting audit. Each signal comes with its denominator:

| Signal | Measures | Denominator |
|---|---|---|
| `release_projection` | handoff `release` block against the release evidence (HD-08 class) | release block keys backed by evidence |
| `refresh_chains` | two or more refresh-only commits after a product merge | product merges in the history window |
| `consumer_status` | Kit `CLOSED` versus consumer `OPEN` | Kit findings present in the consumer ledger, passed by path |

The command is report-only and always exits 0. It reports no general drift rate.

## Limits

- Commands driven through `CliRunner` in tests bypass the entry point and are not recorded. The test suite sets `AGENTIC_KIT_INVOCATION_LEDGER=0`, so Kit subprocesses started by tests do not either.
- A fingerprint carries no BLOCKED reason; the draft points to the command output for it.
- In-process composition is recorded only where an orchestrator reports it with `invocation_ledger.internal_call`. So far that is `transfer continue` → `transfer remote-next`.
