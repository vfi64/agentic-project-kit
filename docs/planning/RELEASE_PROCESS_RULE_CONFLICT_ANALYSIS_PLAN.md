# Release Process Rule Conflict Analysis Plan

Status: active analysis handoff
Date: 2026-06-26
Branch: `codex/release-process-rule-conflict-analysis`
Repository: `vfi64/agentic-project-kit`

## Purpose

Prepare a Codex analysis slice that reviews the release process as a complete lifecycle, not as isolated commands. The goal is to find rules, gates, wrappers, generated handoff projections, release metadata checks, evidence requirements, and transfer protocols that currently block or contradict one another, then propose and implement the smallest safe fixes that make the whole release process reliable end to end.

This document is additive planning evidence. It does not replace generated successor handoff projections and does not change active rule authority by itself.

## Current transition state

- PR #1547 `Harden release process standard-error guardrails` is merged.
- PR #1548 `Refresh handoff state after PR1547` is merged.
- PR #1548 merge commit is `4d3903797990cbf1443cf9e1ba8cbc462c7a964f`.
- The generated latest handoff package on main still records generated head `c2169e6f`, because PR #1548 is the administrative refresh after PR #1547. Do not treat the older red PR #1548 run as the current blocker.
- Local working copies may still be behind main and must be synchronized before any local execution.

## Problem statement

The release process has accumulated multiple protective layers that are individually useful but can deadlock each other when composed:

1. Wrapper-first lifecycle rules require high-level `agentic-kit` commands for PR, merge, release, transfer, evidence, and handoff work.
2. Fresh-context, generated-handoff, and validation gates can block mutating lifecycle commands.
3. Release readiness, release metadata authority, release notes generation, and release publish dry-run/execute controls may disagree about the authoritative stage.
4. Evidence closeout requires finalized repo-readable logs, but release and handoff commands can create volatile files or generated projections that themselves trigger freshness or protected-file checks.
5. Transfer-file discipline prefers one canonical local command, while release work still exposes several separate commands that may require a strict stage model.
6. Generated handoff projections must not be manually edited, but stale generated markers can still create ambiguity after administrative refresh PRs.

Codex must analyze the composed system and not patch one symptom at a time.

## Required source files to inspect first

Codex must read these files before proposing mutations:

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

1. Build a release lifecycle map from clean main to post-release handoff closeout.
2. Identify every command involved in the release lifecycle, including readiness, metadata preparation, release notes, release status, publish dry-run, publish execute, post-release verification, DOI metadata handling, evidence finalization, post-merge complete, and successor handoff regeneration.
3. Classify each gate as one of:
   - prerequisite gate,
   - mutation gate,
   - post-mutation verification,
   - publication gate,
   - evidence closeout gate,
   - handoff/generator gate,
   - recovery-only exception.
4. Detect rule conflicts and deadlocks, especially:
   - fresh-context gate versus context-generation commands,
   - generated handoff freshness versus administrative refresh merge commits,
   - protected-file preservation versus release metadata updates,
   - evidence finalization versus volatile generated report files,
   - release readiness versus release publish dry-run/execute state,
   - transfer-file single-command protocol versus multi-command release workflow,
   - old `./ns` compatibility references versus active `agentic-kit` command authority.
5. Produce a machine-readable conflict table with fields:
   - `id`,
   - `stage`,
   - `rules_in_conflict`,
   - `observed_blocker_or_risk`,
   - `source_files`,
   - `minimal_fix`,
   - `tests_required`,
   - `next_mutation_allowed`.
6. Propose a single authoritative release stage model that names allowed transitions and blocked transitions.
7. Only after the analysis is explicit, implement the smallest guarded code/doc/test slice.

## Non-goals

- Do not publish a release.
- Do not create or push a release tag.
- Do not create GitHub Release artifacts.
- Do not write Zenodo DOI metadata.
- Do not manually edit generated latest handoff projections as the durable rule source.
- Do not broadly replace protected governance/status/handoff/YAML files.
- Do not resurrect removed `./ns` routes as active release workflow instructions.

## Expected implementation direction

Prefer a deterministic release lifecycle state model and one release-readiness composition command over scattered checks. A good target shape is:

1. `release-status --include-remote` reports current lifecycle state without mutation.
2. `release ready --version <target>` runs the full pre-mutation readiness bundle and standard-error scan.
3. `release prepare --version <target> --dry-run` proves metadata changes.
4. `release prepare --version <target> --write` performs only allowed metadata mutations and records evidence.
5. PR lifecycle uses `transfer pr-create-complete ... --post-merge-complete`.
6. Publication remains separately gated: `release-publish --dry-run` before any execute path.
7. Execute path requires explicit capability gates and cannot run from stale context or dirty state.
8. Post-release verification and DOI metadata update are separate documented stages.
9. Final closeout uses evidence finalization and successor handoff package regeneration through supported wrappers.

## Required tests and checks

Codex should add or update tests before changing behavior. Minimum expected coverage:

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
- No release tag, GitHub Release, or DOI mutation happened during this analysis slice.
- Handoff/closeout evidence is generated through supported wrappers, not chat-only claims.
