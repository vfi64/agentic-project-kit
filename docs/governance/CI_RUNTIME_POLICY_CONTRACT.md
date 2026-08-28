# CI Runtime Policy Contract

Status: active

This contract governs runtime optimization for GitHub Actions. It is a
deterministic gate policy, not a confidence heuristic. No optimized path may
weaken safety, determinism, or evidence strength compared with the complete
full-suite fallback.

## Required Check Boundary

The branch-protection-visible `CI` workflow keeps the required `test` job. Gate
selection happens inside that job so a skipped optional job cannot stand in for
success.

PR readiness and merge wrappers may ignore completed `SKIPPED` checks only when
the exact check name is listed in the optional diagnostic allowlist; currently
that allowlist contains only `pytest-parallel-shadow`. The fail-closed rule
covers `skipped required checks` and unlisted skipped checks; they must not
count as success.

The default mode is `FULL_CI`. Any missing, invalid, ambiguous, or unsafe input
selects `FULL_CI`.

`FULL_CI` uses a shallow checkout for the test worktree. The workflow may fetch
only the exact commit endpoints needed for changed-path classification:
pull-request base/head commits on PR events and push `before..current` commits
on push events. If those endpoints cannot be fetched and verified as commits,
changed-path classification falls back to the full repository path set, which
selects the conservative full lane. A full-history checkout is not required for
normal test execution and must not be used as a substitute for deterministic
endpoint proof.

GitHub Actions dependency cache use is performance-only. The workflow may use
`actions/setup-python` pip caching keyed by `pyproject.toml`, but cache hit,
cache miss, cache restore failure, or dependency download timing must not change
gate-mode selection, test selection, safety policy, or PASS/FAIL meaning.

## CI2 Pytest Parallel Required Lane

The branch-protection-visible `test` job runs the exact pytest suite with a
fixed four-worker xdist command:

```bash
python -m pytest -q -n 4 --durations=20
```

This parallel full-suite gate is an execution-mechanics change, not a narrower test selection. The
promotion is based on repeated local and GitHub Actions shadow evidence with
real `PYTEST_PARALLEL_SHADOW_RC=0` outcomes. The serial suite remains part of
the local completion/release evidence contract, but it is no longer the normal
CI critical path once xdist parity is established.

`pytest-parallel-shadow` remains available only as a manual `workflow_dispatch` diagnostic job.
It is not run for ordinary PR, main-push, or admin-refresh cycles, because the
required `test` job now carries the parallel full-suite gate directly.

## CI3 Main-Push Tree Proof

Main-push CI reduction is allowed only with a tree equivalence proof:

- final main tree SHA is present;
- tested pull-request head tree SHA is present;
- both tree SHAs match;
- the push commit is associated with exactly one merged pull request targeting
  `main`;
- the pull request's merge commit SHA matches the push commit;
- the branch-protection-visible `CI` / `test` check passed for that pull
  request;
- no workflow or GitHub Actions helper path changed.

If any condition is missing, `main_push_tree_proof` selects `FULL_CI`. Direct
main pushes, stale base, unknown merge method, failed checks, missing checks, or
workflow changes must not skip the full suite.

Code, test, documentation, governance, manifest, release-state, and site-source
paths may use the tree-proof lane only when the exact final main tree is proven
to be the same tree that already carried a successful pull-request `CI` /
`test` check. This preserves the required check's meaning while avoiding the
redundant post-merge full-suite run.

## CI4 Admin Refresh Light CI

`admin-refresh-light` is allowed only for administrative handoff refresh PRs
whose branch proves one source PR and whose diff exactly matches one known
generated handoff allowlist variant. Supported variants are:

- `current-handoff-refresh`: `.agentic/handoff_state.yaml`,
  `.agentic/operational_handoff_state.yaml`,
  `.agentic/dpa/acceptance/current_handoff_operational_state.json`,
  `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md`.
- `successor-package-refresh`: `docs/handoff/NEXT_CHAT_BOOTSTRAP.md` and the
  latest machine-readable successor package files under
  `docs/reports/handoff-packages/latest/`.
- `post-merge-settle-refresh`: the exact union of `current-handoff-refresh`,
  `successor-package-refresh`, `docs/handoff/START_NEW_CHAT_PROMPT.md`, and
  `docs/reports/terminal/post-pr<source-pr>-successor-chat-handoff.md`.

Extra paths, missing paths, invalid paths, manually edited product files,
unknown source PRs, or non-PASS successor validation select `FULL_CI`.

Accepted refresh PRs run handoff check, variant-specific artifact validation
(`agentic-kit dpa current-handoff-refresh --json` for current-handoff refreshes
or `validation_report.json` PASS verification for successor-package refreshes;
the combined post-merge settle variant runs both),
protected-diff-plan coverage, doc-registry reconcile, doc-registry unregistered
checks, check-docs, and targeted regression tests for touched contracts.
Post-merge status checks remain post-merge lifecycle gates; the PR light gate
must not rely on main-only post-merge state while validating a PR checkout.
The same light gate may run on a main push when the changed paths prove the
source PR through the terminal handoff report; in that case protected-diff-plan
uses the push `before..current` diff instead of pull-request base/head SHAs.

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
