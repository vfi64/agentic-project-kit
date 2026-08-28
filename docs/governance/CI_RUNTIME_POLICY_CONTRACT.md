# CI Runtime Policy Contract

Status: active

This contract governs runtime optimization for GitHub Actions. It is a
deterministic gate policy, not a confidence heuristic. No optimized path may
weaken safety, determinism, or evidence strength compared with the standard
serial full-suite fallback.

## Required Check Boundary

The branch-protection-visible `CI` workflow keeps the required `test` job. Gate
selection happens inside that job so a skipped optional job cannot stand in for
success.

The default mode is `FULL_CI`. Any missing, invalid, ambiguous, or unsafe input
selects `FULL_CI`.

## CI2 Pytest Parallel Shadow

`pytest-parallel-shadow` is a non-blocking GitHub Actions job. It runs
`python -m pytest -q -n 4 --durations=20` with a fixed worker count and
`continue-on-error: true`.

The serial full-suite fallback remains the required gate until repeated shadow
evidence proves parity with serial PASS. Shadow output is diagnostic evidence
for order dependence, shared-state leaks, live-repo collisions, marker
conflicts, and slow GUI/Tkinter isolation risk.

## CI3 Main-Push Tree Proof

Main-push CI reduction is allowed only with a tree equivalence proof:

- final main tree SHA is present;
- tested PR integration tree SHA is present;
- both tree SHAs match;
- successful PR checks are proven;
- no workflow, code, test, release, governance, architecture, manifest, or site
  path changed.

If any condition is missing, `main_push_tree_proof` selects `FULL_CI`. Direct
main pushes, stale base, unknown merge method, failed checks, missing checks, or
unsafe changed paths must not skip the full suite.

The current workflow records the classifier result but does not claim a
tree-proof reduction until those proof inputs are wired.

## CI4 Admin Refresh Light CI

`admin-refresh-light` is allowed only for administrative handoff refresh PRs
whose diff exactly matches the generated handoff allowlist for one source PR and
whose successor package validation is `PASS`.

The allowlist contains only generated handoff state, canonical handoff prompt
projections, latest successor package files, and the matching
`docs/reports/terminal/post-pr<N>-successor-chat-handoff.md` report. Extra
paths, missing paths, invalid paths, manually edited product files, or
non-PASS validation select `FULL_CI`.

Accepted refresh PRs run handoff check, post-merge refresh status, successor
package validation coverage, protected-diff-plan coverage, doc-registry
reconcile, doc-registry unregistered checks, check-docs, and targeted regression
tests for touched contracts.

## CI5 Pages Path Gate

The Pages workflow uses `site/pages_input_manifest.json` as the maintained path
manifest. `pages_path_gate` selects `BUILD_REQUIRED` for explicit dispatch,
unavailable changed paths, invalid paths, manifest problems, site inputs,
release/version projection state, or Pages workflow files.

Only a push whose changed paths are deterministically outside the manifest
selects `BUILD_SKIPPED`. Deploy remains main-only and keeps least-privilege
Pages permissions separate from normal PR CI.

PRs still run the site tests in normal CI when site generator, site claims, or
site fallback behavior changes.

## CI6 Failure Registry Diagnostic

The failure registry starts in diagnostic-only mode. A failure record contains
workflow run ID, failing job, failure class, evidence pointers, suspected root
cause, and next safe action.

Known failure classes are registry counter drift, stale LLM context carrier,
dirty volatile carrier, missing checks, queued/stuck run, Pages deploy issue,
timeout, and test failure.

The registry proposes repair plans only. Repairs are branch-and-PR work and
never automatic direct main mutation.

## CI7 Receipt-Store Decision

Receipt-store replacement is deferred. The current refresh PR mechanism remains
active because exactly-one receipt, append-only enforcement, and successor
read-path discovery are not yet proven.

Replacing refresh PRs requires a later architecture slice with deterministic
successor read-path discovery validation for those three properties and
terminal-report retention as a separate evidence policy decision.
