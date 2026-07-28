# DPA-300 Traceability

Status: draft

Status-date: 2026-07-15

## 1. Requirement matrix

| ID | Requirement | Invariants / decisions | Discovery evidence | Later owner | Planned tests / probes | Gate obligation | Evidence obligation | Rollback consequence |
|---|---|---|---|---|---|---|---|---|
| RL-001 | Projection and partition contracts extend the existing registry only. | DPA-INV-006, DPA-INV-011, DPA-INV-012; ADR-001, ADR-005, ADR-017 | DISC-001 | DPA-300 | PROBE-001; existing-entry regression; unknown-field negatives | malformed or unknown metadata blocks use | exact parser/validator output | remove optional extension and retain manual entry |
| RL-002 | Manual entries remain valid without projection contracts. | ADR-001; DPA-200 | DISC-001 | DPA-300 | full registry regression | no new failure for projection-absent entries | parser and count regression | revert extension without document rewrite |
| RL-003 | Registry metadata is declarative and renderer resolution static. | DPA-INV-006, DPA-INV-007; ADR-005 | DISC-001 | DPA-300 / DPA-400 | executable-field and unknown-renderer negatives | unknown renderer blocks plan | resolved identifier and contract fingerprint | restore prior registry version |
| RL-004 | Validation is side-effect free and precedes rendering. | DPA-INV-004, DPA-INV-015 | DISC-001, DISC-006 | DPA-300 | validation mutation negatives | validation failure blocks Render | validation record | target unchanged |
| RL-005 | Refresh follows Recover→Resolve→Inspect→Validate→Render→Plan→Preflight→Lock→Revalidate→Write→Verify→Record→Release. | DPA-INV-002–005, DPA-INV-008, DPA-INV-015; ADR-003, ADR-016 | DISC-006, DISC-008 | DPA-300 | phase-order and bypass tests | bypass blocks mutation | lifecycle transcript | pre-Write failure no-op; later failure governed recovery |
| RL-006 | Planning is dry-run and execution bound to an exact plan. | DPA-INV-015 | DISC-006 | DPA-300 | no-execute default; wrong-plan rejection | unbound execution blocks | immutable plan | no target change |
| RL-007 | Plans capture all base, source, contract, renderer, target, payload, partition, preserved-region and complete-output guards. | ADR-004, ADR-006, ADR-013, ADR-016 | DISC-001, DISC-008 | DPA-300 | field-omission and fingerprint-domain tests | incomplete plan blocks | complete plan payload | regenerate plan |
| RL-008 | Every captured drift invalidates the plan; no stale prose merge occurs. | DPA-INV-005, DPA-INV-014; ADR-004, ADR-006, ADR-007 | DISC-008 | DPA-300 / DPA-600 | all seven drift-class tests | stale plan blocks Write | compared fingerprints and findings | regenerate; never merge target prose |
| RL-009 | Every projection mutation uses the existing Workspace lock without nested projection mutation. | DPA-INV-004; ADR-003, ADR-006 | DISC-008 | DPA-300 | busy, stale-lock, outer-reentrancy and nested-refresh negatives | lock/reentrancy violation blocks | lock and owner transcript | target unchanged |
| RL-010 | Lifecycle is sole writer of projected, partition and acceptance-state bytes. | DPA-INV-002–004, DPA-INV-016; ADR-003, ADR-013, ADR-016 | DISC-003, DISC-006, DISC-007 | DPA-300 | call-graph and side-effect negatives | direct write finding | writer and state identity | restore or regenerate |
| RL-011 | Region refresh reconstructs and atomically replaces the complete parent. | DPA-INV-014; ADR-013, ADR-017 | DISC-003, DISC-006 | DPA-300 | old-or-new crash tests | inability to prove atomicity blocks | pre/post complete-file fingerprints | restore prior complete target |
| RL-012 | Non-projected bytes remain byte-identical. | DPA-INV-014; ADR-007, ADR-013 | DISC-002, DISC-003, DISC-010 | DPA-300 / DPA-700 | preservation and concurrent-edit negatives | changed preserved bytes invalidate plan | preserved-region fingerprint | restore; no historical merge |
| RL-013 | Successful Write enters `written-unverified`; Verify precedes acceptance. | DPA-INV-004; ADR-014 | DISC-005, DISC-006, DISC-009 | DPA-300 / DPA-500 | write/verify transition tests | Verify failure blocks acceptance | write and verification record | abandon or recover |
| RL-014 | Only DPA-500 may assign `accepted`. | ADR-014 | DISC-005, DISC-009 | DPA-500 | privilege-boundary negatives | lifecycle cannot accept | trust transition evidence | abandon instance |
| RL-015 | Acceptance state is lifecycle state, not evidence, and classifies drift independently. | DPA-INV-010, DPA-INV-016; ADR-004, ADR-016 | DISC-003, DISC-005, DISC-007, DISC-009 | DPA-300 / DPA-500 | accepted-state loss/tamper; source-only, target-only and combined drift | missing/invalid state blocks strict acceptance | state-update result plus non-authoritative evidence | regenerate or restore; evidence deletion does not change state |
| RL-016 | Interrupted refreshes are detected and disposed before a new mutation. | DPA-INV-004; ADR-006, ADR-014, ADR-016 | DISC-006, DISC-008 | DPA-300 / DPA-500 / DPA-700 | crash before/after Write; stale-lock takeover; recovered-plan validity | unresolved interruption blocks new mutation | takeover and recovery disposition | reverify valid plan or regenerate |
| RL-017 | Parent registry entry owns one complete partition contract. | DPA-INV-004, DPA-INV-008; ADR-013, ADR-017 | DISC-001 | DPA-300 / DPA-400 | dangling, duplicate, overlap and unexplained-byte negatives; PROBE-001 | invalid partition blocks Render | effective partition fingerprint | restore prior registry contract |
| RL-018 | Evidence is bounded and never runtime authority. | DPA-INV-010; ADR-002, ADR-011 | DISC-005, DISC-006 | DPA-300 | evidence-input prohibition | evidence cannot satisfy source or acceptance state | mandatory mutation evidence | evidence deletion does not alter semantics |
| RL-019 | Existing writers are adapted rather than supplemented by a parallel DPA command. | DPA-INV-011, DPA-INV-012; ADR-001 | DISC-003, DISC-003b, DISC-004 | DPA-300 / DPA-800 | PROBE-002 writer-inventory and command-path tests | unadapted direct writer blocks adoption | command-to-lifecycle trace | revert adapter while preserving governed entry point |
| RL-020 | An observed `admin-refresh-pr` writer must replace rather than append if the candidate is later approved. | DPA-INV-014; ADR-007, ADR-013 | DISC-003, DISC-003b | DPA-300–700 | PROBE-002 | append accumulation fails conformance | before/after target and transcript | restore prior target; no form preselection |
| RL-021 | Time is evidence only. | DPA-INV-013; ADR-008 | DISC-005, DISC-009 | DPA-500 | unchanged old-plan test | no time-only blocker | timestamp with fingerprints | none |
| RL-022 | Repository-specific mappings remain exact-ref bounded. | DPA-INV-017; ADR-011, ADR-015 | DISC-001–010, DISC-003b | DPA-800 | classification audit | unsupported claim blocks review-ready | cited records | return claim to validation-needed |

## 2. Trust-state mapping

| Lifecycle event | Resulting state | Prohibited result |
|---|---|---|
| renderer returns valid payload | `computed` | `accepted` |
| immutable plan captured | `plan-captured` | Write without execution guard |
| validation or plan rejected | `abandoned` | silent retry or textual merge |
| atomic Write succeeds | `written-unverified` | direct `accepted` |
| Verify fails or interrupted instance is detected | `abandoned` | retain instance as eligible for acceptance |
| Verify succeeds but required gates/evidence are incomplete | `written-unverified` | lifecycle-local acceptance |
| DPA-500 gate set succeeds | `accepted` | acceptance shortcut |

## 3. Invalid-state tests

The implementation MUST reject or detect:

1. second registry or DPA-only command authority;
2. unknown projection, partition or fingerprint version;
3. executable renderer reference or unknown renderer;
4. ambiguous or duplicate target;
5. missing, dangling, duplicate or inconsistent parent partition contract;
6. overlapping regions, unexplained bytes or multiple owners;
7. renderer invocation before validation;
8. mutation without exact plan identity;
9. mutation without Workspace lock;
10. nested projection mutation;
11. any stale base/source/target/contract/renderer/partition/ownership guard;
12. renderer, workflow or evidence writer mutating target/state;
13. in-place region Write;
14. changed preserved bytes silently copied;
15. Write without immediate `written-unverified` state;
16. omitted or failed post-Write verification represented as success;
17. lifecycle assignment of `accepted`;
18. evidence used as acceptance or runtime state;
19. missing acceptance-state record treated as fresh;
20. source drift mislabeled solely as target drift;
21. stale-lock takeover without interrupted-instance disposition;
22. crashed-after-Write bytes silently accepted;
23. append-based current-state accumulation after governed replacement adoption;
24. hard failure caused only by elapsed time.

## 4. Probe mapping

| Probe | DPA-300 questions |
|---|---|
| PROBE-001 | Can the actual registry represent optional projection and parent partition contracts without breaking manual entries or allowing silent fallback? |
| PROBE-002 | Can every then-known writer, including the observed `admin-refresh-pr` path, be routed through plan-bound atomic replacement with Workspace-resolved acceptance state and interrupted recovery? |
| PROBE-003 | Can existing findings carry drift, recovery, state and direct-write outcomes without a parallel finding system? |
| PROBE-005 | Can the existing local lock and transfer orchestration implement the local contract while supplying DPA-600 cross-ref guards? |

## 5. Repository-specific evidence boundary

The following facts are `VERIFIED` only at `vfi64/agentic-project-kit@6a9da7d363ae3f97f347b79a2679f6f848d8cdf3`:

- the registry is document-wide and lacks the proposed projection/partition shape;
- the lifecycle has dry-run triage and planning but no projection content writer;
- Workspace and the reentrant PID-based mutation lock exist;
- `admin-refresh-pr` through `_refresh_operational_handoff_docs()` is an observed writer of `CURRENT_HANDOFF.md`;
- the inspected `chat-switch-complete` path does not write `CURRENT_HANDOFF.md`;
- a bounded block replacement primitive exists but is not used by the observed append path;
- CI runs Ruff, pytest and CLI smoke;
- Git contains recoverable prior target states.

No item proves compatibility or global writer-set completeness.
