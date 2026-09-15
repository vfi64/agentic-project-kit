# Post-v1.0.12 Greenfield Remaining Closeout

Status: implemented with explicit external-validation boundaries  
Date: 2026-09-15  
Kit baseline: `origin/main` at `c2ce60b1`  
Working branch: `codex/gf-009-017-closeout`  
Machine-readable companion: `POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json`

## Scope

This slice addresses the six remaining Greenfield findings identified by the
AGP Cockpit validation ledger. It uses the existing Kit authorities and gates:
the work-finish orchestrator, known-volatile transfer recovery,
continuation-authority freshness, the documentation registry, and the
Planner-Kit-Executor contract.

No public command was removed and no release or PyPI publication was created.
Historical reports remain unchanged.

## Adjudication

| Finding | Current result | Boundary |
|---|---|---|
| `KIT-GF-009` | Implemented in the current checkout | The wrapper now owns commit, handoff refresh, push, PR, merge, and closeout; a real external first-cycle execution remains required for full Greenfield closure. |
| `KIT-GF-011` | Concrete stale successor-projection loop repaired | The known-volatile recovery path is tested; the broader released-package refresh-loop claim still needs an external retest. |
| `KIT-GF-014` | Closed for current checkout and external-fixture semantics | Stale or ambiguous continuation authority blocks before mutation, while a missing handoff remains valid for external workspaces. |
| `KIT-GF-015` | Closed | `canonical_facts` in the documentation registry is the single source; managed paths block on drift and review paths remain advisory. |
| `KIT-GF-016` | Closed for current checkout and external CLI smoke | Planner intent resolution passes through Kit authority and executor remains dry-run by default; onboarding measurement is PASS. |
| `KIT-GF-017` | Open | `agentic-project-kit==1.0.12` was not available from the current PyPI index, and Docker was unavailable because its local daemon socket was not running. |

## GF-015 repair

`docs/DOCUMENTATION_REGISTRY.yaml` now carries a small canonical-fact section.
The new importable validator in `src/agentic_project_kit/documentation_facts.py`
checks relative projection paths and reports deterministic drift. Managed
projections are blocking findings consumed by `check-docs`; review projections
are advisory findings because their surrounding prose remains project-owned.
The implementation is intentionally additive and does not auto-rewrite prose.

## Evidence

The focused regression set passed with **58 tests**. `agentic-kit check-docs`,
`agentic-kit direction validate --root .`, and `agentic-kit doctor` passed.
The external Planner/Executor smoke resolved a valid Hermes intent through the
Cockpit authority with `PASS`; the default executor run remained `PENDING` and
did not mutate the dirty checkout. `agentic-kit onboarding measure --json`
returned `PASS` with zero findings.

The attempted released-package probe is recorded as a boundary, not a failure
hidden as success: PyPI did not offer version `1.0.12`, and Docker was not
running. Therefore this slice does not close `KIT-GF-017` and does not claim
released-package behavior.

## Next safe step

Publish an approved package version containing the current context-carrier
implementation, then run the required isolated external retest for `GF-009`,
`GF-011`, and `GF-017`. Only that evidence can promote the three implementation
statuses above to full released Greenfield closure.
