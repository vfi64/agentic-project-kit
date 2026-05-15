Current version: 0.3.8

# Project Status

Status-date: 2026-05-15
Project: agentic-project-kit
Primary branch: main
Current work branch: release/v0.3.8

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, and documentation-mesh drift auditing.

The project itself has a current state layer so work can be continued from the repository state files. Its development model treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, and release metadata.

## Current State

v0.3.7 is released and post-release verified. Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`. The post-release Zenodo verification is complete for v0.3.7.

Post-v0.3.6 main has advanced beyond the release tag with governance, usability, workflow-cleanup hardening, Pattern Advisor concept preservation, and a small Guided CLI usability improvement:

- PR #163 recorded the verified v0.3.6 DOI metadata on main.
- PR #164 preserved the Deterministic Cell Orchestration idea note and introduced the Layered CLI Usability idea note.
- PR #165 updated `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after the idea-note merge.
- PR #166 hardened `agentic-kit workflow cleanup` so stale `temp/workflow-evidence-*` branches can be removed even when `.agentic/workflow_state` is already `IDLE`.
- PR #167 updated current-state and handoff documentation after workflow cleanup hardening.
- PR #168 added `docs/ideas/PATTERN_ADVISOR.md` as a non-binding idea note / architecture research track.
- PR #170 added read-only `agentic-kit workflow status --explain` guidance for common workflow states.
- PR #171 updated current-state and handoff documentation after PR #170.
- PR #172 completed Guided Workflow Usability v1 by adding read-only safety wording, `current_report` explanation, a README quick command guide, and a guided status compass.

The v0.3.7 release-preparation PR was merged on main after:

```text
0161838 Complete guided workflow status usability (#172)
a2d5e68 Update status and handoff after workflow status explain (#171)
1d0c5f4 Explain workflow status next steps (#170)
```

The latest verified gates before v0.3.7 release preparation were:

- `162 passed`
- `ruff check .` passed
- `agentic-kit check-docs` passed
- `agentic-kit doctor` passed
- `agentic-kit doc-mesh-audit` passed

## Recent completed work since v0.3.5

- PR #158 updated the AI-assisted development roadmap.
- PR #159 added the Deterministic Cell Orchestration decision rule and governed workflow design rules to `AGENTS.md` and state docs.
- PR #160 aligned `agentic-kit workflow request` with the explicit current-work request mechanism.
- PR #161 added `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` as an idea note for Event-Sourcing Light, Capability Matrix, ADR Policy, State-Model Templates, and related governed workflow patterns.
- PR #162 prepared v0.3.6 release metadata.
- PR #163 recorded verified v0.3.6 DOI metadata.
- PR #164 added `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`, `docs/ideas/LAYERED_CLI_USABILITY.md`, and small `AGENTS.md` cross-references.
- PR #165 refreshed current-state and handoff documentation after PR #164.
- PR #166 added stale workflow evidence cleanup from `IDLE` plus a regression test, raising the suite to 156 tests.
- PR #167 refreshed current-state and handoff documentation after PR #166.
- PR #168 added `docs/ideas/PATTERN_ADVISOR.md` as a curated idea note without CLI, code, ADR, release, or pattern-catalog implementation.
- PR #170 added read-only `agentic-kit workflow status --explain`, documented it, and raised the suite to 160 tests.
- PR #171 refreshed current-state and handoff documentation after PR #170.
- PR #172 completed Guided Workflow Usability v1 and raised the suite to 162 tests.

## Idea-note state

The repository has four related non-binding architecture idea notes:

- `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
- `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
- `docs/ideas/LAYERED_CLI_USABILITY.md`
- `docs/ideas/PATTERN_ADVISOR.md`

These documents preserve architecture options without making them automatic implementation requirements.

Deterministic Cell Orchestration remains optional. Use it only when typed cells, independent validation, selective repair, deterministic rendering, or auditability clearly reduce drift and overall workflow complexity.

Layered CLI Usability is a review lens for keeping the public command surface manageable. The intended direction is high functionality and high automation internally while keeping the daily Golden Path simple.

Pattern Advisor remains optional and advisory. It preserves the idea of mapping recurring project evidence to reusable patterns, anti-patterns, and candidate patterns without becoming an autopilot, a gate, or a wrapper-specific subsystem.

No ADR has been created for these idea notes. An ADR should be considered only when DCO, layered CLI usability, Pattern Advisor behavior, capability boundaries, or a guided CLI entry point become binding architecture or public CLI policy.

## Documentation-mesh audit state

- `agentic-kit doc-mesh-audit` exists and currently checks machine-readable drift classes: version mismatch, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- The audit distinguishes current-state documents, release-history documents, governance documents, architecture/design documents, and historical-plan documents.
- The audit can write machine-readable JSON reports and bounded repair plans.
- `agentic-kit doc-mesh-repair` can insert missing historical-source-of-truth banners into known historical-plan documents.
- Version, DOI, stale-state, and missing-document findings remain manual review items.
- The audit is deterministic and bounded. It does not claim semantic proof of documentation quality.

## Workflow request state

- `.agentic/workflow_state` is expected to be `IDLE`.
- `.agentic/current_work.yaml` may remain present with `state: READY`.
- A normal `ns` run in `IDLE` plus `READY` is intentionally a no-op.
- A workflow starts only by explicit request.
- The public path is `agentic-kit workflow request`, `agentic-kit workflow run`, `agentic-kit workflow status`, `agentic-kit workflow status --explain`, and `agentic-kit workflow cleanup`.
- `agentic-kit workflow cleanup` now also removes stale `temp/workflow-evidence-*` branches from `IDLE` when run inside a Git repository.
- `tools/next-step.py` remains a compatibility bridge and should not grow into the long-term public API surface.

## AI-assisted development assessment

The project is strongest as a governed AI-assisted software development layer, not as an autonomous coding agent. Its main design choice is to move durable project state out of the model context and into version-controlled repository files.

Strengths:

- Repository files act as the durable source of truth for status, handoff, architecture constraints, test gates, workflow state, and release evidence.
- Deterministic gates (`pytest`, `ruff`, `check-docs`, `doctor`, `doc-mesh-audit`, and release checks) remain separate from model-generated advice.
- Explicit workflow states reduce blind agent execution and make idle/no-op behavior intentional.
- Temporary workflow evidence branches provide auditable transfer of local outputs when chat context cannot reliably carry all details.
- Release metadata, DOI verification, and post-release checks make publication state reproducible.
- Idea notes preserve useful architecture options without immediately expanding implementation scope.

Limits:

- The project is not a full agent orchestrator.
- Semantic quality review remains advisory and human-owned unless converted into deterministic checks.
- Some compatibility affordances still exist under `tools/` and should remain bounded.
- Onboarding and day-to-day CLI use must stay simple despite the growing governance vocabulary.

Interpretation:

agentic-project-kit should be treated as a governance and state layer for AI-assisted development: the model can help, but repository state, deterministic gates, evidence, and release metadata remain authoritative.

## Roadmap

Near-term public workflow CLI roadmap:

1. Keep `agentic-kit workflow request/run/status/cleanup` as the public path for explicit workflow operation.
2. Keep `tools/next-step.py` as a compatibility bridge, not as the long-term public API surface.
3. Continue hardening state, no-op, failure, cleanup, and evidence behavior through tests and documentation.
4. Watch `workflow cleanup` across future evidence-branch flows to see whether remote branch deletion, missing remotes, or multi-branch cleanup need more explicit UX.

Near-term usability roadmap:

1. Use `docs/ideas/LAYERED_CLI_USABILITY.md` as a review lens before adding new public CLI surface area.
2. Keep the Golden Path close to the Daily layer: `ns`, `doctor`, `check-docs`, and `workflow status`.
3. Place future commands or options into Daily, Guided, Maintainer, or Debug before treating them as part of the public experience.
4. Consider an ADR only if usability layers become binding command policy or capability boundaries.

Future Deterministic Cell Orchestration architecture track:

1. Treat Deterministic Cell Orchestration (DCO) as an optional decision pattern for complex, rule-bound AI-generated outputs.
2. Use DCO when typed cells, independent validation, selective repair, deterministic rendering, or auditability clearly reduce drift.
3. Do not use DCO when a simple Markdown document, CLI command, gate, or report is clearer and easier to maintain.
4. Keep DCO aligned with the semantic quality boundary: it can prove structure and known rules, not broad semantic correctness unless semantics are converted into deterministic checks.
5. Prefer a small later pilot for handoff, review, release, or report artifacts before applying DCO to more complex systems.
6. If a pilot is added, require schema tests, validator tests, bounded repair tests where repair exists, and renderer tests where deterministic rendering exists.

Future Pattern Advisor architecture track:

1. Treat Pattern Advisor as an optional advisory layer for recurring project problem classes.
2. Keep any future Pattern Advisor output advisory-only, not a deterministic gate.
3. Do not implement `patterns suggest`, `advise`, candidate capture, or pattern promotion before a small read-only catalog MVP has proven useful.
4. Keep wrapper-project lessons as evidence sources, not wrapper-specific kit behavior.
5. Consider an ADR only if a public `agentic-kit patterns` / `agentic-kit advise` CLI, binding lifecycle, or advisory behavior becomes maintained architecture.

Near-term documentation-governance roadmap:

1. Use `agentic-kit doc-mesh-audit` manually for documentation-mesh, release, handoff, governance, roadmap, and current-state changes.
2. Collect failure classes and false positives across a few PRs.
3. Use structured JSON reports for review and CI-friendly evidence.
4. Keep bounded repair tools limited to mechanical edits, such as historical banners or later carefully scoped version/DOI list alignment.
5. Keep semantic review advisory and separate from hard gates unless converted into deterministic rules.

Product-positioning roadmap:

1. Document the project as a governed AI-assisted development layer, not as a promise of autonomous agent correctness.
2. Explain the problem solved by the project: chat context drift, branch drift, unclear handoff state, local-output transfer, release-state drift, unmanaged CLI complexity, and recurring architecture-pattern drift.
3. Keep the first-run path simple enough for a new maintainer to understand without reading every governance document.
4. Provide compact example flows for health checks, explicit workflow request/run/status/cleanup, and release verification.

## Project-level state documentation

Project-level state documentation is present on main:

- `.agentic/project.yaml`
- `sentinel.yaml`
- `.agentic/todo.yaml`
- `docs/STATUS.md`
- `docs/TEST_GATES.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/architecture/ARCHITECTURE_CONTRACT.md`
- `docs/architecture/AGENTIC_CODING_RESEARCH_INPUTS.md`
- `docs/architecture/references.bib`
- `docs/DOCUMENTATION_COVERAGE.yaml`
- `docs/WORKFLOW_OUTPUT_CYCLE.md`
- `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
- `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
- `docs/ideas/LAYERED_CLI_USABILITY.md`
- `docs/ideas/PATTERN_ADVISOR.md`

Project-level state documentation is machine-checkable:

- `agentic-kit check-docs` checks the state gate documents.
- `agentic-kit doc-mesh-audit` checks bounded cross-document drift classes for targeted documentation-mesh changes.
- `docs/architecture/ARCHITECTURE_CONTRACT.md` is a required state gate document.
- `docs/DOCUMENTATION_COVERAGE.yaml` is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, semantic quality boundary language, next-step workflow behavior, environment bootstrap, `FAILED` handling, and documentation-mesh audit visibility remain visible.
- `sentinel.yaml` and `.agentic/todo.yaml` are present so the repository validates its own machine-readable task gate configuration.

## Project health diagnostics

- `agentic-kit doctor` checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift including package `__version__` drift.
- `agentic-kit check-docs` checks documentation coverage and deterministic document-quality heuristics.
- `agentic-kit doc-mesh-audit` checks targeted documentation-mesh drift classes but is not yet part of the standard doctor/default workflow.
- `agentic-kit release-plan` and `agentic-kit release-check` support release-state validation before maintainer-owned tagging and publication.
- `agentic-kit post-release-check` verifies GitHub release and Zenodo archive state after publication.

## Current Goal

Prepare v0.3.8 release metadata for the merged Guided CLI Usability v2 status guidance slice.

## Current Blockers

- Local gates must pass on `docs/record-v0.3.7-doi`.
- Release metadata, package version, citation metadata, changelog, status, and handoff must agree before tagging.

## Live Status Commands

Run:

```bash
git status --short
git branch --show-current
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
```

## Next Safe Step

Validate `release/v0.3.8`. If green, open and merge a focused release metadata PR. After merge, tag `v0.3.8`, verify the GitHub release, then perform post-release Zenodo verification and record the version DOI.
