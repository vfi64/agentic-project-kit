# NS Command Migration Classification

Status-date: 2026-06-17
Status: active
Decision status: proposed
Scope: classification only. This document does not migrate or add commands.
Review policy: Review before adding, removing, or redirecting any `agentic-kit` command that replaces old `./ns` semantics.
Project: agentic-project-kit

## Evidence Base

- Mandatory start log: `tmp/codex-ns-migration-start-20260617-162611.log`
- Missing-handoff investigation log: `tmp/codex-ns-migration-handoff-status-20260617-162942.log`
- Classification investigation log: `tmp/codex-ns-migration-classify-investigate-20260617-164459.log`
- Fresh diagnostic evidence: `tmp/ns-migration-evidence.md` and `tmp/ns-migration-evidence.json`
- Required handoff: `docs/handoff/CODEX_NS_COMMAND_MIGRATION_HANDOFF.md`

The old command definitions are reconstructed from `v0.4.6:ns`. Current command-surface evidence comes from the checked-in Typer modules, tests, and command reference on this branch.

## Summary

| old command | old source | current equivalent | decision | proposed target |
|---|---|---|---|---|
| `ns dev` | `v0.4.6:ns:401-404` | partial core only: `src/agentic_project_kit/local_feature_gate.py:32-78` | migrate one missing Python CLI entry | `agentic-kit dev local-feature-gate` |
| `ns go` | `v0.4.6:ns:406-428` | `agentic-kit workflow go` in `src/agentic_project_kit/cli_commands/workflow.py:348-362` | keep existing command, migrate missing guard if confirmed absent | `agentic-kit workflow go` |
| `ns up` | `v0.4.6:ns:430-433` | modern route: `agentic-kit transfer pr-complete` in `src/agentic_project_kit/cli_commands/transfer.py:1186-1370` | document existing command and mark old module obsolete | `agentic-kit transfer pr-complete` |
| `ns upload` | `v0.4.6:ns:436-443` | `agentic-kit workflow upload` and `agentic-kit workflow upload-output` in `src/agentic_project_kit/cli_commands/workflow.py:403-422` | document existing command | `agentic-kit workflow upload` |

There is no single shared implementation core across all four commands. `ns dev` belongs to local feature gates, `ns go` and `ns upload` belong to workflow state handling, and `ns up` belongs to the transfer PR lifecycle.

## `ns dev`

### Old Definition

`v0.4.6:ns:401-404`:

```bash
if [ "${1:-}" = "dev" ]; then
  shift
  PYTHONPATH=src "$PY" -m agentic_project_kit.local_feature_gate --include-pr-hygiene "$@"
  exit $?
fi
```

### Old Semantics

Runs the local feature gate with PR hygiene enabled. The current core prints that it is a local-only safety gate and performs branch/status inspection, pytest, ruff, check-docs, doctor, and optionally PR hygiene without pull, push, merge, tag, release, or branch cleanup.

Current evidence:

- `src/agentic_project_kit/local_feature_gate.py:32-78` implements `run_local_feature_gate`.
- `tests/test_v034_ns_dev_gate_routing.py:21-25` requires the old `./ns dev` shortcut to stay removed.
- `tests/test_v034_ns_dev_gate_routing.py:4-18` preserves only the explicit compatibility shortcut `./ns dev-local-feature-gate`.

### Current Equivalent

No supported `agentic-kit` command is currently equivalent. The implementation core exists, but the supported command surface is still a compatibility `./ns dev-local-feature-gate` route.

### Decision

Migrate. Add a real Python-backed `agentic-kit` command for the existing core. Do not restore `./ns dev`.

### Proposed Target

`agentic-kit dev local-feature-gate`

Rationale: this is not a transfer lifecycle action. A small `dev` Typer group keeps the command local, explicit, and separate from transfer/release automation. The first implementation should preserve an option equivalent to `--include-pr-hygiene`; the old `ns dev` behavior maps to running that option.

### Required Tests

- Core tests for `run_local_feature_gate` command composition, including `include_pr_hygiene=True`.
- CLI registration/help test for `agentic-kit dev local-feature-gate`.
- CLI behavior test that forwards pytest arguments to the core.
- Regression test that `./ns dev` remains absent.
- Command reference snapshot refresh and `tests/test_agentic_kit_command_reference_is_current.py`.

### Risks

- Reintroducing a generic `./ns dev` shortcut would violate the migration direction and existing tests.
- Placing this under `transfer` would imply remote/PR lifecycle semantics that the command must not have.
- Running full local gates can be slow; command text should remain explicit about local-only behavior and side effects.

## `ns go`

### Old Definition

`v0.4.6:ns:406-428`:

```bash
if [ "${1:-}" = "go" ]; then
  shift
  BRANCH="$(git branch --show-current 2>/dev/null)"
  DIRTY="$(git status --short 2>/dev/null)"
  if [ "$BRANCH" != "main" ] && [ -n "$DIRTY" ] && grep -q "git_pull_ff_only" .agentic/current_work.yaml 2>/dev/null; then
    printf 'Refusing governed workflow go on a dirty feature branch because current_work includes git_pull_ff_only.'
    exit 2
  fi
  if [ -x ".venv/bin/agentic-kit" ]; then
    .venv/bin/agentic-kit workflow go "$@"
    exit $?
  fi
  agentic-kit workflow go "$@"
  exit $?
fi
```

### Old Semantics

Requests the configured workflow and runs one bounded step, but first refuses a dirty non-main branch when `.agentic/current_work.yaml` contains `git_pull_ff_only`.

Current evidence:

- `src/agentic_project_kit/cli_commands/workflow.py:348-362` registers `agentic-kit workflow go`.
- `tests/test_workflow_request_cli.py:157-175` verifies request plus one bounded run.
- `tests/test_workflow_request_cli.py:177-192` verifies non-IDLE workflow states are refused.
- `tests/test_workflow_request_cli.py:114-125` currently covers dirty-tree guidance for `workflow status --explain`, not the old `go` guard.

### Current Equivalent

`agentic-kit workflow go` is the command-surface equivalent for the request/run portion. The old dirty feature-branch plus `git_pull_ff_only` guard is not evidenced as part of `workflow go` itself.

### Decision

Keep the existing command. If implementation confirms the guard is absent, migrate only that guard into `agentic-kit workflow go`. Do not add `agentic-kit transfer go` or another duplicate route.

### Proposed Target

`agentic-kit workflow go`

### Required Tests

- Existing workflow go tests must stay green.
- Add a CLI/core test for dirty non-main branch plus `git_pull_ff_only` refusing before `_run_next_step`.
- Add clean-branch or main-branch coverage showing ordinary `workflow go` still runs.
- Command reference refresh only if help/options change.

### Risks

- Missing the old guard can run workflow automation in a dirty feature branch immediately before a fast-forward pull step.
- Adding a duplicate command would fragment the workflow surface.
- Guard logic should use existing `_run_git` and root-aware helpers rather than shell snippets.

## `ns up`

### Old Definition

`v0.4.6:ns:430-433`:

```bash
if [ "${1:-}" = "up" ]; then
  shift
  PYTHONPATH=src "$PY" -m agentic_project_kit.ns_up_pr_completion "$@"
  exit $?
fi
```

### Old Semantics

Runs a bounded PR completion cycle from the current branch. Current module evidence shows the cycle refuses main, refuses dirty worktrees, identifies the current PR, waits for green checks, merges safely, switches to main, pulls main, and verifies local gates.

Current evidence:

- `src/agentic_project_kit/ns_up_pr_completion.py:52-192` implements the old Python module.
- `src/agentic_project_kit/ns_up_pr_completion.py:86` and `src/agentic_project_kit/ns_up_pr_completion.py:181` still call `./ns dev`, so the module is not the desired portable target.
- `tests/test_repo_ns_entrypoint.py:105-120` and `tests/test_repo_ns_entrypoint.py:178-191` keep old module behavior covered.
- `src/agentic_project_kit/cli_commands/transfer.py:1186-1370` implements `agentic-kit transfer pr-complete`.
- `tests/test_transfer_pr_complete_command_contract.py` covers the modern transfer command contract.

### Current Equivalent

`agentic-kit transfer pr-complete` is the supported modern equivalent for the PR completion lifecycle. It waits for CI, performs safe merge, switches and pulls main, acknowledges rules, and runs post-merge completion.

### Decision

Document the existing command as the migration target and mark `agentic_project_kit.ns_up_pr_completion` obsolete for future cleanup. Do not add `agentic-kit up`; do not preserve `ns_up_pr_completion` as the supported route.

### Proposed Target

`agentic-kit transfer pr-complete`

### Required Tests

- Continue running `tests/test_transfer_pr_complete_command_contract.py`.
- Keep command-reference snapshot coverage for `agentic-kit transfer pr-complete`.
- Add or keep regression coverage that old compatibility code does not call removed `./ns dev` once the obsolete module is removed or rewired.
- Use protected-diff-plan for any cleanup because PR lifecycle commands touch governance and post-merge evidence.

### Risks

- The old module still contains `./ns dev` calls and can reintroduce non-portable behavior if reused.
- Replacing old `ns up` behavior with a new shallow wrapper would duplicate transfer lifecycle logic.
- `transfer pr-complete` has LLM-context and post-merge requirements that must stay explicit; migration work must not bypass them for convenience.

## `ns upload`

### Old Definition

`v0.4.6:ns:436-443`:

```bash
if [ "${1:-}" = "upload" ]; then
  shift
  if [ -x ".venv/bin/agentic-kit" ]; then
    .venv/bin/agentic-kit workflow upload "$@"
    exit $?
  fi
  agentic-kit workflow upload "$@"
  exit $?
fi
```

### Old Semantics

Delegates workflow evidence upload to the kit CLI.

Current evidence:

- `src/agentic_project_kit/cli_commands/workflow.py:403-422` registers `agentic-kit workflow upload` and `agentic-kit workflow upload-output`.
- `tests/test_workflow_request_cli.py:195-210` verifies `upload-output` uploads latest bounded output evidence.
- `tests/test_workflow_request_cli.py:213-228` verifies uploaded state is refused.
- `tests/test_workflow_request_cli.py:272-286` verifies `workflow upload` delegates to `upload-output`.

### Current Equivalent

`agentic-kit workflow upload` already exists and is tested. `agentic-kit workflow upload-output` is the explicit canonical action behind the alias.

### Decision

Document existing command. No migration needed.

### Proposed Target

`agentic-kit workflow upload`

### Required Tests

- Existing upload-output and upload alias tests are sufficient unless behavior changes.
- Command reference snapshot must continue to include both commands.

### Risks

- Introducing another upload command under `transfer` could bypass or confuse the workflow evidence lifecycle.
- Any upload behavior change must preserve refusal states such as already uploaded or cleanup pending.

## Implementation Order

1. Add `agentic-kit dev local-feature-gate` as the first real migration slice.
2. Harden `agentic-kit workflow go` with the old dirty-branch `git_pull_ff_only` guard if confirmed absent during implementation.
3. Document or link `agentic-kit transfer pr-complete` as the replacement for old `ns up`; only then remove or rewire obsolete `ns_up_pr_completion`.
4. Leave `agentic-kit workflow upload` unchanged unless tests or command reference drift.

Each slice must update command reference only when the public CLI surface changes.
