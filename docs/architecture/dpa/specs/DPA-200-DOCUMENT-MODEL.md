# DPA-200 — Document Model

Status: review-ready
Status-date: 2026-07-15
Superseded-by: n/a

## 1. Purpose

This specification defines the normative DPA document model. It classifies documents and regions, assigns authority and write ownership, defines target semantics and consumer trust states, and constrains later registry, lifecycle, renderer, gate, concurrency and migration contracts.

DPA-200 conforms to stable DPA-000 and DPA-100 and incorporates DPA-ADR-013 and DPA-ADR-014.

## 2. Scope

DPA-200 defines:

- one primary form for every governed document instance;
- complete-target, registered-region and partition identity;
- projected, manual, historical and partition-byte ownership;
- target-semantics completeness;
- source, configuration and target authority relationships;
- consumer trust states;
- compatibility for documents without projection contracts;
- evidence required before selecting a migration form;
- obligations delegated to DPA-300 through DPA-800.

Concrete schemas, modules, commands, marker conventions and candidate-document classifications remain `NEEDS_MAIN_REPO_VALIDATION`.

## 3. Non-goals

DPA-200 MUST NOT:

1. define executable renderer resolution;
2. define lifecycle write algorithms;
3. define finding severity or gate mappings;
4. define cross-PR serialization mechanisms;
5. select a production migration target or form before DP1 evidence;
6. establish evidence or historical prose as runtime authority;
7. invent canonical history for migration convenience;
8. permit ambiguous, overlapping or incomplete ownership;
9. permit unvalidated output to be represented as accepted state;
10. create a parallel registry, lifecycle, freshness, evidence, Workspace or gate system.

## 4. Identity and partition model

### 4.1 Registered document

A registered document is identified by the existing main-repository documentation registry after validated adoption. Its concrete identity representation is `NEEDS_MAIN_REPO_VALIDATION`.

### 4.2 Projection target identity

A projection contract resolves to exactly one target identity:

- one complete registered document; or
- one registered region inside one registered document.

One renderer invocation MUST NOT compute multiple independently registered targets.

### 4.3 Registered region

A registered region is a non-overlapping, precisely bounded region. Its contract MUST define:

- parent document and region identity;
- boundary representation;
- target semantics;
- payload write owner;
- normalization rules;
- drift comparison domain;
- behavior for missing, duplicate or malformed boundaries.

### 4.4 Document-level partition contract

Every multi-region document MUST have one document-level partition contract.

The partition contract owns:

- boundary markers;
- separators and delimiters;
- boundary normalization;
- region order and adjacency;
- malformed, missing and duplicate boundary behavior.

Partition bytes are written exclusively by the existing document lifecycle.

Renderers MUST return region payload bytes only and MUST NOT emit partition bytes. Manual and historical writers MUST NOT mutate partition bytes.

All document bytes MUST belong to exactly one projected region, manual region, historical region or the partition contract. No byte may be unowned or multiply owned.

## 5. Primary document-form classifier

Every document instance resolves to exactly one primary form.

### 5.1 Manual document

A manual document has no projection contract. Existing registry and lifecycle behavior MUST remain unchanged. Malformed optional projection metadata MUST fail loud rather than silently falling back to manual behavior.

### 5.2 Full projection

A full projection is one complete registered document governed as one projected target.

It MAY be selected only when every target byte is reproducible from declared canonical sources and contract-declared configuration. Independently maintained prose MUST NOT remain inside the target.

### 5.3 Split projection

A split projection separates current projected representation and non-canonical historical or explanatory material into two or more independently registered target identities.

A single document containing projected and non-projected regions MUST NOT be classified as split projection.

Each split target has one owner, independent target semantics and an explicit consumer role. Historical material MUST NOT become renderer input unless separately made canonical by an accepted authority decision.

### 5.4 Hybrid document

A hybrid document is one registered document containing one or more projected registered regions and one or more non-projected regions.

It MUST have a complete partition contract. Every payload region has exactly one write owner. Projected and non-projected regions MUST be non-overlapping, and consumers MUST be able to identify the authoritative current representation.

### 5.5 Managed-head projection

A managed-head projection is an exceptional hybrid subtype with exactly one leading projected region and exactly one following historical region.

It MUST define:

- projected and historical region boundaries;
- lifecycle ownership of the projected payload and partition bytes;
- historical writer and edit policy;
- consumer read assumptions;
- drift and conflict behavior;
- cross-ref serialization requirements;
- rollback inputs and recovery behavior.

It MUST NOT auto-merge historical prose during drift recovery.

Subtype information MAY accompany the primary form but MUST NOT create two primary classifications.

## 6. Authority model

### 6.1 Canonical sources

Projected semantic output MUST derive only from declared canonical sources.

Evidence, mutation plans, reviews and historical prose MUST NOT become canonical sources through convenience, repetition or migration pressure.

### 6.2 Contract-declared configuration

Output-affecting configuration MUST be declared, versioned and included in reproducibility and fingerprint contracts. It may control representation but MUST NOT silently own domain facts.

### 6.3 Projection authority

An accepted projection is authoritative only as the bounded representation delegated by its validated projection contract. It MUST NOT become an independent canonical source for the facts it renders.

### 6.4 Historical regions

Historical regions may have human or evidentiary value but are not canonical state by default. Their writer and mutation policy MUST be explicit.

## 7. Write ownership

Each complete target and payload region has exactly one write owner.

Permitted owner classes are:

- existing document lifecycle for projected targets, projected regions and partition bytes;
- governed manual editor for manual payload regions;
- explicitly governed historical writer for historical payload regions;
- a later accepted owner only for non-projected regions.

No later DPA contract may assign a projected target, projected region or partition byte to a writer other than the existing document lifecycle.

Renderers, workflow orchestration and evidence producers are never target write owners.

## 8. Target semantics

A target-semantics contract MUST declare:

- replacement mode;
- encoding;
- line-ending policy;
- normalization policy;
- terminal-newline policy;
- partition-boundary preservation and replacement behavior;
- whether empty output is valid;
- malformed-boundary behavior;
- prohibited append behavior;
- fingerprint input domain.

A contract missing any required declaration is invalid and MUST fail loud. DM-011 owns planned completeness validation.

Projected append semantics are prohibited unless a later accepted contract preserves deterministic reproduction, partition ownership and the no-history-merge invariant.

## 9. Consumer trust-state model

DPA-200 owns the closed consumer trust-state dimension for generated/projected bytes:

1. `computed` — renderer output exists in memory; lifecycle validation is incomplete.
2. `plan-captured` — a governed mutation plan exists; no accepted state is claimed.
3. `written-unverified` — lifecycle-owned bytes exist in a governed workspace; post-write validation or gates are incomplete.
4. `accepted` — required validation, reproducibility and gates completed for the recorded acceptance scope.
5. `abandoned` — a non-accepted attempt ended by failure, cancellation or supersession; its bytes MUST NOT be represented as accepted.

The document-status token `planned` MUST NOT be used as a consumer trust state.

A new refresh attempt starts at `computed`. Detected drift produces findings and may block new integration. Drift MUST NOT silently or retroactively rewrite the recorded trust state of previously accepted bytes. DPA-500 may explicitly invalidate an acceptance scope through a governed rule.

Manual and historical bytes retain their declared authority and ownership semantics. DPA-500 defines document-level acceptance for hybrid documents from projected trust states, partition validity, non-projected validation obligations and consumer assumptions.

Only `accepted` projected output MAY be represented as accepted repository state.

## 10. Compatibility

Documents without projection contracts retain existing behavior.

Optional projection metadata MUST NOT change unrelated manual documents.

Unknown forms, unknown target semantics, incomplete contracts and ambiguous ownership MUST fail loud. Silent fallback to manual mutation is prohibited.

## 11. DP1 form-selection evidence

Before selecting a production form, DP1 MUST record:

- exact validation ref;
- canonical authority for every rendered fact;
- all readers, read order and consumer assumptions;
- all writers and mutation paths;
- complete reconstruction capability;
- target and partition identity;
- historical-region classification;
- registry and boundary compatibility;
- trust-state and gate placement;
- local and cross-ref concurrency requirements;
- rollback source and demonstrated recoverability.

The selection hierarchy is:

1. full projection when complete reconstruction is proven;
2. split projection when current and non-canonical historical material use separate target identities;
3. managed-head hybrid only as a justified exception;
4. no migration when authority, ownership, compatibility, trust or rollback cannot be established.

A candidate label, model opinion or Discovery record alone is not a form selection. Discovery informs later Probe and Assessment under DPA-ADR-015.

## 12. Normative invalid document-model states

The following are invalid:

1. missing or ambiguous canonical authority;
2. ambiguous target identity;
3. overlapping registered regions;
4. unowned bytes;
5. duplicate write ownership;
6. missing, duplicate, malformed or shared-control partition boundaries;
7. renderer output containing partition bytes;
8. manual or historical mutation of partition bytes;
9. undeclared semantic renderer input;
10. evidence or historical prose used as runtime authority without an accepted authority decision;
11. consumer acceptance asserted before required validation;
12. automatic historical-prose merge;
13. unavailable or invented rollback source;
14. silent fallback from malformed projection metadata to manual behavior;
15. one renderer invocation computing multiple independently registered targets;
16. production form selection without DP1 evidence;
17. a model requiring a parallel registry, lifecycle, freshness, evidence, Workspace or gate system.

The decision matrix and traceability are derived mappings of this catalog and MUST NOT define competing catalogs.

## 13. Delegated obligations

- DPA-300: registry validation, partition validation, lifecycle transitions, direct-write detection, atomic write and crash recovery.
- DPA-400: declared inputs, static resolution, payload-only output and partition-byte rejection.
- DPA-500: partition drift, trust-state gates, explicit acceptance invalidation and hybrid document acceptance.
- DPA-600: stale-attempt, base and cross-ref serialization behavior.
- DPA-700: partition-preserving migration, historical ownership and rollback.
- DPA-800: DP1 Discovery, Probe and Assessment evidence and form-selection output.

Delegation MUST NOT weaken this document model.

## 14. Traceability anchors

Primary invariants:

- DPA-INV-001 through DPA-INV-004;
- DPA-INV-005;
- DPA-INV-008 through DPA-INV-010;
- DPA-INV-011 and DPA-INV-012;
- DPA-INV-014 and DPA-INV-015;
- DPA-INV-017.

Primary decisions: DPA-ADR-001 through DPA-ADR-007, DPA-ADR-009 through DPA-ADR-015.

Detailed requirements are owned by `traceability/DPA-200_TRACEABILITY.md`.

## 15. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- registry support for region and partition representation;
- marker and structural-addressing conventions;
- candidate readers, writers and authority graph;
- lifecycle and direct-write paths;
- finding types and gate placement;
- atomic-write and crash-recovery behavior;
- concurrency mechanisms;
- rollback inputs.

Early DP1 Discovery may inventory these facts but may not decide sufficiency or conformance.

## 16. Review-ready assessment

DPA-200 is `review-ready` because:

- every primary form has a unique classifier;
- authority and ownership include partition bytes;
- target semantics are closed and completeness-tested;
- consumer trust states are closed and collision-free;
- one normative invalid-state catalog exists;
- tests, gates, evidence and rollback are traceable;
- no production form is preselected;
- primary review, secondary verification and maintainer adjudication are complete.

A bounded post-adjudication verification is still required before `stable`.
