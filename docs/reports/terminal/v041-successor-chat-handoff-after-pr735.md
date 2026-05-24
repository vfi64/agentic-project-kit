# Successor Chat Handoff After PR735

We work in the repository `vfi64/agentic-project-kit`.

Do not start from chat memory. Reconstruct the state from the remote repository and the artifacts named here.

## Current safe state

- Main is safe after PR #735.
- Main merge commit: `c6e2690` (`Expand rule registry coverage for communication and execution rules (#735)`).
- Current release remains `0.4.1`; no release, tag, DOI, or GUI expansion happened in this slice.
- PRs #718-#735 established the governed rule-registry baseline:
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
  - PR #730: post-PR729 status and handoff refresh.
  - PR #731: deterministic rule-registry compatibility and conflict checks.
  - PR #732: post-PR731 status and handoff refresh.
  - PR #733: deterministic rule-registry migration-map completeness checks.
  - PR #734: post-PR733 status and handoff refresh.
  - PR #735: coverage expansion to eight mechanisms by adding `chat-communication-rules`, `chat-bootstrap-drift-rules`, and `portable-execution-rules`.

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
- `docs/reports/terminal/pr731-rule-registry-conflicts.log`
- `docs/reports/terminal/pr733-rule-registry-completeness.log`
- `docs/reports/terminal/pr735-rule-registry-coverage.log`

## Current rule-registry status

The governed rule registry is coverage-expanded, not finished.

Implemented:

- `.agentic/rule_mechanism_inventory.yaml`
- `.agentic/rule_migrations.yaml`
- `src/agentic_project_kit/rule_registry_validator.py`
- `agentic-kit rule-registry check`
- workflow-guard enforcement
- patch-preflight enforcement
- coverage for eight mechanisms: `summary-renderer`, `execution-mode-switch`, `rule-preservation-guard`, `workflow-guard`, `patch-preflight`, `chat-communication-rules`, `chat-bootstrap-drift-rules`, and `portable-execution-rules`
- required `category`, `priority`, and `enforcement_phase` metadata for active mechanisms
- deterministic compatibility checks for allowed `category`/`enforcement_phase` combinations
- deterministic conflict checks rejecting ambiguous active mechanisms with same category, priority, and enforcement_phase
- deterministic completeness checks for known legacy rule ids and migration-map dispositions

Still open:

- Continue targeted coverage expansion for remaining release, DOI, evidence, and typed-work-order rules.
- Keep documentation-management rebuild blocked until this targeted rule-registry coverage expansion is merged.

Estimated rule-system rebuild progress after PR735: roughly 90-92%.

## Communication and evidence rules

- `d`, `D`, `f`, `F`, `w`, and `p` are communication signals, not evidence.
- For PASS or normal FAIL, inspect repo-backed evidence before continuing.
- Manual paste is only for terminal kill, broken logging, unavailable evidence, unusable evidence, or explicit user request.
- Relevant workflow blocks must use the canonical structured SUMMARY renderer route.
- Legacy handmade `WORK RESULT` / `NEXT_CHAT_REPLY` summaries are drift.
- A PASS summary after an inner FAIL is a hard workflow defect unless the distinction between WORK, EVIDENCE, and OVERALL is explicit and correct.

## Next safe work

First do a small PR for targeted rule-registry coverage expansion for release/DOI/evidence/typed-work-order rules. Do not combine it with broad documentation migration, release work, GUI work, or major refactoring.

Suggested next PR title:

`Expand rule registry coverage for release and evidence rules`

Suggested scope:

- Add only a few additional active mechanisms or legacy dispositions, preferably release/DOI/evidence/typed-work-order rules still represented only as compatibility anchors.
- Preserve existing validator invariants and tests.
- Add focused tests that the new covered mechanisms have required sources and terms.
- Do not change release metadata, GUI behavior, or documentation registry structure.

After that, close out state again, then reassess whether documentation-management rebuild can resume.

## Required local sync after this handoff PR merges

After the closeout PR is merged, sync local main to the merge commit and verify:

- branch is `main`
- worktree is clean
- `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and this successor handoff prompt are on main
- `agentic-kit rule-registry check`, workflow-guard, patch-preflight, and normal docs gates pass in the active project environment
