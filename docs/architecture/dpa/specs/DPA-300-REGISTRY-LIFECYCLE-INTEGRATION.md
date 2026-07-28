# DPA-300 — Registry and Lifecycle Integration

Status: review-ready

Status-date: 2026-07-17

Authority: normative DPA specification; review-ready lineage includes independent restructure-equivalence verification and explicit Maintainer ratification

## 1. Purpose

This specification defines how document projection and partition contracts integrate with the existing documentation registry and document lifecycle of `vfi64/agentic-project-kit`.

DPA-300 does not create a second registry, lifecycle, evidence service, Workspace abstraction, command family, state authority or gate architecture. It defines the contract by which the existing mechanisms are extended after implementation validation.

Concrete main-repository module names, serialized fields, paths and command mappings remain `NEEDS_MAIN_REPO_VALIDATION` until the corresponding DP1 Probe is executed against an exact validation ref.

## 2. Normative dependencies

DPA-300 depends on:

- DPA-000 for architectural invariants;
- DPA-100 for authority, lifecycle-state, trust-state, drift and fingerprint vocabulary;
- DPA-200 for document forms, registered targets, regions, partition ownership and target semantics;
- DPA-ADR-001 through DPA-ADR-021;
- DP1 Discovery records DISC-001 through DISC-010 and DISC-003b at validation ref `6a9da7d363ae3f97f347b79a2679f6f848d8cdf3`.

Discovery evidence informs this contract but is not normative authority.

## 3. Scope

DPA-300 owns the registry and lifecycle integration contract for projections. It defines:

- optional projection-contract representation in the existing documentation registry;
- one parent-entry partition contract for multi-region documents;
- validation and fail-loud behavior;
- renderer resolution inputs and lifecycle invocation boundaries;
- immutable mutation plans and exact-plan-bound execution;
- local locking, stale-plan detection and atomic complete-file replacement;
- post-write verification and trust-state transitions;
- lifecycle-owned acceptance-state records;
- direct-write and multi-class drift detection;
- interrupted-refresh and stale-lock recovery;
- bounded evidence emission;
- adaptation of existing command paths rather than creation of a parallel DPA command.

DPA-300 does not own renderer implementation semantics, final gate severity, cross-ref serialization, migration selection or rollback policy. Those belong to DPA-400 through DPA-800.

## 4. Responsibility boundaries

### 4.1 Registry

The existing documentation registry MUST remain the sole authority for reviewed declarative projection and partition contracts.

The registry MUST NOT contain executable import paths, arbitrary plugin references, shell fragments or dynamic expressions.

### 4.2 Renderer

A renderer is resolved statically from an approved identifier. It reads declared sources and contract-declared configuration and returns text or bytes for exactly one registered target.

A renderer MUST NOT write, lock, commit, invoke workflows, mutate lifecycle state, assign trust state or trigger another renderer.

### 4.3 Lifecycle

The existing document lifecycle is the sole writer of projected targets, projected regions, partition bytes and lifecycle-owned acceptance state.

It owns validation, rendering invocation, planning, locking, writing, verification, recovery, findings and evidence emission.

### 4.4 Workflow orchestration

Workflow orchestration owns branch- and PR-level sequencing, base selection and integration-time revalidation. It MUST NOT become the target writer or renderer.

### 4.5 Evidence

Evidence records what occurred. It MUST NOT become canonical state, an acceptance-state substitute, a renderer input or authorization for later mutation.

## 5. Registry representation contract

### 5.1 Optional extension and compatibility

A registered document MAY carry optional projection metadata.

A registry entry without projection metadata remains a manual document and retains existing behavior.

Unknown or malformed projection metadata MUST fail loud. It MUST NOT silently downgrade to manual behavior.

The exact serialized field names and parser compatibility remain `NEEDS_MAIN_REPO_VALIDATION` for PROBE-001.

### 5.2 ProjectionContract

A conforming projection contract MUST declare:

- contract schema version;
- one target identity;
- primary document form;
- renderer identifier, renderer interface version and renderer semantic version;
- ordered declared canonical sources;
- ordered contract-declared configuration;
- target semantics and target-semantics version;
- lifecycle policy identifier;
- freshness policy identifier;
- evidence policy identifier;
- fingerprint algorithm and input-domain version;
- migration compatibility version.

For a region target, the projection contract MUST additionally declare:

- parent document identity;
- region identity;
- parent partition-contract identity;
- projected payload target semantics.

A region target MUST inherit boundary ownership, boundary representation, ordering and malformed-boundary behavior from the parent partition contract. It MUST NOT configure those properties independently.

A projected region write owner is fixed to the existing lifecycle and MUST NOT be configurable.

### 5.3 Parent-entry PartitionContract

Every multi-region document MUST declare exactly one partition contract on the parent document's registry entry.

The partition contract MUST declare:

- partition-contract identity and schema version;
- ordered complete region list;
- region identity and owner class for every payload region;
- one boundary representation per adjacent region pair or one document-wide equivalent;
- boundary-marker, separator and delimiter ownership;
- encoding, normalization and line-ending behavior for partition bytes;
- ordering and adjacency constraints;
- behavior for missing, duplicate, malformed or reordered boundaries;
- complete-byte ownership rules explaining every target byte;
- partition fingerprint algorithm and input domain;
- compatibility version.

Partition bytes are owned and written exclusively by the existing lifecycle. Renderers return payload bytes only. Manual and historical writers MUST NOT mutate partition bytes.

The exact serialized shape remains `NEEDS_MAIN_REPO_VALIDATION` for PROBE-001.

### 5.4 Declarative and static form

Projection and partition contracts MUST be data, not executable behavior.

The registry MUST reject:

- arbitrary executable import paths;
- shell commands or fragments;
- dynamic expressions;
- unreviewed globs that become semantic inputs;
- runtime fallback module names;
- renderer identifiers outside the static reviewed mapping;
- unsupported contract, target-semantics, fingerprint or partition versions.

### 5.5 Contract fingerprint

The contract fingerprint MUST cover every contract field that can affect:

- renderer selection or behavior;
- declared semantic inputs;
- target identity;
- output bytes;
- partition representation;
- normalization;
- lifecycle planning;
- freshness or gate interpretation;
- evidence interpretation;
- compatibility behavior.

A registry edit affecting any covered field invalidates existing plans.

## 6. Validation contract

Validation MUST be side-effect free and MUST occur before rendering or planning.

The lifecycle MUST reject:

1. missing required contract or partition fields;
2. unknown contract or partition schema or compatibility version;
3. unknown fingerprint algorithm or input-domain version;
4. unknown renderer identifier, renderer interface version or renderer semantic version;
5. executable or dynamic registry content;
6. ambiguous, duplicate or unsupported target identity;
7. region targets without exactly one valid parent partition contract;
8. missing, dangling, duplicate or inconsistent partition-contract references;
9. regions absent from the parent partition contract's ordered region list;
10. overlapping regions, unowned bytes or duplicate owners;
11. independently configured region boundary ownership or representation;
12. missing declared canonical sources;
13. renderer access to undeclared canonical sources;
14. undeclared output-affecting configuration;
15. incomplete target semantics;
16. unsupported form/target/partition combination;
17. renderer-side-effect requirements;
18. evidence or historical prose as semantic input without an independent accepted authority decision;
19. silent fallback to manual behavior.

Validation failure MUST prevent rendering, planning and mutation.

## 7. Lifecycle state machine

A projection refresh follows these phases in order:

1. **Recover** — detect and disposition interrupted prior refresh instances for the target;
2. **Resolve** — resolve Workspace paths, registry entry, target, partition contract and renderer identity;
3. **Inspect** — read declared sources, target bytes, acceptance state and required repository state;
4. **Validate** — apply registry, authority, ownership and target-semantics validation;
5. **Render** — invoke exactly one renderer for exactly one registered target;
6. **Plan** — capture immutable payload, reconstruction inputs, fingerprints and plan identity;
7. **Preflight** — compare the plan with current base, source, target, contract, renderer, partition, ownership and acceptance state;
8. **Lock** — acquire the existing Workspace mutation lock;
9. **Revalidate** — repeat all mutation-relevant comparisons under the lock without a second render;
10. **Write** — reconstruct and atomically replace the complete target through the lifecycle;
11. **Verify** — reread and compare payload, preserved-region, partition and complete-target fingerprints;
12. **Record** — persist acceptance state, findings and bounded evidence;
13. **Release** — release the lock and return the lifecycle result.

Rendering precedes immutable plan capture because the plan binds the rendered payload. If captured source, contract and renderer fingerprints still match under-lock revalidation, renderer determinism makes a second render unnecessary and prohibited for the same plan.

Failure before Write MUST leave the target unchanged.

A successful Write immediately places the refresh output in `written-unverified`.

Failure after Write MUST emit an explicit finding, keep the bytes non-accepted and invoke the recovery rules in §13.

## 8. Mutation plan

### 8.1 Required fields

A plan MUST capture:

- plan schema version and deterministic plan identity;
- exact base commit identity;
- target identity;
- registry entry identity and contract fingerprint;
- renderer identifier, renderer interface version and renderer semantic version;
- ordered source identities and fingerprints;
- ordered configuration identities and fingerprints;
- pre-mutation complete-target fingerprint;
- partition-contract identity and partition fingerprint where applicable;
- ownership fingerprint;
- target-semantics version;
- planned payload fingerprint;
- expected complete-target fingerprint;
- preserved-region fingerprint where applicable;
- write mode and reconstruction inputs;
- lock scope;
- dry-run status;
- creator context;
- creation timestamp as evidence only.

For region targets, payload, preserved-region, partition and expected complete-target fingerprints are all mandatory and distinct.

A plan MAY store complete expected target bytes. Otherwise it MUST store the payload plus all deterministic reconstruction inputs needed to derive the complete target under the lock.

### 8.2 Dry-run and execution authorization

Planning is dry-run by default.

Mutation requires an explicit execute action bound to the exact plan identity. A generic `--execute` without a matching immutable plan is insufficient.

### 8.3 Plan identity

Plan identity is a deterministic fingerprint over all captured preconditions and output expectations. Any covered change produces a different plan identity.

## 9. Stale-plan classification

A plan is stale when any captured mutation-relevant input no longer matches.

The lifecycle MUST compare independently for:

- base drift;
- source drift;
- target drift;
- contract drift;
- renderer drift;
- partition drift;
- ownership drift.

Multiple drift classes MAY be reported simultaneously.

Any stale-plan result MUST prevent Write. The lifecycle MUST NOT auto-merge target prose or reconstruct from stale target content. The only permitted recovery is a new plan from current authoritative inputs.

Elapsed time alone does not stale a plan.

## 10. Locking and atomic write

### 10.1 Existing Workspace mutation lock

Every projection mutation MUST use the existing Workspace mutation lock.

The lock is local workspace serialization only. It MUST NOT be represented as branch- or PR-level serialization.

A projection refresh MUST NOT initiate another projection refresh or acquire a second target's projection lock while holding the lock. Existing outer orchestration MAY use same-process reentrancy only to wrap exactly one projection refresh with deterministic release behavior.

### 10.2 Sole-writer boundary

Only the lifecycle may write:

- complete projected targets;
- projected payload regions;
- partition bytes;
- lifecycle-owned acceptance-state records;
- target-stored generated metadata when later accepted by contract.

Renderers, workflow coordinators, evidence producers, manual editors and migration helpers are not projection writers.

### 10.3 Atomic replacement

The lifecycle MUST construct the complete post-mutation target before Write.

It MUST atomically replace the complete file or use an equivalent implementation proven by Probe. In-place partial region writes are prohibited.

The target observed by readers is always either the complete pre-write bytes or the complete post-write bytes, never a partial file.

### 10.4 Preserved regions

For region mutation, bytes outside the projected region are reconstruction inputs, not semantic renderer inputs.

They MUST be:

- captured by fingerprint in the plan;
- revalidated under the lock;
- copied byte-identically;
- preserved without semantic interpretation;
- rejected rather than guessed when boundaries cannot be resolved.

Renderer payload MUST NOT include partition bytes unless ADR-013 is explicitly changed.

## 11. Post-write verification

After Write, the lifecycle MUST reread the target and verify:

- complete-target fingerprint;
- payload fingerprint;
- preserved-region fingerprint where applicable;
- partition fingerprint;
- boundary validity and ordering;
- encoding, normalization, line endings and terminal newline;
- target-semantics conformance.

Verification success leaves the bytes `written-unverified` until DPA-500 gates accept them.

Verification failure transitions the refresh instance to `abandoned`, emits a finding and invokes governed recovery. It MUST NOT silently restore prose through merge.

## 12. Acceptance state and direct-write detection

### 12.1 Acceptance-state record

The lifecycle MUST persist the latest accepted plan state as Workspace-resolved `.agentic/` lifecycle state.

The record MUST contain at least:

- target identity and acceptance scope;
- accepted plan identity;
- projection- and partition-contract fingerprints;
- renderer identifier, renderer interface version and renderer semantic version;
- ordered source fingerprints;
- accepted base identity when the projection contract declares base dependence;
- accepted payload fingerprint;
- accepted complete-target fingerprint;
- accepted partition fingerprint where applicable;
- accepted preserved-region fingerprint where applicable;
- ownership fingerprint;
- acceptance gate-set identity and result;
- acceptance timestamp as evidence only.

A mutation plan always captures its exact base. Acceptance state persists that base only for a contract whose semantics or acceptance explicitly depend on it. A base-independent accepted record without a base field is valid and MUST remain evaluable after the attempt-scoped plan has been cleaned up.

The acceptance-state record is lifecycle state. It is not evidence, canonical state, registry authority, target metadata or renderer input. Its concrete path and schema remain `NEEDS_MAIN_REPO_VALIDATION` for PROBE-002.

### 12.2 Drift classification and layered acceptance

Later inspection MUST compare current observations independently with accepted state and active contracts:

- changed source fingerprints produce source drift;
- for complete-target projections, changed actual target bytes against the accepted complete-target fingerprint produce target drift;
- for registered-region projections, changed lifecycle-owned projected payload bytes against the accepted payload fingerprint produce target drift;
- changed lifecycle-owned partition bytes or boundaries produce partition drift;
- changed ownership declarations produce ownership drift;
- changed contract or renderer identity produces contract or renderer drift;
- changed required base produces base drift only when the governing plan, requested operation or accepted contract requires that base.

For registered-region projections, complete-target and preserved-region fingerprints remain mandatory plan, under-lock reconstruction, post-Write verification and recovery guards. After acceptance, a governed change to bytes owned by a declared non-lifecycle owner, performed consistently with the active partition and ownership contracts, does not by itself produce projection target drift or invalidate the accepted lifecycle-owned payload.

An unexplained change to lifecycle-owned projected bytes remains target drift. An unexplained change to partition bytes or boundaries remains partition drift. A change whose responsible owner cannot be established safely MUST fail closed and MUST NOT be presumed authorized.

Multiple findings MAY coexist.

Expected-output recomputation MAY be a secondary integrity check but MUST NOT replace persisted comparison or use evidence as runtime state.

Source drift MUST NOT be mislabeled solely as target drift.

### 12.3 Detection placement

Direct-write and drift detection MUST occur on relevant refresh, preflight, audit and gate paths. An operating-system file watcher is not required.

A mismatch MUST produce an explicit finding and MUST NOT silently normalize, accept or overwrite the target.

## 13. Interrupted-refresh recovery

The Recover phase MUST detect at least:

- a stale projection lock owned by a dead process;
- a mutation plan without a matching completed verification/state sequence;
- target bytes matching a planned-but-unverified output after process loss;
- lifecycle state showing Write without completed Record or Release.

Before a new plan for the same target executes, the detecting lifecycle run MUST:

1. mark the interrupted refresh instance `abandoned`;
2. emit a finding;
3. record stale-lock takeover and interrupted-instance disposition;
4. determine whether an exact recovered plan and every captured guard still match.

If the exact plan and all guards still match, the lifecycle MAY re-run verification and continue from `written-unverified`.

Otherwise it MUST regenerate from current authoritative sources. It MUST NOT silently accept, merge historical prose or use interrupted bytes as authority.

Plan and recovery cleanup MUST remain bounded lifecycle state and MUST NOT create a new canonical history store.

## 14. Evidence contract

The lifecycle MUST record identity-critical evidence fields:

- target and plan identity;
- contract, renderer, source, pre-write target, partition, ownership, payload and expected complete-target fingerprints;
- preserved-region fingerprint where applicable;
- write and verification result;
- trust-state transition;
- acceptance-state update result;
- recovery disposition where applicable;
- findings and failure details.

Additional contextual fields SHOULD include:

- validation ref;
- command entry point;
- lock scope;
- timing;
- workflow/branch/PR context;
- versions and implementation identifiers.

Evidence MUST remain bounded and reproducible. It MUST NOT become a renderer input, canonical source, acceptance-state substitute or authorization for future mutation.

Failure to emit required evidence after Write MUST leave the bytes `written-unverified`, emit a finding and block DPA-500 acceptance. It does not create a new trust-state token.

## 15. Existing-command integration

Existing commands that write candidate documents MUST be routed through the lifecycle when their target becomes registered for projection.

At validation ref `6a9da7d…`, one observed `CURRENT_HANDOFF.md` writer path is:

`agentic-kit transfer admin-refresh-pr`
→ `transfer_repo_actions._refresh_operational_handoff_docs()`

DISC-003b established that the inspected `transfer chat-switch-complete` path does not write `CURRENT_HANDOFF.md` at that ref. Global writer-set completeness is not claimed and MUST be rebuilt at the Probe validation ref.

If `CURRENT_HANDOFF.md` is later selected as a projection target, every then-known writer MUST be adapted to:

- update declared source state before rendering;
- resolve the registry and lifecycle contract;
- produce an immutable plan;
- replace the governed region rather than append accumulated current-state prose;
- preserve non-projected bytes according to the partition contract;
- retain branch and PR orchestration;
- fail loud on marker or partition errors;
- verify, update lifecycle state and emit evidence.

A parallel DPA-only refresh command is prohibited.

The user-facing command entry point MAY evolve through the main repository's own command-deprecation governance. DPA-300 constrains governed target mutation, not permanent CLI naming.

This clause does not select a production document form.

## 16. Trust-state transitions

DPA-300 owns lifecycle transitions among:

- `computed` after a valid renderer result;
- `plan-captured` after immutable plan capture;
- `written-unverified` immediately after successful atomic Write;
- `abandoned` after rejection, invalidation, failed verification, cancellation or detected interruption.

Only DPA-500 owns transition to `accepted`, including its governed gate-set re-acceptance operation over unchanged already-accepted bytes.

A failed Verify keeps the instance non-accepted and transitions it to `abandoned`. A failed evidence write after successful verification leaves it `written-unverified` with a blocking finding.

Drift starts a new refresh attempt at `computed`; it does not silently rewrite prior acceptance history.

## 17. Failure behavior

The lifecycle MUST fail loud for:

- invalid or unknown contracts;
- missing sources;
- unknown renderer identifiers;
- ambiguous targets;
- invalid partition contracts;
- undeclared inputs;
- stale plans;
- lock acquisition failure;
- interrupted-refresh state requiring disposition;
- failed atomic replacement;
- failed post-write verification;
- failed required evidence emission;
- acceptance-state absence or tamper where comparison is required;
- direct writes or drift mismatches;
- ambiguous or unverifiable region ownership.

A warning-only signal never authorizes mutation. Mutation always requires explicit exact-plan-bound execution.

Time alone MUST NOT cause a hard failure.

## 18. Workspace and existing-system integration

Production DPA paths MUST resolve through the existing Workspace abstraction.

This includes:

- registry path;
- target paths;
- acceptance-state path;
- mutation-plan and recovery-state paths;
- lock path;
- evidence/report paths.

Hard-coded production paths are prohibited after validated implementation.

DPA-300 extends existing registry, lifecycle, Workspace, finding and command mechanisms. It MUST NOT create parallel replacements.

## 19. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- serialized projection and partition contract shapes;
- parser unknown-field and version behavior;
- renderer mapping location;
- lifecycle integration points;
- acceptance-state path and schema, including conditional base identity;
- authorized-owner provenance and comparison mechanics;
- interrupted-instance detection mechanics;
- atomic-write implementation;
- complete writer inventory at the Probe ref;
- finding identifiers and severities;
- gate and required-check mapping;
- region-level representability;
- candidate document form eligibility.

Probe confirms compatibility. It does not create architecture silently.

## 20. Planned DP1 Probe obligations

The governed Probe backlog and `traceability/DPA-300_TRACEABILITY.md` own the executable Probe recipes. At minimum, PROBE-001 MUST test projection- and partition-contract parser compatibility, and PROBE-002 MUST test lifecycle-owned plan, state, bounded replacement, recovery, writer integration, conditional base persistence and layered region-comparison behavior at an exact validation ref.

A Probe result that falsifies a required compatibility mapping MUST return the affected contract to adjudication. Probe evidence MUST NOT silently rewrite architecture.

## 21. Conformance demonstration

A conforming implementation MUST demonstrate:

1. manual registry entries retain existing behavior;
2. malformed or unknown projection metadata fails loud;
3. one exact target identity is bound to each plan;
4. plan identity changes for every covered precondition or output change;
5. mutation remains dry-run by default and execution is exact-plan-bound;
6. every production DPA path resolves through Workspace;
7. every projection mutation uses the existing local lock without nested projection mutation;
8. only the lifecycle writes projected targets, partition bytes and acceptance state;
9. complete-file replacement is atomic or Probe-proven equivalent;
10. preserved bytes remain byte-identical and are revalidated under lock;
11. successful Write immediately enters `written-unverified`;
12. post-write verification checks every planned payload, partition, preserved-region and complete-target fingerprint;
13. acceptance state supports independent multi-class drift comparison;
14. base-independent accepted state remains evaluable after plan cleanup;
15. contract-declared base dependence persists and compares accepted base identity;
16. governed non-lifecycle-owner region evolution does not create projection target drift;
17. unexplained lifecycle-owned payload or partition mutation fails with the correct drift class;
18. interrupted refreshes are detected and dispositioned before a new plan;
19. required evidence remains non-authoritative and bounded;
20. no renderer, wrapper or workflow assigns `accepted`;
21. no parallel registry, lifecycle, state, renderer, writer or gate subsystem is introduced.

## 22. Invalid states

A conforming implementation MUST reject or block:

1. projection metadata accepted through a second registry;
2. unknown contract, fingerprint or target-semantics version;
3. unknown renderer identifier;
4. executable renderer path;
5. missing, duplicate or inconsistent partition contract;
6. region target not listed by its parent partition contract;
7. overlapping regions;
8. unowned or multiply owned bytes;
9. independently configured region boundaries;
10. nested projection mutation;
11. renderer or workflow target writes;
12. mutation without exact plan identity;
13. mutation without the Workspace lock;
14. any stale captured guard;
15. partial in-place region write;
16. changed preserved bytes silently reused during a governed mutation plan;
17. missing post-write verification;
18. evidence used as acceptance state;
19. recomputation used instead of persisted accepted comparison;
20. source drift mislabeled solely as target drift;
21. stale-lock takeover without interrupted-instance disposition;
22. crashed-after-Write bytes silently accepted;
23. lifecycle assigning `accepted` outside DPA-500 gate authority;
24. successful Write failing to enter `written-unverified` immediately;
25. a new parallel DPA writer command;
26. append accumulation after governed bounded replacement;
27. hard failure caused only by elapsed time;
28. base-independent accepted state made unevaluable solely because its attempt plan was cleaned up;
29. authorized non-lifecycle-owner region evolution treated automatically as lifecycle target drift;
30. unexplained lifecycle-owned byte change treated as authorized owner evolution.

## 23. Traceability

Detailed requirement, test, Probe, gate, evidence and rollback mappings are in `traceability/DPA-300_TRACEABILITY.md`.

Primary decisions include DPA-ADR-001 through DPA-ADR-021.

## 24. Review-ready exit criteria

DPA-300 is `review-ready` when:

1. this contract, DPA-100 and DPA-200 are internally consistent;
2. registry, partition, lifecycle, acceptance-state and recovery contracts are complete;
3. every normative requirement has test, Probe, gate, evidence and rollback traceability;
4. diagrams match the contract;
5. repository-specific claims remain exact-ref bounded;
6. primary review, secondary verification, maintainer adjudication and independent post-adjudication verification are complete;
7. no production form or implementation success is claimed.

The review-ready criteria are satisfied only together with the accepted restructure-equivalence verification and Maintainer ratification record. The ADR-021 bounded amendment requires DPA-500 post-adjudication verification to confirm synchronized meaning. Stability remains blocked on applicable DP1 Probe evidence and subsequent governed revalidation.
