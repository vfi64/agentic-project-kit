# Post-v1.0.9 Greenfield Patch Recurrence Guard

Status: implemented local retest pass  
Date: 2026-09-07  
Kit baseline: `origin/main` at `1c5f57a7` before this slice  
Current branch: `codex/greenfield-patch-recurrence-guard`  
Machine-readable companion:
`docs/reports/POST_V1_0_9_GREENFIELD_PATCH_RECURRENCE_GUARD_20260907.json`

## Scope

This slice closes `KIT-GF-013` from the AGP Cockpit Greenfield adjudication. It
does not add a second failure database and does not change public CLI command
names. It hardens the existing patch-failure discipline and workflow-guard path
so repeated patch/test misses become a deterministic pre-mutation blocker before
a third mutation in the same patch family.

## Baseline

The existing repository already contained:

- `docs/governance/PATCH_FAILURE_DIAGNOSIS_POLICY.md`;
- `agentic-kit audit-patch-failure-discipline`;
- standard-gates coverage for `agentic-kit audit-patch-failure-discipline`;
- successor-handoff rule text for `patch-cycle-diagnostic-gate`.

The remaining gap was integration. The audit could detect repeated patch
failures, but the main workflow guard did not surface that state as the
pre-mutation escalation required by the Greenfield finding.

## Repair

The repair keeps the existing mechanism and makes its decision explicit:

- `audit-patch-failure-discipline` now reports `next_mutation_allowed`.
- `workflow-guard` calls the existing patch-failure audit, including local
  `tmp/` evidence, and turns repeated failures without later diagnosis into a
  `HARD-FAIL` finding with pattern `patch-cycle-diagnostic-gate`.
- The workflow-guard policy, patch-failure diagnosis policy, documentation
  coverage matrix, rule mechanism inventory, rule test coverage map, and rule
  preservation registry now retain the escalation rule.
- `docs/planning/PROJECT_DIRECTION.yaml` records the closeout as `B1-KIT-022`
  while leaving the other Greenfield/Brownfield follow-ups open.

## Public Contract

After one failed patch/test correction in a patch family, one direct correction
remains allowed.

After a second failed patch/test correction in the same patch family, the next
step must be bounded diagnosis. The guard reports:

```text
pattern_id=patch-cycle-diagnostic-gate
severity=HARD-FAIL
next_mutation_allowed=false
```

Diagnosis evidence resets the local failure count for that patch family. The
next mutation must then be a minimal patch based on the observed current state.

## Validation

Focused validation:

- `./.venv/bin/python -m pytest -q tests/test_patch_failure_discipline_audit.py tests/test_workflow_guard.py tests/test_rule_preservation.py tests/test_rule_mechanism_inventory.py`
  -> 25 passed
- `./.venv/bin/ruff check` on touched source and tests -> PASS
- `agentic-kit workflow-guard check` -> PASS
- `agentic-kit audit-patch-failure-discipline --include-tmp --json` -> PASS,
  `next_mutation_allowed=true`
- `agentic-kit rule-registry check` -> PASS
- `agentic-kit direction validate --root .` -> PASS
- `agentic-kit check-docs` -> PASS

Full repository validation:

- `./.venv/bin/python -m pytest -q` -> 3033 passed, 481 warnings
- `./.venv/bin/ruff check .` -> PASS
- `agentic-kit audit-command-manifest --json` -> PASS, 0 findings
- `agentic-kit docs-audit` -> PASS after
  `agentic-kit doc-registry reconcile --execute --json` refreshed the scope
  decision projection
- `agentic-kit doctor` -> PASS overall, with 76 document-lifecycle report-only
  findings

## Remaining Work

This slice closes only `KIT-GF-013`. It does not close:

- `KIT-GF-001`, `KIT-GF-003`, `KIT-GF-005`, `KIT-GF-009`: external first-cycle
  execution retest work;
- `KIT-GF-007`: generated-vs-manual provenance across DPA/adopt surfaces;
- `KIT-GF-011`: broader mixed handoff/status/report refresh-loop reduction;
- the active Comm-SCI Brownfield Cycle 008 product work.
