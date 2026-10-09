# KIT-GF-064 — Kit release changelog consumption

Source: vfi64/agp-Cockpit main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read-only on 2026-10-09.

## Finding and repair

The self-hosted Kit release path inserted a version section without consuming its
Unreleased entries. External releases already used the lossless GF-060 helper.
The Kit path now calls that same helper only when creating a version section.
Matching uses whitespace-normalized text and occurrence counts; unmatched entries
and historical sections remain unchanged. Refreshing an existing version never
consumes identical future entries. The CLI and dry-run changed-path contract stay
unchanged, so no additional state machine or renderer is needed.

The existing Unreleased backlog was reviewed against v1.0.20 and v1.0.21. Entries
for 022, 048, 049, 052, 053, 054, 055/056, 057, 058, 059, 060 and 061 already
carried by those releases were removed once. Only the unreleased repairs for
035, 023, 065 and this finding remain. This cleanup uses the recorded release
sections; runtime matching does not guess equivalence from finding numbers.

## Regression and expected external retest

Both tests in `tests/test_kit_release_changelog_consumption.py` fail before the
patch and pass after it. A self-hosted Kit fixture verifies dry-run reporting
without writes, exact consumption, preserved history, byte-stable reruns,
unmatched entries and duplicate future entries. Existing external GF-060 tests
remain covered: 17 focused tests and 3306 full-suite tests pass (509 warnings).
Ruff, check-docs and doctor pass.

Release 1.0.22 should consume all four remaining entries when those exact lines
are supplied as summaries, leaving an empty Unreleased heading. After adoption,
the Cockpit should repeat its external release dry/write/rerun test and confirm
that unrelated entries remain. No Cockpit ledger is modified; VERIFIED_FIXED is
reserved for its own retest.

## Compatibility and limits

Summary matching remains deliberately exact after whitespace normalization.
Reworded summaries leave their original entries in Unreleased. No CLI options,
remote-effect declarations or manifest ACK change: `d75e2e2a30bd`.
