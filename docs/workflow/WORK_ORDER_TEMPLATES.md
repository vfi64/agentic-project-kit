Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Work Order Templates

Status: active
Decision status: accepted

## Purpose

Work-order templates move repeated local gate blocks into repository-backed YAML artifacts.
The templates are checked by `agentic-kit work-order check` and are executed only through the work-order runner.

## Safety Boundary

- Templates do not replace the constitutional gates.
- The runner owns PASS and FAIL markers.
- Commands must not print direct PASS markers.
- Commands must include pytest, ruff check, check-docs, and doctor.
- Logs must be written under `docs/reports/terminal/`.

## Initial Template

- `standard-local-gates`: read-only local constitutional gate run for the current slice.
