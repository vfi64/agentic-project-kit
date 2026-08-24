# Post-v1.0.4 A0 Planning Reconciliation

Status: done
Status date: 2026-08-24
Baseline ref: `375d135c` (`Refresh handoff state after PR2135 (#2136)`)
Command manifest: `2ab1c7c2a951`
Canonical authority: `docs/planning/PROJECT_DIRECTION.yaml`

## Purpose

This A0 report reconciles active planning after the v1.0.4 release line and
registers the maintainer-requested hygiene, boundary, and open-question work
program without creating a second planning authority.

The report is evidence for the Direction update only. It does not close remote
branches, issues, or PRs; does not publish releases; and does not adjudicate the
later report-only findings.

## Startup Evidence

- Local `main` was clean and at `375d135c`.
- First-parent release evidence includes PR #2133 (`Prepare release v1.0.4`),
  PR #2135 (`Close out release v1.0.4 DOI metadata`), and PR #2136 (handoff
  refresh after PR #2135).
- `agentic-kit direction validate --json` returned PASS before mutation.
- `agentic-kit direction audit-drift --json` returned PASS before mutation, while
  still reporting `docs/planning/MASTER_IMPLEMENTATION_Q.md` as a historical
  listed source.

## Active Planning Inventory

The fresh Direction inventory at baseline `375d135c` was:

| Section | Count | Open statuses |
| --- | ---: | --- |
| `strategy` | 5 | 5 active |
| `roadmap` | 24 | 1 next, 5 planned, 1 blocked |
| `plans` | 39 | 9 active, 10 planned, 1 blocked |
| `ideas` | 11 | 3 accepted, 8 candidate |
| `done` | 6 | none |
| `discarded` | 7 | none |

No item was closed because of age alone.

## Master Q2 Disposition

`master-implementation-q` no longer represents the next active work order:

- CM3/CM4, LC/ID/K3, P5b/P5d/P6, LC3/TH1, and L Direction items are marked done.
- P5c remains intentionally blocked and maintainer-gated, not ordinary active
  executor work.
- Current active work is better represented by narrower Direction records such
  as release command authority, workflow/kernel hardening, post-merge lifecycle,
  standard-error hardening, Planner-Kit-Executor, onboarding, and the new A/B
  work program.

Decision: preserve `docs/planning/MASTER_IMPLEMENTATION_Q.md` as historical
evidence, but mark `master-implementation-q` as `done` with disposition
`historical_superseded`.

## Current Active/Blocked Dispositions

| Item | Disposition |
| --- | --- |
| `governed-operating-model` | still active strategic boundary |
| `kit-as-os` | still active strategic boundary |
| `professional-single-user-tool` | still active product boundary |
| `python-backed-portable-workflows` | still active implementation boundary |
| `machine-readable-governance` | still active governance direction |
| `pre-gui-hardening-line` | still next; GUI expansion remains gated by wrapper, evidence, rule-refresh, and closeout hardening |
| `p5c-physical-migration` | still blocked and maintainer-gated |
| `workflow-kernel-and-transfer-hardening` | still planned |
| `release-and-doi-governance` | still planned as durable release governance beyond v1.0.4 |
| `gui-gatekeeper-workbench` | still planned, not part of Aufgabe A |
| `documentation-artifact-governance-os` | still planned |
| `lifecycle-backlog-clearance` | still active |
| `governance-doc-backfill` | still active |
| `pre-gui-hardening-plan` | still active |
| `next-turn-workflow-kernel` | still active |
| `release-command-authority` | still active as command-authority hardening, although v1.0.4 publication itself is complete |
| `rule-registry-hardening` | still active |
| `standard-error-hardening-backlog` | still active and directly relevant to A1 |
| `post-merge-lifecycle-state-model` | still active and relevant to B2/B3 evidence discipline |
| `agf-dpa-adoption-tracker` | still blocked |

## Registered Work Program

The new Direction item `post-v1-0-4-hygiene-boundary-work-program` is the single
canonical planning record for this request.

It registers:

- A0 as complete in this slice.
- A1 as report-only findings for PR #2116, PR #2117, and PR #2119.
- A2 as blocked until maintainer adjudication after A1.
- A3 as report-only remote branch/PR/issue classification with no destructive
  cleanup before approval.
- A4 as Hermes independence revalidation.
- B0 as refresh-metric definition before B1.
- B1 with explicit states: `setup_not_started`, `B1_SETUP_COMPLETE`,
  `realbetrieb_running`, `B1_EVALUABLE`, and `final_adjudication_complete`.
- B2 as blocked until B1 is evaluable.
- B3 as independent after A0, with Stage 1 report-only side-effect audit and
  Stage 2 maintainer-gated safety reclassification.

## A0 Exit Criteria

A0 is complete only when:

- Direction validation passes after the update.
- Direction drift audit remains PASS after the update.
- Documentation and local gates do not report a new blocker from this planning
  mutation.
- The PR closeout keeps the repository on a clean, synchronized `main`.
