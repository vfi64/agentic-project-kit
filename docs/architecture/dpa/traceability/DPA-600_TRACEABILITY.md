# DPA-600 Traceability

Status: draft

Status-date: 2026-07-27

This matrix traces DPA-600 requirements without becoming a competing normative
source. Invariant anchors are derived from the canonical register in DPA-000
§7.

| ID | Requirement | Invariants / decisions | Tests | Later work | Evidence / rollback |
|---|---|---|---|---|---|
| CS-001 | Local Workspace locks and cross-ref serialization remain separate authorities. | DPA-INV-004, DPA-INV-005; ADR-003, ADR-006 | local-lock-only, branch-concurrency and PR-concurrency negatives | DP1 Probe; DP2 lifecycle; DP5 gates | lock transcript plus branch/PR identities; regenerate when remote context moved |
| CS-002 | Acceptance-bearing plans capture operation, branch, PR, base and validation-ref identity where applicable. | DPA-INV-004, DPA-INV-005, DPA-INV-017; ADR-006, ADR-021 | missing-field, wrong-branch, wrong-head and wrong-base cases | DP2 plan schema; workflow integration | immutable plan and workflow context; abandon incomplete plan |
| CS-003 | Stale plans block Write, acceptance, required-check publication and merge eligibility. | DPA-INV-004, DPA-INV-005; ADR-004, ADR-006 | stale source, target, contract, renderer, partition, ownership, gate-set and acceptance-state cases | DP2 lifecycle; DP5 gates | structured stale findings; no target mutation; regenerate |
| CS-004 | Time alone is not a hard concurrency failure. | DPA-INV-013; ADR-008 | old unchanged plan with matching identities | DP5 policy | timestamp as evidence only; rerun comparisons if policy requires |
| CS-005 | Branch switch, rebase or reset invalidates acceptance-bearing plan reuse unless full identity revalidation passes. | DPA-INV-005, DPA-INV-017; ADR-006 | branch-change and rebase tests | workflow orchestration | branch/head evidence; recreate plan from current ref |
| CS-006 | PR checks and evidence bind to exact PR head and exact base. | DPA-INV-005, DPA-INV-017; ADR-006 | changed-head, changed-base and stale-check cases | CI/required checks; merge queue | exact head/base evidence; rerun checks |
| CS-007 | Competing PRs with shared target, source, contract, renderer, ownership, gate-set or base dependency require later-candidate revalidation. | DPA-INV-005, DPA-INV-014; ADR-006, ADR-007 | same-target, shared-source and shared-contract PR races | integration workflow | conflict matrix; block later candidate; regenerate |
| CS-008 | Disjoint-target concurrency is allowed only after independence is recorded. | DPA-INV-005, DPA-INV-011 | disjoint target with shared and non-shared dependencies | workflow dependency graph | recorded dependency comparison; fall back to serialization |
| CS-009 | Regeneration from the current validation ref is the default stale-plan recovery. | DPA-INV-004, DPA-INV-014; ADR-006, ADR-007 | stale-plan regeneration; no historical merge | DP2 lifecycle; DPA-700 rollback/migration | abandon stale attempt, preserve finding, create new plan |
| CS-010 | Historical or manual prose is never auto-merged to clear drift. | DPA-INV-014; ADR-007 | clean textual merge with stale projection; manual-region preservation | DPA-700 migration/rollback | preserve ownership boundaries; reject stale generated text |
| CS-011 | Workflow orchestration serializes acceptance-bearing work at the smallest safe dependency scope. | DPA-INV-005, DPA-INV-011, DPA-INV-012; ADR-001, ADR-003 | same target, same partition, shared dependency and read-only audit cases | DP2/DP5 workflow integration | queue/order decision; no parallel DPA workflow |
| CS-012 | Administrative handoff/status refreshes follow the projection serialization contract when they write registered targets. | DPA-INV-004, DPA-INV-005, DPA-INV-011 | writer inventory and admin-refresh race tests | DP2 writer adaptation; DPA-800 command plan | command-to-lifecycle trace; block direct writer |
| CS-013 | Unresolved interrupted or `written-unverified` state blocks merge eligibility. | DPA-INV-004; ADR-014, ADR-016 | crash before/after Write; unresolved recovery check | DP2 recovery; DP5 gates | recovery disposition; preserve prior accepted state |
| CS-014 | Concurrency findings are structured, bounded and non-authoritative. | DPA-INV-010, DPA-INV-011, DPA-INV-012 | missing PR state, unavailable queue state, stale check and evidence-failure cases | existing findings integration | bounded evidence; fail closed for mutation/integration |
| CS-015 | Repository-specific mechanisms remain exact-ref fenced. | DPA-INV-017; ADR-011, ADR-015 | classification audit and unsupported-claim negatives | DP1 Probe; controlled import | mark `NEEDS_MAIN_REPO_VALIDATION`; do not claim conformance |
| CS-016 | Post-integration refreshes bind to the accepted integration ref and force later shared-dependency candidates to revalidate. | DPA-INV-004, DPA-INV-005, DPA-INV-017; ADR-006 | post-integration refresh and later-candidate revalidation cases | workflow integration; DP5 gates | accepted-ref and dependency evidence; block successor evidence when stale |

## Probe obligations

- Verify the existing Workspace lock and stale-lock takeover behavior.
- Verify branch guard, remote-head guard and PR full-SHA guard behavior.
- Verify whether existing required checks bind to exact head and applicable base.
- Verify whether administrative refresh workflows serialize registered
  projection targets or need lifecycle routing.
- Verify whether competing-PR dependency detection can be represented with
  existing workflow state and findings.
- Verify regeneration from the current validation ref without historical-prose
  auto-merge.
- Verify that unresolved `written-unverified` or interrupted state blocks merge
  eligibility.
- Verify that post-integration handoff, state or status refreshes bind to the
  accepted integration ref and invalidate later candidates sharing changed
  dependencies.
- Verify that read-only audits remain concurrent and mutation-free.

## Review boundary

This traceability file is non-normative. Any contradiction is resolved in favor
of DPA-000 through DPA-600 and accepted decisions.
