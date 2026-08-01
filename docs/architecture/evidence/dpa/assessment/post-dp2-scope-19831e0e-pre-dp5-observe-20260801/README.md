# DPA Post-DP2 Scope Assessment Before DP5 Observe

Status: `POST_DP2_SCOPE_ASSESSMENT_RECORDED`

Validation ref: `19831e0e862e4da5e61ca1311dea0796250c15d9`

This package records the current post-DP2 assessment before the DP5 observe
stage record is selected.

The result keeps DP2 implementation at `100%` for the selected self-hosting
scope, keeps bounded DP3/DP4 adjudication accepted, and records
`DP5_NOT_COMPLETE` with observe, warn, block-new and strict still blocked.

It is rollback evidence for the DP5 observe stage: without the stage record, the
assessment returns to the pre-DP5 blocked state.

## Files

- `results.json` - machine-readable pre-observe post-DP2 assessment result.
