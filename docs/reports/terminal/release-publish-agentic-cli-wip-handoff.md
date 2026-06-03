# Release Publish Agentic CLI WIP Handoff

## Current state

Branch:

```text
feature/harden-release-publish-head-guards
```

Status:

```text
 M src/agentic_project_kit/release_publish_core.py
 M tests/test_release_publish_core.py
```

Diff stat:

```text
 src/agentic_project_kit/release_publish_core.py | 37 ++++++++++
 tests/test_release_publish_core.py              | 97 +++++++++++++++++++++++++
 2 files changed, 134 insertions(+)
```

## Active WIP

Branch:

`feature/harden-release-publish-head-guards`

Expected dirty files:

- `src/agentic_project_kit/release_publish_core.py`
- `tests/test_release_publish_core.py`

The current changes are unfinished WIP, not PASS.

## Goal

Implement a clean official `agentic-kit release-publish` command.

Required scope:

1. Replace partial `release_publish_core.py` changes with a guarded dynamic Python core.
2. Register official `agentic-kit release-publish`.
3. Update tests for agentic-kit CLI and guarded publish semantics.
4. No `./ns` calls inside `release_publish_core.py`.
5. Version must be dynamic, not hard-coded to `v0.4.4`.
6. Confirmation token must be `publish-v<version>`.
7. Add optional `--expected-head-sha` with full-SHA guard.
8. Guards required: main branch, clean tree, local tag absence, remote tag absence, GitHub release absence, created tag target.
9. Inconclusive remote tag or GitHub release lookup blocks before tag creation.
10. No tag push if the created tag does not point at expected/current HEAD.
11. Add small tested agentic-kit/core wrapper for guarded tag creation/push if existing code is insufficient.

## Next-chat first commands

```zsh
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
./.venv/bin/agentic-kit boot prompt
./.venv/bin/agentic-kit rules acknowledge --next-allowed-action run_next_command
git branch --show-current
git status --short
git diff --stat
cat docs/reports/terminal/release-publish-agentic-cli-wip-handoff.md
```

## Required verification

```zsh
./.venv/bin/python -m pytest tests/test_release_publish_core.py tests/test_release.py tests/test_release_prep_core.py tests/test_release_preflight_phase.py tests/test_release_doi_safety.py tests/test_v036_release_route_help_safety.py tests/test_repo_ns_entrypoint.py
./.venv/bin/python -m ruff check src/agentic_project_kit/release_publish_core.py src/agentic_project_kit/cli_commands/release.py tests/test_release_publish_core.py
./.venv/bin/python -m ruff check .
./.venv/bin/python -m pytest
```

## Boot prompt snapshot

```text
CHAT_BOOTLOADER

Purpose: bootstrap a successor chat from repository truth.

Mandatory boot sources:
- [present] .agentic/compiled_agent_context.yaml
- [present] .agentic/handoff_state.yaml
- [present] .agentic/rule_mechanism_inventory.yaml
- [present] .agentic/rule_migrations.yaml
- [present] .agentic/rule_preservation.yaml
- [present] docs/STATUS.md
- [present] docs/handoff/CURRENT_HANDOFF.md
- [present] docs/handoff/START_NEW_CHAT_PROMPT.md
- [present] docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- [present] docs/governance/FINAL_SUMMARY_CONTRACT.md
- [present] docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- [present] docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- [present] docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- [present] docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
- [present] docs/planning/WORKFLOW_REDUCTION_FOCUS.md

Mandatory workflow rules:
- Start from repository artifacts instead of chat memory.
- Read mandatory boot sources before repository changes.
- Prefer Python runners for local workflow execution; shell remains a thin adapter.
- Use run_summary_renderer for final summaries in evidence-bearing workflows.
- Evidence-bearing local workflow finalization must use `agentic-kit evidence finalize-log` or a stricter successor. Freehand final PASS footers are not valid closeout evidence.
- Treat d, f, and w as communication signals rather than evidence.
- Run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence before continuing after chat control signals.
- Inspect repo or remote evidence before requesting pasted terminal output.
- Use the supported protected-change planning route before protected YAML, JSON, or Markdown control changes: `./ns protected-change-plan --diff-file <file>` or `python -m agentic_project_kit.protected_change_planner --diff-file <file>`. Do not use `agentic-kit protected-change-plan`; that package CLI command is not registered.
- Before a chat switch, run the closeout prompt and check whether START_NEW_CHAT_PROMPT.md, CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md, and NEXT_CHAT_BOOTSTRAP.md all need updates.

Required first action in a successor chat:
- Read these sources and verify main, open PRs, CI, STATUS, handoff, rule registry, and final-summary contracts before repository changes.
- If continuing after a chat control signal, run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence first.

### RESULT: PASS ###
```

## Handoff check

```text
Persistent handoff state check passed
Documentation registry:
- registry: docs/DOCUMENTATION_REGISTRY.yaml
- version: 1
- documents: 25
- broad_migration_allowed: False
- class:architecture: 1
- class:evidence/log: 2
- class:generated artifact: 1
- class:governance/system: 4
- class:operational/automation: 4
- class:planning: 10
- class:release: 2
- class:user-facing description: 1
```

## Handoff show

```text
Repo: agentic-project-kit
Path: agentic-project-kit
Remote: github.com:vfi64/agentic-project-kit
Version: 0.4.5
Safe state: main @ 435cb68
Next: Start the next chat from the fresh post-PR1011 successor handoff prompt. Verify main at 50c73ac, confirm the post-PR1011 closeout evidence log passes explicit summary inspection, then continue only with B11 Gatekeeper Core or another allowed small test-backed slice.
```
