---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-081 and KIT-GF-082: abandoning a stopped release run, and the cause of a failed wheel download

Date: 2026-10-20
Kit state: CLOSED in candidate; planned release 1.1.5. 081 was found in the Kit's own release
1.1.4, 082 in an external workspace's update to 1.1.4.

## Observation

- KIT-GF-081: the first attempt of release 1.1.4 stopped in B4 (KIT-GF-079) with an open,
  unmerged release PR; no tag, no package and no DOI existed. The owner decided to give the attempt
  up and restart. `release run` had no route for that: the release branch was deleted with
  `transfer branch-delete` (closing the PR), and the run state, log and step files under the tmp
  root were moved aside by hand, which is a hand step on Kit-written state.
- KIT-GF-082: `kit update --version 1.1.4` in an external workspace on macOS stopped in its plan
  with the bare blocker `release_artifact_download_failed`. The update log ended after the pip
  resolution because the downloads were not logged, and the exception behind the blocker was
  dropped. A read-only rerun of the same downloads passed; the Kit wheel took 29.7 s against the
  30 s socket timeout, and the download had a single attempt.

## Repair

1. `agentic-kit release abandon --version <v>` (DESTRUCTIVE orchestrator; effects delete_remote,
   network_read, push). The plan blocks when there is no run state, the worktree has tracked
   changes, the release branch is checked out, a local or remote tag or a GitHub Release exists,
   any gate after B4 was approved or a publication step finished, the release PR was merged, or
   more than one release PR is open. Otherwise it names the branch, its open PR, both branch heads
   and the archive directory `<tmp>/release-run-archive/<version>-<state digest>`; the signature
   covers all of them. The execute needs that signature, `--approved-by` and `--consent-source`; it
   deletes the remote branch through `transfer branch-delete --remote`, checks that the PR is closed
   and unmerged, deletes the local branch through `transfer branch-delete --force` and moves state,
   log and step files into the archive with an `abandon.json` record. It stops before archiving if
   a step fails or the PR stays open.
2. Wheel downloads: every attempt is logged in the update log as a `DOWNLOAD` event (file name,
   attempt, result, error type, duration; never the URL); a timeout, reset or 5xx/429 response is
   retried twice (after 2 and 5 s); the socket timeout is 60 s; a 4xx response or a refused URL is
   not retried; the final blocker reads
   `release_artifact_download_failed: <file>: <error type>: <detail> (attempt n of 3); inspect update log`.

## Regression

`tests/test_release_abandon.py`: plan without remote effect; execute deletes both branches through
the Kit's branch route, checks the PR and archives; eleven blocking cases (tags, GitHub Release,
approved or finished publication steps, merged PR, two open PRs, checked-out branch, dirty
worktree, open PR without branch); signature and attribution required; an open PR after the delete
stops before archiving; manifest classification. `tests/test_kit_update_download.py`: a timeout is
retried and logged without the URL, the final blocker names file and cause, 404 and a refused URL
are not retried, a 503 is retried and the hash is still checked, `prepare_target` passes the update
log.
