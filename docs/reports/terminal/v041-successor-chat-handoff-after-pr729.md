# Successor Chat Handoff After PR729

We work in the repository `vfi64/agentic-project-kit`.

Do not start from chat memory. Reconstruct the state from the remote repository and the artifacts named here.

## Current safe state

- Main is safe after PR #729.
- Main merge commit: `58573ed` (`Add rule registry classification and priority (#729)`).
- Current release remains `0.4.1`; no release, tag, DOI, or GUI expansion happened in this slice.
- PRs #718-#729 established the governed rule-registry baseline:
  - PR #718: mechanism inventory for `summary-renderer` and `execution-mode-switch`.
  - PR #721: migration-aware legacy rule entries.
  - PR #722: standalone rule registry validator.
  - PR #723: `rule-registry check` CLI command.
  - PR #724: workflow-guard integration with `rule-registry-drift` HARD-FAIL findings.
  - PR #725: patch-preflight integration for the governed rule registry.
  - PR #726: post-PR725 status and handoff refresh.
  - PR #727: coverage expansion from 2 to 5 core mechanisms: `summary-renderer`, `execution-mode-switch`, `rule-preservation-guard`, `workflow-guard`, and `patch-preflight`.
  - PR #728: post-PR727 status and handoff refresh.
  - PR #729: required `category`, `priority`, and `enforcement_phase` metadata for active rule mechanisms.

## Mandatory sources to read first

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. `.agentic/handoff_state.yaml`
10. `.agentic/rule_mechanism_inventory.yaml`
11. `.agentic/rule_migrations.yaml`
12. `src/agentic_project_kit/rule_registry_validator.py`
13. `src/agentic_project_kit/workflow_guard.py`
14. `src/agentic_project_kit/patch_artifact_preflight.py`
15. `tests/test_rule_mechanism_inventory.py`
16. `tests/test_rule_registry_validator.py`
17. `AGENTS.md`, `CHANGELOG.md`, `README.md`, `CITATION.cff`, and `docs/releases/VERIFIED_RELEASES.md` only if release or public-facing claims are touched.

## Evidence logs

Use direct-path-first remote fetches for known paths:

- `docs/reports/terminal/pr718a-v5-inventory.log`
- `docs/reports/terminal/pr721-rule-migrations.log`
- `docs/reports/terminal/pr722-rule-registry-validator.log`
- `docs/reports/terminal/pr723-rule-registry-cli.log`
- `docs/reports/terminal/pr724-rule-registry-guard.log`
- `docs/reports/terminal/pr725-rule-registry-preflight.log`
- `docs/reports/terminal/pr727-rule-registry-coverage.log`
- `docs/reports/terminal/pr729-rule-registry-classification.log`

## Current rule-registry status

The governed rule registry is classified, not finished.

Implemented:

- `.agentic/rule_mechanism_inventory.yaml`
- `.agentic/rule_migrations.yaml`
- `src/agentic_project_kit/rule_registry_validator.py`
- `agentic-kit rule-registry check`
- workflow-guard enforcement
- patch-preflight enforcement
- coverage for five core mechanisms: `summary-renderer`, `execution-mode-switch`, `rule-preservation-guard`, `workflow-guard`, and `patch-preflight`
- required `category`, `priority`, and `enforcement_phase` metadata for active mechanisms

Still open:

- Add deterministic compatibility and conflict checks.
- Add completeness checks so known active legacy rules cannot disappear without active, migrated, archived, or rejected status.
- Continue targeted coverage expansion for remaining active communication, evidence, release, bootstrap, and workflow rules.
- Keep documentation-management rebuild blocked until rule-registry coverage and conflict checks are merged.

Estimated rule-system rebuild progress after PR729: roughly 78-80%.

## Communication and evidence rules

- `d`, `D`, `f`, `F`, `w`, and `p` are communication signals, not evidence.
- For PASS or normal FAIL, inspect repo-backed evidence before continuing.
- Manual paste is only for terminal kill, broken logging, unavailable evidence, unusable evidence, or explicit user request.
- Relevant workflow blocks must use the canonical structured SUMMARY renderer route.
- Legacy handmade `WORK RESULT` / `NEXT_CHAT_REPLY` summaries are drift.
- A PASS summary after an inner FAIL is a hard workflow defect unless the distinction between WORK, EVIDENCE, and OVERALL is explicit and correct.

## Next safe work

First do a small PR for deterministic rule-registry compatibility and conflict checks. Do not combine it with completeness checks, release work, GUI work, broad documentation migration, or large coverage expansion.

Suggested next PR title:

`Add rule registry conflict checks`

Suggested scope:

- Extend the rule-registry validator with small, explicit compatibility checks.
- Reject duplicate active mechanism categories at the same priority only if they claim the same enforcement_phase and would create ambiguous enforcement ordering.
- Reject invalid phase/category combinations if needed through a small static matrix.
- Add negative tests for conflicting entries.
- Keep completeness checks and coverage expansion out of this PR.

After that, use a separate PR for rule-registry completeness checks.

## Required local sync after this handoff PR merges

After the closeout PR is merged, sync local main to the merge commit and verify:

- branch is `main`
- worktree is clean
- `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and this successor handoff prompt are on main
- `agentic-kit rule-registry check`, workflow-guard, patch-preflight, and normal docs gates pass in the active project environment
