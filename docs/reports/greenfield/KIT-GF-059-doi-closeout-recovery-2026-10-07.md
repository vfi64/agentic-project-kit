# KIT-GF-059 — Supported failed DOI closeout recovery

Source: agp-Cockpit package 2 task, read 2026-10-07; ledger repository `origin/main` commit `382d00da48c617b516b758f57f1821611cc8db99` (read-only).

## Finding and repair

Confirmed: failed D4 was absent from finished steps while D2 remained finished, leaving the owner with an inspection message and no regeneration route. `release_run` now recognizes both recorded failures and legacy D4 step evidence. A read-only rerun offers the signature-bound D2R gate; a mismatch performs no governed mutation.

The focused `release_run_recovery.DoiRecovery` composes existing closeout, work-start, rule acknowledgement, commit, push and PR-completion routes. It uses a replacement branch from current main to keep the repaired closeout implementation available throughout retries. Completed actions are persisted separately. The existing DOI branch remains intact. The new thin CLI route `transfer pr-close-superseded` calls `pr_superseded_close.close_superseded_pr`, verifying the source head and merged replacement before closing the original PR.

## Contract and tests

The signature binds version, source branch/PR/head, replacement branch, current commit, regenerated metadata paths, bounded write scope and verified DOI facts. Temporary workspace tests cover legacy blocked D4, gate offer, Kit-only mutation routes, wrong/stale signature, dirty starts, resumable failed push, merged-replacement verification, idempotent close, and pure CLI JSON. The CLI argv regression includes all new routes. Remote effects are classified for the new route (KIT-GF-023/025).

A failed D4 that created only a local DOI branch is also recoverable: its branch head replaces the source PR head in the gate, and the close-source action is omitted. The manifest and ACK projections were regenerated through Kit commands; current ACK is `294d5185ed36`.

## External retest and risks

From clean main run `agentic-kit release run --version 1.0.19 --json`, inspect D2R, then execute exactly its signed `next_action`. The owner performs this live recovery; this slice does not run release execution. The replacement PR and its handoff must merge before #2421 closes; final D5 must report `current_verified`. Unexpected dirt and source-head drift block. A crashed subprocess may have completed a remote effect before its result was persisted; existing Kit PR discovery and an already-closed source make retry safe. No tag, package publication or Zenodo publication is part of D2R.
