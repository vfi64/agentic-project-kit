# Patch-Cycle Workflow Analysis

- schema_version: 1
- kind: patch_cycle_workflow_analysis
- workflow_id: patch_cycle_four_slice

## Summary

The existing transfer command set already contains the mutation authority for each part of the patch/handoff cycle. A new workflow engine would duplicate that logic. The safer minimal addition is a read-only state renderer:

```bash
agentic-kit transfer patch-cycle-status --json
```

It derives the current four-slice state from git status, current branch, optional PR metadata, and the generated successor handoff validation report. It does not mutate the repo and does not create a new persistent state file.

## State Model

```text
PATCH_SLICE
  -> PATCH_PR
  -> HANDOFF_REFRESH_SLICE
  -> HANDOFF_REFRESH_PR
  -> POST_MERGE_CLEAN_STATE
```

Stop states are `BLOCKED` and `FAILED_DIAGNOSIS_REQUIRED`. GUI and CLI should show one primary next action when possible, but mutations stay delegated to existing wrappers.

## Existing Command Authorities

- Patch guard: `agentic-kit transfer protected-diff-plan`
- Commit/push: `agentic-kit transfer commit`, `agentic-kit transfer push-current`
- Patch PR: `agentic-kit transfer pr-create-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-status`
- Handoff refresh: `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer prepare-successor-handoff`, `agentic-kit transfer publish-last-report`
- Final clean state: `agentic-kit transfer sync-main`, `agentic-kit transfer post-merge-check`, `agentic-kit transfer repo-status`, `agentic-kit transfer require-fresh-llm-context`

## Design Decision

Use a derived read-only state model first. Do not introduce a parallel workflow state file yet. The authoritative carriers are still git, PR metadata when available, `docs/reports/handoff-packages/latest/validation_report.json`, latest handoff reports, and existing transfer inbox/outbox carriers.

## GUI Impact

A GUI can poll `patch-cycle-status --json` and render:

- current stage,
- each four-slice step,
- blockers,
- allowed next actions,
- dirty paths,
- optional PR metadata,
- handoff freshness.

The GUI should call existing wrappers for mutations rather than shelling out to raw git/gh.

## Next Safe Enhancements

1. Add `patch-cycle-continue --json` only after the read-only status has proven stable.
2. Consider a GUI-only run-id cache if polling derived state is insufficient.
3. Add optional PR auto-detection for current branch once it can be done without GitHub flakiness.
