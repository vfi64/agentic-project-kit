---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-013: workspace-repair-escalation

Date: 2026-10-13
Kit state: CLOSED; fixed_in: 1.0.25 (1.0.25 is planned, not published).
Consumer VERIFIED_FIXED remains the external workspace decision.

## Finding and repair

The existing recurrence audit read only Kit tmp and command-run paths, missing namespaced external evidence. Discovery now resolves both from the workspace. One failure permits correction; two failures in the same slice without later diagnosis return next_mutation_allowed=false and FAIL. Later diagnosis reopens the gate. Ordering uses observed file mtime_ns and stable paths, not elapsed-time thresholds. This enforces diagnosis; it does not claim an automated semantic root-cause analysis.

Prior evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

## Regression

`tests/test_greenfield_adjudication.py` executes installed wheels in disposable external workspaces with synchronized command references, no Kit tests and no Kit documentation registry. Each family has its own test. Existing handoff, audit and executor unit regressions also run. The fixture native Git setup is disposable; no remote project is changed.

## Expected external retest

Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. In workspace tmp_root, create slice1-a-20260101-000001.log containing block not found, then slice1-b-20260101-000002.log containing function not found; retain distinct observed mtime_ns order. After the blocked result add slice1-diagnose-20260101-000003.log containing RESULT=PATCH_FAILURE_DIAGNOSIS_DONE with later mtime_ns.

```text
agentic-kit audit-patch-failure-discipline --include-tmp --json
```

Expected: one failure: next_mutation_allowed=true; two failures: status=FAIL, next_mutation_allowed=false, process.returncode=1; later diagnosis: status=PASS, next_mutation_allowed=true.

Manifest ACK: COMMAND_MANIFEST_ACK 9a7d85b527d8, generated via Kit entrypoint, successor-package and docs/site routes.
