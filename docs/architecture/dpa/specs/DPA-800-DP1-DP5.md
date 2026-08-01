# DPA-800 — DP1–DP5 Implementation Specification

Status: stable

Status-date: 2026-08-01

Authority: normative DPA specification; stable for the accepted Kit-side DP1-DP5 scope through `docs/architecture/evidence/dpa/assessment/DPA_STABLE_PROMOTION_RECORD_20260801.json`

## 1. Purpose

This specification defines the governed implementation path from the DPA Lab
architecture to possible main-repository adoption through DP1, DP2, DP3, DP4 and
DP5.

DPA-800 translates DPA-000 through DPA-700 into exact-ref validation,
implementation, rollout, migration and staged-gate obligations. It does not
execute Probes, mutate the main repository, import Lab files into the Kit or
claim production conformance.

Concrete command names, module paths, fixture files, CI job names, evidence
paths, branch protections, implementation PR numbers, rollout targets and
migration selections remain `NEEDS_MAIN_REPO_VALIDATION` until validated against
an exact main-repository ref.

## 2. Normative dependencies

DPA-800 depends on:

- DPA-000 for architecture purpose, invariants and reversible adoption;
- DPA-100 for classification, validation-ref, evidence, drift, trust-state and
  gate vocabulary;
- DPA-200 for document forms, target identity, partition ownership and
  no-production-form-without-DP1-evidence discipline;
- DPA-300 for registry, lifecycle, plan, lock, Write, Verify, Record and
  recovery contracts;
- DPA-400 for renderer identity, deterministic output, purity and capability
  boundaries;
- DPA-500 for freshness, findings, gates, acceptance state and staged
  enforcement;
- DPA-600 for branch, pull-request and integration serialization;
- DPA-700 for migration, no-migration and rollback;
- DPA-ADR-001, DPA-ADR-002, DPA-ADR-003, DPA-ADR-004, DPA-ADR-005,
  DPA-ADR-006, DPA-ADR-007, DPA-ADR-008, DPA-ADR-009, DPA-ADR-010,
  DPA-ADR-011, DPA-ADR-012, DPA-ADR-013, DPA-ADR-014, DPA-ADR-015,
  DPA-ADR-016, DPA-ADR-017, DPA-ADR-019, DPA-ADR-020 and DPA-ADR-021;
  DPA-ADR-018 is a deferred, non-normative proposal and is not a DPA-800
  dependency;
- `integration/DP1_DISCOVERY_CONTRACT.md` for the governed DP1 Discovery
  substage;
- `MASTERPLAN.md` for execution sequencing, Probe boundaries and mutation
  freezes;
- `reviews/consolidated/PACKAGE_B_START_AUTHORIZATION_20260727.md` for the
  Package B start boundary.

## 3. Scope

DPA-800 owns:

1. DP1 through DP5 stage definitions;
2. exact-ref identities required by each stage;
3. DP1 Discovery, Probe and Assessment entry and exit criteria;
4. PROBE-001, PROBE-002, PROBE-003, PROBE-004 and renderer-Probe recipe
   requirements;
5. DP2 first-production-projection implementation preconditions;
6. DP3 controlled rollout entry and exit criteria;
7. DP4 status-authority discovery and conditional migration entry and exit
   criteria;
8. DP5 staged strict lifecycle-gate adoption entry and exit criteria;
9. controlled import and implementation slicing rules;
10. evidence, rollback, stop-state and adjudication requirements per stage;
11. conformance tests for the implementation sequence.

DPA-800 does not own foundational vocabulary, document-form definitions,
registry/lifecycle/renderer/freshness/concurrency/migration semantics, concrete
production implementation, final target selection, release governance or future
review-economics policy.

## 4. Authority boundary

The Lab specifies and prepares. The main repository implements and owns runtime
state.

DP stages MUST extend existing main-repository authorities:

- registry and contract authority remains in the existing registry system;
- target, partition and acceptance-state writes remain lifecycle-owned;
- renderer execution remains pure and statically resolved;
- findings and gates remain existing-system authorities;
- workflow orchestration owns branch, PR and integration serialization;
- evidence supports inspection but is not runtime authority.

DPA-800 MUST NOT authorize a parallel registry, lifecycle, Workspace,
acceptance-state store, renderer runner, evidence service, gate system, workflow
queue, migration system or release process.

## 5. Package B start boundary

Package B begins only from governed base
`3422b0070cc56393b23e5c05c5c83fd822d9aa50`, after Package A promoted DPA-600
and DPA-700 to `review-ready`.

The parked `dpa-800-dp1-dp5-draft` branch is not a Package B baseline and MUST
NOT be merged, rebased for review, or treated as adopted DPA-800 content. Any
comparison against that branch is draft-input inspection only.

This DPA-800 specification does not authorize Probe execution, DP2
implementation, Kit import, production mutation or DPA stability promotion.

## 6. Stage overview

The DPA implementation path consists of:

1. **DP1 - Proof of Architecture**: exact-ref Discovery, Probe and Assessment;
2. **DP2 - First Production Projection**: first approved projection integrated
   through existing systems;
3. **DP3 - Controlled Rollout**: additional targets introduced under bounded
   evidence and rollback;
4. **DP4 - Status-Authority Discovery and Conditional Migration**: governed
   migration or no-migration outcomes for status/handoff surfaces and other
   candidate documents;
5. **DP5 - Staged Strict Lifecycle-Gate Adoption**: observe, warn, block-new and
   strict enforcement through accepted gate policy.

Each stage MUST have explicit entry criteria, exit criteria, evidence, rollback
and stop conditions.

Stages MAY overlap only where this specification explicitly permits preparation.
Execution that mutates the main repository MUST remain sequenced by the
governing stage entry criteria.

## 7. Exact-ref identities

Every stage MUST distinguish:

- **historical evidence ref**: an older exact ref recorded as scoped evidence;
- **remote revalidation ref**: current remote `origin/main` observed before local
  contact;
- **local confirmation ref**: local checkout ref that confirms remote
  revalidation;
- **Probe validation ref**: exact ref against which Probe fixtures execute;
- **Assessment ref**: exact ref whose Probe results and evidence are
  adjudicated;
- **implementation baseline ref**: exact ref before DP2 mutation begins;
- **implementation result ref**: exact ref after a DP2, DP3, DP4 or DP5 slice;
- **import/adoption ref**: exact ref accepted by Maintainer adjudication for
  controlled import or rollout.

No evidence from one ref class MAY be silently promoted to another. A claim is
current only for the exact ref and scope recorded.

One exact commit MAY hold multiple ref roles only when the evidence record names
every role, scope, limitation and non-promotion boundary explicitly. Ref-role
co-location does not permit skipped revalidation, broader evidence claims or
implicit movement from historical evidence to current validation, implementation
or import authority.

## 8. DP1 purpose and structure

DP1 proves whether the proposed DPA contracts can be implemented safely in the
actual main repository.

DP1 has three substages:

1. **Discovery** - read-only factual inventory;
2. **Probe** - bounded compatibility and behavior tests against reviewable
   contracts;
3. **Assessment** - Maintainer-adjudicated proof-of-architecture conclusion from
   Discovery and Probe evidence.

DP1 remains one logical slice. Discovery may occur early under
`integration/DP1_DISCOVERY_CONTRACT.md`, but early Discovery does not satisfy
Probe or Assessment.

DP1 MUST NOT mutate the main repository except through explicitly governed Probe
fixtures in a suitable environment. Probe execution MUST NOT be represented as
production implementation.

## 9. DP1 Discovery

Discovery is governed by `integration/DP1_DISCOVERY_CONTRACT.md`.

Before any new Discovery or revalidation session, the operator MUST record an
exact current validation ref. Every record MUST be bounded to that ref.

Discovery MAY record facts about:

- registry representation;
- candidate readers and writers;
- authority inputs;
- lifecycle findings;
- lifecycle mutation paths;
- Workspace/path APIs;
- locking and concurrency mechanisms;
- gates and CI;
- candidate history and rollback inputs.

Discovery MUST NOT:

- test whether an observed mechanism satisfies a DPA contract;
- select a production document form;
- select a migration outcome;
- mutate code, state, registry entries or documents;
- reclassify assumptions without a committed evidence record.

Discovery output feeds Probe design and Assessment. It is not conformance
evidence.

## 10. DP1 Probe

Probe is bounded execution against an exact Probe validation ref. Probe tests
whether existing or proposed mechanisms satisfy reviewable DPA contracts.

At minimum, DP1 Probe MUST include:

1. **PROBE-001** - registry, projection-contract and partition-contract
   compatibility;
2. **PROBE-002** - lifecycle, plan, lock, Write, Verify, acceptance-state,
   recovery, re-acceptance, layered acceptance and writer-routing behavior;
3. **PROBE-003** - DPA-600 branch-context, pull-request, integration and
   post-integration serialization behavior;
4. **PROBE-004** - DPA-700 migration-form, rollback-package and renderer
   semantic-version rollback behavior;
5. **Renderer Probes** - renderer-map resolution, deterministic output, purity,
   capability restrictions, semantic versions, operational aborts and bounded
   failure diagnostics.

For any selected target or implementation slice, DP1 Probe evidence is complete
only when every applicable Probe family has exact-ref evidence or Assessment has
explicitly adjudicated that family as not applicable for the selected scope. An
undefined, omitted or unexecuted Probe family MUST NOT satisfy a DP2 entry gate.

Probe preparation MAY occur remotely. Probe execution requires a suitable local
environment and exact ref. Preparation MUST NOT be reported as execution.

Every Probe case MUST declare:

- governing DPA requirement;
- exact fixture identity;
- exact validation ref;
- setup preconditions;
- command or operation under test;
- expected result;
- actual result;
- PASS, FAIL, PARTIAL and BLOCKED criteria;
- evidence path and bounded logs;
- cleanup and rollback;
- limitation and adjudication mapping.

## 11. PROBE-001 minimum contract

PROBE-001 MUST test:

- parser compatibility for optional projection contracts;
- parser compatibility for partition contracts;
- backwards compatibility for existing manual registry entries;
- unknown schema-version handling;
- unknown-field handling;
- missing-required-field rejection;
- target identity and registered-region representation;
- projection and partition fingerprint domains;
- unsupported contract, target-semantics and partition combinations;
- preservation of existing non-projection document behavior.

PROBE-001 MUST NOT select a production target or migration form.

## 12. PROBE-002 minimum contract

PROBE-002 MUST test:

- immutable plan capture;
- source, target, base, contract, renderer, partition and ownership guards;
- local Workspace locking and reentrancy boundaries;
- stale-plan rejection before Write and under lock;
- atomic complete-target or partition-preserving replacement;
- post-Write verification;
- acceptance-state creation, tamper detection and scope validation;
- conditional accepted-base persistence;
- base-independent post-acceptance evaluation;
- gate-set re-acceptance without renderer invocation or target mutation;
- layered acceptance for registered-region projections;
- authorized non-lifecycle-owner evolution;
- out-of-band lifecycle-byte mutation;
- ambiguous ownership failure;
- interrupted write and stale-lock recovery;
- every then-known writer of selected targets, including handoff/status writers
  when those targets are candidates.

PROBE-002 MUST NOT be used to patch writers as a quick fix before evidence is
recorded and adjudicated.

## 13. Renderer Probe minimum contract

Renderer Probes MUST test:

- static renderer-map resolution;
- unknown renderer identifier;
- duplicate or ambiguous renderer identifier;
- interface-version incompatibility;
- semantic-version mismatch;
- implementation-evidence-only change;
- immutable lifecycle-resolved inputs;
- deterministic repeat execution;
- output type and target scope;
- prohibited filesystem writes;
- prohibited network access;
- prohibited subprocess execution;
- prohibited lock, workflow, state and evidence writes;
- nested-renderer prohibition;
- deterministic semantic resource bounds;
- non-semantic operational abort;
- bounded failure diagnostics.

Renderer Probe success is renderer-boundary evidence only. It does not prove the
registry, lifecycle, migration or strict-gate path.

## 14. PROBE-003 workflow-serialization minimum contract

PROBE-003 MUST test:

- branch/worktree/ref identity capture for projection-affecting operations;
- branch switch, rebase and reset stale-plan rejection;
- pull-request head and base identity comparison;
- required-check evidence bound to the exact PR head under review;
- merge eligibility blocked when the PR head, base, source, target, contract,
  renderer, ownership map, partition, gate set or base-context dependency
  changes;
- integration-time revalidation before acceptance-bearing workflow completion;
- rejection of a clean textual Git merge as projection-freshness evidence;
- deterministic regeneration from the current validation ref after stale-plan
  detection;
- competing projection refresh conflict detection across shared targets or
  registered partitions;
- post-integration refresh binding to the accepted integration ref and current
  target/source/contract/renderer state;
- acceptance-bearing evidence publication blocked while plan, branch, PR or
  integration identity remains stale.

PROBE-003 MUST NOT be represented as a workflow-queue implementation or as proof
that a production merge queue already enforces DPA-600.

## 15. PROBE-004 migration and rollback minimum contract

PROBE-004 MUST test:

- migration-form precondition evaluation, including `no migration`;
- lower-risk migration-form rejection before hybrid or managed-head selection;
- migration plan identity and immutable rollback-package capture;
- rollback-package recoverability for target bytes, registry/contracts,
  acceptance state, gate-set identity, writer/reader routing and exact refs;
- rollback before Write;
- rollback after Write before acceptance;
- rollback after acceptance, including explicit acceptance invalidation where
  renderer reproducibility is unavailable;
- renderer semantic-version rollback with retained prior renderer, exact-byte
  restoration and fail-closed unavailable-renderer paths;
- interrupted migration recovery without inferring success from markers,
  historical prose or evidence alone;
- prohibition of new canonical history sources for migration convenience;
- command-generated or command-updated candidate documents changed only through
  their source authority, generator or command contract, not by durable manual
  output patching.

PROBE-004 MUST NOT select a production migration target without Assessment and
Maintainer adjudication.

## 16. DP1 Assessment

Assessment converts Discovery and Probe evidence into a proof-of-architecture
decision.

Assessment MUST classify each discrepancy as exactly one primary class:

1. implementation conforms to the tested DPA requirement;
2. required implementation is missing;
3. implementation exists but differs from the DPA proposal;
4. a DPA assumption is falsified or incomplete;
5. the Probe or fixture is defective;
6. an additional reader, writer, parser, resolver or workflow path was
   discovered;
7. evidence is insufficient or execution is blocked.

For every discrepancy, Assessment MUST record whether architecture,
implementation, fixture or evidence must change. Probe results MUST NOT silently
change normative architecture.

Assessment MAY authorize later DP2 preparation only after Maintainer
adjudication records the accepted result and required amendments.

## 17. DP2 entry criteria

DP2 begins the first production projection only after:

- DPA-300 through DPA-800 are at least `review-ready` for the selected scope or
  have explicit Maintainer-adjudicated bounded amendments;
- every Probe family applicable to the selected target and implementation slice
  has exact-ref evidence, including PROBE-001 for registry/contract behavior,
  PROBE-002 for lifecycle/state/writer behavior, PROBE-003 for
  DPA-600 serialization behavior, PROBE-004 for DPA-700 migration/rollback
  behavior and Renderer Probes for renderer behavior; any non-applicable family
  must be explicitly adjudicated by Assessment;
- Assessment adjudicates every blocking discrepancy;
- the implementation baseline ref is frozen;
- the selected first target, if any, has exact authority, reader, writer,
  partition, gate, concurrency and rollback evidence;
- no direct writer remains unaccounted for;
- rollback and cleanup are demonstrably recoverable;
- Maintainer authorization permits main-repository mutation.

If any criterion is missing, DP2 MUST remain blocked.

## 18. DP2 implementation contract

DP2 MUST implement the first approved projection by extending existing systems.

The DP2 implementation slice MAY include only the minimal mechanisms needed for
the selected first target:

- registry parser and validator extension;
- projection and partition contract handling;
- static renderer resolution;
- lifecycle-owned plan, lock, Write, Verify, Record and Release behavior;
- acceptance-state persistence;
- structured findings and gate integration;
- DPA-600 preflight, under-lock and integration revalidation;
- DPA-700 rollback package where migration is involved;
- writer routing for the selected target;
- bounded evidence and cleanup.

DP2 MUST NOT introduce a parallel system or generalize beyond the selected
target without DP3 authorization.

## 19. DP2 exit criteria

DP2 exits only when:

- the implementation result ref is recorded;
- focused unit and integration tests pass;
- negative tests for unsupported contracts, unknown renderers, direct writers,
  stale plans and gate failures pass;
- rollback has been tested or explicitly blocked before production acceptance;
- evidence records exact commands, refs, limitations and outcomes;
- no migration or conformance claim exceeds the tested scope;
- Maintainer adjudication accepts the result.

DP2 success authorizes only the first accepted projection scope. It does not
authorize broad rollout or strict enforcement.

## 20. DP3 controlled rollout

DP3 extends DP2 to additional targets.

DP3 entry criteria:

- the DP2 result is accepted, bounded and recorded at an exact implementation
  result ref;
- every proposed rollout target has current reader, writer, source-authority,
  target-identity, document-form, DPA-600 dependency and DPA-700 rollback
  evidence;
- PROBE-003 covers the rollout's branch, pull-request and integration
  serialization needs, or Assessment explicitly adjudicates the missing scope;
- PROBE-004 covers every migration or rollback need in the rollout slice, or
  Assessment explicitly adjudicates the missing scope;
- every target slice has an independently revertible plan or explicit rollback;
- Maintainer authorization permits the bounded rollout slice.

If any DP3 entry criterion is missing, DP3 execution MUST remain blocked for the
affected target or slice.

Every DP3 target requires:

- exact target identity;
- source authority graph;
- reader and writer inventory;
- selected document form or no-migration result;
- DPA-600 dependency analysis;
- DPA-700 rollback package when migration is involved;
- focused positive and negative tests;
- rollout evidence and stop criteria.

DP3 MAY run in small slices. Each slice MUST be independently revertible or have
explicit rollback. Batch rollout without per-target evidence is prohibited.

DP3 exits only when:

- every target in the rollout slice has an exact implementation result ref;
- focused positive and negative tests pass for every target in the slice;
- rollback or independently revertible cleanup is tested or explicitly blocked
  before acceptance;
- evidence records target scope, commands, refs, limitations and outcomes;
- no success claim exceeds the accepted target slice;
- Maintainer adjudication accepts the rollout result and authorizes any next
  stage.

## 21. DP4 status-authority discovery and conditional migration

DP4 applies DPA-700 to status, handoff and other authority-sensitive documents.

DP4 entry criteria:

- DP2 and any required DP3 rollout mechanisms for the selected candidate scope
  are accepted or explicitly adjudicated as sufficient for status-authority
  evaluation;
- the current validation ref is recorded;
- reader, writer, generator and command-update inventories are rebuilt at that
  ref for every candidate document;
- PROBE-003 covers the candidate's workflow serialization needs, including
  post-integration refresh where applicable;
- PROBE-004 covers the candidate's migration and rollback needs;
- generated or command-updated candidate documents have identified source
  authority and generator or command-contract boundaries;
- Maintainer authorization permits the bounded DP4 candidate slice.

If any DP4 entry criterion is missing, DP4 MUST stop with `no migration`,
manual preservation or an explicit blocked state for the affected candidate.

DP4 MUST:

- rebuild reader and writer inventories at the current validation ref;
- classify current-state, historical, generated and manual regions;
- classify command-generated and command-updated outputs separately from manual
  Lab control surfaces;
- determine whether each candidate is manual, full projection, split projection,
  hybrid, managed-head or no migration;
- route every approved lifecycle-owned writer through DP2 mechanisms;
- route changes to generated or command-updated outputs through their source
  authority, generator or command contract instead of durable manual output
  patching;
- preserve non-lifecycle-owned bytes;
- record rollback and status-authority consequences;
- avoid wholesale Lab import.

If status authority, reader order, writer routing or rollback cannot be proven,
DP4 MUST select no migration or preserve manual behavior.

DP4 exits only when:

- every candidate in scope has an adjudicated migration, no-migration or manual
  preservation decision;
- generated and command-updated output handling is mapped to source/generator or
  command-contract authority;
- reader, writer, generator and command-update inventories are recorded with
  exact refs and limitations;
- rollback packages or no-migration/manual-preservation evidence are recorded;
- status-authority and handoff consequences are documented;
- Maintainer adjudication accepts the DP4 result and authorizes any next stage.

## 22. DP5 staged strict lifecycle-gate adoption

DP5 moves projection gates through explicit stages:

1. **observe** - record projection findings without blocking unrelated work;
2. **warn** - surface noncompliance prominently while preserving compatibility;
3. **block-new** - prevent new nonconforming projection states;
4. **strict** - block all configured noncompliant states in the accepted scope.

DP5 entry criteria:

- the selected projection scope has accepted DP2, DP3 and DP4 results where
  applicable;
- the target scope, gate set, findings mapping, enforcement stage and rollback
  stage are explicitly identified;
- current evidence shows that required checks fail closed for mutation safety,
  authority interpretation, target identity, byte ownership and acceptance;
- rollback to a less strict stage is tested or explicitly adjudicated as
  blocked before activation;
- documentation, status and handoff synchronization requirements are known;
- Maintainer authorization permits the exact stage transition.

If any DP5 entry criterion is missing, the stage transition MUST remain blocked.

DP5 stage changes require:

- Maintainer authorization;
- exact target and scope;
- current evidence that required checks are reliable;
- rollback path to a less strict stage;
- documentation and handoff synchronization;
- no time-only strict activation.

Unknown findings MUST fail closed when they affect mutation safety, authority
interpretation, target identity, byte ownership or acceptance.

DP5 exits only when:

- the stage transition result ref is recorded;
- findings and gate behavior are evidenced for the accepted scope;
- rollback to the prior or less strict stage is tested or explicitly blocked;
- documentation, status and handoff surfaces are synchronized;
- no unrelated work is blocked beyond the accepted scope;
- Maintainer adjudication accepts the stage result.

## 23. Controlled import

The Lab is never imported wholesale.

Controlled import MUST map each accepted Lab artifact to one of:

- normative specification imported as documentation;
- ADR imported or translated into main-repository governance;
- implementation requirement converted into code and tests;
- Probe evidence retained as evidence;
- historical Lab record not imported;
- rejected or superseded artifact.

Import MUST preserve the main repository as runtime authority. Imported Lab
documents MUST NOT create a second source of truth for current implementation
state.

## 24. Evidence and reports

Every DP execution record MUST include:

- stage and slice identifier;
- repository and exact refs;
- target identity where applicable;
- governing DPA requirements;
- commands or operations executed;
- expected and actual results;
- PASS, FAIL, PARTIAL or BLOCKED conclusion;
- bounded logs or report paths;
- rollback or cleanup result;
- limitations and unsupported claims;
- Maintainer decision required.

Evidence MUST be sufficient to reproduce the conclusion without broad logs,
credentials, private runtime state or chat memory.

## 25. Stop states

Any DP stage MUST stop in a visible blocked state when:

- an exact ref cannot be established;
- required evidence is missing;
- mutation would be required before authorization;
- Probe fixture behavior is ambiguous;
- a direct writer cannot be routed or blocked;
- rollback cannot be proven;
- a gate cannot fail closed for mutation safety;
- branch, PR or integration serialization cannot be inspected;
- a claim would exceed exact-ref evidence;
- Maintainer adjudication is required.

Stop states MUST preserve evidence and MUST NOT be cleaned up merely to continue
the workflow.

## 26. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- concrete Probe fixture files;
- concrete Probe command sequences;
- exact registry parser and validator extension points;
- exact lifecycle implementation modules;
- exact Workspace lock and state paths;
- exact renderer map;
- exact findings and severity mapping;
- exact gate-set identity and CI integration;
- exact writer inventory for selected targets;
- exact reader inventory for selected targets;
- exact rollback-package storage;
- exact migration command paths;
- exact strict-stage configuration and rollback;
- exact import PR boundaries.

No claim in this document states that the current main repository already
conforms.

## 27. Conformance tests

A conforming implementation path MUST test:

1. Discovery evidence cannot satisfy Probe;
2. Probe evidence cannot satisfy Assessment without adjudication;
3. historical evidence ref not treated as current ref;
4. remote revalidation ref not treated as local confirmation ref;
5. Probe preparation not represented as Probe execution;
6. PROBE-001 manual registry compatibility;
7. PROBE-001 unknown projection schema rejection;
8. PROBE-001 partition contract validation;
9. PROBE-002 immutable plan capture;
10. PROBE-002 stale-plan rejection;
11. PROBE-002 local lock behavior;
12. PROBE-002 direct writer detection;
13. PROBE-002 interrupted-write recovery;
14. PROBE-002 acceptance-state tamper detection;
15. PROBE-002 gate-set re-acceptance;
16. PROBE-002 layered acceptance;
17. renderer unknown identifier rejection;
18. renderer side-effect rejection;
19. renderer deterministic repeat execution;
20. renderer semantic-version mismatch;
21. Assessment discrepancy classification;
22. DP2 blocked before Probe adjudication;
23. DP2 first target implemented without parallel system;
24. DP2 rollback or blocked-remediation path;
25. DP2 evidence scope not generalized;
26. DP3 per-target rollout evidence;
27. DP3 batch rollout without per-target evidence rejected;
28. DP4 no-migration outcome for insufficient reader/writer evidence;
29. DP4 migration rollback package;
30. DP4 handoff/status writer routing;
31. DP5 observe stage;
32. DP5 warn stage;
33. DP5 block-new stage;
34. DP5 strict stage with rollback;
35. time-only strict activation rejected;
36. unknown mutation-safety finding failing closed;
37. controlled import map completeness;
38. Lab artifact imported as runtime authority rejected;
39. stop-state evidence preservation;
40. no Kit conformance claim from Lab gates;
41. PROBE-003 branch-context stale-plan rejection;
42. PROBE-003 PR head/base and required-check identity binding;
43. PROBE-003 integration-time revalidation before merge eligibility;
44. PROBE-003 post-integration refresh binding to the accepted integration ref;
45. PROBE-004 migration-form precondition evaluation;
46. PROBE-004 rollback-package recoverability;
47. PROBE-004 post-acceptance rollback and acceptance invalidation;
48. PROBE-004 renderer semantic-version rollback fail-closed paths;
49. DP3 exit criteria before DP4 authorization;
50. DP4 generated-output handling through source, generator or command contract;
51. DP5 entry and exit criteria before strict-stage claims.

## 28. Invalid states

The following are invalid:

1. Discovery represented as Probe;
2. Probe represented as production implementation;
3. Assessment skipped before DP2;
4. stale historical evidence represented as current implementation fact;
5. production form selected without DP1 Assessment;
6. DP2 mutation before exact Probe evidence and Maintainer authorization;
7. first projection implemented through a parallel registry or lifecycle;
8. renderer granted write, lock, workflow, state or evidence authority;
9. direct writer left unaccounted for on an accepted target;
10. acceptance state created from evidence or target bytes alone;
11. rollback source unavailable after migration execution;
12. DP3 batch rollout without per-target evidence;
13. DP4 status migration without reader/writer inventory;
14. DP5 strict mode activated by elapsed time alone;
15. unknown safety finding treated as pass;
16. Lab document imported wholesale as runtime authority;
17. command output or chat memory treated as evidence without committed record;
18. stop-state evidence deleted to unblock work;
19. main-repository conformance claimed from Lab validation;
20. Kit import performed before controlled import planning and authorization;
21. parked DPA-800 branch treated as the Package B baseline;
22. DP2 started while an applicable Probe family is undefined, unexecuted or not
    explicitly adjudicated as non-applicable;
23. DPA-600 serialization behavior implemented before PROBE-003 evidence or
    explicit Assessment adjudication;
24. DPA-700 migration or rollback behavior implemented before PROBE-004 evidence
    or explicit Assessment adjudication;
25. DP3, DP4 or DP5 represented as complete before its exit criteria and
    Maintainer adjudication are satisfied;
26. command-generated or command-updated Kit output durably patched by hand
    instead of changing its source authority, generator or command contract.

## 29. Stable criteria

DPA-800 is `stable` for the accepted Kit-side DP1-DP5 scope when:

1. DP1 through DP5 stage boundaries are complete;
2. exact-ref identity classes are unambiguous;
3. Probe recipe requirements cover registry, lifecycle, renderer, freshness,
   concurrency, migration and rollback;
4. DP2 entry and exit criteria prevent premature implementation;
5. DP3 rollout criteria prevent unbounded expansion;
6. DP4 migration criteria preserve status authority and rollback;
7. DP5 staged strict-adoption criteria preserve fail-closed mutation safety;
8. controlled import avoids wholesale Lab adoption;
9. stop states preserve evidence;
10. every requirement is traced to invariants, tests, later implementation,
    evidence and rollback;
11. diagrams are synchronized;
12. repository-specific mechanisms remain exact-ref fenced;
13. primary review, Maintainer adjudication and independent post-adjudication
    verification are complete;
14. applicable DP1 through DP5 evidence, implementation and rollout records are
    exact-ref recorded and adjudicated in the Stable Promotion record.

Future rollout or target expansion requires fresh exact-ref evidence before it
can inherit this stable scope.
