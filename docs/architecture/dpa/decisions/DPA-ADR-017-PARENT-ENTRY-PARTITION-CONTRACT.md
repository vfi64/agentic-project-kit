# DPA-ADR-017 — Store the Partition Contract on the Parent Registry Entry

Status: ACCEPTED

Status-date: 2026-07-15

## Context

DPA-200 and DPA-ADR-013 assign partition bytes and boundary semantics to one lifecycle-owned document-level partition contract. The DPA-300 draft referenced a partition-contract identity and fingerprint without defining its registry representation, while duplicating boundary fields on individual region targets.

## Decision

A document that contains registered regions MUST declare exactly one partition contract on its parent registered-document entry in the existing documentation registry.

The partition contract MUST declare:

- partition-contract schema version;
- parent document identity;
- complete ordered region identities;
- one owner class for every region;
- which regions are projected;
- adjacency and ordering constraints;
- boundary representation for every boundary or one document-wide boundary rule;
- separator ownership where separators exist;
- normalization and encoding rules affecting partition bytes;
- missing, duplicate, overlapping, reordered and malformed-boundary behavior;
- partition fingerprint algorithm and input-domain version.

A projected region entry MUST declare only:

- parent document identity;
- region identity;
- partition-contract identity;
- the projected region's own target semantics;
- renderer and declared-source references inherited from or bounded by its projection contract.

A projected region MUST NOT independently configure boundary ownership, boundary representation, malformed-boundary behavior or a write owner that differs from lifecycle ownership.

Registry validation MUST reject:

- a region target without a parent partition contract;
- a dangling partition-contract reference;
- a region missing from the parent's ordered region list;
- duplicate or overlapping region identities;
- inconsistent ownership or boundary declarations;
- more than one partition contract for one parent document;
- partition metadata that cannot explain every target byte.

The exact serialized registry shape remains `NEEDS_MAIN_REPO_VALIDATION` and is tested by PROBE-001.

## Alternatives considered

- A separate registry object for each partition contract.
- Boundary declarations duplicated on each region.
- Renderer-owned markers.
- Implicit partition inference from current file bytes.

## Rationale

The parent entry is the existing registry identity for the complete document and is therefore the narrowest extension that avoids a parallel registry object. One declaration site prevents boundary drift between region entries and preserves DPA-ADR-013 ownership.

## Consequences

- DPA-300 must add the parent partition-contract representation and remove duplicate region boundary fields.
- DPA-400 must treat partition bytes as outside renderer payload ownership.
- DPA-500 must use the canonical term `partition drift`.
- DPA-700 must preserve or restore the complete parent partition contract during migration and rollback.
- PROBE-001 must test representability, unknown-field behavior and malformed references in the real registry parser.

## Validation status

NORMATIVE architecture decision. Serialized compatibility with the main repository remains `NEEDS_MAIN_REPO_VALIDATION`.

## Affected specifications

DPA-100, DPA-200, DPA-300, DPA-400, DPA-500, DPA-700, DPA-800.

## Affected DP slices

DP1, DP2, DP4.
