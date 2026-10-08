# KIT-GF-048 — Work finish PR metadata

Source ledger: `vfi64/agp-Cockpit`, `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read at `origin/main` commit `382d00da48c617b516b758f57f1821611cc8db99`. The source workspace remains unchanged. Implementation and validation: 2026-10-08.

## Finding and repair

The human finish route generated a fixed PR body with no release category. It now accepts `--body`, `--body-file` and `--release-note-category`. Focused core module `work_finish_metadata.py` validates the description before any subprocess, deduplicates consistent category markers, and places the canonical marker first so long descriptions remain classifiable. Both full merge and review-only routes carry the same body; review-only handoff markers remain appended.

Unreadable UTF-8 files, simultaneous body options, unknown categories and conflicting markers return BLOCKED before writes. Dry-run JSON exposes `pr_body`. Defaults remain compatible. The route retains its existing conservative remote-effect declaration for push, PR and merge operations.

## Regression and external retest

`tests/test_work_finish_metadata.py::test_work_finish_category_reaches_pr_and_release_notes` exercises both CLI modes from an external temporary workspace, captures the actual PR body passed to the existing route and feeds it to the real release-notes generator with fake GitHub metadata. The result is Fixed with PASS validation even after a 50-line description. Negative CLI cases prove pure JSON and no subprocess execution; core tests cover duplicate markers and defaults.

Cockpit should repeat its ledger regression with a released package: finish a PR using `--release-note-category Fixed`, then generate release notes with GitHub metadata and verify Fixed classification. Only Cockpit sets VERIFIED_FIXED. No release or live publication is included in this slice.
