Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Typed Work Order Evidence Contract

Status: active contract for v0.3.31 pre-GUI execution hardening.

Typed Work Orders are the preferred pre-GUI execution path. They must be able to describe not only the intended operation, but also the evidence expected after execution.

## Required evidence fields

A typed Work Order may define an `evidence` mapping with these fields:

- `type`: evidence type. Initial supported value: `terminal_log`.
- `path`: repo-relative path to the evidence artifact.
- `guard_required`: boolean. When true, `./ns evidence-guard LOGFILE` must pass before the evidence is accepted.
- `expected_final_result`: expected final terminal result marker. Supported values: `PASS`, `FAIL`, `PENDING`, `HARD-FAIL`.
- `on_guard_fail`: result mapping when guard validation fails. Initial supported value: `FAIL`.

## Minimal YAML shape

```yaml
schema_version: 1
id: example.typed-work-order
kind: typed_work_order
operation: run_registered_action
evidence:
  type: terminal_log
  path: docs/reports/terminal/example.log
  guard_required: true
  expected_final_result: PASS
  on_guard_fail: FAIL
```

## GUI boundary

The future Tkinter GUI must not infer success from raw shell text. It must display structured typed Work Order result fields and evidence validation state.

## Runtime boundary for v0.3.31

The contract is intentionally small. Runtime enforcement may start with terminal-log evidence only. Unsupported evidence types must be rejected explicitly rather than treated as PASS.
