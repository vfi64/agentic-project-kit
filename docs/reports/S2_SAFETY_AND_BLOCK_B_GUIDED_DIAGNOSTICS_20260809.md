# S2 Safety And Block B Guided Diagnostics

Date: 2026-08-09
Branch: `codex/freshness-guided-diagnostics`
Manifest SHA: `3d20e7338c12`

## Result

Status: PASS for the current bounded slice.

This slice does not reclassify the command manifest surface classes again. PR #2022 already fixed the intent-oriented surface errors that hid primary user workflows or exposed destructive diagnostics. The remaining large `diagnostic` count is a presentation problem, so this slice adds a second-order GUI / website projection instead of changing command identity.

## Current Counts

- Commands: 251
- Surfaces: `orchestrator=31`, `diagnostic=119`, `primitive=101`
- GUI layers: `primary=31`, `diagnostics=119`, `expert=101`
- Diagnostic priorities: `common_blocker=6`, `claim_evidence=12`, `specialized_audit=20`, `reference_lookup=11`, `advanced_diagnostic=70`, `not_diagnostic=132`
- Guided Diagnostics common blockers: 6
- BOUNDED commands without dry-run: 126
- Projection entries marked `manual_safety_review`: 126
- DESTRUCTIVE diagnostics: 0

## Adjudication

The high `diagnostic` count is acceptable as manifest metadata because diagnostic remains a role/disclosure class, not a GUI primary-screen contract. Block B presentation must therefore consume `diagnostic_priority` and show Guided Diagnostics common blockers before specialized audits.

The READ_ONLY to diagnostic correlation remains non-blocking. A read-only command that inspects, audits, reports, or renders state is often diagnostic by intent; the contract violation would be deriving `diagnostic` from `READ_ONLY` alone. Tests continue to assert specific intent-oriented exceptions.

The BOUNDED-without-dry-run count is not mass-migrated in this slice. Those commands may still be valid bounded wrappers, but GUI and website projections now expose them as `manual_safety_review`, making the risk visible without inventing an unsupported dry-run or weakening command safety.

Readiness, release, PR, remote, and DPA claim surfaces now carry `claim_evidence` metadata. The projection distinguishes gate-output evidence, exact-ref evidence, release evidence, and PR / remote evidence so GUI or website views cannot present prose-only stable, release, DPA, or merge claims as self-evident.

## Guided Diagnostics Common Blockers

- `agentic-kit audit-status-current-state`
- `agentic-kit check-docs`
- `agentic-kit docs-audit`
- `agentic-kit doctor`
- `agentic-kit workflow status`
- `agentic-kit workflow-guard check`

## Evidence

- `python -m pytest -q tests/test_gui_command_projection.py tests/test_cockpit.py tests/test_project_direction.py tests/test_status_current_state_audit.py`: PASS, 77 passed.
- `agentic-kit direction validate --json`: PASS.
- `agentic-kit audit-status-current-state --json`: PASS, including `status_current_state_stale_release_instruction`.
- `agentic-kit cockpit actions --json | python -m json.tool`: PASS.
