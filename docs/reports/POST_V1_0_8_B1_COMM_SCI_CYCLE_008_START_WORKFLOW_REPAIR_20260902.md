# Post v1.0.8 B1 Comm-SCI Cycle 008 Start Workflow Repair

Status: implemented-local-retest-pass
Date: 2026-09-02
Scope: Kit-owned workflow defect found before Comm-SCI Cycle 008 product mutation

## Context

After v1.0.8 publication and the Cycle 007 closeout, Comm-SCI Cycle 008 was
started from the current external integration branch:

- target repository: `vfi64/Comm-SCI-Control-private`
- target base: `origin/feature/ui-access-levels-v2`
- target base head: `ea21b3a336fd1c54e83e5264bf61142c4d23245c`
- intended work branch: `codex/b1-cycle-008-app2-seams`
- starting seam baseline: `legacy_seams_remaining=44`

No Comm-SCI product mutation was made before this Kit defect was found.

## Defect

`agentic-kit work start --from-ref origin/feature/ui-access-levels-v2` invoked
`transfer sync-main` without passing or respecting the selected non-main start
ref. The target worktree was left on `main`, and the workflow blocked before the
Cycle 008 branch could be safely used.

The same retest also exposed that older external workspaces without a
versioned `.agentic/rule_ack/` ignore line could still show
`.agentic/rule_ack/current.json` as raw Git dirty state after
`rules acknowledge`.

## Root Cause

The human workflow adapter treated `work start` as a main/post-merge startup
sequence regardless of `--from-ref`. The lower-level `branch-create` wrapper
also required switching to the start point before creating a branch, which made
remote-tracking refs and tags a weakly tested contract.

Rule acknowledgement persisted valid local capability state, but older external
workspaces had no automatic local exclude repair for that runtime path.

## Repair

- `work start` now distinguishes main start refs from non-main start refs.
- Main start refs keep the sync-main, rules-acknowledge, post-merge-check,
  repo-status, branch-create sequence.
- Non-main start refs fetch refs, acknowledge rules, skip the post-merge check
  as a pre-PR gate, run repo-status, and then create or switch to the work
  branch.
- `branch-create` now accepts any start point that resolves to a commit,
  including tags and `origin/...` refs, without switching to that start point.
- `rules acknowledge` writes an idempotent local Git exclude for
  `.agentic/rule_ack/`, preserving runtime state without product dirty state.

## Retest Evidence

Focused local tests:

- `python -m pytest -q tests/test_human_workflows.py tests/test_transfer_repo_actions.py tests/test_rule_ack.py`
- result: 146 passed
- `ruff check` on touched source and test files: PASS

Real external retest:

- worktree: `/private/tmp/comm-sci-b1-cycle-008-v2`
- command outcome: `work start` PASS
- retained branch: `codex/b1-cycle-008-app2-seams-v2`
- retained head: `ea21b3a336fd`
- raw Git status after local exclude update: clean
- `transfer repo-status --json`: PASS with empty stdout

Fresh detached-start external retest:

- worktree: `/private/tmp/comm-sci-b1-cycle-008-start-retest.85eMmK`
- start point: `origin/feature/ui-access-levels-v2`
- created branch: `codex/b1-cycle-008-start-retest-20260902`
- command outcome: `work start` PASS
- branch-create argv: `git switch -c codex/b1-cycle-008-start-retest-20260902 origin/feature/ui-access-levels-v2`
- retained head: `ea21b3a336fd`
- raw Git status after branch creation: clean
- local Git exclude covers `.agentic/rule_ack/current.json`

## Brownfield Impact

This is a Kit workflow standard defect, not a Comm-SCI product defect. Cycle 008
must continue only after the Kit repair is merged and the target cycle is
restarted from a fresh worktree on the external integration branch.
