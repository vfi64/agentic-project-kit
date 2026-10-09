# KIT-GF-060 — Consume released Unreleased entries

Source: vfi64/agp-Cockpit, docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json,
main commit `afea4be654b5bed910754d05273d18afae79e2f7`, read-only on 2026-10-09.

## Finding and repair

External release-prep inserted the version section but left released bullets in
Unreleased. A focused release_changelog module now removes exactly the matching
bullet occurrences on creating the release section. It preserves the heading,
unmatched text and historical releases. Wrapped entries match normalized
whitespace. Existing release refreshes do not consume future duplicate entries.
First-release spacing is canonical on the first write and subsequent reruns.
The dry run reports CHANGELOG.md and makes no write. No remote effect is added.

## Regression

`tests/test_release_changelog_consumption.py` builds a disposable external Git
workspace. The real release-prep CLI reads three entries via summary-lines-from,
previews without writing, writes one dated section, leaves empty Unreleased and
is idempotent. Real preparation evidence and the metadata authority gate pass
after the fixture commit. Release-publish dry-run passes with real local CLI
checks and simulated remote observations. Additional tests preserve unmatched,
wrapped and duplicate future entries.

## External retest and boundary

Repeat with the released Kit in a disposable Cockpit clone and the same summary
artifact; confirm empty Unreleased, one dated version section, stable rerun and
PASS publish dry-run after the preparation merge. No Cockpit ledger was changed;
VERIFIED_FIXED remains a workspace decision. Changelog consumption is limited
to external workspaces and explicitly supplied matching summaries.

## Slice validation

Full local suite: 3224 passed, 506 existing warnings. Final focused regressions:
75 passed. Ruff, check-docs and doctor PASS; doctor has report-only lifecycle
warnings. Generated command manifest, entrypoints, site and documentation registry
were reconciled. Remote CI and merge identifiers are reported by the Kit closeout.
