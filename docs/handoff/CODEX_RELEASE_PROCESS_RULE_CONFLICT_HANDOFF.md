# Codex Release Process Rule Conflict Handoff

Status: active handoff for Codex analysis
Date: 2026-06-26
Repo: `vfi64/agentic-project-kit`
Branch: `codex/release-process-rule-conflict-analysis`
Base: `main` after PR #1548

## Start state

Use the current remote `main` state as source of truth. Do not work from chat memory.

Known transition evidence:

- PR #1547 `Harden release process standard-error guardrails` is merged.
- PR #1548 `Refresh handoff state after PR1547` is merged.
- PR #1548 merge commit: `4d3903797990cbf1443cf9e1ba8cbc462c7a964f`.
- Older red PR #1548 checks are stale and must not be treated as current blockers.
- The latest generated handoff package records generated head `c2169e6f`, because it represents the post-PR1547 state refreshed by PR #1548.

## Operating rules

Follow the repo-backed execution contract. In case of disagreement, machine-readable repo files win.

Keep these constraints:

- Use `agentic-kit` wrappers as the control plane.
- Prefer wrapper-first, transfer-file second, copy/paste shell only as fallback.
- Stop on BLOCK or FAIL and diagnose before mutation.
- Do not manually edit generated latest handoff projections as durable rule sources.
- Do not broadly replace protected governance/status/handoff/YAML files.
- Do not use stale prompt text or chat summaries as evidence.
- Do not publish a release, push a tag, create a GitHub Release, or write Zenodo DOI metadata in this analysis slice.

## Mission for Codex

Analyze the release process as one composed system. Find rules, gates, commands, generated projections, freshness checks, evidence requirements, and transfer protocols that block, contradict, or race each other.

The goal is to make the release process in its individual stages and as a full lifecycle deterministic, testable, and operationally usable.

## Required first actions

1. Read `docs/planning/RELEASE_PROCESS_RULE_CONFLICT_ANALYSIS_PLAN.md`.
2. Read `docs/reports/handoff-packages/codex-release-process-rule-conflict-analysis-20260626/source_manifest.json`.
3. Read `docs/reports/handoff-packages/codex-release-process-rule-conflict-analysis-20260626/execution_contract.json`.
4. Read the source files listed in the manifest.
5. Build a release lifecycle stage map before editing code.
6. Produce a conflict table before implementing fixes.

## Scope boundary

Allowed:

- read-only release lifecycle analysis,
- tests for lifecycle composition,
- small non-publication code fixes,
- additive documentation of the stage model,
- command-reference/handoff visibility fixes only through supported regeneration paths,
- repo-backed evidence reports.

Out of scope:

- release publication,
- tag creation,
- GitHub Release creation,
- DOI metadata updates,
- manual direct edits to generated latest handoff projections as the rule source,
- broad protected-file rewrites,
- resurrecting removed `./ns` commands as active release paths.

## Expected outputs

Codex should leave these outputs or their supported successors:

- a machine-readable conflict report,
- a Markdown analysis report,
- a release lifecycle stage model,
- tests proving the model and known deadlocks,
- a small implementation slice or a precise blocked-state report,
- final evidence through supported `agentic-kit` wrappers.
