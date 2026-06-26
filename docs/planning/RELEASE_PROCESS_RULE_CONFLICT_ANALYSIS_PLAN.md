# Release Process Rule Conflict Analysis Plan

Status: active analysis handoff
Date: 2026-06-26
Branch: `codex/release-process-rule-conflict-analysis`
Repository: `vfi64/agentic-project-kit`

## Purpose

Prepare a Codex analysis slice that reviews the release process as a complete lifecycle, not as isolated commands. The goal is to find rules, gates, wrappers, generated handoff projections, release metadata checks, evidence requirements, and transfer protocols that currently block or contradict one another.

This document is additive planning evidence. It does not replace generated successor handoff projections and does not change active rule authority by itself.

## Current transition state

- PR #1547 is merged.
- PR #1548 is merged.
- PR #1548 merge commit is `4d3903797990cbf1443cf9e1ba8cbc462c7a964f`.
- The generated latest handoff package may still record generated head `c2169e6f`, because PR #1548 refreshed the post-PR1547 state.
- Local working copies may still be behind main and must be synchronized before any local execution.

## Required source files to inspect first

Codex must read these files before proposing mutations:

- `docs/planning/RELEASE_PROCESS_RULE_CONFLICT_ANALYSIS_PLAN.md`
- `docs/handoff/CODEX_RELEASE_PROCESS_RULE_CONFLICT_HANDOFF.md`
- `docs/reports/release-process-rule-conflict-analysis-20260626/README.md`
- `docs/reports/release-process-rule-conflict-analysis-20260626/CODEX_PROMPT.md`
- `docs/reports/release-process-rule-conflict-analysis-20260626/execution_contract.json`
- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/reports/handoff-packages/latest/execution_contract.json`
- `docs/reports/handoff-packages/latest/source_manifest.json`
- `docs/reports/handoff-packages/latest/validation_report.json`
- `docs/reports/handoff-packages/latest/successor_context.yaml`
- `docs/reports/handoff-packages/latest/successor_prompt.md`
- `.agentic/compiled_agent_context.yaml`
- `.agentic/transfer_safety_rules.yaml`
- `.agentic/transfer/one_command_transfer_protocol.yaml`
- `docs/planning/project_direction.yaml`
- `docs/DOCUMENTATION_REGISTRY.yaml`
- `docs/reference/agentic-kit-commands.json`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/STATUS.md`
- `src/agentic_project_kit/*release*`
- `src/agentic_project_kit/*transfer*`
- `tests/*release*`
- `tests/*transfer*`

## Analysis tasks

1. Build a release lifecycle map from clean main to final handoff closeout.
2. Identify every command involved in readiness, metadata preparation, release notes, release status, publication gating, post-release verification, DOI metadata handling, evidence finalization, post-merge completion, and successor handoff regeneration.
3. Classify each gate as prerequisite, mutation, verification, publication, evidence, handoff/generator, or recovery-only.
4. Detect rule conflicts and deadlocks, especially around fresh context, generated handoff freshness, protected files, volatile reports, readiness versus publication state, transfer protocol composition, and legacy command references.
5. Produce a machine-readable conflict table with `id`, `stage`, `rules_in_conflict`, `observed_blocker_or_risk`, `source_files`, `minimal_fix`, `tests_required`, and `next_mutation_allowed`.
6. Propose one authoritative release stage model.
7. Only after the analysis is explicit, implement the smallest guarded code/doc/test slice.

## Boundaries

- No release publication in this analysis slice.
- No tag or DOI changes in this analysis slice.
- Do not manually edit generated latest handoff projections as the durable rule source.
- Do not broadly replace protected governance/status/handoff/YAML files.
- Do not restore removed `./ns` routes as active release workflow instructions.

## Expected implementation direction

Prefer a deterministic release lifecycle state model and one release-readiness composition command over scattered checks.

A good target shape is:

1. read-only release status,
2. release readiness bundle,
3. release metadata dry-run,
4. release metadata write with evidence,
5. PR lifecycle through supported transfer wrappers,
6. separate publication dry-run before execute path,
7. separate post-release verification and DOI metadata stages,
8. final closeout through evidence and successor handoff wrappers.

## Required tests and checks

Expected coverage:

- release stage model unit tests,
- rule-conflict fixture tests,
- command-composition tests for release workflow,
- protected-file release metadata tests,
- fresh-context exception tests for diagnostic/read-only commands,
- transfer/handoff freshness tests for admin refresh merge commits,
- regression tests for removed `./ns` release routes.

Run only repo-supported gates. Stop on BLOCK or FAIL.

## Done criteria

- A Codex analysis report exists in repo-backed form.
- The conflict table is machine-readable.
- The release lifecycle has one documented stage model.
- At least one small, tested, non-publication fix is implemented or a precise follow-up plan exists if implementation is unsafe.
- Handoff/closeout evidence is generated through supported wrappers, not chat-only claims.
