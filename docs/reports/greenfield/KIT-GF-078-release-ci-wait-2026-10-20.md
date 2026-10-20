---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-078: release-run work finish waited 300 s for a CI that takes over five minutes

Date: 2026-10-20
Kit state: CLOSED in candidate; planned release 1.1.4. Found in the Kit's own release 1.1.3.

## Observation

`work finish` called `transfer pr-create-complete --timeout-seconds 300` (and `pr-wait-ci
--timeout-seconds 300` without merge). The Kit's full CI took 5 to 5.5 minutes in release 1.1.3:

- B4 (release PR #2571) just passed.
- D4 (DOI PR #2573) stopped after 319 s; `pr-wait-ci` reported TIMEOUT while the test job was still
  pending. Because only a GH_ERROR read failure selected the resume of the existing DOI PR, the
  run needed D2R: a regenerated replacement PR #2574 with a second CI run, and #2573 closed.
- E1 (archive PR #2576) stopped the same way; its CI turned green 26 s later, and the PR was
  completed by a hand-written `transfer pr-complete 2576 --timeout-seconds 900`, because E1 had no
  route for its own open archive PR.

## Repair

1. `work finish --ci-timeout-seconds` (default 900, minimum 60) sets the CI wait of
   `pr-create-complete` and `pr-wait-ci`; a longer wait only waits while checks are pending.
2. The release run passes `--ci-timeout-seconds 900` explicitly to every work finish (B4, D3/D4,
   E1), so a later default change cannot shorten it.
3. A D4 that stopped with `PR readiness outcome: TIMEOUT` in `pr-wait-ci` selects the signed resume
   of the existing DOI PR (exact head SHA, `pr-complete` with 900 s), like a GH_ERROR read failure;
   red CI still regenerates through D2R.
4. An E1 whose earlier attempt is BLOCKED looks for its open archive PR. Exactly one open PR from
   the archive branch to main whose head carries byte-identical evidence (sha256 of the signed
   snapshot) is completed with `pr-complete --expected-head-sha <head> --timeout-seconds 900`; the
   gate names mode, PR and head, so its signature covers them. Other evidence blocks; no open PR
   takes the ordinary route.

## Regression

`tests/test_release_run_ci_wait.py`: default and explicit wait, every release work finish carries
it, TIMEOUT resumes and red CI does not, E1 completes an identical archive PR, refuses different
evidence and falls back without a PR. The next release run is the live retest.
