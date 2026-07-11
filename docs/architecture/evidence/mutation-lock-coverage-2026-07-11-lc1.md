# Mutation Lock Coverage Evidence (LC1)

Generated: 2026-07-11

Primary command: `./.venv/bin/agentic-kit audit-mutation-lock-coverage --json`

Mode: report-only evidence. LC1 does not add lock wrappers and does not hook this
audit into the standard gate suite.

Architecture authority: `docs/architecture/KIT_AS_OS_ARCHITECTURE.md` section
4 rule 7 and section 5.5. Mutating kernel operations must serialize through
`.agentic/tmp/workspace.lock`; read-only operations must remain lock-free.

## Result Summary

The audit is intentionally blocking in report mode so LC2 and LC3 can decide and
remediate the remaining coverage gaps.

```json
{
  "blocking_by_category": {
    "A": 89,
    "C": 151
  },
  "blocking_by_classification": {
    "runtime_mutation": 36,
    "unknown": 204
  },
  "blocking_finding_count": 240,
  "classification_summary": {
    "generated_reference": 9,
    "metadata_literal": 27,
    "report_writer": 101,
    "runtime_mutation": 36,
    "unknown": 204
  },
  "finding_count": 377,
  "findings_by_category": {
    "A": 110,
    "B": 4,
    "C": 263
  },
  "non_blocking_by_classification": {
    "generated_reference": 9,
    "metadata_literal": 27,
    "report_writer": 101
  },
  "non_blocking_finding_count": 137,
  "result_status": "BLOCK"
}
```

Implementation categories above are the audit command's current categories:

- `A`: git branch/history mutation pattern.
- `B`: GitHub mutation pattern.
- `C`: filesystem mutation pattern.

The LC planning taxonomy below maps those findings to the architectural
decision categories used by LC2 and LC3.

## Method

Primary reproducible audit:

```bash
./.venv/bin/agentic-kit audit-mutation-lock-coverage --json
./.venv/bin/agentic-kit audit-mutation-lock-coverage
```

Supporting grep battery:

```bash
grep -rn --exclude-dir=__pycache__ "acquire_workspace_lock" src/agentic_project_kit/
grep -rn --exclude-dir=__pycache__ "workspace_mutation_lock" src/agentic_project_kit/
grep -rn --exclude-dir=__pycache__ "subprocess" src/agentic_project_kit/ | grep -n "\"git\"\|'git'"
grep -rn --exclude-dir=__pycache__ -E "\"(push|switch|checkout|commit|add|mv|restore|clean|stash|tag|merge|rebase)\"" src/agentic_project_kit/ | grep -v tests
grep -rn --exclude-dir=__pycache__ "\"gh\"\|'gh'" src/agentic_project_kit/
grep -rn --exclude-dir=__pycache__ -E "write_text|open\(.*[\"']w|safe_dump|shutil\.|os\.replace|os\.rename" src/agentic_project_kit/ | grep -v tests
grep -rn --exclude-dir=__pycache__ "def " src/agentic_project_kit/transfer_repo_actions.py
```

The original LC1 prompt did not exclude `__pycache__`; the exact command
therefore reports local binary runtime artifacts in a developer checkout. This
evidence excludes `__pycache__` for the supporting grep output. The primary
audit scans only Python source files.

## Lock Entrypoints Found

```text
src/agentic_project_kit/workspace_upgrade.py:140:    with acquire_workspace_lock(plan.root, "workspace_upgrade"):
src/agentic_project_kit/transfer_repo_actions.py:678:    with acquire_workspace_lock(Path("."), "commit_paths"):
src/agentic_project_kit/transfer_repo_actions.py:773:    with acquire_workspace_lock(Path("."), "push_current"):
src/agentic_project_kit/workspace_init.py:148:    with acquire_workspace_lock(plan.root, "workspace_init"):
src/agentic_project_kit/transfer_repo_actions.py:562:    with workspace_mutation_lock(Path("."), 'branch_create'):
```

Marker-only contract references found:

```text
src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py:339:    mutation_lock_contract = "workspace_mutation_lock"
src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py:133:    mutation_lock_contract = "workspace_mutation_lock"
src/agentic_project_kit/transfer_repo_actions.py:615:    mutation_lock_contract = "workspace_mutation_lock"
src/agentic_project_kit/transfer_repo_actions.py:929:    mutation_lock_contract = "workspace_mutation_lock"
```

These marker-only references are useful breadcrumbs but are not equivalent to a
`with workspace_mutation_lock(...)` or `with acquire_workspace_lock(...)` block.

## Inventory Table

| Function or family | Module:line evidence | LC category | Lock status | Evidence |
|---|---:|---|---|---|
| `workspace_init` | `workspace_init.py:148` | A workspace-state-mutating | direct | Acquires `acquire_workspace_lock(plan.root, "workspace_init")`. |
| `workspace_upgrade` | `workspace_upgrade.py:140` | A workspace-state-mutating | direct | Acquires `acquire_workspace_lock(plan.root, "workspace_upgrade")`. |
| `branch_create` | `transfer_repo_actions.py:562` | B git-worktree-mutating, C remote-mutating when `push=True` | direct | Current source wraps the whole operation in `workspace_mutation_lock(Path("."), 'branch_create')`. This supersedes the historical LC1 prompt's expected branch_create gap. |
| `commit_paths` | `transfer_repo_actions.py:678` | B git-worktree-mutating | direct | Acquires `acquire_workspace_lock(Path("."), "commit_paths")`. |
| `push_current` | `transfer_repo_actions.py:773` | C remote-mutating | direct | Acquires `acquire_workspace_lock(Path("."), "push_current")`. |
| `ensure_remote_head` | `transfer_repo_actions.py:923` | C remote-mutating when auto-pushes | inherited/unclear | Has marker-only contract and calls `push_current(...)` for auto-push. LC2 must decide whether inherited locking is sufficient. |
| `branch_switch` | `transfer_repo_actions.py:614` | B git-worktree-mutating | FEHLT | Has marker-only contract but no `with` lock block around `git switch` or optional pull. Audit reports six runtime-mutation findings at lines 635, 637, 645, 646, 649, 651. |
| `pull_current` | `transfer_repo_actions.py:1161` | B git-worktree-mutating | FEHLT | Executes `git pull --ff-only` without a nearby lock marker. |
| `branch_delete` | `transfer_repo_actions.py:1174` | B git-worktree-mutating, C remote-mutating when `remote=True` | FEHLT | Executes local branch delete or remote branch delete without a nearby lock block. |
| `pr_create` | `transfer_repo_actions.py:1014` | C remote-mutating | inherited/unclear | Calls `ensure_remote_head(...)` and then `gh pr create`; no outer lock block. |
| `pr_merge_safe` | `transfer_repo_actions.py:1222` | C remote-mutating | FEHLT | Runs the merge wrapper command after preflight without a nearby lock block. |
| `admin_refresh_pr` | `transfer_repo_actions.py:1580` | A workspace-state-mutating, B git-worktree-mutating, C remote-mutating | FEHLT | Performs branch creation, document refresh, commit/push/PR operations without an outer lock block. Audit reports four git mutation findings in this function plus filesystem findings in `_refresh_operational_handoff_docs`. |
| `branch_create_command` | `cli_commands/transfer_repo_after_pr.py:36` | B wrapper entrypoint | inherited/unclear | Wrapper calls protected `branch_create(...)`; audit flags the wrapper because the marker is not near the command function. |
| `pr_create_complete_command` | `cli_commands/transfer_pr_create_flow.py:316` | C wrapper entrypoint | marker-only | Has marker-only contract, but no actual lock block at the command boundary. |
| `pr_complete_command` | `cli_commands/transfer_pr_merge_flow.py:100` | C wrapper entrypoint | marker-only | Has marker-only contract, but no actual lock block at the command boundary. |
| Report/evidence writers | many modules | D read-only or evidence-output side effects | non-blocking | Taxonomy classifies `report_writer`, `generated_reference`, and `metadata_literal` findings as non-blocking. |

## Gap List

Current hard gaps and uncertain inherited-lock cases:

| LC category | Count basis | Representative gaps | Notes |
|---|---:|---|---|
| A workspace-state-mutating | 151 blocking filesystem findings | `admin_refresh_pr`, `_refresh_operational_handoff_docs`, workflow/transfer state writers, validation output writers | LC2 must decide which state/evidence writes require serialization and which stay report-only/non-blocking. |
| B git-worktree-mutating | included in 89 blocking git findings | `branch_switch`, `pull_current`, `branch_delete`, `admin_refresh_pr`, remote-next sync helpers | `branch_create`, `commit_paths`, and `push_current` are already directly protected in current source. |
| C remote-mutating | included in 89 blocking git findings and 4 GitHub-pattern findings | `pr_create`, `pr_merge_safe`, `admin_refresh_pr`, PR wrapper entrypoints | Some flows inherit lock through `push_current`; LC2 must define whether wrapper-level outer locks are required. |
| D read-only | 137 non-blocking findings | metadata literals, generated references, report writers | These remain visible but must not block LC1. |

Top blocking source files by finding count:

```text
src/agentic_project_kit/transfer_repo_actions.py: 16
src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py: 15
src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py: 9
src/agentic_project_kit/cli_commands/transfer_evidence_flow.py: 8
src/agentic_project_kit/next_turn_runner.py: 8
src/agentic_project_kit/agent_command_runner.py: 7
src/agentic_project_kit/communication_rule_context.py: 7
src/agentic_project_kit/gui_task_editor.py: 7
src/agentic_project_kit/local_garbage_collector.py: 7
```

## Branch Create Recheck

The historical LC1 text said `branch_create()` must appear as missing lock
coverage. Current source no longer matches that baseline:

```text
src/agentic_project_kit/transfer_repo_actions.py:561:def branch_create(...)
src/agentic_project_kit/transfer_repo_actions.py:562:    with workspace_mutation_lock(Path("."), 'branch_create'):
```

Therefore this evidence treats `branch_create()` as protected. The remaining
branch-create related audit findings are wrapper-level (`branch_create_command`)
or broader branch lifecycle findings, not the core `branch_create()` function.

## Limitations

- This is a static source audit. It detects nearby lock markers and common git,
  GitHub, and filesystem mutation patterns; it does not prove every dynamic
  call chain.
- Marker-only strings are intentionally not treated as direct lock acquisition
  in this evidence.
- The current audit categories are implementation-oriented. LC2 should settle
  the normative rule for inherited locks, wrapper boundary locks, and evidence
  writers before LC3 changes code.
- LC1 remains report-only. Standard gates must stay green while the gap list is
  reviewed.
