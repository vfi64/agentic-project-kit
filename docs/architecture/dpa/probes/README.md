# DPA Probe Package

Status: probe-package-staged

Status-date: 2026-07-28

Document class: architecture

## Scope

This directory stages the DPA-IMPORT-3 Probe preparation package imported from
the DPA Lab closeout line.

The package contains prepared DP1 Probe manuals, the current Probe backlog, a
selected-writer fixture plan, a main-repository validation checklist, a prepared
fixture manifest and cleanup/Assessment rules.

This is Probe package staging only. It is not Probe execution, not DP2
implementation, not production mutation, not a full Probe PASS claim and not a
Kit conformance claim.

## Imported package

- `DP1_PROBE_BACKLOG.md`
- `DP1_PROBE_MANUALS_20260727.md`
- `DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`
- `DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`
- `MAIN_REPO_VALIDATION_CHECKLIST.md`
- `fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`
- `fixtures/DP1_PROBE_CLEANUP_AND_ASSESSMENT_PLAN_20260727.md`

The imported package preserves Lab snapshot refs, including historical Kit
validation ref `c788a8c530eb0984d088a86e8e7951145581abbe` and command manifest
acknowledgement `COMMAND_MANIFEST_ACK 8610cfd2990a`. Those refs are historical
inputs. Any future Probe execution in this Kit must freeze and record a fresh
current validation ref and command manifest acknowledgement first.

## Evidence boundary

Prepared and historical DP1 evidence snapshots are staged under
`docs/architecture/evidence/dpa/`.

The read-only baseline evidence is `PASS_WITH_LIMITATIONS`. The mutation
sandbox evidence is `PARTIAL`. Neither result satisfies full DP1 Probe PASS,
Assessment, DP2 entry, stable promotion or Kit conformance.

Current Kit-side readiness preflights under
`docs/architecture/evidence/dpa/probes/` now include PROBE-001 registry
compatibility, PROBE-002 lifecycle readiness, WRT-CH-001 administrative refresh
observation, PROBE-003 workflow serialization readiness, Renderer Probe
readiness and PROBE-004 migration and rollback readiness. Except for PROBE-001
registry compatibility, these remain partial or observation-only inputs and keep
DP2 blocked.

## Generated-output boundary

Generated or command-updated Kit outputs remain source-owned, generator-owned or
command-owned. Probe planning and later Probe execution must not manually patch
generated successor-handoff package files, prompt projections or other
command-updated outputs as durable target bytes.

WRT-CH-006 records this boundary in the successor execution contract via
`handoff_projection_contract.dpa_generated_output_contract`, with
`src/agentic_project_kit/dpa_successor_projection.py` as the explicit DPA
validation surface.
