# Mutation Lock Coverage Evidence (Post-LC3)

Generated: 2026-07-11

Command: `./.venv/bin/agentic-kit audit-mutation-lock-coverage --json`

Status: PASS

Blocking findings: 0

## Result Summary

LC3 applies the LC2 same-PID reentrancy decision to the active runtime mutation
surface. Core transfer runtime mutators now acquire `workspace_mutation_lock`;
nested same-PID mutators reuse the outer lock and release only at the outer
context boundary.

```json
{
  "blocking_finding_count": 0,
  "classification_summary": {
    "delegated_runtime_reference": {
      "count": 60,
      "counts_as_blocking": false
    },
    "filesystem_side_effect": {
      "count": 149,
      "counts_as_blocking": false
    },
    "generated_reference": {
      "count": 9,
      "counts_as_blocking": false
    },
    "metadata_literal": {
      "count": 27,
      "counts_as_blocking": false
    },
    "report_writer": {
      "count": 101,
      "counts_as_blocking": false
    },
    "review_visible_reference": {
      "count": 86,
      "counts_as_blocking": false
    }
  },
  "finding_count": 432,
  "non_blocking_finding_count": 432,
  "result_status": "PASS"
}
```

## Remediated Runtime Mutators

The LC1 gap table's active runtime transfer mutators are covered by direct locks
or same-PID inherited locks:

| Function or family | LC3 coverage |
|---|---|
| `branch_create` | already directly protected by `workspace_mutation_lock` |
| `branch_switch` | directly protected by `workspace_mutation_lock` |
| `pull_current` | directly protected by `workspace_mutation_lock` |
| `branch_delete` | directly protected by `workspace_mutation_lock` |
| `pr_create` | directly protected; nested `ensure_remote_head` / `push_current` uses same-PID reentrancy |
| `pr_merge_safe` | directly protected |
| `admin_refresh_pr` | directly protected after the read-only refresh-only check |
| `commit_paths` | already directly protected by `acquire_workspace_lock` |
| `push_current` | already directly protected by `acquire_workspace_lock` |

## Non-Blocking Visibility

False-positive-prone filesystem side effects, generated references, metadata
literals, report writers, and delegated runtime references remain present in
JSON and text output. They do not block the standard suite unless they become an
unlocked core runtime git/GitHub mutator.

## Gate Adoption

`agentic-kit standard-gates-audit-suite` now includes
`agentic-kit audit-mutation-lock-coverage`.
