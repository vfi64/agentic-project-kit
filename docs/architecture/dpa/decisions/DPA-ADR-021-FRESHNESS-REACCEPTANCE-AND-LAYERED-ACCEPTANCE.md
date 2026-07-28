# DPA-ADR-021 — Operation-scoped base context, mutation-free re-acceptance and layered acceptance

Status: ACCEPTED

Status-date: 2026-07-17

## Context

The DPA-500 primary architecture review identified three bounded evaluability defects:

1. base-context freshness referred to an accepted plan even when no live plan exists after acceptance;
2. gate-set changes had no governed path back to acceptance without rendering and rewriting unchanged bytes;
3. authorized evolution of non-lifecycle-owned regions in hybrid documents was indistinguishable from out-of-band mutation of lifecycle-owned bytes.

The Maintainer adjudication accepted all three findings and selected layered acceptance for registered-region projections.

## Decision

### 1. Operation-scoped base context

Base or ref identity is operation-scoped unless a projection contract explicitly declares semantic or acceptance dependence on a base identity.

A mutation plan MUST capture the exact base required for that attempt. A later audit, re-acceptance or integration operation MUST evaluate the base or ref context required by that operation.

Acceptance state MUST persist an accepted base identity only when the accepted contract declares base dependence. Absence of a persisted base identity for a base-independent contract is valid and MUST NOT make ordinary post-acceptance freshness evaluation indeterminate.

### 2. Mutation-free gate-set re-acceptance

The lifecycle SHALL support governed gate-set re-evaluation without rendering or target mutation.

This operation is permitted only when every applicable freshness dimension other than gate-set freshness is `fresh`, the current target bytes and acceptance record remain valid for the accepted scope, and no contract, source, configuration, renderer, target, partition, ownership or required base mismatch exists.

The lifecycle runs the complete current required gate set against the existing accepted bytes. On gate `pass`, it MAY update only lifecycle-owned acceptance state and bounded evidence with the new gate-set identity and result. On `warning` or `failure`, it MUST leave target bytes and the prior acceptance record unchanged and emit structured findings.

This operation MUST use the existing lifecycle, Workspace resolution, state writer, lock policy and gate authority. It creates no second acceptance path.

### 3. Layered acceptance for registered-region projections

For complete-target projections, post-acceptance target freshness compares the complete-target fingerprint.

For registered-region projections, post-acceptance projection freshness compares lifecycle-owned projected payload bytes, lifecycle-owned partition bytes and boundaries, ownership declarations and applicable target semantics. Complete-target and preserved-region fingerprints remain mandatory mutation-plan guards and post-Write verification inputs.

A governed change to bytes owned by a declared non-lifecycle owner, performed consistently with the active partition and ownership contracts, does not by itself create projection `target drift`, does not make the lifecycle-owned payload stale and does not require regeneration or re-acceptance. It MAY produce bounded informational evidence that the prior complete-target fingerprint was superseded by authorized owned-region evolution.

A change to lifecycle-owned projected payload bytes produces `target drift`. A change to lifecycle-owned partition bytes or boundaries produces `partition drift`. A change to ownership declarations produces `ownership drift`. Ambiguous ownership, malformed boundaries or inability to prove the responsible owner MUST fail closed.

## Alternatives considered

- persist every plan base permanently and require it for all later freshness checks;
- require full render, target write and acceptance for every gate-policy change;
- strict complete-target acceptance in which every authorized manual-region edit invalidates projection acceptance;
- ignore preserved-region and complete-target changes without ownership validation.

## Rationale

The accepted model preserves exact-plan mutation safety while keeping post-acceptance freshness evaluable. It avoids mass regeneration for policy-only changes and distinguishes normal governed evolution of manual or historical regions from unauthorized mutation of lifecycle-owned bytes.

## Consequences

- DPA-300 acceptance-state and direct-write clauses require a synchronized bounded amendment.
- DPA-500 requires a gate-set re-acceptance operation, explicit operation-scoped base rules and layered region-freshness semantics.
- Traceability and conformance tests must distinguish authorized non-lifecycle-owner edits from out-of-band lifecycle-byte edits.
- Concrete acceptance-state schema, state-write ordering, locking and command integration remain `NEEDS_MAIN_REPO_VALIDATION`.
- No current production implementation or Probe success is claimed.

## Validation status

NORMATIVE architecture decision. Main-repository representation and implementation remain pending exact-ref Probe and implementation evidence.

## Affected specifications

DPA-100, DPA-300, DPA-500, DPA-600, DPA-800.

## Affected DP slices

DP1, DP2, DP3 and DP5.
