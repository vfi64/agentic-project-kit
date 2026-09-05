# Post-v1.0.8 Sampleproject First-Cycle Retest

Status: implemented external retest partial pass  
Date: 2026-09-05  
Kit branch: `codex/external-first-cycle-retest`  
External target: `vfi64/sampleproject`  
Machine-readable companion:
`docs/reports/POST_V1_0_8_SAMPLEPROJECT_FIRST_CYCLE_RETEST_20260905.json`

## Scope

This report records a controlled external first-cycle retest against the neutral
`vfi64/sampleproject` fork after the AGP Cockpit Greenfield adjudication. The
test used the current local Kit checkout as the executable under test and the
external repository only as a target workspace. It does not claim released PyPI
package behavior.

The retest focused on the Greenfield findings that required external lifecycle
evidence rather than code inspection:

- fresh external `workspace init`;
- first-cycle `work start` without a previous successor package;
- external health gates after adoption;
- first-cycle `work finish` planning, commit, push, PR creation, and existing-PR
  recovery;
- the forked-repository GitHub CLI context when both `origin` and `upstream`
  remotes exist.

## Target Setup

The external repository had:

- `origin = git@github.com:vfi64/sampleproject.git`;
- `upstream = git@github.com:pypa/sampleproject.git`;
- baseline main head `621e497` before setup;
- no `.agentic/` workspace state before adoption.

Setup PR #2, `Adopt agentic external workspace`, was created and merged in
`vfi64/sampleproject`; final target main after setup was `9f85262`. The setup
PR had no status checks in GitHub, so it was merged manually as a controlled
test-repository setup step rather than as proof that the Kit merge wrapper can
merge no-check PRs.

## External Retest Matrix

| Area | Result | Evidence |
| --- | --- | --- |
| `workspace init` on a fresh external repo | PASS | Created `.agentic/config.yaml`, state files, registries, rule files, CI templates, and `docs/archive/README.md`. |
| `check` after workspace init | PASS | `workspace_mode=external_manifest_workspace`. |
| `doctor` after workspace init | PASS | Overall PASS with expected optional warnings for target-owned missing project files. |
| `governance check` after workspace init | PASS | External manifest workspace path accepted. |
| `transfer status` after workspace init | PASS with BLOCKED primary state while dirty | Reported `transfer_file_state=NO_COMMAND`; dirty workspace and missing rule acknowledgement were correct blockers before commit. |
| `standard-gates-audit-suite` after workspace init | PASS | External gate set ran successfully. |
| `rules acknowledge` after workspace init | PASS | Rule acknowledgement remained local runtime state and was not committed. |
| Setup commit/push | PASS | Commit `b8c6121`, branch `codex/first-cycle-workspace-init`, setup PR #2. |
| `work start --branch codex/first-cycle-runtime-smoke` from external main | PASS | First-cycle post-merge check was a NOOP: no successor package exists yet, so post-merge check is not applicable. |
| `work check --profile code` on the first work branch | PASS | Repo status, check, governance, doctor, and standard-gates audit passed. |
| `work finish --dry-run` for the first work branch | PASS | Path selection, protected-diff-plan, and remote preflight passed. |
| External commit/push for the first work branch | PASS | Commit `153c3b9`, branch `codex/first-cycle-runtime-smoke`. |
| `transfer pr-create` without a manual `GH_REPO` override | PASS | Created `https://github.com/vfi64/sampleproject/pull/3`; the Kit pinned GitHub CLI context to `origin` despite the `upstream` remote. |
| `transfer pr-existing-for-branch` without a manual `GH_REPO` override | PASS | Found PR #3 through the existing `gh pr list --head ...` path. |
| `transfer pr-create-complete` against the existing PR | BLOCKED as expected | Recovered PR #3 idempotently, then blocked at `pr-complete` because the target repo reports `decision=no-checks`. |
| Cleanup | PASS | PR #3 was closed unmerged and remote branch `codex/first-cycle-runtime-smoke` was deleted. |

## Repair Performed In The Kit

The external test exposed one additional Kit-owned workflow defect: GitHub CLI
commands inside the PR lifecycle could inherit the wrong repository context in a
forked target that has both `origin` and `upstream`. This caused PR create,
complete, or recovery steps to query the wrong repository unless `GH_REPO` was
provided manually.

The repair deliberately reuses existing mechanisms:

- `repo_identity` now exposes an origin-derived GitHub CLI environment helper.
- `transfer pr-create`, `transfer pr-existing-for-branch`, `transfer
  pr-create-complete`, `transfer pr-wait-ci`, and `transfer pr-merge-safe`
  receive or bind `GH_REPO` from the repository's `origin` remote when available.
- `transfer pr-create-complete` no longer uses the obsolete raw
  `gh pr view --head ...` fallback. It delegates existing-PR lookup to the
  already existing `transfer pr-existing-for-branch` command.
- CI readiness fallback calls also receive the same origin-pinned GitHub CLI
  context.

No new PR or handoff subsystem was introduced.

## Greenfield Finding Impact

| Finding | Retest impact |
| --- | --- |
| KIT-GF-001 | External workspace init is now retested successfully in a neutral external repository. Remaining provenance questions stay under KIT-GF-007. |
| KIT-GF-003 | First-cycle work start no longer requires a previous successor package. Full successor-package post-merge proof remains blocked by the target repo's no-checks boundary. |
| KIT-GF-005 | External first-cycle start behavior is retested as PASS. |
| KIT-GF-009 | First-cycle finish planning, commit, push, PR creation, and existing-PR recovery are retested. Full merge/post-merge closeout was not claimed because the target repository has no status checks. |
| KIT-GF-010 | Rule acknowledgement remained local runtime state during the retest; released-package retest is still deferred to the next package release. |
| KIT-GF-011 | This slice fixes a concrete PR lifecycle context defect but does not close the broader mixed handoff/status/report refresh-loop item. |

## Boundary

The `vfi64/sampleproject` fork currently reports no required PR checks. The Kit
must continue to treat `no-checks` as not green. Therefore this retest cannot be
used as evidence that `transfer pr-complete` or `work finish --execute --merge`
can safely merge and post-merge-closeout a no-check external PR.

That boundary is intentional: no-checks is a target repository validation gap,
not green CI evidence.

## Validation

Focused local validation:

- `python -m pytest -q tests/test_successor_handoff_package.py
  tests/test_transfer_startup_hardening_commands.py::test_transfer_pr_existing_for_branch_finds_single_pr
  tests/test_transfer_startup_hardening_commands.py::test_transfer_pr_existing_for_branch_resolves_current_branch
  tests/test_transfer_startup_hardening_commands.py::test_transfer_pr_existing_for_branch_blocks_multiple_matches
  tests/test_transfer_startup_hardening_commands.py::test_transfer_pr_existing_for_branch_reports_gh_failure
  tests/test_transfer_pr_complete_command_contract.py::test_transfer_pr_create_complete_uses_existing_pr_when_create_fails
  tests/test_transfer_pr_complete_command_contract.py::test_transfer_pr_create_complete_passes_live_status_context_to_pr_complete
  tests/test_pr_ci_readiness.py`
  -> 63 passed.
- `ruff check .` -> PASS.

Full local validation after report and Direction updates:

- `python -m pytest -q` -> 3026 passed, 482 warnings.
- `ruff check .` -> PASS.
- `agentic-kit check-docs` -> PASS.
- `agentic-kit direction validate --root .` -> PASS, 0 findings.
- `agentic-kit audit-command-manifest --json` -> PASS, 0 findings.
- `agentic-kit doctor` -> PASS overall, with 76 document-lifecycle
  report-only findings.
- `agentic-kit workflow-guard check` -> PASS.
- `agentic-kit doc-registry reconcile --root . --json` -> PASS, projection
  no longer stale after the execute refresh.

External runtime validation:

- `agentic-kit work finish --dry-run ...` in `vfi64/sampleproject` -> PASS.
- `agentic-kit transfer pr-create ...` without manual `GH_REPO` -> PASS, PR #3
  created in `vfi64/sampleproject`.
- `agentic-kit transfer pr-existing-for-branch ...` without manual `GH_REPO`
  -> PASS, PR #3 found.
- `agentic-kit transfer pr-create-complete ... --timeout-seconds 3` -> BLOCKED
  at `pr-complete` because PR status was `decision=no-checks`; this is the
  expected fail-closed result.
- `gh pr close 3 --repo vfi64/sampleproject --delete-branch` -> PASS cleanup.
