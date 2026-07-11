# Path Literal Active-Class Enforcement Evidence (P5b)

Generated: 2026-07-11
Branch: `codex/p5b-resolver-evidence`
Scope: P5b active-class enforcement for path literals and repository identity literals.

## Commands

```bash
./.venv/bin/agentic-kit audit-path-literals --enforce-active --json
./.venv/bin/agentic-kit audit-path-literals --enforce-active
./.venv/bin/agentic-kit standard-gates-audit-suite
```

## Enforcement Summary

`agentic-kit audit-path-literals` remains report-only by default. The new
`--enforce-active` mode is used by the standard gate suite and fails only active
classes:

- active path literals outside `workspace.py` and declared exceptions;
- active repository identity literals outside declared exceptions.

Reference, message, template, resolver-source, and declared-exception literals
remain visible in the report and non-blocking.

## Current Counts

| Field | Count |
|---|---:|
| status | PASS |
| blocker count | 0 |
| active path literals | 0 |
| active repository identity literals | 0 |
| non-blocking path literals | 362 |
| non-blocking repository identity literals | 4 |
| affected modules | 70 |
| path literals | 362 |
| repository identity literals | 4 |

## Classification Summary

Path literal classes:

| Class | Modules | Literals | Disposition |
|---|---:|---:|---|
| `reference_or_message` | 68 | 338 | non-active |
| `resolver_source` | 1 | 13 | non-active |
| `template_data` | 1 | 11 | non-active |

Repository identity classes:

| Class | Modules | Literals | Disposition |
|---|---:|---:|---|
| `reference` | 1 | 2 | non-active |
| `template` | 2 | 2 | non-active |

## Active Literal Closure

The active `tmp/` literal previously visible in the transfer runner warning path
was removed from the active class by routing it through the workspace resolver:
`load_workspace(Path(".")).tmp_file("instruction-lint-warnings.log")`.

This preserves behavior while keeping mutable runtime paths behind the existing
workspace abstraction.

## Manual Reference-Or-Message Samples

| File | Literal | Finding |
|---|---|---|
| `src/agentic_project_kit/handoff_prompt.py` | `docs/TEST_GATES.md` | Successor-prompt source text. The module does not construct a `Path` from this literal or perform file IO with it. |
| `src/agentic_project_kit/instruction_lint.py` | `docs/reference/agentic-kit-commands.json` | Rejection-message text for a missing or stale command-manifest ACK. It is emitted as diagnostic text, not used for active path access. |
| `src/agentic_project_kit/action_registry.py` | `docs/reports/command_runs and docs/reports/terminal` | Action metadata describing mutation scope. It is not parsed into paths by the registry and does not steer behavior by itself. |

These samples remain visible as non-blocking taxonomy findings. They are
deliberately not suppressed, because the audit should continue to expose
reference text while blocking only active path and identity classes.

## Standard Gate Adoption

`agentic-kit standard-gates-audit-suite` now includes
`audit-path-literals --enforce-active`.

Latest branch-local suite result:

```text
STANDARD_GATES_AUDIT_SUITE
STATUS=PASS
CHECK_COUNT=14
BLOCKER_COUNT=0
CHECK=PASS|audit-path-literals --enforce-active|0|- template: modules=2 literals=2 disposition=non-active
```
