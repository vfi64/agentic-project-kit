---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-003: canonical-handoff-applicability

Date: 2026-10-13
Kit state: CLOSED; fixed_in: 1.0.25 (1.0.25 is planned, not published).
Consumer VERIFIED_FIXED remains the external workspace decision.

## Finding and repair

The public handoff CLI default still named the legacy path. A focused applicability module now resolves all default handoff readers/refresh through the workspace authority. Missing implicit external state is NO_PREVIOUS_HANDOFF only without predecessor package evidence. Explicit missing paths, malformed state and lost predecessor state fail without traceback; refresh never fabricates missing state.

Prior evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

## Regression

`tests/test_greenfield_adjudication.py` executes installed wheels in disposable external workspaces with synchronized command references, no Kit tests and no Kit documentation registry. Each family has its own test. Existing handoff, audit and executor unit regressions also run. The fixture native Git setup is disposable; no remote project is changed.

## Expected external retest

Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit handoff check
agentic-kit handoff show
agentic-kit handoff prompt
agentic-kit transfer post-merge-check --json
agentic-kit work recover --json
```

Expected: process.returncode=0 for virgin handoff readers; stdout contains NO_PREVIOUS_HANDOFF and canonical namespace path; explicit missing target/predecessor loss exits 1.

Manifest ACK: COMMAND_MANIFEST_ACK 9a7d85b527d8, generated via Kit entrypoint, successor-package and docs/site routes.
