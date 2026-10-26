---
artifact_type: validation_report
schema_version: 1
---

Status: completed
Status-date: 2026-10-26
Superseded-by: n/a
Document class: evidence

# D1 — Shared task selection implementation

Owner decision: option A on 2026-10-26. PR #2650 continues the reviewed contract
without a second planning or administrative proposal PR. No release.

## Result and authority

`task_routes.py` is the single reviewed route source within the command manifest
authority. Schema 3 / metadata schema 2 binds commands and route schema 1 together
in the manifest identity. Schema 2 keeps the historical command-only identity.
Legacy raw/tag payloads and sorting remain unchanged; unsupported intent schemas
and identity mismatch stop with INVALID_INPUT. The original proposal YAML and
its design simulation remain archived review fixtures, not runtime inputs.

The pure finite evaluator serves the existing command selector. The thin CLI
adapter observes local root/HEAD, configured origin default branch and Git status.
PR observation requires explicit opt-in and reads only the named origin PR;
number/repository/head bindings are checked. No search, fetch, mutation or
caller-supplied fact file fills gaps. Observation races invalidate the result.

The generated task guide and tasks.json share that manifest export. Eleven
intents are mapped; all other commands remain explicitly unassigned in this
bounded matrix and discoverable in the complete and diagnostic catalogs.
Selection never constructs argv or grants execution authority. Release run is
guarded even without execute; existing run state or a local version tag blocks
the fresh-release intent. Remote absence is not asserted; release gates remain
mandatory. Network-read metadata conservatively covers the optional PR read.

## Validation

- Fixed implementation commit 485037a8: full local suite, 4237 passed, 545 existing
  warnings, rc 0; 500.07 seconds. Earlier dirty-source audit failures were expected
  pinning refusals; the suite was restarted on the committed source, not weakened.
- Final focused runtime/release-content checks: 76 passed, rc 0, including malformed-envelope and malformed-contract regression cases before any observation.
- Ruff, check-docs, direction validation, doctor and canonical Pages-fallback
  build passed. Doctor retains the existing 76 report-only lifecycle warnings.
- Local browser inspection confirms eleven generated task cards, prerequisites,
  unassigned-command count and links to complete/diagnostic reference. Narrow
  layout uses wrapping text; no physical-phone test was performed.
- Final CI and merge/handoff identifiers are obtained from PR #2650 and the Kit
  closeout output, rather than precomputed here.

## Limits and remaining work

No paid model pilot or consumer-workspace run was performed. Passing structural
checks does not establish semantic adequacy for every task, universal mutation
protection, or context-token savings. W1 navigation UX/mobile acceptance and W3
command-detail pages remain separate planning steps. The shipped 1.1.6 wheel is
not retroactively changed by this source-tree feature. Archived findings, release
receipts and offline observations retain their original evidence scope.
