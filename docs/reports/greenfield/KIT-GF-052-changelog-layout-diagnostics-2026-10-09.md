# KIT-GF-052 — Precise release changelog diagnostics

Source: vfi64/agp-Cockpit, docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json,
main commit `afea4be654b5bed910754d05273d18afae79e2f7`, read-only on 2026-10-09.

## Finding and repair

Release-publish kept only bullet starts and reported that CHANGELOG.md would
change, hiding lost continuation lines and separated lists. The focused
release_changelog module now diagnoses unsupported target-release lines with
version, line numbers, type and bounded excerpts (20 examples, then a count).
The consistency check includes this diagnosis and preserves preparation JSON
errors instead of displaying the closing brace. External release preparation
rejects unsupported existing target sections before metadata writes. Multiline
summary arguments also block before preparation, with their argument index.

The supported canonical layout remains one list of one-line bullets. This is the
explicit diagnostic/early-rejection repair permitted by the finding. It does not
silently flatten or remove semantic text. Only the target version is checked;
historical releases and Unreleased remain outside this layout validation.

## Regression

tests/test_release_changelog_diagnostics.py uses disposable external workspaces
and the real CLI. A wrapped entry names its continuation line in the publish
consistency blocker; a one-line fixture passes. Write and dry-run tests verify
continuations, paragraphs and second lists block without changing any file.
Additional tests reject multiline summaries, expose JSON errors, bound detail
size, and leave other release versions alone.

## Expected external retest and risk

Retest the released Kit in a disposable Cockpit clone: wrap a target-version
bullet, confirm the exact line diagnosis, restore its canonical one-line layout
and confirm the publish dry run passes. Existing malformed target sections now
require an explicit reviewed correction before external preparation proceeds.
No command options or remote effects change; manifest ACK remains
`COMMAND_MANIFEST_ACK e272fbfc980c`. No release, tag or publication was performed.
No Cockpit ledger was changed; VERIFIED_FIXED remains a workspace decision.

## Slice validation

Full local suite: 3235 passed, 506 existing warnings. Focused regressions:
60 passed. Ruff, check-docs and doctor PASS, with existing report-only
lifecycle warnings. Documentation registry reconciled.
