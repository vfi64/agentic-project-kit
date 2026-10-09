# KIT-GF-055 follow-up — C3 visibility and safe resume

Source: vfi64/agp-Cockpit, docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json,
main commit `afea4be654b5bed910754d05273d18afae79e2f7`, read-only on 2026-10-09;
additional maintainer instruction from 2026-10-08 to fix the 1.0.20 C3 incident
in the next patch. This is a follow-up to dispatch identification, not a new ID.

## Finding and repair

The 1.0.20 dispatch at 13:06:09.780519 UTC became visible as run 37781745637
at 13:06:12 UTC. One immediate lookup saved an empty run ID and blocked resume.
The focused release_run_dispatch module records intent atomically before the API
call and dispatches against the release tag. It captures a pre-dispatch inventory
to reject old runs within GitHub's whole-second timestamps. Identification checks
workflow, event, head and creation time with six attempts two seconds apart.
Ambiguous or missing identity blocks. Resume searches the recorded dispatch,
including after an uncertain API response, without sending another dispatch.
Legacy states without sufficient identity block. Every lookup is logged.

## Regression and external retest

External fixture tests in tests/test_release_consent_dispatch.py verify delayed
visibility, state persisted before dispatch, bounded timeout, search on resume,
one dispatch only, stale/wrong-head/wrong-event rejection and ambiguity blocking.
Retest against a disposable workspace and non-publishing workflow with delayed
visibility; verify the saved run identity and a single workflow dispatch.
No production release, tag or package publication was executed for this patch.
No Cockpit ledger was changed; the workspace owns VERIFIED_FIXED.

## Boundary

An uncertain dispatch deliberately remains recorded even if the API reports an
error; inspection is safer than automatically repeating a possible remote effect.
Concurrent release runner processes are not supported by this slice. Logs and
blocked state retain the evidence required for diagnosis.

## Slice validation

Full local suite: 3224 passed, 506 existing warnings. Final focused regressions:
75 passed. Ruff, check-docs and doctor PASS; doctor has report-only lifecycle
warnings. Generated command manifest, entrypoints, site and documentation registry
were reconciled. Remote CI and merge identifiers are reported by the Kit closeout.
