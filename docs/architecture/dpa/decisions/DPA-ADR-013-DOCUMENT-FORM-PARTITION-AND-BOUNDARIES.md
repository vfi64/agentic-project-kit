# DPA-ADR-013 — Partition document forms and own boundary bytes

Status: ACCEPTED
Status-date: 2026-07-15
Review origin: Claude DPA-200 R-M01/R-M02; ChatGPT DPA-200 technical verification

## Context

The initial DPA-200 draft allowed a single-document split projection, a hybrid document and managed-head projection to describe overlapping structures. It also required exhaustive byte ownership without assigning marker, separator or delimiter bytes.

## Decision

1. A **split projection** is exclusively an arrangement of two or more independently registered target identities. Each target may be a complete registered document. A single document partitioned into projected and non-projected regions is not classified as split projection.
2. A **hybrid document** is one registered document containing at least one projected registered region and at least one non-projected region.
3. A **managed-head projection** is an exceptional hybrid subtype containing exactly one leading projected region and exactly one following historical region.
4. Every conforming document instance has exactly one primary form classification. Subtype information may be recorded in addition to, but not instead of, the primary form.
5. Boundary bytes belong to a document-level **partition contract**. The existing document lifecycle is their exclusive write owner.
6. Renderer output MUST exclude partition-boundary bytes. Manual and historical editors MUST NOT mutate them.
7. A boundary mutation outside the lifecycle is boundary drift and MUST fail loud through the later DPA-300/DPA-500 contracts.

## Alternatives considered

- Keep split projection as both multi-target and single-document form.
- Collapse all partitioned forms into one generic form.
- Assign each boundary to an adjacent region.
- Let renderer output include boundary markers.

## Rationale

The chosen taxonomy produces one deterministic classification per legal structure while preserving managed-head exceptionalism. Lifecycle-owned boundary bytes satisfy exhaustive ownership without sharing control between renderer and manual writers.

## Consequences

DPA-200, its matrix and diagrams must use the partition key above. DPA-300 must validate partition contracts and detect boundary writes. DPA-400 must reject renderer output containing boundaries. DPA-500 owns boundary-drift findings. DPA-700 must preserve partition bytes during rollback.

## Validation status

NORMATIVE architecture decision. Concrete marker syntax and registry support remain `NEEDS_MAIN_REPO_VALIDATION`.

## Affected specifications

DPA-200, DPA-300, DPA-400, DPA-500, DPA-700, DPA-800.

## Affected DP slices

DP1–DP4.