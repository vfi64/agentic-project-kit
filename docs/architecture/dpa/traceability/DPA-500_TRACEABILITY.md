# DPA-500 Traceability

Status: draft

Status-date: 2026-07-17

This matrix traces DPA-500 requirements without becoming a competing normative source. Invariant anchors are derived from the canonical register in DPA-000 §7.

| ID | Requirement | Invariants | Tests | Later work | Evidence / rollback |
|---|---|---|---|---|---|
| FG-001 | Freshness is multidimensional and time alone is not authority | DPA-INV-004, DPA-INV-013 | no-time-only staleness; dimension comparison cases | DP1 Probe; DP2 lifecycle integration | exact-ref comparison evidence; preserve prior accepted state |
| FG-002 | Acceptance state is lifecycle state, not evidence | DPA-INV-004, DPA-INV-010, DPA-INV-016 | missing, malformed, scope-mismatched state | DP2 acceptance-state implementation | bounded state/evidence separation; no silent reconstruction |
| FG-003 | DPA-100 drift classes remain top-level and independent subreasons remain separately reportable | DPA-INV-004, DPA-INV-011, DPA-INV-012 | base/source/target/contract/renderer/partition/ownership drift and subreasons | DP2 findings; DP5 strict gates | structured findings; regenerate from current ref |
| FG-004 | Mandatory safety failures produce gate failure and block mutation and acceptance | DPA-INV-004, DPA-INV-006, DPA-INV-007, DPA-INV-015 | stale-plan, invalid contract, unknown renderer, nondeterminism, side effects | DP2 mutation path; DP5 enforcement | attempt abandoned; no accepted partial output |
| FG-005 | Freshness classification, gate decision and consumer trust state remain distinct | DPA-INV-004, DPA-INV-010 | read-only failure without mutation; warning cannot accept | DP2 audit UX; DP5 policy | record classification, decision and state separately |
| FG-006 | Staged enforcement is explicit, reversible and not time-triggered | DPA-INV-011, DPA-INV-012, DPA-INV-013 | observe/warn/block-new/strict transitions | DP5 adoption | configuration and decision evidence; revert stage safely |
| FG-007 | Renderer drift uses identifier/interface/semantic distinctions | DPA-INV-007, DPA-INV-008 | identifier, interface, semantic, evidence-only changes | DP1 renderer Probe; DP2 integration | semantic version controls freshness; implementation evidence remains evidence |
| FG-008 | Region mutation evaluates payload, preserved bytes, partition and complete target independently | DPA-INV-004, DPA-INV-014 | plan/write/verify payload, preserved-region and partition cases | DP2 first projection | preserve manual/history bytes; regenerate only lifecycle-owned payload |
| FG-009 | Interrupted writes never imply acceptance | DPA-INV-004 | written-unverified recovery paths | DP2 recovery | retain attempt evidence; verify exact bytes or regenerate |
| FG-010 | Evidence is bounded and non-authoritative | DPA-INV-010 | evidence failure and unavailable checks | DP2 evidence integration | no fabricated success; preserve state distinction |
| FG-011 | Existing main-repository registry, lifecycle and gates remain production authority | DPA-INV-011, DPA-INV-012 | no parallel freshness, gate or state path | controlled import; DP2/DP5 | import only approved contracts; remove lab-only scaffolding after adoption |
| FG-012 | Missing mandatory inputs cause indeterminate or invalid evaluation and fail-closed gate failure | DPA-INV-004, DPA-INV-017 | missing mandatory evaluation input | DP2 validation | explicit finding; no mutation |
| FG-013 | Base context is operation-scoped and persisted only for declared base dependence | DPA-INV-004, DPA-INV-005, DPA-INV-017 | base-independent audit after plan cleanup; base-dependent accepted comparison | DP2 state; DPA-600 integration | conditional state field; preserve accepted state when base is irrelevant |
| FG-014 | Gate-set-only change can be re-evaluated and re-accepted without render or target write | DPA-INV-004, DPA-INV-010, DPA-INV-011, DPA-INV-012, DPA-INV-016 | re-acceptance pass; warning/failure preserving state; no renderer/write | DP2 lifecycle; DP5 staged adoption | state-only atomic update; retain prior state on failure |
| FG-015 | Layered acceptance distinguishes governed non-lifecycle-owner evolution from lifecycle-owned drift | DPA-INV-004, DPA-INV-014 | authorized owner edit; out-of-band payload edit; partition edit; ambiguous owner | DP2 region integration; DP4 migration | preserve manual/history bytes; fail closed when ownership cannot be proven |
| FG-016 | Attempt-scoped renderer failures do not overwrite the classification of previously accepted bytes | DPA-INV-004, DPA-INV-007, DPA-INV-008 | failed attempt beside unchanged accepted target | DP2 lifecycle integration | separate attempt evidence and target evaluation |

## Probe obligations

- Map DPA-100 drift classes and DPA-500 finding subreasons to existing main-repository findings and severities.
- Verify the existing pass/warning/failure gate representation, gate-set identity, strict-adoption controls and command integration.
- Verify acceptance-state schema, Workspace path, conditional base identity and crash-safe persistence order.
- Verify lifecycle-owned re-acceptance without renderer invocation or target mutation.
- Verify how governed non-lifecycle-owner provenance is represented and distinguished from out-of-band lifecycle-byte writes.
- Demonstrate that existing non-projection documents retain compatible behavior.
- Demonstrate observe, warn, block-new and strict policy stages without weakening mutation safety.

## Review boundary

This traceability file is non-normative. Any contradiction is resolved in favor of DPA-000 through DPA-500 and accepted decisions.
