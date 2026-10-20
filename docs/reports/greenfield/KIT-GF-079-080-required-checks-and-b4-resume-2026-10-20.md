---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-079 and KIT-GF-080: late required checks and a release PR left open by B4

Date: 2026-10-20
Kit state: CLOSED in candidate; planned release 1.1.4. Found in the Kit's own release 1.1.4.

## Observation

The Kit's CI runs its suite in three shards; the required `test` job verifies them and starts only
after them (`needs:`), so GitHub creates the `test` check minutes after the PR's other checks.

- KIT-GF-079: B4 of release 1.1.4 (release PR #2582) ran `pr wait-ci`, which saw `classify`, the
  three shards and the skipped diagnostic job and reported READY_TO_MERGE at 15:06:36 UTC, the
  second the `test` job was created. `merge-if-green` then saw `mergeStateStatus` UNSTABLE and
  refused, so B4 ended BLOCKED. Readiness supported expected checks, but no Kit route passed any;
  an absent required check counted as nothing to wait for. The slice PR #2580 itself passed by
  timing.
- KIT-GF-080: B4's `work finish` had already committed the release metadata and its handoff
  refresh, pushed `codex/release-1.1.4` and opened #2582. A new release run blocked with
  `changed-paths-drift`; B4 had no route to finish its own PR.

## Repair

1. `gates.required_checks` in `.agentic/config.yaml` names checks that must exist; `pr wait-ci`
   adds them to its expected checks, so readiness stays WAITING (`expected check missing`) until
   each is present and green. The Kit declares `test`.
2. After a failed B4 the B4 gate turns into `resume-existing-release-pr` only when exactly one open
   PR from the release branch targets main, the branch holds exactly `Prepare release <v>` (with
   exactly the approved paths) and `Refresh handoff for Release <v>` on the approved base, and main
   still is that base. The gate names PR, head and base; its execution runs `transfer pr-complete`
   with the exact head and the 900 s wait. Anything else blocks without a remote effect.

## Regression

`tests/test_release_b4_resume_and_required_checks.py`: a missing required check keeps readiness
waiting, `pr wait-ci` passes the declared names, invalid declarations are refused, the Kit
declares `test`; B4 resumes its own PR, blocks on a moved main, extra or foreign commits and other
paths, and stays ordinary without a failed attempt.
