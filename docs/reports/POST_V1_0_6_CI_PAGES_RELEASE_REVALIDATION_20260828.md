# Post-v1.0.6 CI, Pages, and Release Revalidation

Status: active evidence report
Status-date: 2026-08-28
Repository: `vfi64/agentic-project-kit`

## Purpose

This report records the follow-up revalidation after the post-v1.0.6
deterministic CI runtime work and external LLM review notes. It is evidence, not
a new rule source. Repository contracts, tests, workflow files, and release
commands remain authoritative.

## Public Pages State

External checks at `2026-08-28T21:54:54Z` showed:

| URL | Result | Notes |
|---|---:|---|
| `https://github.com/vfi64/agentic-project-kit` | 200 | Repository homepage reachable. |
| `https://vfi64.github.io/agentic-project-kit/` | 200 | Generated project site reachable; page contains `Generated repository projection` and build commit `a0c9d5556758706a38c66a5a4d8501ae564513b7`. |
| `https://vfi64.github.io/agentic-project-kit/quickstart/` | 200 | Live Actions Pages route for generated quickstart. |
| `https://vfi64.github.io/agentic-project-kit/workflows/` | 200 | Live Actions Pages route for workflow chooser. |
| `https://vfi64.github.io/agentic-project-kit/commands/index.html` | 200 | Complete command reference reachable. |
| `https://vfi64.github.io/agentic-project-kit/commands/guided.html` | 200 | Guided command projection reachable. |
| `https://vfi64.github.io/agentic-project-kit/commands/diagnostics.html` | 200 | Diagnostic command projection reachable. |
| `https://vfi64.github.io/agentic-project-kit/claims/index.html` | 200 | Claim evidence projection reachable. |
| `https://github.com/vfi64/agentic-project-kit/blob/main/docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md` | 200 | Brownfield guide reachable through GitHub. |
| `https://vfi64.github.io/agentic-project-kit/site/index.html` | 404 | Legacy docs-fallback path is not served by the current Actions artifact deployment. |

The current GitHub Pages API reports `status: built`, `build_type: workflow`,
and public URL `https://vfi64.github.io/agentic-project-kit/`. Pages run
`33194126912` for main commit `a0c9d5556758706a38c66a5a4d8501ae564513b7`
completed successfully; `build` and `deploy` jobs both completed successfully.

Finding: the live site itself was not broken, but README public links still used
the legacy `/site/quickstart/` and `/site/workflows/` URL shape. Those links are
wrong for the current Actions artifact deployment and were corrected to
`/quickstart/` and `/workflows/`. A regression test now blocks reintroducing the
old live-link shape.

The versioned docs-source fallback remains a separate contract. Running
`site/scripts/build.py --docs-pages-fallback --json` refreshed
`docs/site/site.json` after the roadmap count changed; the existing byte-for-byte
fallback staleness test now passes again.

## CI and SKIPPED Policy

The required branch-protection-visible CI job remains `test`. Runtime mode
selection happens inside that job. The required full-suite command is
`python -m pytest -q -n 4 --durations=20`.

The `pytest-parallel-shadow` job is manual diagnostic evidence only:
`if: github.event_name == 'workflow_dispatch'`, `continue-on-error: true`, and no
dependency from the required `test` job.

PR readiness and merge wrappers already cover the real skipped-shadow failure
class:

- optional `pytest-parallel-shadow` with conclusion `SKIPPED` is neutral when
  the required `test` check is successful;
- unlisted skipped checks block as unknown or blocked;
- an optional skipped shadow alone is not green evidence.

The main-push tree proof checks the required `CI/test` check plus tree
equivalence. A new regression test records that a skipped
`pytest-parallel-shadow` check does not block tree proof when `CI/test` passed,
and that a skipped required `CI/test` check is not success.

The determinism claim remains bounded: repeated or targeted parallel runs are
regression evidence against observed order dependence, not a mathematical proof
that no hidden order dependence can exist.

## Workflow Error Closed

The observed workflow error was in `transfer pr-merge-safe`: the wrapper could
auto-switch to `main` before invoking the inner `agentic-kit pr merge-if-green`,
so a self-hosting PR that repaired merge/readiness code could still execute the
old main implementation.

The wrapper now fails closed unless it is running from one of these clean local
contexts:

- `main`; or
- the exact local PR head branch, with local `HEAD` matching the expected full PR
  head SHA.

Dirty worktrees still block after one bounded known-volatile repair attempt.
Unexpected PR base branches are refused before the inner merge command runs.

## Cache

`actions/setup-python@v6` with `cache: "pip"` was already present. This slice
does not claim to add caching from zero. It makes the cache dependency explicit
with `cache-dependency-path: pyproject.toml` in CI and Pages setup steps.

Cache behavior remains performance-only. Cache hit, miss, restore failure, or
download timing must not affect gate mode selection, selected tests, security
policy, or PASS/FAIL semantics.

## Release 1.0.7 Readiness

The latest published release remains `v1.0.6`, published on 2026-08-26. No
`v1.0.7` release or tag exists at this checkpoint, so the next release would be
`1.0.7`, not `1.0.8`.

A `1.0.7` release is justified after this repair branch and its post-merge
handoff refresh are green, because post-v1.0.6 main contains real behavioral
changes: CI runtime policy, admin-refresh light CI, main-push tree proof,
parallel required pytest, failure-registry diagnostics, skipped-shadow merge
handling, and this `pr-merge-safe` self-hosting fix.

Release is not ready merely because changes exist. Before publication, the
release slice still needs the normal release-prep, version/metadata, release
notes, packaging, public Pages revalidation from final main, and post-release
verification gates.

## B2 and Receipt Store

The receipt-store state remains `feasible-partial`. It may reduce source-tree
mutation for merge SHA or CI receipt propagation, but it is not yet proven to
eliminate the entire administrative refresh PR.

The next B2 decision must ask whether final post-merge receipt state may live
outside the managed source tree without weakening successor discovery. At
minimum, the model must fail closed for missing receipts, duplicate receipts,
wrong merge SHA, wrong base branch, wrong ancestry, unreachable receipts,
rewritten/deleted receipt refs, and disagreement between receipt store and
repository state.

## B3 Boundary

The fresh command catalog still reports `BOUNDED: 166`. The roadmap records B3
as `stage_1_in_progress` with `audited_count: 19`, so 147 items remain if the
current baseline count remains comparable.

B3 is independent of the CI repair. It should continue only as report-only
call-chain and side-effect evidence until a maintainer adjudicates any
`BOUNDED -> READ_ONLY` reclassification.
