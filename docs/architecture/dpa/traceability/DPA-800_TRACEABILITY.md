# DPA-800 Traceability

Status: draft

Status-date: 2026-07-27

This matrix traces DPA-800 requirements without becoming a competing normative
source. Invariant anchors are derived from the canonical register in DPA-000
§7.

| ID | Requirement | Invariants / decisions | Tests | Later work | Evidence / rollback |
|---|---|---|---|---|---|
| DP-001 | DP1 Discovery, Probe and Assessment remain distinct substages. | DPA-INV-010, DPA-INV-017; ADR-011, ADR-015 | discovery-as-probe and probe-as-assessment negatives | DP1 execution | exact records per substage; stop before overclaim |
| DP-002 | Exact-ref identities are typed and cannot be silently promoted. | DPA-INV-017; ADR-009, ADR-011 | stale historical ref and remote/local mismatch cases | DP1-DP5 | ref-class evidence; revalidate or block |
| DP-003 | Package B starts from the current governed base, not the parked stale branch. | DPA-INV-010, DPA-INV-017; ADR-011 | parked-branch-as-baseline negative | DPA-800 review; Package B PR | parked-branch record; reconstruct from current base |
| DP-004 | PROBE-001 tests registry and contract compatibility only. | DPA-INV-006, DPA-INV-011, DPA-INV-012 | parser, unknown-field and manual-entry cases | DP1 Probe | compatibility evidence; no form selection |
| DP-005 | PROBE-002 tests lifecycle, state, writer routing and recovery. | DPA-INV-004, DPA-INV-011, DPA-INV-012, DPA-INV-016 | plan, lock, write, acceptance and recovery cases | DP1 Probe; DP2 | recovery evidence; no quick writer patch |
| DP-006 | Renderer Probes test identity, determinism, purity and capability boundaries. | DPA-INV-007, DPA-INV-008, DPA-INV-009 | renderer-map, side-effect, semantic-version cases | DP1 Probe; DP2 | renderer evidence; restore prior mapping |
| DP-007 | Assessment classifies every discrepancy before implementation. | DPA-INV-010, DPA-INV-017 | discrepancy classification cases | Maintainer adjudication | architecture/implementation/fixture/evidence disposition |
| DP-008 | DP2 starts only after all applicable Probe families, Assessment and Maintainer authorization. | DPA-INV-011, DPA-INV-012, DPA-INV-017 | undefined-probe and premature-DP2 negatives | DP2 implementation | blocked state; no mutation |
| DP-009 | DP2 extends existing authorities for one first target. | DPA-INV-004, DPA-INV-011, DPA-INV-012 | no-parallel-system and first-target scope cases | DP2 | implementation ref; rollback or bounded revert |
| DP-010 | DP3 rollout requires entry criteria, per-target evidence, rollback and exit adjudication. | DPA-INV-001, DPA-INV-012, DPA-INV-017 | batch rollout and missing-exit negatives | DP3 | per-target records; stop failed slice |
| DP-011 | DP4 status migration requires entry criteria, fresh reader/writer/generator/command-update discovery and exit adjudication. | DPA-INV-001, DPA-INV-010, DPA-INV-014 | status reader/writer, generated-output and no-migration cases | DP4 | rollback package or manual preservation |
| DP-012 | DP5 stage transitions require entry criteria, exit criteria, reversibility and no time-triggered strict activation. | DPA-INV-004, DPA-INV-013 | observe/warn/block-new/strict and no-time-only cases | DP5 | stage decision and rollback record |
| DP-013 | Controlled import maps artifacts and avoids wholesale Lab adoption. | DPA-INV-011, DPA-INV-012 | import-map completeness and Lab-authority negatives | controlled import | artifact disposition; remove unsupported imports |
| DP-014 | Stop states preserve evidence and require adjudication where needed. | DPA-INV-010, DPA-INV-017 | blocked-state cleanup negative | DP1-DP5 | preserved reports; Maintainer decision |
| DP-015 | Repository-specific implementation claims remain exact-ref fenced. | DPA-INV-017; ADR-011, ADR-015 | unsupported-claim audit | DP1-DP5 | mark `NEEDS_MAIN_REPO_VALIDATION` |
| DP-016 | PROBE-003 tests DPA-600 branch, PR, integration and post-integration serialization. | DPA-INV-004, DPA-INV-011, DPA-INV-012, DPA-INV-017; ADR-006 | branch, PR, required-check, integration and regeneration cases | DP1 Probe; DP2-DP5 | exact workflow evidence; no merge-queue conformance claim |
| DP-017 | PROBE-004 tests DPA-700 migration forms, rollback packages and renderer semantic-version rollback. | DPA-INV-010, DPA-INV-011, DPA-INV-012, DPA-INV-014; ADR-007 | migration-form, rollback, no-history-source and generated-output cases | DP1 Probe; DP2-DP4 | rollback evidence; no production target selection |
| DP-018 | Exact ref roles may co-locate only with explicit role, scope and limitation evidence. | DPA-INV-017; ADR-009, ADR-011 | multi-role-ref evidence negative | DP1-DP5 | record every role; no silent promotion |

## Probe obligations

- Prepare PROBE-001, PROBE-002, PROBE-003, PROBE-004 and renderer-Probe
  manuals from this contract.
- Execute Probes only against exact validation refs in a suitable environment.
- Preserve PASS, FAIL, PARTIAL and BLOCKED outcomes with bounded evidence.
- Map every discrepancy to architecture, implementation, fixture or evidence
  disposition before DP2.
- Rebuild writer and reader inventories at the Probe validation ref.
- Treat a Probe family as non-applicable only when Assessment explicitly records
  the scope and rationale.

## Review boundary

This traceability file is non-normative. Any contradiction is resolved in favor
of DPA-000 through DPA-800 and accepted decisions.
