---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-069: release runner consumes the publish orchestration verdict

Date: 2026-10-13
Kit state: CLOSED in candidate; planned fix release 1.0.25.
Consumer VERIFIED_FIXED remains an independent external retest decision.
Manifest ACK: COMMAND_MANIFEST_ACK 9633a3a680ad (no CLI declaration changes).

## Finding and repair

The release runner reclassified every publish check as requiring PASS, rejecting
the orchestration's legitimate external-workspace SKIP verdict at C1 and C2.
The runner now delegates to release_publish_payload_ok in the orchestration
module. It consumes status PASS and an explicit integer blocker_count of zero.
The existing _check_blocks policy remains the sole check-level verdict: PASS
and SKIP do not block; FAIL, WARN and unknown states do. Missing or malformed
summaries remain blocked. Return-code failures remain blocked independently.
No release approval, signature or publication capability is changed.

Persisted runs already retry the first unfinished step. A C1 failure is not
recorded as finished, so after the fix the same run continues from C1 and retains
its B4 approval and attributed upfront consent. No state surgery is needed.

## Regression

Tests: tests/test_release_run_publish_verdict.py, plus existing release-run and
publish-orchestration tests. Positive and negative cases derive payloads from
the actual ReleasePublishPlan, including SKIP, FAIL, WARN and unknown checks;
malformed summary fields fail closed.

The installed-wheel external fixture synchronizes the command reference and
has no Kit tests or documentation registry. The real publish planner produces
SKIP for docs audit and command reference check. An isolated legacy-validator
control reproduces C1 BLOCKED after a normally signed B4. Restoring the fixed
validator resumes C1 then C2, with the exact B4 approval and consent retained.
The runner and publication observations are controlled; both publish plans are
dry-only and no GitHub tag, release or consumer acceptance is claimed.

## Expected external retest

Use the consumer's actual next release (Cockpit 0.2.6), a clean disposable
external clone and its declared publication/approval policy. Adopt Kit 1.0.25
and synchronize references. With the genuine attributed consent for that
release, resume the existing C1-stopped run or start the next release normally:

```text
agentic-kit release-publish --version {version} --dry-run --json
agentic-kit release run --version {version} --approved-by {owner} --consent-source {consent} --json
```

Require publish status PASS, blocker_count 0, external checks SKIP and C1 PASS.
Per-gate mode must await the normal signed C2 approval; upfront mode must use
the recorded B4 consent and progress through C2. A deliberate failing metadata
check must keep publication blocked. Never reuse a different version's consent
or edit run state. A live consumer publication requires the owner's consent;
the regression fixture itself performs no publication.

## Scope

The repair adds a small authoritative payload adapter to the existing publish
core; release_run remains a delegating boundary. Rewriting the legacy runner
would exceed this focused policy-consistency fix; its monolith remains a named
technical debt, with step execution/state persistence the next cohesive extract.
