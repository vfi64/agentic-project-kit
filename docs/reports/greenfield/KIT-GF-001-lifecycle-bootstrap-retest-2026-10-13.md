---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-001: lifecycle-bootstrap-retest

Date: 2026-10-13
Kit state: CLOSED; fixed_in: 1.0.24 (1.0.25 is planned, not published).
Consumer VERIFIED_FIXED remains the external workspace decision.

## Finding and repair

No longer reproducible in a wheel built from v1.0.24 or in the candidate. Init preserves project-owned planning Markdown, check status=PASS and doctor Overall: PASS. External default warn policy does not silently adopt the Kit documentation constitution. An explicitly adopted lifecycle contract remains applicable.

Prior evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

## Regression

`tests/test_greenfield_adjudication.py` executes installed wheels in disposable external workspaces with synchronized command references, no Kit tests and no Kit documentation registry. Each family has its own test. Existing handoff, audit and executor unit regressions also run. The fixture native Git setup is disposable; no remote project is changed.

## Expected external retest

Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit workspace init --root . --execute --json
agentic-kit check --json
agentic-kit doctor
```

Expected: process.returncode=0; check.status=PASS; doctor stdout contains Overall: PASS.

Manifest ACK: COMMAND_MANIFEST_ACK 9a7d85b527d8, generated via Kit entrypoint, successor-package and docs/site routes.
