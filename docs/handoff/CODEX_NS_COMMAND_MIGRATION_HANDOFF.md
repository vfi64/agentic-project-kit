# Codex NS Command Migration Handoff

Status-date: 2026-06-17
Scope: classification-first migration of remaining meaningful `./ns` command semantics to the supported `agentic-kit` Python CLI surface.

## Closeout status after PR #1406

This Codex handoff has been fulfilled for the four classified command families. Do not restart the same migration loop unless a fresh scan finds an active runtime entrypoint.

Completed slices:

- PR #1398: classified `ns dev`, `ns go`, `ns up`, and `ns upload`.
- PR #1400: added `agentic-kit dev local-feature-gate` and moved release prep/gate away from the old `./ns` compatibility route.
- PR #1402: migrated the old `ns go` dirty-branch guard into `agentic-kit workflow go`.
- PR #1404: removed the obsolete `ns_up_pr_completion` route; supported replacement is `agentic-kit transfer pr-complete`.
- PR #1406: removed the active `./ns upload` shortcut; `ns-menu` uses `agentic-kit workflow upload`.

Next work must be a fresh slice based on current `main`, not a continuation of this handoff.


## Current Verified Start State

The mandatory Codex start block completed successfully.

- Start log: `tmp/codex-ns-migration-start-20260617-162611.log`
- Start result: `RESULT=CODEX_NS_MIGRATION_START_DONE`
- Start return code: `0`
- Branch: `main`
- HEAD: `7ae57568a83d3258c97ad830f26d954058086d1b`
- origin/main: `7ae57568a83d3258c97ad830f26d954058086d1b`
- Worktree: clean at start
- `agentic-kit transfer post-merge-check`: PASS / NOOP
- `agentic-kit transfer repo-status`: PASS
- `agentic-kit docs-audit`: PASS

The required diagnostic command exists and produced fresh evidence:

- Command: `agentic-kit transfer diagnose-removed-ns-commands`
- JSON evidence: `tmp/ns-migration-start-evidence.json`
- Markdown evidence: `tmp/ns-migration-start-evidence.md`

This file was added after an explicit missing-file investigation:

- Status log: `tmp/codex-ns-migration-handoff-status-20260617-162942.log`
- Result: `RESULT=CODEX_NS_HANDOFF_STATUS_DONE`
- Finding: no current remote branch, PR, or visible commit contained `docs/handoff/CODEX_NS_COMMAND_MIGRATION_HANDOFF.md`.

## Non-Goals

Do not restore `./ns` as the supported command surface.

Do not begin product migration before a classification document is committed and merged.

Do not add broad shell compatibility logic when a thin Typer command and importable Python core can represent the behavior.

Do not bypass transfer, evidence, protected-file, release, or remote-mutation gates.

Do not manually edit generated reports as part of the classification slice.

## Migration Direction

The target supported interface is:

```bash
./.venv/bin/agentic-kit ...
```

All remaining meaningful old `./ns ...` semantics should either map to an existing `agentic-kit` command or become a real tested Python-backed `agentic-kit` command.

Every new command must follow the local architecture pattern:

- focused importable module under `src/agentic_project_kit/`;
- thin Typer adapter under the current CLI command structure;
- tests for core behavior;
- tests or smoke coverage for CLI/help/registration where appropriate;
- command-reference refresh when the CLI surface changes.

## Candidate Commands To Classify First

The first classification slice must classify these exact command families:

- `ns dev`
- `ns go`
- `ns up`
- `ns upload`

Fresh diagnostic evidence from the start run reported:

| command | old hits | new hits | main hits | removed/decreased |
|---|---:|---:|---:|---|
| `ns up` | 13 | 3 | 3 | True |
| `ns dev` | 12 | 8 | 14 | True |
| `ns go` | 12 | 1 | 7 | True |
| `ns upload` | 5 | 2 | 2 | True |

The classification must use repository-backed evidence, not command-name guesses.

## Required Classification Fields

For each candidate command, record:

- old definition with path and line evidence from `0.4.6`;
- old semantics;
- current equivalent `agentic-kit` command, if one exists;
- decision: migrate, document existing command, reject, or mark obsolete;
- proposed target command name;
- required tests;
- risks and compatibility concerns;
- whether a shared implementation core exists across candidates.

## Investigation Commands For Classification

Run these in one logged local block before drafting the classification document:

```bash
git show 0.4.6:ns || true
git show 0.4.6:ns-menu || true
git grep -n -E 'ns dev|ns go|ns up|ns upload|ns-dev|ns-go' 0.4.6 -- ns ns-menu tools src tests docs .agentic scripts bin || true
git grep -n -E 'ns dev|ns go|ns up|ns upload|ns-dev|ns-go' HEAD -- ns ns-menu tools src tests docs .agentic scripts bin || true
git diff --unified=80 0.4.6..0.4.8 -- ns ns-menu tools src tests docs .agentic scripts bin | sed -n '1,260p'
./.venv/bin/agentic-kit transfer diagnose-removed-ns-commands \
  --old 0.4.6 \
  --new 0.4.8 \
  --json-out tmp/ns-migration-evidence.json \
  --md-out tmp/ns-migration-evidence.md
```

## Initial Hints To Verify, Not Assume

`ns dev` likely relates to local feature-gate safety. Current code contains `src/agentic_project_kit/local_feature_gate.py`; tests intentionally guard against restoring `./ns dev` as a shortcut.

`ns go` may overlap with transfer/workflow continuation commands such as `agentic-kit transfer continue`, `agentic-kit transfer remote-next`, or `agentic-kit transfer run-and-log`. Verify old semantics before deciding.

`ns up` must be reconstructed from the old `0.4.6` definition. Do not infer upload or PR behavior from the name alone.

`ns upload` may overlap with transfer report publication, but no upload command may bypass evidence or protected-file lifecycle rules.

## First Allowed Product Slice

Only after this handoff file is present on `main`, create a separate classification branch.

Recommended classification target:

```text
docs/planning/NS_COMMAND_MIGRATION_CLASSIFICATION.md
```

The classification PR must be additive and must not implement command migration.

## Required Gates For Classification Slice

Minimum local validation before commit:

```bash
./.venv/bin/python -m ruff check docs/planning/NS_COMMAND_MIGRATION_CLASSIFICATION.md
./.venv/bin/python -m pytest tests/test_agentic_kit_command_reference_is_current.py
./.venv/bin/agentic-kit docs-audit
./.venv/bin/agentic-kit check-docs
./.venv/bin/agentic-kit doctor
./.venv/bin/agentic-kit transfer protected-diff-plan --label ns-command-migration-classification
```

If the classification changes the command surface, also run:

```bash
./.venv/bin/agentic-kit transfer command-reference-refresh
./.venv/bin/python -m pytest tests/test_agentic_kit_command_reference_is_current.py
```

## Stop Rule

If the classification uncovers multiple plausible target designs for a command, do not implement one silently. Record the alternatives and stop at the classification PR.

If protected-diff-plan blocks, stop and inspect the blocker before commit.

If a command would require changing release, transfer, or evidence lifecycle rules, treat that as an architecture decision and keep it outside the first migration slice.
