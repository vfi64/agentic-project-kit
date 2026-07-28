# DPA-700 Traceability

Status: draft

Status-date: 2026-07-27

This matrix traces DPA-700 requirements without becoming a competing normative
source. Invariant anchors are derived from the canonical register in DPA-000
§7.

| ID | Requirement | Invariants / decisions | Tests | Later work | Evidence / rollback |
|---|---|---|---|---|---|
| MR-001 | Migration outcomes include no migration, manual, full, split, hybrid and managed-head. | DPA-INV-001, DPA-INV-012, DPA-INV-017; ADR-007 | outcome classification and no-migration cases | DP1 Assessment; DP4 migration | exact outcome record; reopen only with new evidence |
| MR-002 | Form selection follows the lower-risk hierarchy before hybrid or managed-head. | DPA-INV-014; ADR-007 | full/split rejection before managed-head | DP1 Assessment | recorded rejection reasons; choose no migration when unproven |
| MR-003 | Migration selection requires exact-ref authority, reader, writer, gate, partition and rollback evidence. | DPA-INV-010, DPA-INV-011, DPA-INV-017 | missing authority, reader, writer and rollback negatives | DP1 Discovery/Probe/Assessment | no migration; preserve manual behavior |
| MR-004 | Migration plans are immutable, dry-run by default and bound to DPA-600 context. | DPA-INV-004, DPA-INV-005, DPA-INV-015 | plan identity, stale context and execution authorization cases | DP2 lifecycle; DP4 migration | abandon stale plan; regenerate from validation ref |
| MR-005 | Rollback packages are bounded state/evidence, not canonical history stores. | DPA-INV-010, DPA-INV-014; ADR-002, ADR-007 | missing rollback input and broad-evidence negatives | DP4 rollback | restore exact prior bytes/state or block remediation |
| MR-006 | Full projection requires every byte to be reconstructable from declared canonical sources. | DPA-INV-001, DPA-INV-006, DPA-INV-014 | non-canonical byte negative | DP1 authority graph | reject full projection; lower-risk outcome |
| MR-007 | Split projection uses separate registered target identities and preserves all identities on rollback. | DPA-INV-001, DPA-INV-004, DPA-INV-012 | split identity and rollback tests | DP4 migration | per-target rollback evidence |
| MR-008 | Hybrid and managed-head are exceptional and require complete partition ownership and applicable DPA-600 workflow-serialization maturity. | DPA-INV-003, DPA-INV-005, DPA-INV-014; ADR-013, ADR-017 | boundary, overlap, writer, reader-order and DPA-600-maturity cases | DP4 migration; DPA-600 integration | complete target rollback package; no automatic history merge |
| MR-009 | Non-lifecycle-owned bytes are preserved and never regenerated merely to clear findings. | DPA-INV-014; ADR-007, ADR-021 | manual/history preservation and partition drift cases | DP2 lifecycle; DP4 migration | preserve or restore exact bytes; fail closed on ambiguity |
| MR-010 | Migration target mutation uses the DPA-300 lifecycle only. | DPA-INV-004, DPA-INV-011, DPA-INV-012 | direct writer and bypass negatives | DP2 implementation | restore prior target; route writer through lifecycle |
| MR-011 | Acceptance state is created or migrated only after lifecycle verification and gates pass. | DPA-INV-004, DPA-INV-010, DPA-INV-016 | premature acceptance and target-byte reconstruction negatives | DP2 state; DP5 gates | restore or invalidate state explicitly |
| MR-012 | Rollback before and after acceptance is explicit and preserves accepted production meaning. | DPA-INV-004, DPA-INV-014; ADR-014, ADR-016 | before-Write, after-Write, after-acceptance rollback tests | DP4 migration | governed rollback operation; blocked remediation when unproven |
| MR-013 | Renderer semantic-version rollback is explicit, invalidates acceptance for non-reproducible exact-byte restore and fails closed when rollback inputs are unavailable. | DPA-INV-007, DPA-INV-008; ADR-019, ADR-020 | changed, removed and retained renderer-version cases; non-reproducible exact-byte restore acceptance invalidation | DP1 renderer Probe; DP4 rollback | regenerate with current renderer or restore exact bytes with invalidated acceptance |
| MR-014 | Interrupted migration recovery never infers success from generated markers or historical prose. | DPA-INV-004, DPA-INV-010, DPA-INV-014 | ambiguous interrupted state cases | DP2 recovery; DP4 migration | abandon, restore or Maintainer remediation |
| MR-015 | Migration evidence is bounded and non-authoritative. | DPA-INV-010, DPA-INV-011, DPA-INV-012 | evidence-as-input and broad-log negatives | DP4 evidence | evidence explains decision; state/contracts remain authority |
| MR-016 | Repository-specific migration mechanisms remain exact-ref fenced. | DPA-INV-017; ADR-011, ADR-015 | unsupported-claim audit | DP1/DP4 | mark `NEEDS_MAIN_REPO_VALIDATION`; no conformance claim |

## Probe obligations

- Verify reader inventory and consumer-order assumptions for candidate targets.
- Verify writer inventory and direct-writer routing for candidate targets.
- Verify rollback-package storage, cleanup and recoverability.
- Verify registry, projection-contract and partition-contract migration paths.
- Verify acceptance-state migration and rollback.
- Verify renderer semantic-version retention or exact-byte fallback behavior.
- Verify that exact-byte rollback without renderer reproducibility explicitly
  invalidates acceptance for the restored scope.
- Verify interrupted migration recovery across before-Write, after-Write and
  after-acceptance scenarios.
- Verify that no migration is selected when authority, compatibility or rollback
  cannot be proven.

## Review boundary

This traceability file is non-normative. Any contradiction is resolved in favor
of DPA-000 through DPA-700 and accepted decisions.
