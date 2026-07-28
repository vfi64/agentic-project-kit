# DPA-900 — Future Evolution and Review Economics

Status: review-ready

Status-date: 2026-07-27

Authority: normative DPA specification; review-ready after Package C primary review, Maintainer adjudication and independent post-adjudication verification; not stable, not implementation evidence and not a main-repository conformance claim

## 1. Purpose

This specification defines how the Document Projection Architecture evolves
after the initial DPA-000 through DPA-800 architecture package without turning
every future change into a full-series review.

DPA-900 establishes proportionate review paths, equivalence verification,
mechanical consistency checks, decision records, evidence boundaries and final
closeout criteria. It reduces review cost by shrinking and classifying the
surface under review. It MUST NOT reduce semantic correctness, evidence
discipline, authority clarity, rollback safety, Maintainer visibility or
Maintainer decision rights.

DPA-900 does not execute Probes, mutate the main repository, import Lab
artifacts into the Kit or claim production conformance.

Repository-specific command names, generated-file mechanisms, CI checks, review
automation, report paths, state files and branch-protection behavior remain
`NEEDS_MAIN_REPO_VALIDATION` until validated against an exact main-repository
ref.

## 2. Normative dependencies

DPA-900 depends on:

- DPA-000 for architecture purpose, invariants, no-parallel-system discipline
  and final series success criteria;
- DPA-100 for classification, document status, progress status, evidence,
  authority and trust-state vocabulary;
- DPA-200 for document form, target identity and normative ownership boundaries;
- DPA-300 for lifecycle ordering, immutable planning, Record, recovery and
  lifecycle-owned state semantics;
- DPA-400 for renderer identity, deterministic output and purity boundaries;
- DPA-500 for freshness, findings, gate decisions, acceptance state and staged
  enforcement;
- DPA-600 for branch, pull-request and integration serialization;
- DPA-700 for migration, no-migration, rollback and no-new-history-source
  discipline;
- DPA-800 for DP1 through DP5 sequencing, exact-ref identities, Probe families,
  Assessment and controlled import boundaries;
- DPA-ADR-001, DPA-ADR-002, DPA-ADR-003, DPA-ADR-004, DPA-ADR-005,
  DPA-ADR-006, DPA-ADR-007, DPA-ADR-008, DPA-ADR-009, DPA-ADR-010,
  DPA-ADR-011, DPA-ADR-012, DPA-ADR-013, DPA-ADR-014, DPA-ADR-015,
  DPA-ADR-016, DPA-ADR-017, DPA-ADR-019, DPA-ADR-020 and DPA-ADR-021.

DPA-ADR-018 is a deferred, non-normative proposal and is not a DPA-900
dependency. DPA-900 owns the normative disposition of the independent-context
verification topic for this specification series. DPA-ADR-018 remains historical
input unless separately adjudicated.

## 3. Scope

DPA-900 owns:

1. future DPA change classes;
2. risk-based review-depth selection;
3. high-risk triggers requiring the full governed review path;
4. bounded fast paths for low-risk changes;
5. diff-scoped equivalence verification;
6. independent-context verification triggers and eligibility;
7. machine-checkable consistency controls;
8. generated and command-updated output handling for review economy;
9. decision and adjudication requirements for reduced review paths;
10. review-cost and defect-rate measures;
11. fallback to full review when equivalence or safety cannot be proven;
12. final DPA closeout-readiness criteria.

DPA-900 does not own concrete implementation commands, the main repository's
production review system, CI configuration, release policy, branch protection,
runtime state, Probe execution, Kit import, renderer implementation or adoption
execution.

## 4. Authority boundary

Review economy is governance logic, not runtime authority.

The main repository remains the sole runtime authority. The Lab may define
future review paths and import criteria, but it MUST NOT become a live review
queue, status database, evidence service, command runner or release authority.

Maintainer adjudication remains required for every normative change path that
can alter architecture meaning, implementation authority, mutation safety,
acceptance state, rollback, gate behavior, Probe interpretation, import scope or
stable/adopted status.

Deterministic checks MAY reduce review surface. They MUST NOT replace
Maintainer adjudication, exact-ref evidence, required Probes or independent
verification where those controls are required by risk.

## 5. Change classes

Every future DPA, import, Probe, governance or implementation-planning change
MUST be classified before review path selection.

The change classes are:

1. **normative semantic change** - changes requirement meaning, authority,
   status, invariant interpretation, lifecycle behavior, migration selection,
   rollback consequence, gate behavior or implementation precondition;
2. **bounded normative amendment** - changes a known requirement surface after
   evidence, review or adjudication identifies a specific correction;
3. **semantic-preserving restructure** - moves, splits, deduplicates or rewrites
   text while asserting unchanged normative meaning;
4. **derived-artifact synchronization** - updates traceability, diagrams,
   status surfaces, prompts or indexes to match already-governed normative
   state;
5. **editorial-only change** - spelling, formatting, reference-label or wording
   clarity that cannot change a requirement, status, authority or evidence
   interpretation;
6. **deterministic generated-output update** - output reproduced from an
   accepted generator, source manifest or command contract without manual
   semantic editing;
7. **main-repository implementation change** - code, workflow, gate, generated
   artifact, command, state or release behavior in `vfi64/agentic-project-kit`;
8. **evidence record update** - bounded recording of observations, commands,
   results or review outputs without turning evidence into authority.

A change touching multiple classes MUST follow the highest-risk applicable
class unless a Maintainer adjudication explicitly splits the change into
separate commits or review paths.

## 6. Risk levels

Each change MUST receive one primary risk level:

1. **R0 - mechanical**: deterministic, reproducible and fully checked by an
   accepted gate or generator; no semantic interpretation required;
2. **R1 - editorial**: human-readable wording or formatting with no plausible
   change to requirement meaning, status, authority, evidence scope, review path
   or command behavior;
3. **R2 - derived synchronization**: non-normative artifact alignment with an
   already accepted normative source, where drift can be reviewed directly;
4. **R3 - bounded semantic**: a small normative or governance correction with a
   known source, known affected surface, preserved authority model and no new
   runtime mutation path;
5. **R4 - high-impact semantic**: a change involving authority, invariants,
   accepted statuses, lifecycle writes, renderer execution, gates, workflow
   serialization, migration, rollback, acceptance state, controlled import,
   Probe interpretation, DP2 through DP5 execution or production behavior;
6. **R5 - adoption or strict-enforcement**: a change that enables adoption,
   stable status, strict gates, production mutation, release blocking behavior
   or broad rollout.

Unknown, mixed or disputed risk MUST be treated as the higher plausible risk
until Maintainer adjudication records a narrower classification.

Default minimum risk floors:

| Change class | Minimum risk | Notes |
|---|---|---|
| 1. normative semantic change | R4 | MAY be R5 when adoption, stable status, strict gates, production mutation, release blocking behavior or broad rollout are enabled. |
| 2. bounded normative amendment | R3 | MUST escalate to R4 or R5 when the amended surface touches a high-impact or adoption/strict-enforcement trigger. |
| 3. semantic-preserving restructure | R3 | Requires equivalence verification before any promotion, certification or reduced-path acceptance. MUST escalate when equivalence cannot be bounded or when R4/R5 semantics are touched. |
| 4. derived-artifact synchronization | R2 | MUST escalate when the synchronization introduces or changes normative meaning, status, authority or implementation preconditions. |
| 5. editorial-only change | R1 | MUST escalate when any reviewer cannot prove editorial-only scope from the diff. |
| 6. deterministic generated-output update | R0 | Applies only when reproducibility, source input, generator identity and no manual semantic editing are proven. |
| 7. main-repository implementation change | R4 | MUST escalate to R5 when it enables adoption, strict enforcement, stable status, production mutation, release blocking behavior or broad rollout. |
| 8. evidence record update | R2 | MUST escalate to R3 or higher when the record is used to close findings, authorize status change, support merge eligibility, support adoption or affect implementation authority. |

The minimum floor is not a permission to use the corresponding lower-cost path.
Any high-risk trigger, mixed class or unresolved equivalence question MUST
escalate to the higher applicable risk level.

## 7. Review paths

The allowed review paths are:

1. **fast mechanical path** for R0;
2. **editorial path** for R1;
3. **synchronization path** for R2;
4. **bounded amendment path** for R3;
5. **full governed review path** for R4;
6. **adoption or strict-enforcement path** for R5.

Every path MUST record:

- exact ref or exact diff range;
- change class;
- risk level;
- files in scope;
- normative owner, if any;
- reviewer role requirements;
- deterministic checks required;
- Maintainer decision required or explicit reason it is not required;
- rollback, revert or supersession path;
- known limitations.

No path may certify a change by chat memory, model agreement or author
assertion alone.

## 8. Fast mechanical path

The fast mechanical path MAY be used only when:

- the output is produced by an accepted deterministic generator or command
  contract;
- the source input, generator identity and output target are recorded;
- a deterministic check confirms reproducibility or expected diff shape;
- no manual semantic editing occurred in the generated output;
- no normative status, authority or requirement meaning changes.

Generated or command-updated Kit outputs MUST be changed through their source
authority, generator or command contract. A durable manual patch to such output
is invalid unless Maintainer adjudication explicitly records a temporary repair
and the later source-of-truth correction.

The fast mechanical path may update derived Lab prompts or handoff projections
only when their source relationship is explicit. Manual Lab control surfaces
with no repository generator are not generated-output fast-path artifacts.

## 9. Editorial path

The editorial path MAY be used for R1 changes when all of the following hold:

- no normative keyword is added, removed, weakened or strengthened;
- no status value changes;
- no requirement, invariant, authority, evidence classification, review path,
  Probe obligation, implementation precondition or rollback consequence changes;
- no file is moved to a different normative owner;
- deterministic text integrity and repository gates pass.

If any reviewer cannot prove the change is editorial-only from the diff, the
change MUST escalate to the synchronization path or bounded amendment path.

## 10. Synchronization path

The synchronization path MAY be used for R2 changes when a derived artifact
drifts from an already accepted normative or adjudicated source.

Synchronization MUST:

- name the source artifact and exact ref;
- name the derived artifact;
- state the mismatch;
- update only the derived surface needed to remove the mismatch;
- preserve normative meaning;
- run deterministic gates that can detect map, status, syntax or conflict
  drift.

Synchronization MUST NOT introduce new requirements, new status decisions or new
implementation authority.

## 11. Bounded amendment path

The bounded amendment path applies to R3 changes.

A bounded amendment MUST:

- identify the source finding, Probe discrepancy, review finding, Maintainer
  request or exact-ref evidence that requires the change;
- identify the smallest normative surface that can correct it;
- list affected traceability, diagrams, ADRs, prompts, status surfaces and
  review records;
- include Maintainer adjudication before accepted review findings become
  normative;
- preserve existing authority boundaries unless the change explicitly escalates
  to the full governed review path;
- receive independent post-adjudication verification when the amendment changes
  a review-ready or stable specification's normative body.

Promotion after a bounded amendment MUST remain status-only under DPA-ADR-020.

## 12. Full governed review path

The full governed review path is required for R4 changes and for any lower-risk
change whose semantic equivalence cannot be proven.

The path MUST include:

1. complete draft or amendment package;
2. exact immutable review target;
3. traceability and diagram synchronization;
4. internal pre-review audit;
5. primary architecture review;
6. Maintainer adjudication;
7. bounded correction batch;
8. independent post-adjudication verification when the correction changes
   normative text or closes review findings;
9. status-only promotion only after required verification passes;
10. preserved limitations and `NEEDS_MAIN_REPO_VALIDATION` fences.

The full path MUST be used for new authorities, invariant changes, lifecycle
write behavior, renderer execution semantics, gate behavior, DPA-600
serialization, DPA-700 migration or rollback, DPA-800 DP-stage gates, controlled
import semantics and any production mutation claim.

## 13. Adoption or strict-enforcement path

The adoption or strict-enforcement path is required for R5 changes.

In addition to the full governed review path, R5 requires:

- exact main-repository validation ref;
- local confirmation ref where mutation or execution is involved;
- applicable PROBE-001, PROBE-002, PROBE-003, PROBE-004 and renderer-Probe
  evidence, or explicit Assessment non-applicability for the selected scope;
- Assessment adjudication of every blocking discrepancy;
- implementation baseline and implementation result refs;
- rollback or deactivation evidence;
- staged adoption plan with observe, warn, block-new and strict stages where
  gates are involved;
- Maintainer authorization before production mutation, Kit import, stable status
  or strict enforcement.

R5 MUST NOT use elapsed time, prior review success or Lab gate success as a
substitute for exact-ref implementation evidence.

## 14. Equivalence verification

Equivalence verification is a diff-scoped review that determines whether a
change preserves already-certified normative meaning.

It MUST be used for change class 3, semantic-preserving restructure, before the
candidate change receives promotion, certification or reduced-path acceptance.
It MAY be used for large wording cleanup, projection regeneration or
derived-artifact synchronization when the author claims unchanged meaning.

An equivalence verification MUST:

- identify the certified source ref and candidate ref;
- identify the exact diff range;
- list every load-bearing requirement, status, invariant anchor, authority,
  evidence classification, Probe obligation, review path and rollback
  consequence in scope;
- state whether each load-bearing item is unchanged, strengthened, weakened,
  moved without semantic change, missing or newly introduced;
- identify every genuine semantic difference for Maintainer disposition;
- fail or escalate when the verifier cannot bound the comparison.

The verifier MUST NOT be the context that authored the restructure or rewrite
unless Maintainer adjudication explicitly accepts the residual risk for an R0 or
R1 change.

Equivalence verification does not prove main-repository implementation
conformance.

## 15. Independent-context verification

Independent-context verification addresses authorship-context bias. The relevant
separation is between the context that authored or applied a change and the
context that verifies the committed artifact.

Independent-context verification is required when:

- a review-ready or stable normative body changes after primary review;
- a bounded correction batch closes primary-review findings;
- equivalence verification would authorize promotion after restructuring;
- a change enables DP2 through DP5 mutation, adoption, strict gates, Kit import,
  production conformance or stable status;
- a Maintainer identifies authorship bias or correlated-review risk as material.

A qualifying verifier MUST:

- start from the exact immutable target ref;
- read repository artifacts rather than chat memory;
- disclose prior exposure and authorship;
- for independent-context verification triggered by R4 or R5 work, or by
  closure of primary-review findings, complete and record blind-first evaluation
  before reading prior findings, adjudication summaries or proposed correction
  text;
- run deterministic local gates when available and report unavailable gates;
- report exact findings, limitations and a verdict.

When blind-first evaluation is required, the verification prompt MUST separate
the blind-first evaluation phase from the later finding-closure mapping phase.
Prior findings MAY be read only after the verifier has recorded independent
findings, limitations and initial answers for the blind-first scope.

A different model family or human reviewer MAY reduce correlation risk, but
vendor diversity is not mandatory by itself. A disqualified reviewer MUST return
an independence-blocked outcome rather than partial assurance.

## 16. Mechanical consistency checks

Future DPA work SHOULD convert recurring synchronization requirements into
deterministic checks when the rule is stable and cheaply machine-checkable.

Eligible checks include:

- canonical DPA map and document-header status alignment;
- invariant anchor existence;
- duplicate or competing normative homes;
- status-token consistency across status, roadmap and handoff surfaces;
- exact-ref presence in review prompts and records;
- forbidden live `.agentic/` state in the Lab;
- generated-output source/generator markers where such a contract exists;
- merge-conflict markers and whitespace errors;
- broken local links for required artifacts;
- review-ready promotion commits that change normative bodies.

Mechanical checks MUST report a bounded failure. They MUST NOT claim semantic
correctness unless the semantic property has been encoded as a deterministic
rule.

## 17. Review-economy records

Every reduced-cost path MUST leave enough record for a later reviewer to
understand why the full path was not used.

At minimum, the record MUST include:

- change class and risk level;
- selected review path;
- exact ref or diff range;
- files changed;
- deterministic checks run;
- skipped controls and the reason each was not required;
- Maintainer adjudication when required;
- rollback or revert path;
- limitations.

For R3 through R5 changes, the record MUST also state why a lower-risk path was
insufficient.

## 18. Cost and defect measures

DPA review economy is successful only when cost falls without assurance loss.

The Lab and later main repository SHOULD track:

- number of full-document rereads avoided by accepted equivalence or
  synchronization paths;
- number of deterministic checks covering recurring drift classes;
- number of post-review synchronization defects found before and after the
  check existed;
- review turnaround time by risk level;
- correction commits per package;
- reopened findings caused by stale status, missing refs, generated-output
  confusion or cross-artifact drift;
- instances where a lower-risk path escalated to a full review.

Metrics are governance evidence only. They MUST NOT become release authority or
override a required review, Probe or Maintainer decision.

## 19. Final DPA closeout criteria

The DPA specification series may be considered complete for pre-import Lab
architecture when:

1. DPA-000 through DPA-900 are `review-ready` or better;
2. all open review findings affecting the pre-import architecture are
   adjudicated;
3. traceability, diagrams, status surfaces and handoff surfaces are synchronized;
4. DPA-900 classifies future change paths and fallback rules;
5. controlled import planning identifies which Lab artifacts become main-repo
   documentation, ADRs, implementation requirements, evidence, historical
   records, rejected artifacts or superseded artifacts;
6. Probe manuals for PROBE-001, PROBE-002, PROBE-003, PROBE-004 and renderer
   Probes are prepared enough for exact-ref local execution;
7. no Lab artifact claims Probe success, production implementation, Kit import,
   DPA stable status or main-repository conformance without exact evidence;
8. no generated or command-updated Kit output is scheduled for durable manual
   patching instead of source, generator or command-contract handling;
9. every remaining Mac/main-repository task is expressed as exact-ref
   validation, Probe execution, evidence adjudication, bounded amendment or
   implementation work rather than unresolved architecture design.

Final pre-import Lab closeout does not itself authorize production mutation,
stable promotion, Kit import, release publication or strict enforcement.

## 20. Main-repository validation boundary

The following remain `NEEDS_MAIN_REPO_VALIDATION`:

- concrete main-repository review commands;
- exact generated-output source and command contracts in the Kit;
- exact CI checks and branch-protection behavior;
- exact report and evidence paths;
- exact command-generated handoff package behavior;
- exact import destination paths;
- exact release and strict-gate authorization mechanisms;
- exact implementation of any mechanical consistency check not already present
  in this Lab.

No claim in this document states that the current main repository already
implements DPA-900 review paths.

## 21. Conformance tests

A conforming DPA-900 governance implementation MUST test:

1. R0 mechanical change accepted only with deterministic reproducibility;
2. R1 editorial change rejected when a normative keyword changes;
3. R2 synchronization rejected when no accepted source is named;
4. R3 bounded amendment rejected without source finding or evidence;
5. R4 change forced into the full governed review path;
6. R5 change forced into adoption or strict-enforcement path;
7. mixed-risk change follows the highest applicable risk;
8. unknown risk escalates rather than defaulting to a fast path;
9. generated Kit output cannot be durably hand-patched without source or command
   disposition;
10. manual Lab prompt is not misclassified as generated output without generator
    evidence;
11. equivalence verification fails when a load-bearing requirement is missing;
12. equivalence verification records newly introduced semantic differences;
13. authoring context cannot self-certify high-risk equivalence;
14. independence-blocked verification cannot be recorded as PASS;
15. anchored prompt for R4/R5 or primary-review-finding closure is rejected
    when it requires reading prior findings before blind-first evaluation;
16. promotion commit that changes normative body is rejected;
17. deterministic check failure blocks reduced-path certification;
18. metrics cannot override a required review or Probe;
19. final DPA closeout fails when controlled import planning is missing;
20. final DPA closeout fails when Probe manuals are missing;
21. final DPA closeout fails when main-repository conformance is claimed from
    Lab evidence alone.

## 22. Invalid states

The following are invalid:

1. review cost reduced by skipping a required evidence source;
2. author intent treated as equivalence proof;
3. chat memory treated as verification evidence;
4. a generated or command-updated Kit output durably patched by hand without
   source, generator or command-contract disposition;
5. a manual Lab surface excluded as generated without repository evidence;
6. a normative semantic change classified as editorial-only;
7. a high-risk change accepted through the fast mechanical path;
8. an independence-blocked review recorded as a substantive PASS;
9. a promotion commit changing normative body after verification;
10. a metric used as release, adoption, conformance or stability authority;
11. a deterministic check presented as proof of semantic correctness beyond its
    encoded rule;
12. a lower-risk path selected merely to avoid review effort;
13. controlled import performed before artifact disposition and Maintainer
    authorization;
14. strict enforcement activated without exact-ref evidence and rollback;
15. DPA final closeout recorded while unresolved architecture-design blockers
    remain hidden by status wording.

## 23. Review-ready criteria

DPA-900 may become `review-ready` when:

1. change classes and risk levels are complete and non-overlapping enough for
   reviewer use;
2. every high-risk trigger escalates to the full governed path or the adoption
   and strict-enforcement path;
3. fast paths are bounded to mechanical, editorial or derived synchronization
   changes that preserve assurance;
4. equivalence verification has exact-ref, diff-scope and independence
   requirements;
5. independent-context verification is role-based and proportionate rather than
   vendor-bound;
6. generated and command-updated output handling preserves source/generator or
   command-contract authority;
7. mechanical checks are explicitly scoped and do not overclaim semantic proof;
8. cost and defect measures cannot override required evidence or Maintainer
   decisions;
9. final DPA closeout criteria preserve Probe, import, stable-promotion and
   production-mutation boundaries;
10. every requirement is traced to invariants, tests, later implementation,
    evidence and rollback;
11. diagrams are synchronized;
12. repository-specific mechanisms remain exact-ref fenced;
13. primary review, Maintainer adjudication and any required post-adjudication
    verification are complete.

DPA-900 MUST NOT become `stable` before final pre-import architecture closeout,
controlled import planning, applicable Probe evidence, implementation evidence
and Maintainer adjudication exist at exact refs.
