# Remote Hygiene A3 Classification - 2026-08-24

Status: classification_done_deletion_pending_maintainer_adjudication
Status date: 2026-08-24
Baseline ref: `f7808a37` (`Refresh handoff state after PR2139 (#2140)`)
Full classification data: `docs/reports/branch_hygiene/remote_hygiene_a3_classification_20260824.json`

## Scope

This is the A3 report-only classification pass for remote branch refs, open pull
requests, and open issues. No remote branch was deleted, no pull request was
closed, and no issue was closed.

The current repo-backed remote task carrier `gui-transfer-tasks` is protected as
`open-intentional` because it carries `.agentic/transfer/inbox/current.yaml`.

## Methods

- `git ls-remote --heads origin`
- `gh pr list --state open --limit 200`
- `gh issue list --state open --limit 200`
- `gh api --paginate 'repos/vfi64/agentic-project-kit/pulls?state=all&per_page=100'`

The classification combines branch ref SHA, open PR head refs, full PR API
history, merged-at state, head-SHA match, default-branch status, and Dependabot
actor evidence. It does not use `--merged` as a deletion criterion.

## Fresh Counts

| Quantity | Fresh count | Assignment snapshot |
| --- | ---: | ---: |
| Remote branch refs | 392 | 392 |
| Open pull requests | 7 | 7 |
| Open Dependabot PRs | 5 | 5 |
| Open non-Dependabot PRs | 2 | 2 |
| Open issues | 1 | 2 |
| Full PR records loaded | 2136 | not specified |
| Merged PR records loaded | 2087 | not specified |

The only snapshot deviation is open issues: current GitHub state has 1 open
issue, not 2.

## Classification Counts

| Class | Count | Deletion posture |
| --- | ---: | --- |
| `active-pr-head` | 7 | protected; not deletable before PR adjudication |
| `merged` | 310 | candidate only after maintainer adjudication and restore snapshot |
| `open-intentional` | 2 | protected |
| `stale` | 23 | candidate only after maintainer adjudication and restore snapshot |
| `unclear` | 50 | protected until resolved |

Disposition counts:

| Disposition | Count |
| --- | ---: |
| `candidate_for_maintainer_adjudication_after_snapshot` | 310 |
| `closed_unmerged_pr_head_candidate_for_adjudication` | 23 |
| `merged_pr_exists_but_branch_head_sha_differs` | 12 |
| `no_associated_pr_found_in_api_history` | 38 |
| `protected_default_branch` | 1 |
| `protected_open_pr_head` | 2 |
| `protected_open_pr_head_dependabot` | 5 |
| `protected_repo_backed_remote_task_carrier` | 1 |

## Protected Open PR Heads

| PR | Branch | Actor | Reason |
| ---: | --- | --- | --- |
| #1867 | `agent/agf-capture-ledger` | `vfi64` | active draft PR head |
| #1865 | `agent/record-ros-review-economy-research` | `vfi64` | active draft PR head |
| #2104 | `dependabot/github_actions/actions/github-script-9` | `app/dependabot` | active Dependabot PR head |
| #2103 | `dependabot/github_actions/actions/deploy-pages-5` | `app/dependabot` | active Dependabot PR head |
| #2102 | `dependabot/github_actions/actions/configure-pages-6` | `app/dependabot` | active Dependabot PR head |
| #1868 | `dependabot/github_actions/actions/setup-python-7` | `app/dependabot` | active Dependabot PR head |
| #1512 | `dependabot/github_actions/actions/checkout-7` | `app/dependabot` | active Dependabot PR head |

## Open Issues

| Issue | Title | Actor | Updated |
| ---: | --- | --- | --- |
| #1866 | Adopt the Agentic Governance Framework after Lab validation | `vfi64` | 2026-07-20T08:12:02Z |

## Deletion Readiness

No deletion is authorized by this report.

Before any future deletion charge, the maintainer must approve the class or
batch, and the repository must create a restore-capable mirror, bundle, or
equivalent full ref/object snapshot. The JSON report is a complete SHA and
decision list for review, but it is not by itself a restore guarantee after
remote garbage collection.

## A3 Disposition

Classification is complete for the fresh snapshot. Deletion remains blocked for
maintainer adjudication and restore-snapshot preparation.
