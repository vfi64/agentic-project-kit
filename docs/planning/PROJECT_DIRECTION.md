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

During the consolidation sequence, the older `docs/strategy/`, `docs/planning/`,
`docs/plans/`, `docs/ideas/`, and `docs/roadmap/` documents are migration
sources. Their active steering content is migrated into
`PROJECT_DIRECTION.yaml`; completed and discarded material is recorded in the
`done` and `discarded` sections; obsolete files are deleted only after a
reference-clean protected-diff slice.

Do not add new free-form planning Markdown under `docs/planning/` for active
strategy, roadmap, plan, or idea work. Add structured entries to
`PROJECT_DIRECTION.yaml` instead, or use a temporary/historical document only
when a later cleanup path is explicit.
