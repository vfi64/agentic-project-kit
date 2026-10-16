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

## Limits

- Commands driven through `CliRunner` in tests bypass the entry point and are not recorded.
- In-process composition is recorded only where an orchestrator reports it with `invocation_ledger.internal_call`. So far that is `transfer continue` → `transfer remote-next`.
