# KIT-GF-118: first release without a previous tag

Date: 2026-11-15

Scope: `release run` A2/A3 (`release ready`, `release prepare`),
`transfer standard-error-scan --before-release`, `release-notes-generate`,
the B4 gate (`release_run.py`), and the new `release_range.py`.

Status: fixed in this change; not released.

## Finding

A project created by `agentic-kit init` has no `v*` tag, and no Kit command
creates one. Its first `release run` blocked in A2: `standard-error-scan`
reported `release-from-tag` ("no local v* git tag could be derived") and the
route only named the log. Independently, `release-notes-generate` blocked every
product commit without a PR number (`missing_pr_number`); the commits of `init`
and of the workspace adoption are direct commits by construction. The block
also applies under `publication: none`: the private fallback only replaces the
category `Unclassified`. The release fixture hid the defect, because it creates
`v0.1.0` itself. Observed in the probe before the live run 0107, which set the
tag by hand.

## Change

Owner decision 2026-11-15. Without a previous `v*` tag the release is the first
release (`release_range.resolve`): its notes start at the root commit
(`release-notes-generate --first-release`), and a product commit without a PR
number is listed as a direct commit (evidence `direct_commit`, rendered
"direct commit") instead of blocking. Only the first release: from the second
release on the PR evidence stays mandatory. A first release is only derived
when the origin lists no `v*` tag either; tags the clone has not fetched block
(`release-tags-not-fetched`), an unreadable origin blocks too. The B4 gate of
`release run` carries `first_release` (range `root`, root commit, direct
commits); the approval signature binds it. `init` still creates no tag.

## Regression evidence

`tests/test_release_first_release.py`: notes from the root with direct commits
under the standard policy, a second release still blocking without PR evidence,
`--first-release` refusing an existing tag, the range resolution with unfetched
and unreadable origin tags, the B4 gate field and its signature, and the CLI
requiring exactly one lower bound. They fail against the previous code. Journey
J6 (`reference/journeys.json`, fixture `external_init`) runs `init`, the
recovery with `--publication none`, the CI update and `release run` up to the
B4 gate of the first release without a hand tag or hand configuration.

## Boundaries

`release run` pushes and publishes, so the finding has no local machine
contract; J6 covers it offline and the live run before 1.4.0 on GitHub. Under a
publishing policy the init and adoption commits still need a release-note
category (KIT-CHK-RELEASE-NOTE-CATEGORY); their subjects match no heuristic, so
such a first release still blocks on classification. No release or consumer
`VERIFIED_FIXED` is claimed.
