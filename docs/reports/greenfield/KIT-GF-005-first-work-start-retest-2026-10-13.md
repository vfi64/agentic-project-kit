---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-005: first-work-start-retest

Date: 2026-10-13
Kit state: CLOSED; fixed_in: 1.0.24 (1.0.25 is planned, not published).
Consumer VERIFIED_FIXED remains the external workspace decision.

## Finding and repair

No longer reproducible with v1.0.24 or candidate wheel. In a clean initialized Git repo with a tracking main and local bare origin, work start succeeds and explicitly skips prior post-merge checks. A missing upstream is a genuine repository safety prerequisite, not evidence of a predecessor-state defect.

Prior evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

## Regression

`tests/test_greenfield_adjudication.py` executes installed wheels in disposable external workspaces with synchronized command references, no Kit tests and no Kit documentation registry. Each family has its own test. Existing handoff, audit and executor unit regressions also run. The fixture native Git setup is disposable; no remote project is changed.

## Expected external retest

Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. Clean main tracks origin/main; local bare origin contains the initial committed workspace; no previous merge or successor package.

```text
agentic-kit work start --branch codex/gf005-retest --from-ref main --json
```

Expected: result_status=PASS; post-merge-check step stdout says not applicable.

Manifest ACK: COMMAND_MANIFEST_ACK 9a7d85b527d8, generated via Kit entrypoint, successor-package and docs/site routes.
