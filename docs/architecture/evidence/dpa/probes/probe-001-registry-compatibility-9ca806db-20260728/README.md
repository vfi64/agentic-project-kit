# PROBE-001 Registry Compatibility Evidence

Status: SATISFIED_FOR_CURRENT_KIT_REF

Status-date: 2026-07-28

Run ID: `probe-001-registry-compatibility-9ca806db-20260728`

Kit validation ref: `9ca806dba1c92b83514beba2b49f0a083c9bdc9a`

Implementation merge ref: `0133e185367f00cfcbd5873bc13c09843eafc283`

Handoff refresh merge ref: `9ca806dba1c92b83514beba2b49f0a083c9bdc9a`

Command manifest: `COMMAND_MANIFEST_ACK ff86b5a8c9f1`

## Scope

This evidence records the Kit-side PROBE-001 registry compatibility slice after
PR #1896 and its generated post-merge handoff refresh PR #1897.

It verifies the current documentation-registry parser accepts existing manual
registry entries and structurally validates optional DPA `ProjectionContract`
and `PartitionContract` metadata. It does not execute DP2 production mutation,
does not claim full DPA conformance and does not alter generated handoff
projections manually.

## Fixture Coverage

| Required PROBE-001 case | Evidence |
|---|---|
| Existing manual registry entries unchanged | `agentic-kit docs-registry` passed with 177 registered documents. |
| Valid optional ProjectionContract | `test_documentation_registry_accepts_dpa_projection_contract` passed. |
| Valid parent-entry PartitionContract | `test_documentation_registry_accepts_dpa_partition_and_region_projection` passed. |
| Unknown projection schema version | `test_documentation_registry_rejects_unknown_dpa_projection_schema` passed. |
| Unknown projection field | `test_documentation_registry_rejects_unknown_dpa_projection_field` passed. |
| Missing required projection field | `test_documentation_registry_rejects_missing_dpa_projection_field` passed. |
| Missing, dangling or inconsistent registered-region reference | dangling parent and missing parent-region tests passed. |
| Unsupported target-semantics and partition combination | complete-document plus partition-contract rejection test passed. |

## Local Evidence

- `git rev-parse HEAD` -> `9ca806dba1c92b83514beba2b49f0a083c9bdc9a`
- `git rev-parse origin/main` -> `9ca806dba1c92b83514beba2b49f0a083c9bdc9a`
- `git status --short` -> clean before evidence-file mutation
- `.venv/bin/python -m pytest -q tests/test_documentation_registry.py` -> `38 passed`
- `.venv/bin/agentic-kit docs-registry` -> PASS summary, 177 documents
- `.venv/bin/agentic-kit dpa readiness --json` before this evidence update -> `DP2_BLOCKED`, 40%

Full machine-readable results are in `results.json`.
