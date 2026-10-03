# KIT-GF-032 slice E — `release ready` in an external workspace

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-032, observation GF-E041). Slices A–D are recorded in this directory.

## Retest before this slice

Kit main `c912afe0` (slices A–D merged: #2350, #2352, #2354, #2356), sandbox clone of agp-Cockpit main `3762b8a` with `publication: none`. `release ready --version 0.1.0` was still BLOCKED by the standard-error scan:

1. The fresh-context check reported `outbox_missing` and `latest_handoff_report_missing`. In an external workspace the carriers live in excluded runtime paths (`.agentic/transfer/outbox`, `.agentic/state/handoff/transfer_handoff_reports`), and `release ready`'s own sync-main (normalize-session) removes them. After `transfer refresh-llm-context-carriers`, a standalone scan passes this step.
2. `release-notes-generate` blocked six unclassified PR items. PR bodies in that workspace carry no `release-note-category:` line, and merged PR bodies cannot be reclassified without a remote write.
3. The scan wrote `tmp/release-<n>-summary-lines.json` into the workspace root. That path is not ignored there, so the next sync-main stopped on `external_dirty_worktree`.

The sandbox also showed a fourth gap in the private chain: `release prepare --write` ran the Kit's `site/scripts/build.py`, which does not exist in the workspace.

## Change

- `release ready` runs `transfer refresh-llm-context-carriers` after sync-main, in external manifest workspaces only. The Kit's self-hosting run is unchanged.
- The release-oriented standard-error scan writes the summary lines to the workspace temp root, `load_workspace(root).tmp_file(...)`. That is `tmp/` in the Kit and `.agentic/tmp` in an external workspace, the same path that `release prepare` already used.
- `build_release_notes_report` uses a private fallback under `publication: none`:
  - an item that no PR category, label or subject heuristic classifies is listed under Changed;
  - its confidence is `fallback` and its evidence records `unclassified_private_fallback`;
  - the report gets a warning, also listed under Known Issues, and validation passes;
  - every other policy, and a workspace without a manifest, keeps blocking.
- `release prepare --write` records the docs-pages fallback refresh as skipped when an external workspace has no `site/scripts/build.py`; in the Kit a missing script stays a failure.

## Evidence

Kit branch editable, same sandbox. The sandbox's local commit was given PR evidence and a successor-package refresh, which mirrors a cockpit lifecycle.

- `release ready --version 0.1.1 --json` → PASS for all five steps: sync-main, refresh-llm-context-carriers, standard-error-scan, doc-lifecycle-release-review and release-status.
- `release prepare --version 0.1.1 --write --json` → PASS, with docs-pages-fallback-refresh skipped. It changed `pyproject.toml`, `CHANGELOG.md` and Kit projections.
- After a simulated merge and a committed `.agentic/release/ENABLE_LIVE_PUBLISH`:
  - `release-publish --version 0.1.1 --execute --allow-execute --json` created annotated tag `v0.1.1` at HEAD and pushed only that tag to the sandbox origin;
  - a rerun reported both as already present at HEAD.

## Regression

`tests/test_release_external_ready_carriers_notes.py` (9 tests) covers:

- the carrier refresh after sync-main, and its absence without a manifest;
- the summary-lines path in `.agentic/tmp`;
- the private fallback and its dependence on the publication policy;
- the skipped and the regular docs-pages fallback step, and that a Kit-style layout never skips it.

Five of these tests fail on Kit main `c912afe0`.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its retest with a released Kit.
