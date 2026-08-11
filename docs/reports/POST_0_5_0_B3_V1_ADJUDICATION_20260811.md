Status: decision
Status-date: 2026-08-11
Scope: Phase B3 v1.0 readiness adjudication

# Phase B3: v1.0 Readiness Adjudication

## Decision

Keep `v1-0-milestone` as `planned`.

The Post-0.5.0 validation work materially improved the Kit-as-OS evidence base,
but it does not yet justify a 1.0 stability claim. Brownfield and Greenfield
paths both work for important bounded slices, while full external continuation
and one integrated schema-bump migration remain open.

## Evidence Inputs

- `docs/reports/POST_0_5_0_BROWNFIELD_COMM_SCI_READONLY_20260811.md`
- `docs/reports/POST_0_5_0_BROWNFIELD_COMM_SCI_ADOPTION_B1_5_20260811.md`
- `docs/reports/POST_0_5_0_GREENFIELD_B2_20260811.md`
- `docs/reports/POST_0_5_0_SITE_GOVERNANCE_PACKAGING_20260811.md`

## Acceptance Review

| Criterion | Current result | Adjudication |
|---|---|---|
| The self-hosting litmus has passed. | The Kit repository has active self-hosting gates, generated handoff packages, command-manifest gates, doctor checks, and post-merge checks. | Substantially met for the Kit repo. |
| `workspace adopt/init` is stable on at least one real external project. | Comm-SCI read-only assessment and bounded local adoption passed. Target tests passed. Rollback passed after a Kit fix. | Partially met; not yet remote-PR or successor-continuation ready. |
| Too-old and too-new `kit_schema_version` failure paths are tested. | Newer-schema failure and invalid/missing schema failure paths are covered. A mocked v0->v1 path tests stepwise upgrade behavior. | Met for current schema-contract behavior. |
| A tested workspace upgrade transformation exists before or with the first schema bump. | A simulated v0->v1 test exists, and current real workspaces are already schema v1. No real schema bump has happened yet. | Mechanism exists; real first bump remains future work. |

## Why This Is Not 1.0 Yet

The evidence now supports the claim that the Kit can:

- generate and validate a disposable Python CLI project;
- initialize an operating-layer workspace in a real external Python project;
- inventory external authority surfaces without automatic conformance claims;
- keep existing foreign-repo governance intact;
- remove generated operating-layer state idempotently after the rollback fix;
- expose the GitHub Pages website through a `docs/` fallback projection.

The evidence does not yet support these stronger 1.0 claims:

- an external repository can complete the full Kit handoff/continuation loop;
- `agentic-kit check` and `agentic-kit doctor` have a clean external-workspace
  contract distinct from self-hosting and generated-project contracts;
- a remote external adoption PR can run target CI and close without manual
  workflow interpretation;
- the first real manifest schema bump has exercised a non-mocked migration.

## Roadmap Result

`v1-0-milestone` remains planned. Comm-SCI remains the first real external
adoption evidence target, now upgraded from candidate-only evidence to a
bounded local adoption result with documented limits.

## Next Safe Work

- Add an external-workspace mode for `check`, `doctor`, and handoff validation.
- Decide whether target-repo adoption should have a no-remote, draft-PR, or full
  PR rollout path.
- Keep generated-project mode and operating-layer workspace mode visibly
  distinct unless a later architecture change unifies them.
- Exercise the first real manifest schema bump with a deterministic migration
  before promoting 1.0.
