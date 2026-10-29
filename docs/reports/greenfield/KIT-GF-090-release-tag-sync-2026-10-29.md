---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-090 — missing local release tags after synchronization

## Reproduction

Baseline: main `6d5fe5b2dc542c9ff6975e87dd2f0d8353e67f8b`, Kit 1.1.7.
The supplied consumer diagnostic found local tags through 1.1.5 while origin
also carried 1.1.6 and 1.1.7. No existing tag diverged. The consumer checkout
was only inspected; its missing tags were not repaired during this slice.

An independent disposable clone of the public origin reproduced the defect:
delete only the fixture's v1.1.7, then release-status reports prepared and
local_tag_exists false (rc 0). release-publish dry-run fails (rc 1): preparation
would change CHANGELOG.md and README.md. sync-main returns PASS (rc 0), yet
v1.1.7 remains absent. This uses the default fetch configuration, without a
remote.origin.tagOpt override. It is an observed path, not a claim that Git
never auto-follows tags with explicit refspecs.

## Cause and repair

The existing release-publish current_verified exception is correct. Missing
local tags prevent that state. Reapplying preparation to a closed-out release
would reset README publication status to pending and remove the DOI paragraphs.
Neither release-publish nor the historical CHANGELOG format is changed.

The shared git_tag_sync module fetches origin tag refs atomically, without force
or pruning, under the existing workspace mutation lock. Conflicts preserve local
tags and report tag name, local/remote targets and tag object IDs. Different
annotated tag objects remain conflicts even when their commits match.

| Audited path | Decision |
|---|---|
| transfer_repo_actions branch-switch --pull, fetch-origin, pull-current | Shared adapter after origin updates; tag failure is BLOCKED. sync-main uses branch-switch. |
| pr_closeout_complete, both main pulls | Shared adapter; stop before further closeout steps on failure. |
| transfer_pr_merge_flow main-pull | Covered by transfer_observed_subprocess, retaining step evidence. |
| remote_next fetch/pull | Shared adapter; stop on failure. |
| transfer_remote_next current/order branch fetch/pull | Shared adapter; no order execution after failure. |
| release_prep_core main pull | Shared adapter; stop before metadata writes. |
| agent_command_runner pull | Shared adapter; display tag errors before command execution. |
| transfer_rebase fetch/fallback | Shared adapter; no fallback or rebase after a tag conflict. |
| human_workflows fetch-all with tags | Shared adapter; verify tags through the same primitive. |

Release-status adds local_release_tag_missing and recommends sync-main when a
closeout receipt exists but its local version tag is absent. Pre-release state
without that receipt is unchanged. No command or remote-effect classification
changes; a blocker never grants permission to force or delete tags.

## Verification and limits

The first eight Git regressions failed against the previous code. The separate
release-state regression also failed before its status change. Real bare-origin
tests cover existing/new branch commits, annotated tags, conflicts, atomic
refusal, idempotency and restoration of current_verified. Existing orchestration
assertions explicitly include the new tag fetch rather than dropping checks.

The local finding contract is bounded to a disposable external release fixture,
tag restoration and external doctor, with publication disabled. release-status
declares network_read even without include-remote: its existing local-runner
classification is preserved. Direct lifecycle regressions and the separate
real Kit-checkout replay cover release-status and the Kit's standard audit suite.

Validation completed so far:

- Targeted transfer/release/doctor regression selection: 320 passed, rc 0.
- KIT-GF-090 machine contract: PASS 1, FAIL 0, rc 0.
- The original disposable Kit clone now obtains v1.1.7 through sync-main;
  release-status returns current_verified with no blockers; doctor and its
  standard audit suite return PASS, all rc 0.
- Ruff, check-docs and standard-gates-audit-suite: PASS, rc 0. The 76 existing
  document-lifecycle findings remain report-only.

The first full run found one effect-boundary regression (4324 passed, one failed).
The general transfer runner and workflow step runner were narrowed so only their
actual origin-update call sites reach tag synchronization. The original static
remote-effect implementation test and manifest declarations remain unchanged.
The follow-up selection passed 234 tests, including the original failure and
the existing branch-drift and workspace-lock assertions. The final complete
`python -m pytest -q` run passed 4325 tests (550 legacy-profile warnings), rc 0,
in 1097.83 seconds. The machine contract and original disposable Kit-clone replay
both passed again after the runner correction. PR CI is checked separately on
the exact published head. Local Kit evidence does not assign consumer
VERIFIED_FIXED. No release is performed.
