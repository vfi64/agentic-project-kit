# KIT-GF-119: category of direct commits in the first release

Date: 2026-11-15

Scope: `release-notes-generate --first-release` (`release_notes.py`), used by
`release ready`, `release prepare` and `release run` A2/A3.

Status: fixed in this change; not released.

## Finding

KIT-GF-118 lists commits without a PR number as direct commits in the first
release. Their category still came from the subject heuristics only: the init
commit ("Initialize agentic project") and a workspace adoption commit match
none, and no PR exists that could carry a `release-note-category`. Under a
publishing policy (anything but `publication: none`) the first release of an
init project therefore still blocked on KIT-CHK-RELEASE-NOTE-CATEGORY. Under
`publication: none` the private fallback already listed them under `Changed`.
Found while verifying KIT-GF-118 (order 0111).

## Change

In the first release an unclassified direct commit is listed under `Changed`
with confidence `fallback`, evidence
`unclassified_first_release_direct_commit` and a warning naming the commits.
Only direct commits and only in the first release: a commit with a PR still
needs its category, and from the second release on an unclassified commit
still blocks.

## Regression evidence

`tests/test_release_first_release.py`:
`test_first_release_lists_unclassified_direct_commits_under_changed_with_a_warning`
(fails on the previous code with "Unclassified product release-note items")
and `test_a_second_release_still_blocks_an_unclassified_commit`.

## Boundaries

`release run` pushes and publishes, so the finding has no local machine
contract. The live run before 1.4.0 uses `publication: none`, where the private
fallback applies first. No release or consumer `VERIFIED_FIXED` is claimed.
