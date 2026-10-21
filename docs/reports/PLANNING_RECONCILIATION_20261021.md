# Planning reconciliation — 2026-10-21

Status: historical evidence
Authority: docs/planning/PROJECT_DIRECTION.yaml (`meta.planning_reconciliation`)
Baseline: ffbbd19445225ae22a6444f10c2c12523d09acec (main after PR #2591 and its handoff refresh #2592).
Previous: docs/reports/PLANNING_RELEASE_RECONCILIATION_20261011.md (baseline e4029264, Kit 1.0.23).

## Why

The last reconciliation described Kit 1.0.23. Seven releases followed (1.0.24, 1.0.25, 1.1.0 to
1.1.4), the findings KIT-GF-066 to 082 were recorded, and the roadmap's only `next` item
(`pre-gui-hardening-line`) does not name a concrete slice. The generated handoff still pointed the
successor at "the next governed DPA DP2 slice". A successor could not tell from the authority what
comes next.

## Method

Read only: all six Direction sections at the baseline; the 96 published releases (v0.2.0 to v1.1.4)
through the paginated GitHub releases API; the Kit catalog `external-findings-status.json`; the
installed-wheel retest `agentic-kit greenfield retest --all` of Kit 1.1.4, run in the external Cockpit
workspace on 2026-10-20; the Cockpit ledger at agp-Cockpit main 7157b8e9. No target was changed and
no operational retest was rerun.

## Findings

| Surface | State at the baseline |
| --- | --- |
| Releases | v1.1.4 is current (`current_verified`, DOI 10.5281/zenodo.23505873). KIT-GF-081 and 082 are merged (PR #2591) and unreleased. |
| GF catalog | 80 numbered families (001-082 without 019 and 020) and RULE-REGISTRY-BOOTSTRAP; all CLOSED except KIT-GF-070 (PARTIAL). |
| Executable retests | Under 1.1.4: PASS 8, FAIL 0, NO_MACHINE_CONTRACT 34, NOT_RUN_LOCALLY 37 (081 and 082 add two owner-remote families). VERIFIED_FIXED in a consumer still needs hand-collected evidence for most families. |
| External ledger | 16 Cockpit families (001-010, 012-016, 018) are OPEN against a Kit closure; KIT-GF-081 awaits release; KIT-GF-082 is not recorded yet. |
| kit-control-effectiveness-measurement | Steps 1-4 done; step 5 part 1 done (11 of 11 injected faults detected), part 2 prepared and waiting for the owner's choice of agent, token budget and task count. |
| website-evidence-and-command-navigation | Accepted 2026-10-17, no step started; W0 first, then W2, W1-P0 in parallel. |
| Handoff next slice | `.agentic/operational_handoff_state.yaml` still named a DPA DP2 slice; replaced by the owner order below. |

## Owner order (2026-10-21)

1. This reconciliation.
2. `external-retest-machine-contracts`: machine contracts for the 34 local families without one
   (closing KIT-GF-070), a resync of the Cockpit ledger, then release 1.1.5 with KIT-GF-070, 081
   and 082 after the owner's go.
3. `kit-control-effectiveness-measurement`, step `gate-and-context-benchmark`, part 2, once the owner
   has chosen agent, budget and task count.
4. `website-evidence-and-command-navigation` in its own sequencing.

The Brownfield, B2/B3, lifecycle and P5c priorities of the previous reconciliation stay as they were.
