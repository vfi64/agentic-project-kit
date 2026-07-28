# DPA-ADR-016 — Persist Acceptance State and Recover Interrupted Refreshes

Status: ACCEPTED

Status-date: 2026-07-15

## Context

DPA-300 requires direct-write detection and lifecycle recovery. The primary review found that accepted fingerprints had no non-evidentiary storage locus and that process loss between Lock and Release left refresh state, stale-lock takeover and written-but-unverified bytes undefined.

## Decision

The lifecycle SHALL persist one acceptance-state record for each accepted projection target or registered projected region.

The acceptance-state record:

- is lifecycle state;
- is not evidence;
- is not canonical source state;
- is not registry authority;
- is not a semantic renderer input;
- is written exclusively by the lifecycle;
- MUST be resolved through the existing Workspace abstraction;
- SHALL reside in Workspace-resolved `.agentic/` lifecycle state after validated implementation.

Its exact path and serialized schema remain `NEEDS_MAIN_REPO_VALIDATION` until DP1 Probe evidence exists.

The accepted record MUST contain at least:

- target and region identity where applicable;
- accepted plan identity;
- contract fingerprint;
- renderer identity and version fingerprint;
- ordered source fingerprints;
- accepted precondition or base identity;
- accepted output fingerprint;
- accepted complete-target fingerprint;
- partition fingerprint where applicable;
- acceptance event identity and timestamp as evidence-only context.

Drift classification SHALL compare current state independently with the accepted record:

- changed source fingerprints produce source drift;
- changed target bytes relative to the accepted output produce target drift;
- changed partition bytes or partition contract produce partition drift;
- changed contract, renderer, base or ownership inputs produce their corresponding drift class;
- multiple drift classes MAY be emitted together.

Recomputation MAY be used as a secondary integrity check but SHALL NOT replace persisted accepted-state comparison.

Before a new refresh plan or mutation for a target, the lifecycle MUST detect interrupted prior refresh state, including stale locks, plans without a completed verification/record sequence and target bytes matching a planned-but-unverified output.

An interrupted prior instance MUST be transitioned to `abandoned` by the detecting lifecycle operation and MUST emit a finding before a new mutation proceeds.

Bytes written by an interrupted instance MAY be re-verified only when:

- the exact recovered plan is available;
- every captured guard still matches;
- the target exactly matches the planned complete output;
- partition and preserved-region fingerprints still match.

Otherwise the generated content MUST be regenerated from declared canonical sources. It MUST NOT be silently accepted, merged with current target prose or used as an authority source.

Stale-lock takeover for a projection refresh MUST record the takeover, interrupted-instance identity and recovery disposition.

Atomic replacement MUST preserve the invariant that the target contains either the complete previous bytes or the complete planned replacement bytes, never an in-place partial region mutation.

## Alternatives considered

- Store accepted fingerprints in evidence records.
- Use recomputation alone.
- Always accept matching bytes after a crash.
- Always roll back or always regenerate without considering a still-valid recovered plan.
- Add a sixth consumer trust state for recovery or evidence failure.

## Rationale

Evidence cannot become runtime authority under DPA-INV-010. A lifecycle-owned state record allows drift classes to be distinguished without creating a parallel authority. Conditional re-verification avoids unnecessary rewrites while retaining plan and source integrity. Existing trust states already express interrupted attempts through `abandoned` and written output through `written-unverified`.

## Consequences

- DPA-300 must define acceptance-state fields, direct-write classification and interrupted recovery.
- DPA-500 must map the resulting findings and prohibit acceptance when required evidence or recovery checks are incomplete.
- DPA-600 must preserve cross-ref invalidation and competing-refresh behavior.
- DPA-700 must govern rollback when recovered-plan verification is not permitted.
- DPA-800 must specify implementation and negative-path tests.
- PROBE-002 must validate Workspace path compatibility and recovery behavior.

## Validation status

NORMATIVE architecture decision. Concrete main-repository state path, schema and implementation remain `NEEDS_MAIN_REPO_VALIDATION`.

## Affected specifications

DPA-100, DPA-300, DPA-500, DPA-600, DPA-700, DPA-800.

## Affected DP slices

DP1, DP2, DP3, DP5.
