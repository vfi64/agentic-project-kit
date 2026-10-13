---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-016: contract-first-executor-retest

Date: 2026-10-13
Kit state: CLOSED; fixed_in: 1.0.13 (1.0.25 is planned, not published).
Consumer VERIFIED_FIXED remains the external workspace decision.

## Finding and repair

The existing Planner-Kit-Executor route is executable externally. An installed-wheel fixture plans a declared Kit check intent (PASS), dry-runs it without execution, then executes the read-only step (PASS). Unknown commands cannot become PASS. The adapter is kit-local and command authority is the synchronized manifest; this proves the bounded executor contract, not arbitrary autonomous planning.

Prior evidence: docs/reports/POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json

## Regression

`tests/test_greenfield_adjudication.py` executes installed wheels in disposable external workspaces with synchronized command references, no Kit tests and no Kit documentation registry. Each family has its own test. Existing handoff, audit and executor unit regressions also run. The fixture native Git setup is disposable; no remote project is changed.

## Expected external retest

Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit executor plan {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --execute --json
```

Expected: plan.result_status=PASS; dry-run.executed=false; execute.result_status=PASS, executed=true; unknown command plan is not PASS.

Intent example (intent_path), declaring the contract before execution:

```yaml
schema_version: 1
id: external-gf016
title: External read-only contract
executor_adapter: kit-local
block_dirty_worktree: false
steps:
  - id: check
    kind: command
    argv: [agentic-kit, check, --json]
```

Manifest ACK: COMMAND_MANIFEST_ACK 9a7d85b527d8, generated via Kit entrypoint, successor-package and docs/site routes.
