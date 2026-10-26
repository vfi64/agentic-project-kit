---
artifact_type: architecture_decision
status: proposed
schema_version: 1
---

# D1 ADR — Shared task-to-command selection

Date: 2026-10-26. **Proposed, not adopted.** This document requests an owner decision;
it changes neither command selection nor authorization. Canonical planning remains
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

The accompanying YAML is an **inactive review fixture**, not that runtime export.
Only tests and the design renderer read it. After adoption, implementation must
move the reviewed rows into the existing authority and generate any documentation
matrix from that export. Never leave both files as writable runtime authorities.

Preserve existing `--raw` and `--task` behavior: task tags still list candidates.
Propose an explicit future intent-selection mode on `command-for`; do not silently
reinterpret broad tags such as closeout or transfer. The exact CLI interface and
manifest schema migration are implementation acceptance decisions, not shipped flags.

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
consumers, and refuse unsupported route schemas or identity mismatch. This proposal
does not change the current manifest hash algorithm, ACK or schema.

## Scope and non-goals

Selection returns a command candidate and its current manifest contract; it never
constructs executable shell text, changes repository state or grants consent. It does
not add automatic retries, remote discovery, fuzzy language inference, deprecation,
command removal, GUI execution, a benchmark, or a claim of context-token savings.

A typed, small fixture is useful here because routes and failure outcomes can be
checked independently. No DCO repair platform or additional planning authority is needed.

## Adoption gate

The owner must accept direction A, the fact/identity boundary and the initial matrix
before runtime implementation or website navigation uses it. A merged **proposed**
ADR is preserved review material, not that acceptance. The next implementation slice
must include shared export, consumer agreement, capability/identity checks and migration
tests as specified in `docs/reference/TASK_COMMAND_SELECTION_CONTRACT.md`.
