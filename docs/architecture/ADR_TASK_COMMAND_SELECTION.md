---
artifact_type: architecture_decision
status: accepted
schema_version: 1
---

Status: accepted
Status-date: 2026-10-26
Superseded-by: n/a
Document class: architecture

# D1 ADR — Shared task-to-command selection

Date: 2026-10-26. **Accepted by the owner: option A.** Selection is advisory; it never changes execution authorization. Canonical planning remains
`docs/planning/PROJECT_DIRECTION.yaml#d1-shared-task-command-selection`.

## Problem and evidence

W1-P0 found 35 tagged orchestrators but only two with additional task-tag candidates.
Thirty-three have only structural tags. Eight tags match several orchestrators.
Neither tag availability nor selector order identifies user intent, operation state,
authorized execution or a preferred route. See
`docs/reports/task_tag_inventory_20261026/README.md`.

## Recommended direction (A)

Extend the **existing command manifest authority** with one explicit `task_routes`
export. Define each route once next to the existing command metadata; export it to
both the human website and model-facing `command-for` consumer. Reuse the current
selector module for pure evaluation, not a parallel runtime selector or policy engine.

The original YAML remains an **archived inactive review fixture**. Only historical tests and the design renderer read it. Current rows live in task_routes.py and are generated into the manifest. Never edit the historical fixture to change runtime routing. The website and CLI share that manifest export.

Preserve existing `--raw` and `--task` behavior: task tags still list candidates.
Use the explicit intent-selection mode on `command-for`; do not silently
reinterpret broad tags such as closeout or transfer. The CLI and schema migration are specified and tested in the shared selection contract.

## Alternatives

- **B: keep tags and choose the first match.** Small implementation, but ignores
  intent, state and the different meanings of closeout. Reject as the preferred-route model.
- **C: a website-owned YAML router.** Simple editorial navigation, but creates a
  second command truth and diverges from agent selection. Reject as runtime authority.
- **D: a general workflow/policy engine.** Expressive but duplicates existing Kit
  state machines and expands validation/maintenance scope. Defer; finite equality
  predicates suffice for the reviewed first matrix.

## Identity and compatibility decision

Routes must be covered by the **same authenticated manifest identity** as the command
metadata before production use. Adding an unhashed root field is unacceptable.
Implementation must explicitly version the manifest/selection contract, test old
consumers, and refuse unsupported route schemas or identity mismatch. The implementation uses manifest schema 3 / metadata schema 2 and route schema 1. Its identity hashes commands and task_routes together; schema 2 retains the historical command-only hash. Older consumers cannot verify schema 3 through the old command-only hash and must upgrade before intent selection.

## Scope and non-goals

Selection returns a command candidate and its current manifest contract; it never
constructs executable shell text, changes repository state or grants consent. It does
not add automatic retries, remote discovery, fuzzy language inference, deprecation,
command removal, GUI execution, a benchmark, or a claim of context-token savings.

A typed, small fixture is useful here because routes and failure outcomes can be
checked independently. No DCO repair platform or additional planning authority is needed.

## Recorded adoption

The owner accepted direction A, the fact/identity boundary and the initial matrix on 2026-10-26 (reply “A”). A merged **proposed**
ADR is preserved review material, not that acceptance. The next implementation slice
must include shared export, consumer agreement, capability/identity checks and migration
tests as specified in `docs/reference/TASK_COMMAND_SELECTION_CONTRACT.md`.
