Current version: 0.3.5

# Project Status

Status-date: 2026-05-13
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/dco-decision-rule

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, and documentation-mesh drift auditing.

The project itself has a current state layer so work can be continued from the repository state files. Its development model treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, and release metadata.

## Current State

v0.3.5 is released and post-release verified.

v0.3.5 release evidence is verified:

- GitHub Release v0.3.5 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.5 version DOI: `10.5281/zenodo.20169965`.
- `agentic-kit post-release-check --version 0.3.5` passed.
- The post-release Zenodo verification is complete for v0.3.5.
- PR #157 recorded the verified v0.3.5 DOI metadata on main.
- PR #158 updated the AI-assisted development roadmap after v0.3.5.

Recent completed work since v0.3.3:

- PR #143 added the first bounded `agentic-kit doc-mesh-audit` slice with tests, documentation coverage, README v0.3.2 DOI restoration, and the modular implementation rule.
- PR #144 documented the adoption policy: targeted special gate first, possible later promotion to `doctor`, and only then possible default `ns` integration after stabilization.
- PR #145 added JSON report output for `agentic-kit doc-mesh-audit --report`.
- PR #146 added bounded documentation mesh repair planning through `agentic-kit doc-mesh-audit --repair-plan`.
- PR #147 added `agentic-kit doc-mesh-repair` for the first safe automatic repair class: inserting missing historical-source-of-truth banners into historical-plan documents.
- PR #153 made the `ns` idle state require an explicit workflow request.
- PR #154 added explicit `ns` workflow request mode.
- PR #155 documented explicit `ns` workflow request mode.
- PR #156 prepared v0.3.5 release metadata.
- PR #157 recorded v0.3.5 DOI metadata.
- PR #158 documented the post-v0.3.5 AI-assisted development roadmap.

Documentation-mesh audit state:

- `agentic-kit doc-mesh-audit` exists and currently checks machine-readable drift classes: version mismatch, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- The audit distinguishes current-state documents, release-history documents, governance documents, architecture/design documents, and historical-plan documents.
- The audit can write machine-readable JSON reports.
- The audit can write bounded repair plans.
- `agentic-kit doc-mesh-repair` can insert missing historical-source-of-truth banners into known historical-plan documents.
- Version, DOI, stale-state, and missing-document findings remain manual review items.
- The audit is intentionally deterministic and bounded. It does not claim semantic proof of documentation quality.

Workflow request state:

- `.agentic/workflow_state` is expected to be `IDLE` after the v0.3.5 post-release cycle.
- `.agentic/current_work.yaml` may remain present with `state: READY`.
- A normal `ns` run in `IDLE` plus `READY` is intentionally a no-op.
- A workflow run now requires an explicit request.
- The current internal compatibility path is `tools/next-step.py --request` followed by `ns`.
- The next public-product step is to expose the same request behavior through `agentic-kit workflow request`.

## AI-assisted development assessment

The project is currently strongest as a governed AI-assisted software development layer, not as an autonomous coding agent. Its main design choice is to move durable project state out of the model context and into version-controlled repository files.

Strengths:

- Repository files act as the durable source of truth for status, handoff, architecture constraints, test gates, workflow state, and release evidence.
- Deterministic gates (`pytest`, `ruff`, `check-docs`, `doctor`, `doc-mesh-audit`, and release checks) remain separate from model-generated advice.
- Explicit workflow states reduce blind agent execution and make idle/no-op behavior intentional.
- Temporary workflow evidence branches provide auditable transfer of local outputs when chat context cannot reliably carry all details.
- Release metadata, DOI verification, and post-release checks make publication state reproducible.

Limits:

- The project is not a full agent orchestrator.
- Semantic quality review remains advisory and human-owned unless converted into deterministic checks.
- Some workflow affordances are still internal (`tools/next-step.py`) and should move behind public CLI commands.
- Onboarding must stay simple despite the growing governance vocabulary.

Interpretation:

agentic-project-kit should be treated as a governance and state layer for AI-assisted development: the model can help, but repository state, deterministic gates, evidence, and release metadata remain authoritative.

## Roadmap

Near-term public workflow CLI roadmap:

1. Add `agentic-kit workflow request` as the public equivalent of `tools/next-step.py --request`.
2. Keep `tools/next-step.py` as a compatibility bridge, not as the long-term public API surface.
3. Add tests showing that READY/IDLE plus `workflow request` activates the request state and that a normal `ns` remains a no-op without an explicit request.
4. Add or update documentation for the public `agentic-kit workflow request/run/status/cleanup` path.
5. Add `agentic-kit workflow status` next, so users can inspect workflow state without reading `.agentic/current_work.yaml` directly.
6. Add `agentic-kit workflow cleanup` for explicit cleanup of uploaded temporary evidence branches.
7. Reassess whether `agentic-kit workflow run` should call the same runner used by `ns`, or remain a safer status/request-oriented command first.

Future Deterministic Cell Orchestration architecture track:

1. Treat Deterministic Cell Orchestration (DCO) as an optional decision pattern for complex, rule-bound AI-generated outputs.
2. Use DCO when typed cells, independent validation, selective repair, deterministic rendering, or auditability clearly reduce drift.
3. Do not use DCO when a simple Markdown document, CLI command, gate, or report is clearer and easier to maintain.
4. Keep DCO aligned with the semantic quality boundary: it can prove structure and known rules, not broad semantic correctness unless semantics are converted into deterministic checks.
5. Prefer a small later pilot for handoff, review, release, or report artifacts before applying DCO to more complex systems such as SCI traces.
6. If a pilot is added, require schema tests, validator tests, bounded repair tests where repair exists, and renderer tests where deterministic rendering exists.

Near-term documentation-governance roadmap:

1. Use `agentic-kit doc-mesh-audit` manually for documentation-mesh, release, handoff, governance, and roadmap changes.
2. Collect failure classes and false positives across a few PRs.
3. Use structured JSON reports for review and CI-friendly evidence.
4. Keep bounded repair tools limited to mechanical edits, such as historical banners or later carefully scoped version/DOI list alignment.
5. Keep semantic review advisory and separate from hard gates unless converted into deterministic rules.

Product-positioning roadmap:

1. Document the project as a governed AI-assisted development layer, not as a promise of autonomous agent correctness.
2. Add a short problem-oriented explanation: chat context drift, branch drift, unclear handoff state, local-output transfer, and release-state drift.
3. Keep the first-run path simple enough for a new maintainer to understand without reading every governance document.
4. Provide a compact example flow: request workflow, run gate, upload evidence, inspect status, cleanup evidence.

Project-level state documentation is present on main:

- .agentic/project.yaml
- sentinel.yaml
- .agentic/todo.yaml
- docs/STATUS.md
- docs/TEST_GATES.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/architecture/ARCHITECTURE_CONTRACT.md
- docs/architecture/AGENTIC_CODING_RESEARCH_INPUTS.md
- docs/architecture/references.bib
- docs/DOCUMENTATION_COVERAGE.yaml
- docs/WORKFLOW_OUTPUT_CYCLE.md

Project-level state documentation is machine-checkable:

- `agentic-kit check-docs` checks the state gate documents.
- `agentic-kit doc-mesh-audit` checks bounded cross-document drift classes for targeted documentation-mesh changes.
- `docs/architecture/ARCHITECTURE_CONTRACT.md` is a required state gate document.
- `docs/DOCUMENTATION_COVERAGE.yaml` is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, semantic quality boundary language, next-step workflow behavior, environment bootstrap, `FAILED` handling, and documentation-mesh audit visibility remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own machine-readable task gate configuration.

Project health diagnostics are CLI-supported:

- `agentic-kit doctor` checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift including package `__version__` drift.
- `agentic-kit check-docs` checks documentation coverage and deterministic document-quality heuristics.
- `agentic-kit doc-mesh-audit` checks targeted documentation-mesh drift classes but is not yet part of the standard doctor/default workflow.
- `agentic-kit release-plan` and `agentic-kit release-check` support release-state validation before maintainer-owned tagging and publication.
- `agentic-kit post-release-check` verifies GitHub release and Zenodo archive state after publication.

## Current Goal

Record the DCO decision rule and architecture track so future agents must check whether cell-based structured outputs would reduce drift before choosing a simpler or more complex output shape.

## Current Blockers

- Local gates must pass on the DCO decision-rule branch.
- `agentic-kit doc-mesh-audit` should be run because this changes governance and roadmap wording.
- DCO is not implemented yet; this branch only records the decision rule and future architecture track.

## Live Status Commands

Run:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit doc-mesh-audit
```

## Next Safe Step

Validate the focused DCO decision-rule documentation branch. If green, open and merge a documentation PR. After merge, return to `feature/workflow-request-cli` and implement `agentic-kit workflow request` as the public equivalent of `tools/next-step.py --request`, with tests and documentation updates.
