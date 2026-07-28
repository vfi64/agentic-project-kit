# DPA-500 — Freshness and Gates

Status: review-ready

Status-date: 2026-07-17

Authority: normative DPA specification, review-ready after primary review, Maintainer adjudication and independent post-adjudication verification; stability remains subject to applicable Probe evidence

## 1. Purpose

This specification defines freshness evaluation, structured findings, consumer-trust consequences, gate behavior and staged enforcement for registered document projections.

DPA-500 extends the existing main-repository documentation registry, lifecycle, findings and gate architecture. It does not create a second freshness engine, finding taxonomy, gate runner, evidence store, acceptance database or runtime authority.

Repository-specific finding identifiers, severity mappings, command names, workflow integration points, persistence mechanics and strict-adoption switches remain `NEEDS_MAIN_REPO_VALIDATION` until validated against an exact main-repository ref.

## 2. Normative dependencies

DPA-500 depends on:

- DPA-000 for canonical invariants;
- DPA-100 for authority, classification, consumer trust-state, drift, freshness, fingerprint and gate vocabulary;
- DPA-200 for target identity, document form, partition ownership and target semantics;
- DPA-300 for registry contracts, lifecycle ordering, immutable plans, acceptance state, recovery and evidence boundaries;
- DPA-400 for renderer identity, immutable inputs, semantic versions, deterministic output, purity and failure behavior;
- DPA-ADR-013, DPA-ADR-014, DPA-ADR-016, DPA-ADR-017, DPA-ADR-019, DPA-ADR-020 and DPA-ADR-021.

## 3. Scope

DPA-500 owns:

1. projection freshness dimensions and classification;
2. freshness evaluation inputs;
3. projection-specific finding subreasons mapped to the DPA-100 drift vocabulary;
4. abstract finding semantics;
5. consumer trust-state consequences;
6. gate-decision semantics within the existing DPA-100 gate vocabulary;
7. staged enforcement rules;
8. handling of missing, stale, tampered or unverifiable acceptance state;
9. operation-scoped base-context evaluation;
10. mutation-free gate-set re-acceptance;
11. layered acceptance for registered-region projections;
12. recovery-facing gate behavior;
13. freshness and gate test obligations.

DPA-500 does not own foundational vocabulary, registry serialization, target rendering or writing, lifecycle lock implementation, cross-ref serialization, concrete finding codes or severities, command UX, migration-form selection or production implementation.

## 4. Authority boundary

Freshness evaluation is lifecycle-owned and gate-integrated.

A renderer MUST NOT assign freshness classification, emit authoritative findings, select severity, assign consumer trust state, decide gate pass/warning/failure, repair stale state or accept its own output.

Evidence MAY explain a decision but MUST NOT become the authority that decides freshness or acceptance.

The existing main-repository gate architecture remains the sole production gate authority. DPA-500 defines the projection-specific contract that the existing architecture must later implement.

## 5. Freshness model

Freshness is multidimensional. A projection is `fresh` only when every applicable declared dimension is current and verifiable for the evaluated target identity and requested operation.

The mandatory dimensions are:

1. **contract freshness** — the registered projection and partition contracts match the accepted contract identity and fingerprint;
2. **source freshness** — every declared canonical source matches the accepted ordered source fingerprints;
3. **configuration freshness** — output-affecting contract-declared configuration matches the accepted configuration fingerprint;
4. **renderer freshness** — renderer identifier and semantic version match the accepted identities and interface compatibility remains valid;
5. **target freshness** — for a complete-target projection, current complete-target bytes match the accepted complete-target fingerprint; for a registered-region projection, lifecycle-owned projected payload bytes match the accepted payload fingerprint;
6. **partition and target-semantics freshness** — lifecycle-owned partition bytes, boundaries, ownership declarations, encoding, normalization, line endings and target-semantics versions match the accepted contract and state as applicable;
7. **gate-set freshness** — the acceptance state records the gate-set identity required by the current contract and enforcement policy;
8. **acceptance-state freshness** — the acceptance record is present, parseable, correctly scoped and internally coherent;
9. **base-context freshness** — the base, repository or workflow identity required by the governing plan or requested operation remains current.

Base context is operation-scoped unless the projection contract explicitly declares semantic or acceptance dependence on a base identity. A base-independent post-acceptance audit MUST NOT become `indeterminate` merely because no live mutation plan exists.

Time alone MUST NOT make a projection stale unless time is an explicitly declared semantic source or an accepted policy requires bounded revalidation for a reason independent of output equivalence. Time alone MUST NOT activate strict enforcement.

## 6. Freshness classification and scope

Freshness classification is distinct from consumer trust state, lifecycle attempt outcome, finding severity, gate decision and enforcement stage.

The projection-specific classifications are:

- `fresh` — every applicable mandatory dimension matches and is verifiable;
- `stale` — one or more comparable current dimensions differ from accepted state;
- `invalid` — the contract, target, partition, acceptance state or comparison boundary cannot be interpreted safely;
- `indeterminate` — mandatory current information or evaluation machinery is unavailable and neither `fresh`, `stale` nor `invalid` can be established safely.

These classifications do not extend the closed DPA-100 consumer trust-state vocabulary.

A classification applies to the projection context evaluated by the current operation. A failed renderer attempt may be `invalid` and `abandoned` without reclassifying previously accepted bytes whose own freshness continues to derive from the dimensions in §5.

The same evaluated tree, lifecycle state, operation context and declared inputs MUST produce the same classification and finding set.

## 7. Evaluation inputs

A freshness evaluation MUST use only lifecycle-resolved and Workspace-resolved inputs.

At minimum it evaluates:

- registered target identity;
- projection-contract identity and fingerprint;
- partition-contract identity and fingerprint when applicable;
- current declared-source fingerprints;
- current configuration fingerprint;
- renderer identifier, interface version and semantic version;
- current payload, partition and complete-target fingerprints as applicable;
- preserved-region fingerprint when required as a plan, write or verification guard;
- ownership fingerprint;
- target-semantics version;
- acceptance-state record;
- current required gate-set identity;
- base or ref context required by the governing plan, accepted contract or requested operation.

Missing mandatory input MUST classify the evaluation as `indeterminate` or `invalid` according to the failure type and MUST produce an explicit finding. It MUST NOT be interpreted as fresh or as permission to infer prior state.

## 8. Acceptance state

Acceptance state is lifecycle state, not evidence.

A valid acceptance-state record MUST be scoped to exactly one registered target identity and MUST contain sufficient identities and fingerprints to reproduce every applicable comparison required by DPA-300 through DPA-500.

The record MUST include, directly or through a versioned schema:

- target identity and acceptance scope;
- projection-contract identity and fingerprint;
- partition-contract identity and fingerprint when applicable;
- renderer identifier, interface version and semantic version;
- ordered source fingerprints;
- configuration fingerprint;
- accepted payload fingerprint;
- accepted complete-target fingerprint;
- accepted partition fingerprint when applicable;
- accepted preserved-region fingerprint when applicable as verification or recovery state;
- ownership fingerprint;
- target-semantics version;
- gate-set identity and accepted gate result;
- accepted lifecycle outcome;
- accepted base identity only when the contract declares base dependence;
- acceptance timestamp as evidence metadata only;
- schema version.

For registered-region projections, complete-target and preserved-region fingerprints remain required plan, write, verification and recovery guards. They are not by themselves post-acceptance projection-freshness comparators after a proven governed change by the declared non-lifecycle owner.

An acceptance-state record is malformed or unusable when it lacks required fields, uses an unknown schema version, names another target, cannot be parsed, contradicts the active target contract or contains internally inconsistent fingerprints.

Malformed or unusable acceptance state MUST NOT be repaired silently from current target bytes or evidence.

## 9. Consumer trust-state consequences

DPA-500 applies, and does not extend, the DPA-100 consumer trust-state vocabulary:

- `computed` remains bytes produced without an immutable mutation plan;
- `plan-captured` remains bytes owned by an immutable lifecycle plan and its guards;
- `written-unverified` remains written bytes whose required verification, evidence and gates are incomplete;
- `accepted` remains bytes accepted by the complete required gate set with acceptance state recorded;
- `abandoned` remains a refresh instance ended by rejection, failure, invalidation or interruption and cannot later become accepted.

A freshness classification of `stale`, `invalid` or `indeterminate` does not create a new trust state. It produces findings and gate consequences while preserving recorded state unless the lifecycle contract requires a transition for the active attempt.

Only complete post-Write verification, required gate `pass`, successful acceptance-state persistence and lifecycle completion may produce `accepted`, except that §15.6 permits lifecycle-owned re-acceptance of unchanged already-accepted bytes after gate-set-only change.

No state may be promoted to `accepted` by suppression, evidence presence, elapsed time, successful rendering alone or a previously green workflow run.

## 10. Drift vocabulary and finding subreasons

DPA-500 MUST use the closed DPA-100 drift classes:

1. `base drift`;
2. `source drift`;
3. `target drift`;
4. `contract drift`;
5. `renderer drift`;
6. `partition drift`;
7. `ownership drift`.

Projection-specific findings MAY refine those classes with stable subreasons:

- projection-contract or output-affecting configuration change under `contract drift`;
- partition-contract or partition-owned target-semantics change under `partition drift`;
- declared-source fingerprint change under `source drift`;
- renderer identifier, interface-version or semantic-version change under `renderer drift`;
- complete-target mismatch for complete-target projections or lifecycle-owned payload mismatch for region projections under `target drift`;
- lifecycle-owned partition-byte or boundary mismatch under `partition drift`;
- declared byte-owner mapping change under `ownership drift`;
- required repository base or ref mismatch under `base drift`.

A governed change to bytes owned by a declared non-lifecycle owner, consistent with the active partition and ownership contracts, is not projection drift. It MAY produce bounded informational evidence that the earlier complete-target fingerprint was superseded by authorized owned-region evolution.

An out-of-band or unexplained change to lifecycle-owned projected payload bytes is `target drift`. A change to lifecycle-owned partition bytes or boundaries is `partition drift`. Ambiguous ownership or inability to prove the responsible owner is a non-drift contract/interpretation failure and MUST fail closed.

The following are finding causes or lifecycle failures, not new drift classes:

- missing, malformed, tampered or scope-mismatched acceptance state;
- gate-set mismatch;
- renderer nondeterminism;
- renderer side effect or prohibited capability use;
- renderer operational abort;
- bounded renderer failure diagnostic;
- post-Write verification failure;
- acceptance-state persistence failure;
- evidence recording failure;
- unavailable mandatory evaluation machinery.

Concrete identifiers and mapping to existing main-repository findings remain `NEEDS_MAIN_REPO_VALIDATION`.

Independent dimensions and subreasons MUST remain separately visible. A generic stale message MUST NOT erase which comparisons or evaluations failed.

## 11. Finding contract

Each projection freshness finding MUST be structured and bounded. It MUST include:

- DPA-100 drift class when the finding represents drift, otherwise an explicit non-drift category;
- projection-specific subreason;
- target identity;
- lifecycle phase or operation;
- freshness classification;
- expected and observed identity or fingerprint when safe and useful;
- whether target mutation occurred;
- current consumer trust state;
- applicable contract or gate-set identity;
- remediation category;
- bounded evidence reference when available.

Findings MUST NOT include secrets, unbounded file content or fabricated expected values.

Multiple independent failures MUST remain separately reportable even when one gate decision blocks the operation.

Severity and user-facing wording are implementation mappings owned by the existing main-repository finding system and remain subject to exact-ref validation.

## 12. Gate decisions

DPA-500 uses the DPA-100 gate vocabulary:

- `pass` — every required check for the requested operation passed;
- `warning` — only explicitly non-blocking findings exist under the active staged policy;
- `failure` — the requested operation MUST NOT proceed, integrate or become accepted.

Evaluation-machinery failure or unavailable mandatory input MUST yield `failure` for mutation, acceptance, integration and strict validation. The finding MUST preserve whether the underlying classification was `indeterminate` or `invalid`.

A `warning` decision MUST NOT authorize acceptance when any mandatory acceptance check failed.

Gate decision, freshness classification and consumer trust state are related but distinct. A read-only audit may return `failure` while preserving prior target bytes and recorded lifecycle state.

## 13. Mandatory failure conditions

The following MUST produce gate `failure` for mutation, acceptance and integration regardless of staged rollout mode:

- malformed or ambiguous target or partition contract;
- missing required declared source;
- unknown renderer identifier;
- renderer interface incompatibility;
- renderer semantic-version mismatch against an immutable execution plan;
- stale plan after preflight or under-lock revalidation;
- partition invalidity;
- target identity mismatch;
- ambiguous or unverifiable byte ownership;
- renderer nondeterminism during required verification;
- renderer side effect or prohibited capability use;
- operational abort represented as successful output;
- truncated or invalid output;
- post-Write verification failure;
- acceptance-state write failure after target Write;
- evidence or lifecycle state represented as canonical source without accepted authority;
- unavailable mandatory evaluation machinery.

A staged policy MAY control whether pre-existing noncompliance blocks unrelated read-only commands, but it MUST NOT weaken new mutation or acceptance safety.

## 14. Staged enforcement

Adoption MUST be staged through the existing gate and lifecycle architecture:

1. **observe** — emit structured findings and evidence without changing mutation behavior not already protected by existing safety rules;
2. **warn** — surface projection-specific noncompliance prominently while preserving bounded compatibility;
3. **block-new** — prevent creation or acceptance of new nonconforming projection states while allowing explicitly governed legacy states to remain readable;
4. **strict** — fail every in-scope nonconforming operation under the active gate policy.

The stage token `warn` MUST NOT be used as the gate-decision token `warning`.

Stage transitions MUST be explicit, reviewable, reversible and controlled by existing configuration or Direction authority. They MUST NOT be activated by elapsed time alone.

Unknown findings MUST fail closed when they affect mutation safety, contract interpretation, target identity, byte ownership or acceptance. Treatment of unrelated unknown findings remains a main-repository policy decision.

No lab statement activates production strict mode.

## 15. Freshness checks by operation

### 15.1 Read-only audit

A read-only audit MUST evaluate all applicable dimensions and return structured findings without mutation. Gate `pass` in a read-only audit does not create or update acceptance state.

### 15.2 Dry-run plan

Dry-run MUST resolve current contract, sources, renderer identities, target state, ownership and required gates and MUST produce a plan fingerprint-bound to those inputs.

Dry-run success does not authorize later execution after drift.

### 15.3 Mutation execution

Before Write, execution MUST revalidate every plan-bound identity and fingerprint under the lifecycle lock. Any mismatch or mandatory evaluation failure MUST abandon the attempt before Write.

### 15.4 Post-Write verification

After Write, the lifecycle MUST verify target bytes, payload, preserved regions, partition preservation, boundaries, ownership, target semantics, renderer-output equivalence where required and every mandatory gate.

Only complete success permits acceptance-state recording and transition to `accepted`.

### 15.5 Integration or protected workflow

Integration MUST reject evidence or output produced from a mismatched or unverifiable base, source, lifecycle-owned target bytes, contract, renderer, partition, ownership, gate-set or acceptance-state context. DPA-600 owns cross-ref serialization mechanics.

### 15.6 Gate-set re-evaluation and re-acceptance without target mutation

The lifecycle MAY re-evaluate and update acceptance after a gate-set-only change without rendering or writing the target.

This operation is valid only when:

- the target already has a valid accepted state;
- every applicable dimension except gate-set freshness is `fresh`;
- current lifecycle-owned target bytes, partition bytes, ownership and target semantics match accepted state and contract;
- any required base context for the operation is current;
- no contract, source, configuration, renderer, target, partition, ownership or acceptance-state mismatch exists.

The operation MUST run the complete current required gate set against the existing accepted bytes. It MUST NOT invoke a renderer or write target bytes.

On gate `pass`, the lifecycle MAY update only lifecycle-owned acceptance state and bounded evidence with the new gate-set identity and result. This state write MUST use the existing Workspace resolution, lifecycle writer, lock policy and crash-safe persistence contract.

On gate `warning` or `failure`, the lifecycle MUST leave target bytes and the prior acceptance record unchanged and emit structured findings.

This is a re-acceptance operation, not a second acceptance authority or a shortcut around mandatory checks.

## 16. Renderer-related findings

DPA-400 failure classes map into DPA-500 as follows:

- unknown or changed renderer identifier: `renderer drift` where comparable, otherwise non-drift contract-resolution failure; gate `failure` before rendering;
- incompatible interface version: `renderer drift`; gate `failure` before rendering;
- changed semantic version: `renderer drift`, freshness `stale`, stale plans invalidated;
- changed implementation evidence without semantic change: evidence update only unless Probe or policy identifies an unversioned semantic change;
- nondeterministic output: active attempt freshness `invalid`, attempt `abandoned`, gate `failure`;
- side effect or capability violation: active attempt freshness `invalid`, attempt `abandoned`, gate `failure`;
- deterministic semantic-bound violation: renderer failure, attempt `abandoned`, no acceptance;
- operational safety abort: attempt `abandoned`, structured non-drift finding, no semantic output and no acceptance;
- bounded failure diagnostic: lifecycle-translated finding only, never acceptance authority.

A raw repository commit change MUST NOT by itself create renderer semantic drift when declared renderer semantic version and behavior contract remain unchanged. Implementation identity remains evidence-only.

## 17. Target, ownership and partition handling

For complete-target projections, target freshness compares the complete-target fingerprint.

For registered-region projections, post-acceptance projection freshness MUST independently evaluate:

- lifecycle-owned projected payload fingerprint;
- lifecycle-owned partition fingerprint and boundary validity;
- ownership fingerprint;
- target-semantics compatibility.

Preserved-region and complete-target fingerprints remain mandatory for plan capture, under-lock revalidation, atomic reconstruction, post-Write verification and interrupted-operation recovery.

A governed edit to a non-lifecycle-owned region, performed by its declared owner and consistent with the active partition contract, does not create projection `target drift`, does not make the lifecycle-owned payload stale and does not require regeneration or gate-set re-acceptance.

An unexplained edit to lifecycle-owned payload bytes is `target drift`. An edit to lifecycle-owned partition bytes or boundaries is `partition drift`. A changed owner mapping is `ownership drift`. An ambiguous edit whose responsible owner cannot be proven MUST fail closed.

Manual or historical regions MUST NOT be regenerated merely to clear projection findings.

## 18. Recovery and interrupted operations

A target left `written-unverified` after interruption MUST NOT be treated as accepted.

Recovery MUST inspect current target bytes, acceptance state, interrupted-attempt state, plan identity where available, ownership, applicable contract and gate-set identities.

Recovery MAY verify and complete recording only when exact written bytes and all required identities can be proven to match the governed plan and current contract. Otherwise it MUST preserve evidence, report findings and require regeneration or Maintainer-governed remediation.

Recovery MUST NOT reconstruct acceptance state from target bytes alone.

A failed re-acceptance state write MUST leave the prior accepted record intact or produce an explicit recoverable state according to the validated persistence contract. It MUST NOT fabricate the new gate-set identity.

## 19. Evidence behavior

Gate evidence is non-authoritative and bounded.

Evidence MUST record identity-critical fields:

- exact evaluated ref or tree identity;
- target identity and evaluated operation;
- contract, renderer and gate-set identities;
- freshness classification;
- DPA-100 drift classes and finding subreasons;
- gate decision and enforcement stage;
- mutation, verification or re-acceptance phases reached;
- prior and resulting consumer trust states;
- acceptance-state update result.

Evidence SHOULD additionally record evaluated dimensions, contextual fingerprints, limitations, unavailable checks, command entry point, lock scope, timing and workflow context.

Evidence failure after Write or re-acceptance is a lifecycle failure. It MUST NOT erase the distinction between verified target bytes and recorded acceptance state and MUST NOT fabricate success.

Exact evidence ordering relative to acceptance-state persistence remains `NEEDS_MAIN_REPO_VALIDATION` and MUST preserve crash-safe semantics.

## 20. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- concrete mapping to existing finding identifiers and severities;
- current gate-set representation and configuration authority;
- exact acceptance-state schema and Workspace path;
- conditional base-identity serialization;
- re-acceptance command and locking integration;
- authorized-owner provenance representation;
- strict-adoption switches and defaults;
- command-specific gate integration;
- unknown-finding behavior outside mutation safety;
- evidence/state persistence ordering;
- CI job and required-check placement;
- compatibility behavior for existing registered non-projection documents;
- performance bounds for repository-wide freshness evaluation.

No claim in this document states that the current main repository already conforms.

## 21. Conformance tests

A conforming implementation MUST test:

1. fresh accepted complete-target projection;
2. fresh accepted registered-region projection;
3. missing acceptance state producing `indeterminate` or `invalid` and gate `failure`;
4. malformed acceptance state;
5. target-scope mismatch in acceptance state;
6. contract drift;
7. source drift;
8. configuration change mapping deterministically to `contract drift`;
9. renderer identifier drift;
10. renderer interface incompatibility;
11. renderer semantic-version drift;
12. implementation-evidence-only change without semantic drift;
13. complete-target byte drift;
14. registered-region lifecycle-owned payload drift;
15. authorized non-lifecycle-owner region edit without projection drift or staleness;
16. out-of-band non-owner edit failing closed;
17. partition drift;
18. target-semantics-related contract or partition drift;
19. gate-set mismatch as a non-drift finding cause;
20. post-acceptance base-independent audit without a live plan;
21. contract-declared base dependence using persisted accepted base identity;
22. stale plan before lock;
23. stale plan after lock revalidation;
24. nondeterministic renderer output without reclassifying prior accepted bytes;
25. renderer side-effect detection;
26. semantic resource-bound failure;
27. operational abort without accepted output;
28. bounded failure-diagnostic translation;
29. post-Write verification failure;
30. acceptance-state recording failure;
31. evidence recording failure;
32. interrupted `written-unverified` recovery;
33. gate-set re-acceptance pass without render or target write;
34. gate-set re-acceptance warning/failure preserving prior acceptance state;
35. observe, warn, block-new and strict enforcement stages;
36. pass, warning and failure gate decisions;
37. no time-only staleness or strict activation;
38. unavailable mandatory input failing closed;
39. read-only audit producing findings without mutation or acceptance-state update;
40. separation of freshness classification, drift class, trust state, gate decision and enforcement stage.

Tests MUST prove that successful rendering alone cannot produce `accepted` and that re-acceptance cannot change target bytes.

## 22. Invalid states

The following are invalid:

1. freshness inferred from target existence alone;
2. missing acceptance state treated as fresh;
3. evidence treated as acceptance state;
4. target bytes used to reconstruct authority silently;
5. independent drift dimensions collapsed into an unstructured result;
6. finding causes represented as new DPA-100 drift classes;
7. freshness classifications represented as consumer trust states;
8. enforcement stages represented as gate decisions;
9. stale plan executed after a bound input changed;
10. warning policy allowing mandatory acceptance failure to pass;
11. operational abort represented as renderer success;
12. nondeterministic or side-effecting output accepted;
13. interface incompatibility or semantic-version drift ignored;
14. implementation commit SHA used as automatic semantic version;
15. partition drift repaired by renderer output;
16. manual or historical bytes regenerated to clear projection findings;
17. authorized manual-region evolution classified automatically as projection target drift;
18. unexplained lifecycle-owned byte changes treated as authorized owner evolution;
19. `written-unverified` represented as accepted;
20. acceptance-state recording failure hidden;
21. unavailable mandatory input interpreted as pass;
22. strict mode activated by time alone;
23. base-independent evaluation failing solely because no accepted plan remains;
24. gate-set mismatch requiring target rewrite when all other dimensions are fresh;
25. re-acceptance invoking a renderer or writing target bytes;
26. a lab gate represented as main-repository runtime conformance.

## 23. Review-ready criteria

DPA-500 may become `review-ready` when:

1. freshness dimensions and classifications are complete and consistent with DPA-100 through DPA-400 and ADR-021;
2. DPA-100 drift classes and DPA-500 finding subreasons are cleanly separated;
3. operation-scoped base evaluation is implementable;
4. mutation-free gate-set re-acceptance is complete and crash-safe at the contract level;
5. layered acceptance distinguishes authorized non-lifecycle-owner evolution from out-of-band lifecycle-byte changes;
6. finding, consumer trust-state and gate semantics are unambiguous;
7. staged enforcement preserves fail-closed mutation safety;
8. acceptance-state and recovery behavior are complete;
9. every requirement is traced to invariants, tests, later implementation, evidence and rollback;
10. diagrams are synchronized;
11. repository-specific mappings remain exact-ref fenced;
12. primary review, Maintainer adjudication and independent post-adjudication verification are complete.

DPA-500 MUST NOT become `stable` before applicable freshness, finding, gate, recovery, re-acceptance, layered-acceptance and strict-adoption Probes have evidence at an exact main-repository validation ref.
