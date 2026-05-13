Current version: 0.3.3

# Project Status

Status-date: 2026-05-13
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/plan-documentation-drift-audit

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, and workflow evidence capture.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

v0.3.3 is released and post-release verified.

Recent completed work since v0.3.2:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` so package-version drift is detected.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running local workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage for it.
- PR #141 prepared and released v0.3.3.

v0.3.3 release scope:

- Package-version drift detection.
- `ns` / `next-step.py` workflow usability.
- Project-local workflow environment bootstrap.
- Explicit `FAILED` workflow-state handling.

v0.3.3 release evidence:

- GitHub Release v0.3.3 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.3 version DOI: `10.5281/zenodo.20151924`.
- `agentic-kit post-release-check --version 0.3.3` passed.
- The post-release Zenodo verification is complete for v0.3.3.

Open planning item: documentation-mesh drift audit.

The project has a useful `docs/DOCUMENTATION_COVERAGE.yaml` matrix and deterministic document-quality gates, but these gates mainly check required terms and structural visibility. They do not fully prove that the whole documentation mesh is current, non-redundant, and semantically consistent.

Next documentation-governance work should audit the full documentation mesh for:

A. Aktualität / currency of release, roadmap, state, handoff, README, architecture, and workflow documents.
B. Redundanzen / duplicated status, release, roadmap, DOI, workflow, and gate explanations.
C. Konsistenz / agreement between project state, handoff, changelog, README, coverage matrix, architecture contract, and generated-project guidance.
D. automatische Aktualisierung und sichernder automatischer Test / deterministic checks and bounded repair tools that can detect or repair known drift classes.

Candidate implementation direction:

- Add a deterministic documentation-mesh audit command before adding broad repair behavior.
- Start with machine-checkable invariants such as current version, current release DOI list, branch/state labels, release-vs-pre-release wording, current workflow state, duplicated but inconsistent DOI/version lists, and stale release-candidate phrasing after publication.
- Report findings as structured data before any repair command is introduced.
- Add tests for each detected drift class.
- Add bounded repair tools only for mechanical edits, for example replacing release-candidate wording after a verified release, aligning version/DOI lists, or updating known current-state fields.
- Do not claim semantic proof; keep advisory review separate from deterministic gates.

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
- `docs/architecture/ARCHITECTURE_CONTRACT.md` is a required state gate document.
- `docs/DOCUMENTATION_COVERAGE.yaml` is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, semantic quality boundary language, next-step workflow behavior, environment bootstrap, and `FAILED` handling remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own machine-readable task gate configuration.

Project health diagnostics are CLI-supported:

- `agentic-kit doctor` checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift including package `__version__` drift.
- `agentic-kit check-docs` checks documentation coverage and deterministic document-quality heuristics.
- `agentic-kit release-plan` and `agentic-kit release-check` support release-state validation before maintainer-owned tagging and publication.
- `agentic-kit post-release-check` verifies GitHub release and Zenodo archive state after publication.

## Current Goal

Record the v0.3.3 DOI and the documentation-mesh drift audit as the next planning item without starting the large audit/refactor in this PR.

## Current Blockers

- Local gates must pass on `docs/plan-documentation-drift-audit`.
- The actual documentation-mesh audit command, tests, and repair tooling still need a separate implementation slice.

## Live Status Commands

Run:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

## Next Safe Step

Run the standard local gate on `docs/plan-documentation-drift-audit`. If green, merge this planning/DOI update. Then start a focused implementation branch for the documentation-mesh audit command and tests.
