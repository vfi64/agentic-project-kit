---
artifact_type: evidence
status: active
---

# Local upstream merge lifecycle

PR #2658 could not receive merge CI because its documentation additions conflicted
with newer main. The Kit had a rebase-start route and a conflict-file staging
route, but no safe completion route. A rebase would additionally require rewriting
an already published branch. This repair instead adds a local merge lifecycle.

## Bounded implementation

`transfer merge-upstream` previews a start, continue or abort action. Its approval
signature binds branch, HEAD, exact target, worktree status, index content and
merge message. Execution rechecks under the existing workspace mutation lock.
The CLI also requires the existing rules-confirmed capability for every execute,
including abort. Rule failures are not bypassed, even during recovery.

Start never commits automatically. It preserves conflicts and reports CONFLICT,
or stops as READY_TO_COMMIT. A new preview and approval are required to continue
after resolution. Abort discards explicitly reviewed tracked merge progress and
preserves untracked files. Already integrated start is NOOP. There is no fetch,
push, GitHub merge, rebase or force push in this route. Existing rebase behavior
and conflict-resolution generators are unchanged. Git hooks remain enabled.

The Git operation state is authoritative; no parallel state schema, new dependency
or DCO framework is introduced. Core behavior is in a focused module and the CLI
is a thin adapter. Generated registries and handoffs still use their owners.

## Regression evidence

Before implementation the existing rebase tests passed (8); the eleven initial
new regression cases failed because the new route did not exist. After the
implementation, expanded core/CLI and inventory coverage plus the old rebase
tests passed: 24 tests. Real local Git fixtures cover conflict preservation,
index/head/upstream signature drift, dirty/protected/wrong branches, linked
worktrees, continuation, abort and untracked preservation. An explicit boundary
test verifies the rules-confirmed check before CLI execution.

The full local suite passed: 4295 tests, 545 warnings, 159.98 seconds with
`python -m pytest -q -n 4 --dist worksteal`. Focused lifecycle, inventory, rebase
and release-content coverage passed (44 tests); the generated D1 matrix tests
passed (38). The first full run identified its stale manifest identity; the
existing matrix renderer regenerated that projection without changing its test.
Lint, check-docs and doctor passed after canonical handoff regeneration.

The exact CI head is reported by the PR closeout. No release is
part of this repair. No private consumer identity or raw local paths are included.

## Exact-state safety follow-up

An additional isolated fixture found that late, unstaged resolution edits could
leave both status and index unchanged. The first abort preview fingerprint did
not capture their bytes. A reproducing regression failed before correction.
The plan now also hashes the unstaged binary diff, so a stale abort signature
blocks and preserves the late resolution. There are no new flags or effects.
The full follow-up suite passed: 4296 tests, 545 warnings, 346.92 seconds.
The 22 targeted lifecycle/rebase tests, lint, check-docs and doctor passed.
A non-editable candidate controller independently confirmed that changing the
unstaged resolution changes the abort signature. No safety check was skipped.
