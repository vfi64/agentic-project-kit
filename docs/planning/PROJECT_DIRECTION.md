# Project Direction

Status: active
Decision status: accepted
Review policy: required

`docs/planning/PROJECT_DIRECTION.yaml` is the canonical machine-readable source
for active strategy, roadmap, plans, candidate ideas, completed planning items,
and discarded direction choices.

This Markdown file is only a human-readable orientation view. It must not become
an independent planning source, and it must not contain strategy, roadmap, or
plan details that are absent from `PROJECT_DIRECTION.yaml`.

During the consolidation sequence, older scattered planning documents are
migration sources. Idea content has been migrated into
`PROJECT_DIRECTION.yaml`; completed and discarded material is recorded in the
`done` and `discarded` sections; obsolete files are deleted only after a
reference-clean protected-diff slice.

Do not add new free-form planning Markdown under `docs/planning/` for active
strategy, roadmap, plan, or idea work. Add structured entries to
`PROJECT_DIRECTION.yaml` instead, or use a temporary/historical document only
when a later cleanup path is explicit.

The latest bounded planning review is recorded in
`PROJECT_DIRECTION.yaml` under `meta.planning_reconciliation`, including its
exact checkout baseline, evidence limits and remaining priorities. Historical
Q2 instructions are retained in `MASTER_IMPLEMENTATION_Q.md` as superseded
reference material.

Completed goals remain in the canonical YAML, either with `status: done` in
their original section or in `done`. Stable IDs, acceptance and evidence retain
their context and dependencies. The review recommends against an additional
manually maintained completion list; historical specifications, evidence files
and Git history already preserve the detail.

The imported PAA v0.3 proposal is integrated under `proof-assurance-assessment`
in the canonical YAML. Its complete review input is retained as a historical
reference; phase decisions and current scope belong to the YAML. The separate
`dpa-current-evidence-continuity` item records the current DPA evidence blocker.
