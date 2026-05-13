Current version: 0.3.3

# Project Status

Status-date: 2026-05-13
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/doc-mesh-gate-policy

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, and documentation-mesh drift auditing.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

v0.3.3 is released and post-release verified.

Recent completed work since v0.3.2:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` so package-version drift is detected.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running local workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage for it.
- PR #141 prepared and released v0.3.3.
- PR #143 added the first bounded `agentic-kit doc-mesh-audit` slice with tests, documentation coverage, and the modular implementation rule.

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

Documentation-mesh audit state:

- `agentic-kit doc-mesh-audit` exists and currently checks machine-readable drift classes: version mismatch, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- The audit distinguishes current-state documents, governance documents, architecture/design documents, and historical-plan documents.
- The audit is intentionally deterministic and bounded. It does not claim semantic proof of documentation quality.

Adoption policy for `doc-mesh-audit`:

- For now, `doc-mesh-audit` remains a targeted special gate.
- It is required for changes to cross-document state, release metadata, documentation taxonomy, historical planning documents, DOI/version lists, handoff/status wording, documentation coverage, or cross-document drift rules.
- It is not yet part of every normal `ns`/default local gate run.
- After several successful PRs without false positives, reassess whether to integrate it into `agentic-kit doctor` as a documented project-health check.
- Only after that stabilization step, reassess whether the default `ns` workflow should run it unconditionally.

Rationale:

The audit is useful but still young. Adding it immediately to every standard workflow could block unrelated code changes because of documentation-taxonomy or historical-plan rules. The safer path is targeted use first, then promotion to `doctor` or the default workflow after observed stability.

Near-term documentation-governance roadmap:

1. Use `agentic-kit doc-mesh-audit` manually for documentation-mesh, release, handoff, governance, and roadmap changes.
2. Collect failure classes and false positives across a few PRs.
3. Add structured report output if needed before broad workflow integration.
4. Add bounded repair tools only for mechanical edits, for example aligning version/DOI lists, inserting historical banners, or updating known current-state fields.
5. Keep semantic review advisory and separate from hard gates unless converted into deterministic rules.

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

Document the adoption policy for `agentic-kit doc-mesh-audit`: targeted special gate first, possible later promotion to `doctor`, and only then possible integration into the default `ns` workflow.

## Current Blockers

- Local gates must pass on `docs/doc-mesh-gate-policy`.
- No code change should be introduced in this slice.

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

Run the standard local gate on `docs/doc-mesh-gate-policy`. Because this is a documentation-mesh policy change, also run `agentic-kit doc-mesh-audit`. If green, open and merge the focused documentation policy PR.
