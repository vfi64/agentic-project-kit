# KIT-GF-046 — work finish blocks its own handoff commit after the handoff refresh

Source: `vfi64/agp-Cockpit` ledger family KIT-GF-046 (GF-E062). Observed on 2026-10-05 in the owner's `work finish --branch codex/release-summary-line --execute` run (KIT-GF-045, #2389), whose branch changed the command manifest.

## Finding

`work finish --execute` acknowledges the rules before the work commit and after it (`rules-acknowledge-post-work-commit`), then runs `handoff-refresh` (`transfer chat-switch-complete --render-prompt`). When the branch changed the command manifest, the refresh rewrites handoff projections that carry the manifest ACK and belong to the rule snapshot (`docs/handoff/*`, `docs/reports/handoff-packages/latest/*`). The following `handoff-commit` (`transfer commit` of those projections) requires `rules_confirmed` and blocked with `dirty_worktree` and `snapshot_id_mismatch`; the work commit was already made, nothing was pushed, and the owner had to rerun `work finish` with the handoff paths.

## Reproduction

Disposable clone of `main` at `1b93d316` with a local bare origin: `work start --branch codex/rt46`, change one CLI help text, `commands sync-entrypoints --execute` (manifest sha `1a5c17347b35`), `work finish --execute` with all changed paths → BLOCKED at `handoff-commit` with exactly the reasons above. A manual `rules acknowledge` followed by the same `transfer commit` then passed, so `dirty_worktree` is a consequence of the missing acknowledgement, not a separate defect.

## Fix

`work finish` runs `rules-acknowledge-post-handoff-refresh` between `handoff-projection-status` and `handoff-commit` when the refresh changed handoff projections; a failed acknowledgement blocks before the handoff commit. Without projection changes the step is skipped and `handoff-commit` stays a no-op as before.

## Regression coverage

- `tests/test_human_workflows.py::test_work_finish_acknowledges_rules_after_handoff_refresh_before_handoff_commit`
- `tests/test_human_workflows.py::test_work_finish_blocks_before_handoff_commit_when_post_refresh_acknowledgement_fails`
- `tests/test_human_workflows.py::test_work_finish_skips_the_post_refresh_acknowledgement_without_handoff_changes`

The first two fail on `main` at `1b93d316` and pass with the fix. The reproduction above, repeated with the fix, passes `rules-acknowledge-post-handoff-refresh`, `handoff-commit`, `rules-acknowledge-post-closeout` and `push-current`; it stops only at `pr-create-complete` because the disposable clone has no GitHub remote.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest with a released Kit.
