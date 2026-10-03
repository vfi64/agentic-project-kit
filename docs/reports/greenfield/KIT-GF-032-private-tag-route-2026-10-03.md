# KIT-GF-032 slice D — Private tag route for external release publishing

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-032), read from `origin/main` commit `3762b8aa2b3d7850dae2b75f7e31ce0e678c5221`. Earlier KIT-GF-032 slices A–C are recorded in this directory.

## Change

`publication: none` no longer disables `release-publish` completely. It now keeps the release preparation and metadata authority checks, then plans the private release path expected by external workspaces: an annotated release tag and `git push origin <tag>`.

Live execution remains fail-closed. It still requires `--execute`, `--allow-execute`, and `.agentic/release/ENABLE_LIVE_PUBLISH`. When enabled, the private path creates or reuses an annotated local tag at the current HEAD and pushes only that tag. It does not create or inspect a GitHub Release, run `post-release-check`, publish to PyPI, or query Zenodo.

The tag checks resolve the commit target of annotated tags locally and remotely, so rerunning the command is idempotent when the existing tag already points to the release commit and blocks when a tag points elsewhere.

## Regression

`tests/test_release_publish_orchestration.py` covers the external-workspace private route:

- `publication: none` dry-run plans the annotated tag and tag push while skipping docs-audit, command-reference, and GitHub Release calls.
- live execution with the explicit capability creates an annotated tag and pushes that tag only.
- `--json` on the changed route remains pure parseable JSON.
- existing public release-publish behavior remains covered, including idempotent tags, remote tag mismatch blocking, and GitHub release creation.

Focused validation in this slice: `17 passed` for `tests/test_release_publish_orchestration.py`.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
