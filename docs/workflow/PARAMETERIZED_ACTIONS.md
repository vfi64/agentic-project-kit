Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Parameterized Actions

Status: active
Decision status: accepted

## Purpose

Parameterized actions define auditable action objects before the project adds more mutating Git, PR, release, DOI, and finalize automation.

The MVP is intentionally read-only. It exposes action metadata through `agentic-kit actions list`, `agentic-kit actions show <id>`, `./ns action-list`, and `./ns action-show <id>`.

## Safety Boundary

- Action specs are metadata, not executors.
- Dry-run is the default posture.
- Mutating variants require later explicit execute flags, machine-readable preconditions, postconditions, and repo-backed evidence.
- GUI/Cockpit controls should consume these action specs instead of assembling raw shell snippets.

## Initial Specs

- `pr-check-merge`
- `release-verify`
- `doi-record`
- `finalize-release`

## Next Step

The next slice may add dry-run validators for individual specs. Actual remote mutation remains out of scope until those validators are deterministic and covered by tests.
