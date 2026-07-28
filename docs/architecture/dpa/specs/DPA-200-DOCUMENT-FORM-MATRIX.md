# DPA-200 — Document-Form Decision Matrix

Status: review-ready
Status-date: 2026-07-15
Owner: `specs/dpa/DPA-200-DOCUMENT-MODEL.md`
Superseded-by: n/a

## 1. Purpose and authority

This matrix is a normative companion to DPA-200. DPA-200 owns the document model and invalid-state catalog. This matrix operationalizes but MUST NOT redefine them.

Concrete schemas, marker conventions, readers, writers and lifecycle behavior remain `NEEDS_MAIN_REPO_VALIDATION`.

## 2. Decision symbols

- `PERMITTED`
- `CONDITIONAL`
- `EXCEPTIONAL / CONDITIONAL`
- `PROHIBITED`
- `NOT_APPLICABLE`

A permitted entry is not a production-form selection. DP1 evidence remains mandatory.

## 3. Unique primary form matrix

| Primary form | Identity shape | Region shape | Non-projected content | Required partition | Selection status |
|---|---|---|---|---|---|
| Manual document | no projection target | existing manual structure | manual/historical under existing behavior | existing manual structure | PERMITTED |
| Full projection | one complete registered document target | no independently maintained region | none inside target | full-target ownership domain | CONDITIONAL |
| Split projection | two or more independently registered target identities | targets are separate identities | history/explanation outside projected target | per-target contracts | CONDITIONAL |
| Hybrid document | one registered document | one or more projected regions plus one or more non-projected regions | manual and/or historical regions | one document-level partition contract | EXCEPTIONAL / CONDITIONAL |
| Managed-head projection | primary form: hybrid; subtype: managed-head | exactly one leading projected region plus one following historical region | historical tail | one lifecycle-owned partition contract | EXCEPTIONAL / CONDITIONAL |

A single document with projected and non-projected regions is always hybrid, never split. Managed-head is a subtype and not a second primary classification.

## 4. Form-selection preconditions

### Manual

- no projection contract;
- existing behavior unchanged;
- malformed optional metadata fails loud.

### Full projection

- every byte reproducible from declared canonical sources and contract-declared configuration;
- no independently maintained prose;
- target identity and target semantics complete;
- readers, writers, gates and rollback known.

### Split projection

- two or more independently registered target identities;
- projected current representation and non-canonical history/explanation are separate targets;
- each target has one owner and explicit consumer role;
- rollback preserves all identities.

### Hybrid

- one document-level partition contract;
- all payload and partition bytes owned exactly once;
- projected, manual and historical regions non-overlapping;
- every projected region independently registered;
- consumers identify current authoritative representation;
- partition, lifecycle, gate, serialization and rollback obligations defined.

### Managed-head subtype

- exactly one leading projected region and one following historical region;
- lifecycle owns projected payload and partition bytes;
- explicit historical writer and edit policy;
- append cannot alter partition or projected bytes;
- stale-plan and competing-PR guards required;
- no automatic historical merge;
- rollback inputs recoverable.

## 5. Region-combination matrix

| Projected payload | Manual payload | Historical payload | Partition ownership | Result |
|---|---|---|---|---|
| absent | complete document | optional under manual contract | existing manual structure | PERMITTED manual |
| complete document | absent | absent | full-target lifecycle ownership | CONDITIONAL full projection |
| separate registered target | absent | separate registered target | independent target contracts | CONDITIONAL split projection |
| one or more regions | one or more regions | optional | lifecycle-owned partition contract | EXCEPTIONAL / CONDITIONAL hybrid |
| one leading region | absent | one following region | lifecycle-owned partition contract | EXCEPTIONAL / CONDITIONAL managed-head hybrid subtype |
| overlapping payload regions | any | any | ambiguous | PROHIBITED |
| any unowned byte | any | any | incomplete | PROHIBITED |
| renderer emits boundary bytes | any | any | renderer/lifecycle conflict | PROHIBITED |
| manual or historical writer changes boundaries | any | any | out-of-band partition mutation | PROHIBITED |

## 6. Authority and write-owner matrix

| Class | Authority role | Renderer input | Permitted writer | Prohibited behavior |
|---|---|---|---|---|
| Canonical source | owns domain facts | yes when declared | existing authoritative mechanism | renderer mutation or circular target authority |
| Contract configuration | representation input | yes when declared/versioned | governed configuration owner | hidden or unversioned input |
| Projected payload | bounded accepted representation | no unless independently canonical | existing lifecycle only | renderer, workflow, evidence or ad hoc manual write |
| Partition bytes | structural ownership only | no | existing lifecycle only | renderer/manual/history mutation |
| Manual payload | declared human-maintained content | no by default | governed manual editor | lifecycle projection write without contract |
| Historical payload | non-canonical history by default | no | governed historical writer | automatic merge or semantic renderer input |
| Evidence | supports inspection | no | governed evidence producer | runtime input or target ownership |

## 7. Consumer trust-state transition matrix

| From | To | Permitted by | Required condition | Consumer representation |
|---|---|---|---|---|
| none | `computed` | renderer | declared inputs resolved; no mutation | not accepted |
| `computed` | `plan-captured` | lifecycle planner | contract and expected output validated for planning | not accepted |
| `plan-captured` | `written-unverified` | lifecycle writer | explicit authorization, lock and stale-plan revalidation | not accepted |
| `written-unverified` | `accepted` | lifecycle plus gates | post-write reproducibility and required checks pass | accepted for recorded scope |
| any non-accepted state | `abandoned` | lifecycle/workflow | failure, cancellation or supersession | never accepted |
| `abandoned` | `computed` | new refresh attempt | authoritative inputs resolved again | new attempt, not accepted |
| `accepted` | `computed` | new refresh attempt | changed source, target, base or contract context | prior acceptance record unchanged unless DPA-500 explicitly invalidates it |

No renderer, manual editor or workflow coordinator may declare `accepted`.

## 8. Invalid-state mapping

The following matrix checks derive from DPA-200 §12:

1. missing/ambiguous authority;
2. ambiguous target identity;
3. overlapping regions;
4. unowned bytes;
5. duplicate ownership;
6. malformed or shared-control boundaries;
7. renderer partition output;
8. manual/history partition mutation;
9. undeclared semantic input;
10. evidence/history as runtime authority;
11. premature acceptance;
12. automatic history merge;
13. unavailable rollback source;
14. silent malformed-contract fallback;
15. multi-target renderer invocation;
16. form selection without DP1 evidence;
17. parallel subsystem requirement.

## 9. Delegated enforcement

| Obligation | Owner |
|---|---|
| Registry, partition and contract validation | DPA-300 |
| Lifecycle planning, locking, writing and direct-write detection | DPA-300 |
| Renderer payload-only and one-target behavior | DPA-400 |
| Trust gates, partition drift and acceptance invalidation | DPA-500 |
| Cross-ref serialization | DPA-600 |
| Migration, history and rollback | DPA-700 |
| DP1 Discovery, Probe, Assessment and form decision | DPA-800 |

## 10. DP1 evidence checklist

Before form selection DP1 records:

- exact validation ref;
- registry and target identity;
- canonical authority for every rendered fact;
- configuration and fingerprint domain;
- all readers, writers and order assumptions;
- partition representation and malformed-boundary behavior;
- history classification;
- trust and gate placement;
- concurrency requirements;
- rollback source and demonstrated recoverability;
- reason lower-risk forms were accepted or rejected.

Incomplete or contradictory evidence requires `no migration`.

Discovery under ADR-015 inventories facts only. Probe and Assessment determine compatibility and form outcome.

## 11. Traceability

This matrix operationalizes DPA-INV-001 through DPA-INV-005, DPA-INV-008 through DPA-INV-012, DPA-INV-014, DPA-INV-015 and DPA-INV-017, plus DPA-ADR-013 through DPA-ADR-015.

Detailed mappings are in `traceability/DPA-200_TRACEABILITY.md`.
