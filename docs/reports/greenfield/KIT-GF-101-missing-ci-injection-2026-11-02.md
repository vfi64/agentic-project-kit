# KIT-GF-101: explicit CI injection for an initialized workspace

Status: CLOSED/unreleased. No release is performed by this fix.

## Defect

An older external workspace can have a Kit-managed CI source without the optional
workflow injection. The updater requires both files, while workspace init refuses
an initialized workspace. Previously ci-update refreshed only the source and did
not offer an explicit way to create the missing workflow. The external update
stopped before any installation/update step; that evidence was preserved.

## Correction and verification

`workspace ci-update --inject-ci` previews creation of a missing managed workflow.
Only explicit execution writes it. The existing default does not opt in. Core
logic stays in workspace_ci_update.py and the CLI passes the flag through.
Unknown/custom source and workflow files remain blocked. Paths must remain in
the workspace; execution rechecks the plan under the existing workspace lock.

Before implementation, the new regression suite had three failures and four
passes. After implementation, 30 focused tests passed, including the existing
workspace initialization/CI regressions and eight new checks. They cover preview,
execution, idempotence, the default opt-out, custom files, a workflow appearing
after planning, creation of both missing paths and a symlinked parent escape.
Ruff passed. The machine contract checks the same opt-in boundary from a wheel.
Final suite and gate results will be recorded after execution.

No dependencies, version bump, release or B activation are part of this fix.
The two managed paths remain derived Kit outputs; consumers do not hand-edit
them. External workspace identities and local evidence paths are kept private.
