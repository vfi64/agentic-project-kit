# Post-v1.0.8 Successor Projection Volatile Boundary

Status: implemented local retest pass  
Date: 2026-09-05  
Kit branch: `codex/successor-projection-volatile-boundary`  
Machine-readable companion:
`docs/reports/POST_V1_0_8_SUCCESSOR_PROJECTION_VOLATILE_BOUNDARY_20260905.json`

## Scope

This report records a bounded repair for `B1-KIT-011` / `KIT-GF-011`.

The Greenfield evidence showed that Kit-generated tracked successor handoff
projections could become dirty after closeout and then block the next supported
lifecycle path. The blocked commands were not failing because of user product
changes; they were reclassifying Kit-owned generated continuation projections as
product dirtiness.

This slice does not remove the committed successor package model and does not
claim that all mixed handoff/status/report refresh-loop work is closed. It
narrows one concrete failure path: stale or freshly re-rendered latest successor
projection files are now handled by the existing known-volatile recovery model.

## Root Cause

The repository already had a known-volatile transfer recovery mechanism for
runtime carriers such as transfer inbox/outbox files, rule acknowledgement, and
transfer report artifacts.

The successor handoff package and canonical prompt projections were missing from
that model:

- `restore-known-volatile` did not restore tracked successor package projection
  files or remove untracked regenerated ones;
- `normalize-session` used a static list instead of the workspace resolver, so
  namespace paths in manifest-bearing external workspaces were not reliably
  recognized;
- `post-merge-complete` classified dirty successor projections as product paths;
- `post-merge-settle` inspected local dirtiness but did not run the existing
  known-volatile cleanup when all dirtiness was generated/report-like state.

## Repair

The repair stays inside the existing transfer recovery machinery:

- exact latest successor package files are now named as known generated
  projections for both the legacy self-hosting paths and manifest workspace
  namespace paths;
- canonical generated handoff prompt projections are likewise classified as
  known generated projections;
- `restore-known-volatile` resolves the same files through `Workspace`, so path
  overrides and external manifest workspaces use their configured handoff roots;
- `normalize-session` uses the dynamic workspace-aware volatile path list;
- `post-merge-complete` classifies these paths as generated/report artifacts
  instead of product changes;
- `post-merge-settle` now uses the same bounded known-volatile preflight cleanup
  when the local worktree contains only generated/report artifacts.

The allowlist is exact-file based. It does not make `docs/handoff/`, `.agentic/`,
`docs/reports/`, `docs/STATUS.md`, or `docs/handoff/CURRENT_HANDOFF.md`
generally volatile.

## Retest

Focused validation:

- `python -m pytest -q tests/test_volatile_paths.py tests/test_transfer_normalize_session_contract.py tests/test_transfer_startup_hardening_commands.py tests/test_transfer_post_merge_complete_command.py tests/test_transfer_post_merge_settle_command.py`
  -> 77 passed.
- `python -m pytest -q` -> 3031 passed, 481 warnings.
- `ruff check .` -> PASS.
- `agentic-kit check-docs` -> PASS.
- `agentic-kit direction validate --root .` -> PASS, 0 findings.
- `agentic-kit audit-command-manifest --json` -> PASS, 0 findings.
- `agentic-kit workflow-guard check` -> PASS.
- `agentic-kit doctor` -> Overall PASS, with 76 document-lifecycle
  report-only findings.

The focused tests cover:

- exact successor projection path matching;
- non-product dirty-state filtering in `normalize-session`;
- `restore-known-volatile` restoring tracked successor projections;
- `post-merge-complete` classifying successor projections as generated/report
  artifacts;
- `post-merge-settle` using known-volatile cleanup before running the lifecycle.

## Greenfield Finding Impact

| Finding | Impact |
| --- | --- |
| KIT-GF-011 | Locally repaired for the concrete stale successor projection path that blocked `restore-known-volatile`, `normalize-session`, and `post-merge-settle`. |
| B1-KIT-011 | Improved but not closed. The broader goal of reducing all mixed handoff/status/report refresh loops still requires release-package and external Greenfield retest evidence. |

## Boundary

This report is checkout evidence only. It does not claim released PyPI behavior.
Released-package confirmation must wait until a later published version contains
this change and a new external retest validates it.
