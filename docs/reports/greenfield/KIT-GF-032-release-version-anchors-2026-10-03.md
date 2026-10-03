# KIT-GF-032 slice A — Release version anchors of external workspaces

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-032; observation GF-E038 from the Kit 1.0.14 retest).

## Problem

In an external workspace with `publication: none`, `release-check` failed on files that exist only in the Kit's own repository: `src/agentic_project_kit/__init__.py`, `CITATION.cff`, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md` and the README marker ``Version `x` ``. The same list was hard-coded in `release-plan` and in the release commit integrity check of `release-publish`.

## Result (slice A)

`agentic_project_kit/release_version_sources.py` is the single source of the release version anchors:

- Self-hosting layout (the Kit package exists, or a legacy root without a workspace manifest): the previous anchor set, unchanged.
- External workspace (workspace manifest, no Kit package): `pyproject.toml`; a literal package `__version__` (`__init__.py`, `version.py` or `_version.py` of the package named in `pyproject.toml`) only where one is declared; `CHANGELOG.md` when present (Kit headings and Keep-a-Changelog headings); `CITATION.cff` when present or required by a Zenodo publication policy; `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` only when they carry a `Current version:` line.

`release-check`, `release-plan` and the release commit integrity check use these anchors.

## Not in this slice

Release preparation (`release-prep`, `release prepare`), `release ready`/`release-status` (first release without a previous tag, version consistency), the documentation and currency audits, and the private tag route remain open in KIT-GF-032 (slices B–D).

## Regression evidence

`tests/test_release_version_sources.py` uses manifest-bearing external workspaces shaped like agp-Cockpit (indirect `__version__`, own CHANGELOG, no CITATION): release-check passes without Kit files, still fails on the workspace's own stale files, honours a literal package version, Keep-a-Changelog headings without prefix false positives, status files only with a version line, the Zenodo policy, and the integrity check of `release-publish`. The existing release tests are unchanged except the source-text contract test, which now reads the anchor module.

This slice does not set `VERIFIED_FIXED` in the agp-Cockpit ledger; that status remains owned by the external workspace retest after a Kit release.
