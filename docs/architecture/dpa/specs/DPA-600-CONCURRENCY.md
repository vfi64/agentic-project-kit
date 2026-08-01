# DPA-600 — Concurrency and Workflow Serialization

Status: stable

Status-date: 2026-08-01

Authority: normative DPA specification; stable for the accepted Kit-side DP1-DP5 scope through `docs/architecture/evidence/dpa/assessment/DPA_STABLE_PROMOTION_RECORD_20260801.json`

## 1. Purpose

This specification defines how document projection work is serialized across
local refresh attempts, worktrees, branches, pull requests and integration
checks.

DPA-600 extends the existing registry, lifecycle, Workspace, findings and gate
architecture defined by DPA-300 through DPA-500. It does not create a second
lock manager, workflow queue, merge engine, evidence store, projection command
family or production adoption path.

Repository-specific command names, GitHub integration details, queue mechanics,
lock-file schema, status-check wiring, merge-queue policy and exact branch
protections remain `NEEDS_MAIN_REPO_VALIDATION` until validated against an exact
main-repository ref.

## 2. Normative dependencies

DPA-600 depends on:

- DPA-000 for canonical invariants and no-parallel-system discipline;
- DPA-100 for authority, drift, finding, gate and consumer trust-state
  vocabulary;
- DPA-200 for target identity, document form, partition ownership and target
  semantics;
- DPA-300 for registry contracts, lifecycle ordering, immutable plans,
  Workspace resolution, local locking, Write, Verify, Record and recovery;
- DPA-400 for pure renderer boundaries, renderer identity and renderer semantic
  versioning;
- DPA-500 for freshness classification, finding consequences, gate decisions,
  operation-scoped base-context evaluation and staged enforcement;
- DPA-ADR-003, DPA-ADR-004, DPA-ADR-006, DPA-ADR-007, DPA-ADR-008,
  DPA-ADR-014, DPA-ADR-016, DPA-ADR-017, DPA-ADR-019, DPA-ADR-020 and
  DPA-ADR-021.

## 3. Scope

DPA-600 owns:

1. the boundary between local locking and cross-ref serialization;
2. operation, branch and pull-request identities required by projection plans;
3. stale-plan rejection across local, branch and pull-request contexts;
4. integration-time revalidation before merge, publication or acceptance-bearing
   workflow completion;
5. competing projection refresh conflict detection;
6. deterministic regeneration from the current validation ref after drift;
7. workflow serialization obligations for projected targets and partitions;
8. cross-ref evidence requirements;
9. conformance tests for concurrent and stale-plan scenarios.

DPA-600 does not own renderer implementation, target writing, acceptance-state
persistence, freshness vocabulary, gate outcome vocabulary, migration-form
selection, rollback policy, concrete CI implementation, command UX or production
main-repository mutation.

## 4. Authority boundary

The existing document lifecycle remains the sole writer of projected targets,
projected regions, partition bytes and lifecycle-owned acceptance state.

The lifecycle owns local refresh ordering from DPA-300:

Recover -> Resolve -> Inspect -> Validate -> Render -> Plan -> Preflight -> Lock
-> Revalidate -> Write -> Verify -> Record -> Release.

Workflow orchestration owns branch- and pull-request-level sequencing, base
selection, integration-time revalidation and competing-PR conflict disposition.
It MUST NOT become the renderer, target writer, acceptance-state authority or
freshness classifier.

The existing gate architecture remains the production gate authority. DPA-600
defines the projection-specific serialization contract that the existing
architecture must later enforce.

Evidence MAY explain concurrency decisions. Evidence MUST NOT itself decide that
a stale plan is fresh, that a conflict is safe, or that a pull request is
eligible to merge.

## 5. Serialization layers

Projection concurrency has distinct layers. A conforming implementation MUST
keep them separately visible:

1. **refresh-attempt serialization** -- one lifecycle attempt for one registered
   target or declared target partition;
2. **local Workspace locking** -- local process and worktree mutation
   serialization while the lifecycle is writing;
3. **branch-context serialization** -- branch-scoped plan validity against the
   source, target, contract, renderer and base observed by that branch;
4. **pull-request serialization** -- exact PR head and base validation before
   PR evidence, required checks or merge eligibility are accepted;
5. **integration serialization** -- repository-level ordering when a merge,
   queue, administrative refresh or post-merge workflow could invalidate another
   projection plan;
6. **post-integration refresh** -- bounded successor handoff, state refresh or
   status refresh after accepted integration, when such refresh is owned by the
   existing repository workflow.

The local Workspace lock serializes only layer 1 and layer 2. It MUST NOT be
represented as proof of branch, pull-request or integration serialization.

Layer 3 through layer 6 are workflow-orchestration responsibilities. They MUST
reuse existing repository mechanisms where possible and MUST NOT introduce a
parallel DPA-only workflow system.

## 6. Concurrency identity

Every acceptance-bearing projection plan MUST capture enough identity to prove
that the plan is still being executed in the same concurrency context.

At minimum, the plan or its bound workflow context MUST record:

- registered target identity;
- partition identity and target-semantics version when applicable;
- plan identity and attempt identity;
- operation kind;
- repository identity when the workflow can operate across repositories;
- worktree identity or equivalent local Workspace context;
- branch name or detached-ref identity;
- local head commit at plan creation;
- remote tracking ref and observed remote head when applicable;
- intended base commit or base ref used by the operation;
- pull-request number, exact PR head and exact PR base when applicable;
- source fingerprints;
- pre-mutation complete-target fingerprint;
- lifecycle-owned payload fingerprint when applicable;
- partition, ownership and preserved-region fingerprints when applicable;
- projection contract fingerprint;
- renderer identifier, interface version and semantic version;
- gate-set identity required by the operation;
- acceptance-state identity or absence;
- lock scope expected by the lifecycle;
- validation-ref identity when the plan is generated from a governed validation
  ref.

The concrete serialized shape remains `NEEDS_MAIN_REPO_VALIDATION`.

Missing mandatory concurrency identity MUST fail closed before mutation,
acceptance, integration or merge eligibility. A partial plan MAY be useful as a
dry-run diagnostic, but it MUST NOT authorize Write or integration.

## 7. Local Workspace locking

Every projection mutation MUST use the existing Workspace mutation lock defined
by DPA-300.

The local lock MUST protect:

- target bytes written by the lifecycle;
- partition bytes owned by the lifecycle;
- lifecycle-owned acceptance state;
- attempt-state transitions that must remain crash-recoverable;
- lock-scoped evidence that records the mutation result.

The local lock MUST NOT protect:

- another branch in another worktree;
- another pull request;
- the remote target branch;
- an external merge queue;
- a status check produced for a different exact head;
- a post-merge administrative refresh running on a later base.

Same-process reentrancy MAY exist only when existing orchestration wraps exactly
one projection refresh with deterministic release behavior. A projection refresh
MUST NOT invoke another projection refresh or acquire a second target's
projection lock while holding the lock.

Stale local locks remain a DPA-300 recovery concern. DPA-600 requires only that a
stale-lock takeover MUST NOT be treated as cross-ref serialization.

## 8. Stale-plan rule

A plan is stale when any mandatory captured identity or fingerprint relevant to
the requested operation no longer matches current authoritative inputs.

The stale-plan comparison MUST include every applicable DPA-300 drift class:

1. base drift;
2. source drift;
3. target drift;
4. contract drift;
5. renderer drift;
6. partition drift;
7. ownership drift.

It MUST additionally include DPA-500 gate-set and acceptance-state freshness when
the operation can mutate target bytes, mutate acceptance state, publish evidence
as current, satisfy a required check or merge a pull request.

Elapsed time alone MUST NOT stale a plan. Time MAY be recorded as evidence and
MAY trigger a warning or required revalidation policy only when that policy is
explicitly accepted and does not replace identity and fingerprint comparisons.

An unavailable mandatory comparison is `indeterminate` or `invalid` under
DPA-500. For mutation, acceptance, required-check publication or integration it
MUST fail closed.

Any stale-plan result MUST prevent Write, acceptance-state update,
acceptance-bearing evidence publication and merge eligibility. The lifecycle or
workflow MUST abandon the stale attempt and require a new plan from current
authoritative inputs.

## 9. Branch-context serialization

Projection plans are branch-context scoped. A plan created on one branch MUST
NOT be executed or represented as current on another branch unless the workflow
proves that every mandatory concurrency identity still matches.

A branch-context plan becomes stale when:

- the local branch head changes after plan creation in a way that affects
  source, target, contract, renderer, partition, ownership, gate-set or required
  base context;
- the branch is rebased, reset or retargeted without regenerating the plan;
- the intended base ref moves and the operation requires the newer base;
- a registered target is changed by a non-lifecycle owner outside the accepted
  ownership contract;
- a workflow attempts to reuse evidence or checks from a different exact head.

Multiple branches MAY independently produce valid local dry-run plans. That does
not imply that all plans remain valid after one branch merges. The later branch
MUST revalidate against the current integration ref before merge eligibility.

## 10. Pull-request serialization

Pull-request projection evidence and required checks MUST bind to an exact PR
head and an exact PR base.

A PR-level projection check MUST fail closed or become stale when:

- the PR head SHA differs from the head used for plan generation or check
  execution;
- the target branch base SHA differs from the base used by an
  acceptance-bearing plan and the operation requires current-base validation;
- another merged PR changes any registered projection target, declared source,
  projection contract, partition contract, renderer semantic identity, ownership
  map, gate-set policy or acceptance-state context relevant to the plan;
- the PR changes a projected target outside the lifecycle path;
- the PR carries projection evidence that cannot be traced to the exact head;
- branch protection, required-check or merge-queue state cannot be inspected.

Workflow orchestration MUST NOT merge a PR solely because local lifecycle checks
passed earlier on a now-stale branch context.

When two PRs affect disjoint projection targets and no shared source, contract,
renderer, partition, ownership, gate-set or base-context dependency exists, the
workflow MAY treat them as independent. The independence decision MUST be
recorded with the compared identities.

When two PRs affect the same registered target, the same lifecycle-owned
partition, a shared declared source, a shared projection contract, a shared
renderer semantic identity or a shared gate-set policy, the later integration
candidate MUST revalidate after the earlier integration candidate lands.

## 11. Integration-time revalidation

Before merge, publication or any equivalent integration action, workflow
orchestration MUST revalidate the candidate against the current integration ref.

Integration-time revalidation MUST verify:

- exact candidate head;
- exact target base;
- registered target identity and current target bytes;
- declared source fingerprints;
- projection and partition contract fingerprints;
- renderer identifier, interface version and semantic version;
- ownership and target-semantics identities;
- gate-set identity;
- acceptance-state identity or absence when relevant;
- whether any competing integration candidate has changed a shared dependency;
- whether generated evidence and checks were produced from the same exact head
  and applicable base.

If any mandatory comparison fails, is unavailable or is out of scope for the
available workflow, the integration decision MUST fail closed. The candidate MAY
be regenerated from the current validation ref or returned for Maintainer
adjudication.

## 12. Regeneration after drift

The only default recovery from a stale projection plan is a new plan from current
authoritative inputs at the current validation ref.

Regeneration MUST:

1. abandon the stale attempt without accepting its output;
2. preserve bounded evidence and findings explaining why the attempt became
   stale;
3. reread current sources, target bytes, contracts, renderer identity, ownership,
   partition state, gate-set policy and operation base context;
4. render a new payload through the DPA-400 renderer boundary;
5. capture a new immutable DPA-300 plan;
6. repeat preflight, lock, under-lock revalidation, Write, Verify, Record and
   Release as a new attempt.

Regeneration MUST NOT:

- auto-merge historical prose;
- use stale target content as authority;
- reconstruct acceptance state from target bytes alone;
- patch preserved regions merely to clear projection findings;
- merge generated output from two stale plans;
- silently carry required-check success from an old head to a new head.

Manual or historical regions remain governed by DPA-200 ownership and DPA-500
layered-acceptance rules. DPA-700 will define migration and rollback choices; it
does not authorize DPA-600 to merge historical prose automatically.

## 13. Workflow serialization

Workflow orchestration MUST serialize acceptance-bearing projection work at the
smallest safe dependency scope.

The default dependency scope is a registered target. A narrower partition scope
MAY be used only when DPA-200 ownership, DPA-300 plan guards and DPA-500
freshness comparisons prove that partitions are independent for the requested
operation.

Workflow orchestration MUST serialize operations that share:

- one registered target;
- one lifecycle-owned partition;
- one declared source whose fingerprint affects output;
- one projection or partition contract;
- one renderer semantic identity whose change could affect output;
- one ownership map;
- one gate-set policy required for acceptance or integration;
- one base-context requirement.

Read-only audits MAY run concurrently when they cannot mutate target bytes,
acceptance state, workflow state, required checks or integration decisions. A
read-only audit that discovers stale or invalid state MUST NOT repair it unless a
separate acceptance-bearing lifecycle operation is authorized.

Administrative refreshes and handoff/status refreshes are workflow operations.
When such operations write registered projection targets or lifecycle-owned
state, they MUST follow the same target, partition, plan, lock and integration
serialization contract.

Post-integration refreshes that run after an accepted integration on a new base
MUST bind to the accepted integration ref and MUST re-read the current target,
source, contract, renderer, ownership, gate-set and acceptance-state identities
they publish as current. A post-integration refresh MUST NOT publish successor
handoff, state or status evidence as current when a mandatory comparison is
stale, indeterminate or unavailable. When a post-integration refresh changes a
registered projection target, lifecycle-owned state or workflow-visible
dependency, later integration candidates sharing that dependency MUST
revalidate before merge eligibility.

## 14. Conflict handling

A projection conflict exists when concurrent work changes or proposes to change
the same serialization dependency scope and the later candidate cannot prove that
its plan remains current.

The required default disposition is:

1. block mutation, acceptance or integration for the later candidate;
2. record the stale or conflicting identities;
3. require regeneration from the current validation ref;
4. preserve the prior accepted state until a new attempt passes.

Maintainer adjudication MAY select a non-default disposition only when it is
recorded as an explicit governance decision and does not contradict DPA-000
through DPA-500. A chat-memory statement, stale review note or unverified
evidence record is insufficient.

Textual Git merge success MUST NOT be represented as projection conflict
resolution. A clean textual merge may still contain stale projection output.

## 15. Multi-target operations

The preferred production operation computes and writes one registered target per
lifecycle attempt, as defined by DPA-300 and DPA-400.

When outer workflow orchestration must coordinate multiple targets, it MUST:

- resolve each target through the registry;
- compute an explicit dependency graph;
- acquire no nested projection locks from within a lifecycle attempt;
- execute target attempts in deterministic order;
- stop before later targets when an earlier target fails in a way that changes
  shared dependencies;
- record which target attempts are accepted, abandoned or not started;
- avoid representing partial multi-target success as repository-wide
  projection conformance.

Cross-target workflow ordering remains outside renderer authority.

## 16. Failure and recovery

Failure before DPA-300 Write MUST leave the target unchanged.

Failure after Write remains governed by DPA-300 recovery and DPA-500 gate
behavior. DPA-600 adds only that cross-ref evidence and workflow state MUST NOT
represent the attempt as merge-eligible while recovery is unresolved.

If the workflow cannot determine whether a required plan, lock, branch, PR or
integration identity is current, it MUST fail closed for mutation and
integration.

If a local lock is stale but cross-ref state has moved, recovery MUST first
dispose the interrupted local attempt under DPA-300 and then regenerate from the
current validation ref. It MUST NOT reuse the old branch or PR evidence as a
current check.

## 17. Findings and evidence

Concurrency findings MUST be structured and bounded. They MUST include:

- target identity;
- operation kind;
- plan identity when available;
- branch or ref context when available;
- pull-request number, head and base when applicable;
- validation ref when applicable;
- stale or conflicting identity;
- DPA-100 drift class when the finding represents drift;
- non-drift category when the finding represents missing workflow state,
  unavailable comparison, queue conflict or check-head mismatch;
- whether target bytes changed;
- whether acceptance state changed;
- whether integration, merge eligibility or required-check publication was
  blocked;
- recommended recovery: regenerate, revalidate, wait for prior integration,
  abandon, or Maintainer adjudication.

Evidence SHOULD additionally record compared fingerprints, required check names,
workflow operation identity, queue/order decision, lock scope and known
limitations.

Evidence MUST NOT include credentials, private runtime state or broad logs.

## 18. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- exact Workspace lock implementation and stale-lock takeover behavior;
- exact branch guard and remote-head guard behavior;
- exact pull-request head/base APIs and failure modes;
- whether current checks can bind to exact PR head and base;
- whether existing administrative refresh serialization covers registered
  projection targets;
- whether merge queue, required checks or manual merge flows can enforce
  integration-time revalidation;
- whether existing findings can represent concurrency subreasons without a
  parallel taxonomy;
- where acceptance-bearing concurrency evidence is persisted;
- whether disjoint-target independence can be checked deterministically;
- whether existing local workflow commands can regenerate safely from the current
  validation ref;
- how post-merge handoff/status refreshes are ordered with projection checks.

No claim in this document states that the current main repository already
conforms.

## 19. Conformance tests

A conforming implementation MUST test:

1. local mutation uses the existing Workspace lock;
2. local lock does not satisfy branch or PR serialization;
3. reentrant wrapper around exactly one projection refresh;
4. nested projection refresh rejected while holding the lock;
5. stale local lock takeover with interrupted-attempt disposition;
6. stale source fingerprint before lock;
7. stale target fingerprint before lock;
8. stale contract fingerprint before lock;
9. stale renderer semantic identity before lock;
10. stale partition or ownership identity before lock;
11. stale base context before integration;
12. stale gate-set identity before acceptance or integration;
13. stale acceptance-state identity before re-acceptance;
14. under-lock revalidation catching a target change after preflight;
15. branch switch or rebase invalidating a plan;
16. PR head update invalidating prior evidence and checks;
17. PR base update requiring integration-time revalidation;
18. competing PR merged against the same registered target;
19. competing PR merged against a shared declared source;
20. competing PR merged against shared contract, renderer, ownership or gate-set
    dependencies;
21. disjoint-target PRs accepted only after dependency independence is recorded;
22. clean textual merge with stale projection output rejected;
23. required-check result from a different exact head rejected;
24. unavailable branch protection or PR state failing closed for integration;
25. regeneration from the current validation ref after drift;
26. stale generated prose not merged with current target prose;
27. read-only audit concurrent with no mutation or repair;
28. administrative refresh serialized when it writes a registered projection
    target;
29. unresolved post-Write recovery blocking merge eligibility;
30. post-integration refresh bound to the accepted integration ref and current
    dependency identities;
31. evidence failure not fabricating current concurrency state.

## 20. Invalid states

The following are invalid:

1. local Workspace lock represented as cross-PR serialization;
2. projection plan executed on a different branch without full revalidation;
3. acceptance-bearing evidence reused after branch rebase or reset;
4. PR check treated as current for a different head SHA;
5. PR check treated as current for a required newer base without revalidation;
6. clean textual merge treated as proof of projection freshness;
7. stale generated output merged with current target prose;
8. historical prose auto-merged to resolve projection drift;
9. required source, target, contract, renderer, partition or ownership comparison
   omitted;
10. missing branch, PR or queue state interpreted as pass;
11. stale plan allowed to Write;
12. stale plan allowed to update acceptance state;
13. stale plan allowed to publish current required-check evidence;
14. stale plan allowed to merge;
15. competing same-target PRs merged without later-candidate revalidation;
16. shared-source or shared-contract dependency ignored;
17. disjoint-target independence assumed without recorded comparison;
18. workflow orchestration writing target bytes directly;
19. renderer performing lock, workflow or merge decisions;
20. evidence used as the authority that decides freshness or merge eligibility;
21. local stale-lock takeover treated as proof that remote state is current;
22. unresolved `written-unverified` or interrupted state represented as
   merge-eligible;
23. time alone used as a hard concurrency failure;
24. automatic repair of stale target bytes outside the lifecycle;
25. DPA Lab validation represented as main-repository runtime conformance.

## 21. Stable criteria

DPA-600 is `stable` for the accepted Kit-side DP1-DP5 scope when:

1. local locking and cross-ref serialization boundaries are unambiguous;
2. concurrency identity requirements are complete and consistent with DPA-300
   plans and DPA-500 freshness;
3. branch, pull-request and integration stale-plan rules are complete;
4. post-integration refresh ordering and revalidation obligations are complete;
5. competing projection refresh conflicts have deterministic default
   dispositions;
6. regeneration from the current validation ref is the default recovery for
   stale plans;
7. no historical prose auto-merge path remains;
8. workflow serialization uses existing repository authorities rather than a
   parallel system;
9. findings and evidence are bounded and non-authoritative;
10. every requirement is traced to invariants, tests, later implementation,
   evidence and rollback;
11. diagrams are synchronized;
12. repository-specific mechanisms remain exact-ref fenced;
13. primary review, Maintainer adjudication and independent post-adjudication
   verification are complete;
14. applicable concurrency, stale-plan, branch, pull-request, integration,
   regeneration and workflow-serialization evidence is exact-ref recorded in
   the Stable Promotion record.

Future workflow or target expansion requires fresh exact-ref evidence before it
can inherit this stable scope.
