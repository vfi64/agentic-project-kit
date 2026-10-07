# KIT-GF-058 — DOI closeout changelog section

Source: agp-Cockpit package 2 task, read 2026-10-07; ledger repository `origin/main` commit `382d00da48c617b516b758f57f1821611cc8db99` (read-only).

## Finding and repair

Confirmed: `post_release_closeout._metadata_updaters.update_changelog` inserted before the first version heading, placing facts in Unreleased. The updater and pending-marker remover now share a section matcher for the exact version, bounded by the next level-two heading. Existing facts outside that section do not suppress the correct insertion. Unreleased and historical release sections are preserved.

## Regression

`test_doi_closeout_inserts_facts_in_version_section_below_unreleased` checks the 1.0.19 shape, current-state DOI facts, historical preservation and idempotency. `test_doi_fact_outside_version_section_does_not_suppress_closeout` covers the previously produced misplaced fact. Tests run in temporary external fixtures with no live publication.

## External retest and limitations

Regenerate 1.0.19 closeout using the supported recovery introduced by KIT-GF-059. Both DOI facts must appear inside v1.0.19, and repeating closeout must produce no further changes. Previously misplaced prose in Unreleased is preserved; no manual DOI correction or release action occurs in this slice.
