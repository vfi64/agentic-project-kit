# Post-v1.0.5 B2 Successor Package / Handoff Projection Adjudication

Status: adjudicated_boundary_retained  
Date: 2026-08-26  
Prerequisite: `B1_EVALUABLE` from `docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.md`

## Question

B2 asks whether the separation between the deterministic Successor Handoff
Package and human-facing handoff prompt projections is a necessary safety
boundary or a historically grown mechanism that should be collapsed.

## Evidence Considered

- `docs/reports/POST_V1_0_4_B0_REFRESH_METRIC_DEFINITION_20260824.md`
- `docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`
- `tests/test_successor_handoff_package.py`
- B1 Comm-SCI cycles 003-005, where mixed report/status/handoff updates
  required extra generated successor refresh PRs before post-merge checks
  returned PASS/NOOP.

## Adjudication

The separation is a safety boundary and should remain.

The B1 evidence shows why: generated package freshness and human-readable
handoff projections can drift independently. When a mixed handoff/report/status
PR changed repository state after a generated package was produced, the
post-merge lifecycle correctly required a generated-only successor refresh
before treating the state as ready. Collapsing the typed package and prompt
projection would hide that distinction instead of removing the underlying
freshness problem.

The boundary also preserves the architecture contract:

- machine-readable state remains the canonical continuation surface;
- Markdown prompts are projections, not independent sources of truth;
- successor chats can validate exact refs before trusting prose;
- refresh friction remains measurable under B0 instead of being optimized away
  by weakening the check.

## What Is Historical

The boundary is valid, but some workflow shape around it is still historical
friction:

- one real external work PR can currently produce multiple visible
  administrative refresh PRs;
- `pr-merge-safe` can succeed remotely while not returning a local terminal PASS
  in the observed external path;
- mixed evidence/report/status refreshes make operator sequencing harder than
  the safety property itself requires.

These are ergonomics and lifecycle-orchestration follow-ups, not reasons to
remove the package/projection boundary.

## Decision

Keep the Successor Handoff Package as the canonical generated state and keep
human-facing handoff prompts as projections.

Future work may reduce extra administrative PRs or improve refresh orchestration
only if it preserves these invariants:

- stale generated heads remain blocking or explicitly WARN/NOOP according to
  the current lifecycle contract;
- package validation remains machine-readable;
- generated prompt projections do not become a separate authority;
- B0 refresh-cost evidence is not retroactively changed.

B2 is therefore adjudicated as `adjudicated_boundary_retained`. No product-code
change is required for B2 in this slice.
