# DPA-700 — Migration and Rollback

Status: review-ready

Status-date: 2026-07-27

Authority: normative DPA specification; review-ready after Package A primary review, Maintainer adjudication and secondary technical verification; not stable, not implementation evidence and not a main-repository conformance claim

## 1. Purpose

This specification defines how an existing repository document MAY become a
registered projection target and how that migration can be stopped, rolled back
or rejected without inventing a new runtime authority.

DPA-700 extends the DPA-200 document-form model, DPA-300 lifecycle, DPA-400
renderer contract, DPA-500 freshness/gate contract and DPA-600 concurrency
contract. It does not create a second registry, lifecycle, renderer map, rollback
database, evidence service, workflow queue, history store or production adoption
path.

Repository-specific reader inventories, writer inventories, command mappings,
rollback storage, migration commands, state schemas, CI checks and production
document selections remain `NEEDS_MAIN_REPO_VALIDATION` until validated against
an exact main-repository ref.

## 2. Normative dependencies

DPA-700 depends on:

- DPA-000 for migration principles, reversibility and no-new-history discipline;
- DPA-100 for authority, historical record, document-form, drift, renderer
  identity and consumer trust-state vocabulary;
- DPA-200 for document forms, target identity, partition ownership, non-projected
  byte ownership and invalid states;
- DPA-300 for lifecycle ordering, immutable plans, local locking, atomic Write,
  Verify, Record and interrupted-refresh recovery;
- DPA-400 for renderer purity, declared inputs, renderer semantic versions and
  renderer failure boundaries;
- DPA-500 for freshness, gate decisions, acceptance-state behavior, layered
  acceptance and staged enforcement;
- DPA-600 for branch, pull-request and integration serialization;
- DPA-ADR-001, DPA-ADR-002, DPA-ADR-003, DPA-ADR-006, DPA-ADR-007,
  DPA-ADR-013, DPA-ADR-014, DPA-ADR-016, DPA-ADR-017, DPA-ADR-019,
  DPA-ADR-020 and DPA-ADR-021.

## 3. Scope

DPA-700 owns:

1. migration outcomes for existing documents;
2. the decision hierarchy among full projection, split projection,
   managed-head hybrid, other hybrid and no migration;
3. preconditions for selecting a migration form;
4. migration-plan identity and rollback-package requirements;
5. preservation of non-lifecycle-owned bytes;
6. rollback before Write, after Write before acceptance and after acceptance;
7. renderer semantic-version rollback consequences;
8. acceptance-state migration and rollback;
9. interrupted migration recovery;
10. migration evidence and finding requirements;
11. migration and rollback conformance tests.

DPA-700 does not own DP1 Discovery, Probe or Assessment execution, concrete
main-repository implementation, command UX, final production target selection,
freshness vocabulary, gate outcome vocabulary, cross-ref serialization mechanics
or stable promotion.

## 4. Authority boundary

Migration is a governed workflow that prepares or changes registered projection
contracts and then uses the existing lifecycle for projection mutation.

The existing main repository remains the only runtime authority. A Lab migration
draft, review, prompt, diagram or audit MUST NOT be represented as production
migration evidence.

The registry owns projection and partition contracts. The lifecycle owns target
and acceptance-state writes. Renderers compute payload bytes only. Workflow
orchestration owns sequencing across refs. Evidence explains decisions but MUST
NOT become runtime authority, rollback authority or semantic renderer input.

A migration helper MAY prepare a plan, evidence or operator checklist. It MUST
NOT write projected target bytes directly, assign `accepted`, bypass gates,
invent a canonical history source or repair stale output outside the lifecycle.

## 5. Migration outcomes

Every migration assessment MUST result in exactly one of these outcomes:

1. `no migration`;
2. `manual document`;
3. `full projection`;
4. `split projection`;
5. `hybrid document`;
6. `managed-head projection`.

`manual document` is the result when the document remains outside DPA projection
with existing behavior preserved. `no migration` is the result when migration is
unsafe, unsupported, unverifiable or unnecessary for the assessed target.

A migration outcome is not production selection until DP1 Assessment records
exact-ref evidence and Maintainer adjudication accepts the selection.

## 6. Decision hierarchy

Migration form selection MUST use this hierarchy:

1. choose `full projection` only when every target byte is reconstructable from
   existing declared canonical sources and contract-declared configuration;
2. choose `split projection` when the current authoritative representation and
   non-canonical history or explanation can use separate registered target
   identities with clear consumers and rollback;
3. choose `managed-head projection` only as a justified exceptional hybrid when
   one leading projected region and one following historical region preserve
   required users and the applicable DPA-600 workflow-serialization contract is
   `review-ready` for the selected scope or explicitly Maintainer-adjudicated as
   sufficient for that scope;
4. choose another `hybrid document` only when a complete partition contract,
   ownership model, reader model, writer model and rollback plan exist;
5. choose `manual document` or `no migration` when authority, readers, writers,
   consumers, compatibility, serialization, gates or rollback cannot be proven.

Lower-risk forms MUST be accepted or rejected explicitly before a higher-risk
form is selected. A managed-head or hybrid outcome MUST explain why full and
split projection are insufficient.

No new canonical history source MAY be introduced for migration convenience.

## 7. Preconditions for migration selection

Before a migration form can be selected, DP1 evidence MUST identify:

- exact validation ref;
- current target identity and document form;
- canonical authority for every rendered fact;
- non-canonical historical, explanatory or manual regions;
- every current reader and consumer order assumption that can affect safety;
- every current writer and writer path known at the validation ref;
- current gates and status checks that protect the document;
- proposed projection and partition contracts;
- renderer identifier, interface version and semantic version;
- source, configuration and target-semantics fingerprint domains;
- partition representation and malformed-boundary behavior;
- DPA-600 serialization dependencies;
- rollback source, rollback scope and recoverability proof;
- compatibility behavior for existing manual users.

Missing, contradictory or inaccessible evidence MUST produce `no migration` or a
bounded `manual document` outcome. It MUST NOT be papered over by Lab prose.

Discovery evidence alone may support preparation but MUST NOT select a verified
production form. Probe and Assessment remain required for production selection.

## 8. Migration plan

Every migration that can affect a registered target, projection contract,
partition contract, lifecycle state, acceptance state, writer routing, reader
expectation or gate behavior MUST have an immutable migration plan.

At minimum, the migration plan MUST capture:

- migration plan identity;
- target identity and current document form;
- selected migration outcome;
- exact validation ref;
- branch, PR and integration context required by DPA-600;
- pre-migration target fingerprint;
- pre-migration registry and contract fingerprints;
- pre-migration acceptance-state identity or absence;
- pre-migration gate-set identity;
- source and configuration fingerprints;
- renderer identifier, interface version and semantic version;
- target-semantics and partition identities;
- byte ownership map;
- reader inventory and writer inventory boundaries;
- rollback package identity;
- expected post-migration target, registry, state and gate identities;
- invalidation conditions;
- explicit no-new-history-source assertion.

The concrete serialized shape remains `NEEDS_MAIN_REPO_VALIDATION`.

The migration plan MUST be dry-run by default. Execution requires explicit
authorization, current DPA-600 revalidation and the DPA-300 lifecycle for any
target mutation.

## 9. Rollback package

A rollback package is bounded state and evidence needed to undo or abandon a
migration safely. It is not a new canonical history store.

At minimum, a rollback package MUST include:

- exact pre-migration validation ref and target fingerprint;
- exact pre-migration target bytes when target bytes might be changed;
- pre-migration registry, projection-contract and partition-contract bytes or
  fingerprints sufficient for restoration;
- pre-migration lifecycle-owned acceptance state when present;
- pre-migration gate-set identity;
- pre-migration writer and reader routing facts that are changed by migration;
- migration plan identity;
- intended rollback operation and limits;
- proof that rollback inputs are recoverable in the expected environment.

If exact rollback inputs cannot be preserved safely, the migration MUST NOT
execute. A repository's ordinary Git history MAY be a rollback input only when
the plan proves the required bytes, state and contracts are recoverable from the
exact ref without relying on generated prose as semantic authority.

Rollback evidence MUST be bounded. It MUST NOT copy secrets, broad logs, private
runtime state or unrelated repository content.

## 10. No-migration outcome

`no migration` is a valid safety outcome, not a failure to complete the Lab
specification.

`no migration` MUST be selected when:

- canonical authority for projected content is absent or ambiguous;
- readers require a representation that cannot be preserved safely;
- writers cannot be inventoried or routed without direct-write risk;
- partition ownership cannot cover every byte exactly once;
- rollback inputs are unavailable;
- renderer semantic version requirements cannot be satisfied;
- DPA-600 serialization cannot be enforced;
- required gates cannot fail closed;
- a production form would require a new canonical history source;
- migration would weaken manual-document compatibility without explicit
  adjudication.

`no migration` MAY be temporary. Later exact-ref evidence MAY reopen migration
assessment.

## 11. Full projection

Full projection MAY be selected only when all bytes of the target can be
recomputed from existing declared canonical sources and contract-declared
configuration.

Full projection requires:

- complete target identity and target semantics;
- complete source authority graph;
- no manual or historical bytes inside the projected target;
- one lifecycle writer for target bytes;
- renderer determinism under DPA-400;
- DPA-500 freshness and gate checks;
- DPA-600 integration-time revalidation;
- rollback to exact pre-migration target, registry and acceptance-state context.

Full projection MUST NOT be selected merely because generated output resembles
the existing target. Semantic authority must be declared and validated.

## 12. Split projection

Split projection MAY be selected when the current authoritative representation
and non-canonical history or explanation can safely become separate registered
target identities.

Split projection requires:

- a distinct target identity for each target;
- one owner per target;
- explicit consumer role and reader order for each target;
- no hidden dependence on the historical target for renderer output;
- writer routing for each target;
- rollback that preserves all target identities;
- gates that can evaluate each target without collapsing authority.

Split projection MUST NOT be represented as one hybrid document. Separate
targets require separate registry and lifecycle treatment.

## 13. Hybrid and managed-head projection

Hybrid document forms are exceptional. They MAY be selected only when full and
split projection are rejected with recorded reasons and the repository still
requires one document containing projected and non-projected regions.

Every hybrid outcome requires:

- one document-level partition contract;
- every byte owned exactly once;
- non-overlapping projected, manual and historical regions;
- independently registered projected regions;
- lifecycle ownership of projected payload and partition bytes;
- explicit manual or historical writer policy;
- reader assumptions that identify the current authoritative region;
- DPA-600 serialization for partition and target conflicts;
- rollback inputs for complete target, payload, preserved regions and
  partition bytes.

Managed-head projection is the exceptional hybrid subtype with exactly one
leading projected region followed by one historical region. It additionally
requires:

- proof that consumers can treat the leading region as current authority;
- proof that appending history cannot mutate partition or projected bytes;
- explicit historical writer and edit policy;
- no automatic historical merge during drift recovery or rollback;
- demonstrated rollback of both projected head and preserved historical tail.

If a historical writer can change partition bytes, boundary bytes or projected
payload bytes, managed-head migration MUST be rejected.

## 14. Preservation rules

Non-lifecycle-owned bytes MUST be preserved according to DPA-200 ownership and
DPA-500 layered-acceptance rules.

Migration MUST NOT:

- use historical prose as renderer input unless an independent accepted
  authority contract declares it canonical;
- regenerate manual or historical regions merely to clear projection findings;
- mutate partition bytes through a manual or historical writer;
- silently normalize preserved bytes;
- copy stale generated output into a new target as authority;
- collapse manual, historical and projected ownership into one writer.

For region migrations, the lifecycle MUST verify payload, preserved-region,
partition and complete-target fingerprints before acceptance.

## 15. Migration execution boundary

A migration workflow MAY perform preparation, planning, status checks, evidence
recording and operator guidance. Any target mutation MUST be executed by the
DPA-300 lifecycle.

A migration execution path MUST follow this outer order:

1. **Assess** -- confirm that DP1 evidence and Maintainer authorization select a
   migration outcome;
2. **Plan** -- create an immutable migration plan and rollback package;
3. **Preflight** -- compare plan identities under DPA-600;
4. **Lock** -- acquire only the local locks owned by the lifecycle for the
   target mutation;
5. **Migrate** -- route target mutation through the lifecycle;
6. **Verify** -- verify target, partition, ownership, state and gate outcomes;
7. **Record** -- record bounded evidence, findings and status;
8. **Release** -- release local locks and return workflow result;
9. **Revalidate** -- perform DPA-600 integration-time revalidation before merge
   or publication.

Failure before target Write MUST leave target bytes unchanged. Failure after
Write follows DPA-300/DPA-500 recovery and DPA-700 rollback rules.

## 16. Acceptance-state migration

A manual document without projection acceptance state MUST NOT gain `accepted`
state merely because a migration plan exists.

Acceptance state for a migrated projection MAY be created or updated only after:

- the selected projection contract is valid;
- the lifecycle has produced or verified exact target bytes;
- DPA-500 freshness and gates pass for the accepted scope;
- DPA-600 integration context is current for the operation;
- rollback evidence has been recorded or intentionally classified as unavailable
  before execution.

Migration MUST NOT reconstruct acceptance state from target bytes alone,
evidence alone or historical prose.

If a migrated target previously had projection acceptance state, the migration
plan MUST preserve enough pre-migration state to restore or invalidate it
explicitly during rollback.

## 17. Rollback before acceptance

Before acceptance, rollback MUST preserve the previous accepted production
meaning.

If failure occurs before Write, rollback is a no-op for target bytes and MUST
record the abandoned migration attempt.

If failure occurs after Write but before acceptance, rollback MUST either:

- restore exact pre-migration target bytes, registry/contract state and
  lifecycle state from the rollback package; or
- abandon the target in a visible `written-unverified` or equivalent failure
  state and require Maintainer-governed remediation when exact restoration cannot
  be proven.

Rollback before acceptance MUST NOT declare migrated bytes accepted.

## 18. Rollback after acceptance

After acceptance, rollback is a governed migration operation, not a silent undo.

Rollback after acceptance MUST:

- identify the accepted migration state being rolled back;
- identify the target form to restore or replace;
- prove the rollback source and pre-rollback target state;
- use the DPA-300 lifecycle for target mutation;
- apply DPA-500 gates to the restored or replacement state;
- apply DPA-600 serialization before integration;
- record findings and evidence;
- preserve or explicitly invalidate acceptance state.

Rollback after acceptance MAY return a target to manual form, full projection,
split projection, hybrid, managed-head or no migration only when the same DPA-700
selection and rollback requirements are satisfied.

If rollback cannot prove safe restoration, the required result is blocked
remediation, not automatic historical merge.

## 19. Renderer semantic-version rollback

Renderer semantic versions are output-relevant contract inputs.

When renderer semantic version changes, existing accepted projections become
stale according to DPA-500. Migration or rollback MUST either:

- regenerate with the current accepted renderer semantic version and current
  authoritative inputs;
- execute a still-supported prior renderer semantic version through an accepted
  static renderer mapping; or
- restore exact pre-migration target bytes and applicable state from the rollback
  package without claiming renderer reproducibility.

When rollback restores exact pre-migration target bytes and applicable state
without claiming renderer reproducibility, the restored projection MUST NOT
retain or receive `accepted` acceptance state for the restored scope. The
lifecycle MUST explicitly invalidate acceptance for that scope, so that DPA-500
`renderer drift` evaluation governs the next operation.

If a prior renderer semantic version is no longer executable and exact rollback
bytes or state are unavailable, automated rollback MUST fail closed. The
available outcomes are no migration, blocked remediation or a new migration plan
using current authoritative inputs.

A renderer implementation commit SHA MUST NOT substitute for renderer semantic
version. Retaining implementation evidence alone is not sufficient for
semantic-version rollback.

## 20. Writer and reader migration

Migration MUST inventory every known writer for the target at the validation ref
and classify whether each writer:

- remains manual and outside DPA;
- is removed;
- is routed through the DPA-300 lifecycle;
- writes only declared non-lifecycle-owned regions under a partition contract;
- is blocked until further governance.

An unadapted direct writer for lifecycle-owned projected bytes blocks migration.

Migration MUST also inventory reader assumptions that affect safety, including
whether readers consume the first current-state block, the whole document,
historical sections, generated markers, status fields or gate outputs.

If readers cannot be made compatible with the selected form, migration MUST
select a lower-risk form or no migration.

## 21. Interrupted migration recovery

Interrupted migration recovery MUST inspect:

- migration plan identity;
- rollback package availability;
- target bytes;
- registry and contract bytes;
- lifecycle attempt state;
- acceptance state;
- gate-set identity;
- branch, PR and integration context;
- writer routing state.

Recovery MAY complete migration recording only when exact target bytes, state,
contracts and gates can be proven to match the governed plan and current
authorities.

Otherwise recovery MUST preserve evidence, emit findings, abandon the attempt
and restore from the rollback package or require Maintainer-governed remediation.
It MUST NOT infer success from target bytes, generated markers or historical
prose alone.

## 22. Findings and evidence

Migration findings MUST be structured and bounded. They MUST include:

- target identity;
- migration plan identity when available;
- selected or rejected migration outcome;
- validation ref;
- authority, reader, writer, partition, renderer, gate or rollback dimension
  involved;
- DPA-100 drift class when the finding represents drift;
- non-drift category for missing evidence, unsupported form, rollback
  unavailability or interrupted migration;
- whether target bytes changed;
- whether acceptance state changed;
- whether rollback was executed, blocked or unnecessary;
- recommended next disposition.

Evidence SHOULD additionally record compared fingerprints, rollback-package
identity, writer-inventory limits, reader-inventory limits, serialization
context and known unsupported claims.

Evidence MUST NOT be used as semantic renderer input or as the authority that
selects a migration form.

## 23. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- exact reader inventory for any candidate production target;
- exact writer inventory for any candidate production target;
- exact status-authority graph;
- exact registry and projection-contract schema migration;
- exact partition representation and marker behavior;
- exact rollback-package storage and cleanup;
- exact acceptance-state path and schema migration;
- exact command path for migration and rollback;
- exact integration with branch protections, required checks and merge queue;
- exact retained renderer semantic-version execution policy;
- exact compatibility behavior for existing manual documents;
- exact evidence paths and retention limits.

No claim in this document states that the current main repository already
conforms.

## 24. Conformance tests

A conforming implementation MUST test:

1. no-migration outcome for missing canonical authority;
2. no-migration outcome for unknown reader behavior;
3. no-migration outcome for unadapted direct writer;
4. no-migration outcome for unavailable rollback source;
5. lower-risk form rejected before managed-head selection;
6. full projection accepted only when every byte is canonical-source
   reconstructable;
7. split projection with separate target identities and rollback;
8. hybrid projection with complete partition ownership;
9. managed-head projection with protected historical tail;
10. historical writer attempting to mutate boundary bytes;
11. evidence or historical prose used as renderer input rejected;
12. manual bytes regenerated to clear findings rejected;
13. rollback package missing pre-migration target bytes rejected;
14. rollback package missing acceptance-state handling rejected;
15. migration plan dry-run default;
16. migration execution without DPA-600 revalidation rejected;
17. target mutation outside lifecycle rejected;
18. failure before Write leaving target unchanged;
19. failure after Write before acceptance restoring exact prior bytes;
20. failure after Write before acceptance when restoration cannot be proven;
21. successful migration acceptance only after gates pass;
22. acceptance state not reconstructed from target bytes;
23. rollback after acceptance as a governed migration operation;
24. rollback to manual form;
25. rollback to prior projection contract;
26. changed renderer semantic version invalidating old plan;
27. prior renderer semantic version no longer executable with exact bytes
   available;
28. prior renderer semantic version no longer executable without exact bytes;
29. exact-byte rollback without renderer reproducibility invalidating acceptance
   state for the restored scope;
30. interrupted migration completion only when exact state matches plan;
31. interrupted migration failing closed when state is ambiguous;
32. writer routing update preserving manual-document compatibility;
33. reader order compatibility for managed-head;
34. no new canonical history store;
35. bounded evidence without secrets or broad logs;
36. Lab migration validation not represented as main-repository conformance.

## 25. Invalid states

The following are invalid:

1. production migration form selected without exact DP1 Assessment evidence;
2. full projection selected while any target byte lacks canonical authority;
3. split projection represented as one hybrid document;
4. hybrid selected without complete partition ownership;
5. managed-head selected without protected boundary and historical writer policy;
6. no-migration treated as architecture failure;
7. new canonical history store created for migration convenience;
8. historical prose used as semantic renderer input without accepted authority;
9. historical prose auto-merged during migration or rollback;
10. manual or historical bytes regenerated to clear projection findings;
11. unadapted direct writer left able to mutate lifecycle-owned bytes;
12. reader assumptions ignored during form selection;
13. migration plan lacking rollback package;
14. rollback package lacking exact recoverable inputs;
15. target bytes changed outside the lifecycle;
16. migration Write performed without local lock and stale-plan revalidation;
17. migrated output accepted before gates pass;
18. acceptance state reconstructed from target bytes or evidence alone;
19. `written-unverified` migration represented as accepted;
20. rollback after acceptance performed as silent undo;
21. renderer implementation evidence substituted for renderer semantic version;
22. unavailable prior renderer semantic version treated as reproducible;
23. rollback depending on unavailable repository history;
24. interrupted migration inferred successful from generated markers;
25. Lab migration draft represented as Kit runtime conformance;
26. `accepted` acceptance state retained over bytes restored without renderer
    reproducibility.

## 26. Review-ready criteria

DPA-700 may become `review-ready` when:

1. migration outcome hierarchy is complete and consistent with DPA-000 through
   DPA-600;
2. `no migration` is a first-class safe outcome;
3. full, split, hybrid and managed-head forms have complete preconditions;
4. preservation rules protect non-lifecycle-owned bytes;
5. rollback package requirements are complete and bounded;
6. rollback before and after acceptance is unambiguous;
7. acceptance-state migration and rollback do not create authority from target
   bytes or evidence;
8. renderer semantic-version rollback consequences are complete;
9. interrupted migration recovery fails closed;
10. writer and reader migration boundaries are explicit;
11. repository-specific mechanisms remain exact-ref fenced;
12. every requirement is traced to invariants, tests, later implementation,
   gates, evidence and rollback;
13. diagrams are synchronized;
14. primary review, Maintainer adjudication and independent post-adjudication
   verification are complete.

DPA-700 MUST NOT become `stable` before applicable migration, rollback, writer,
reader, renderer-version, acceptance-state and interrupted-migration Probes have
evidence at an exact main-repository validation ref.
