Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Governance Check

Status: active
Decision status: accepted

## Purpose

`agentic-kit governance check` is a read-only constitutional gate. It verifies that the repository still has the required state, architecture, handoff, work-order, and parameterized-action documents and that the active handoff and work-order contracts validate.

## Boundary

- The command is read-only.
- It does not run Git mutation, PR merge, release, tag, or DOI actions.
- It is a deterministic MUST-gate for future governed work-order execution and GUI/Cockpit control paths.

## Shortcuts

- `agentic-kit governance check`
- `./ns governance-check`
