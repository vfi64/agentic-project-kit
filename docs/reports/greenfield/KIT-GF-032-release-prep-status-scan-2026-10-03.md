# KIT-GF-032 slice B — release-prep, release-status and the release scan in external workspaces

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-032). Retest after slice A: `release ready --version 0.1.1` in a clone of agp-Cockpit with `publication: none` was BLOCKED by nine standard-error-scan steps, most of them Kit self-hosting assumptions.

## Result (slice B)

- `release-prep` (`prepare_release_state`): an external workspace updates only its own version anchors (slice A): `pyproject.toml`, a literal package `__version__` (quotes kept), `CITATION.cff` when present or required by a Zenodo policy, status files with a `Current version:` line, and a `## vX.Y.Z - date` CHANGELOG section (re-runs replace it; a first release lands after an Unreleased section). No README marker, no Zenodo pending line without a Zenodo policy.
- `release-status`: the package version comes from the workspace anchors (an indirect `__version__` leaves `pyproject.toml` as authority, no `package_init_version_mismatch`); CITATION is required only when present or Zenodo is configured; without a Zenodo policy the DOI steps are not applicable and the lifecycle ends with the tag; under `publication: none` remote lookups are skipped even with `--include-remote`.
- `transfer standard-error-scan --before-release`: in an external workspace `command-reference-check` (runs the Kit's own test file), `audit-doc-currency` (Kit DOI/handoff currency) and `audit-planning-docs-consolidation` are recorded as skipped, and only existing release test paths are passed to `command-composition-check`.

Retest result in the agp-Cockpit clone: the scan blockers fell from nine to four. Remaining: `docs-audit` (Kit document-lifecycle headers applied to external planning documents despite `doc_lifecycle: warn` — slice C), `release-notes-generate` (unclassified items: the workspace's pull requests carry no `release-note-category:` line or label — a workspace convention), and `post-merge-check` / fresh-context checks that depend on the clone's transfer state.

## Not in this slice

Documentation and currency audits scoped to the workspace (slice C) and the private tag route under `publication: none` (slice D).

## Regression evidence

`tests/test_release_external_workspace.py` (agp-Cockpit shape): release-status without init/citation blockers and without remote lookups, lifecycle ending with the tag; release-prep touching only workspace files, dry run, literal package version, first release and re-run, Zenodo policy requiring CITATION; the scan skipping the self-hosting checks. Kit self-hosting behaviour is unchanged (existing tests).

This slice does not set `VERIFIED_FIXED` in the agp-Cockpit ledger.
