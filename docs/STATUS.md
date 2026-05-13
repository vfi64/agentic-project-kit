Current version: 0.3.5

# Project Status

Status-date: 2026-05-13
Project: agentic-project-kit
Primary branch: main
Current work branch: post-release/record-v0.3.5-doi

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, and documentation-mesh drift auditing.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

v0.3.5 is released and post-release verified.

Recent completed work since v0.3.3:

- PR #143 added the first bounded `agentic-kit doc-mesh-audit` slice with tests, documentation coverage, README v0.3.2 DOI restoration, and the modular implementation rule.
- PR #144 documented the adoption policy: targeted special gate first, possible later promotion to `doctor`, and only then possible default `ns` integration after stabilization.
- PR #145 added JSON report output for `agentic-kit doc-mesh-audit --report`.
- PR #146 added bounded documentation mesh repair planning through `agentic-kit doc-mesh-audit --repair-plan`.
- PR #147 added `agentic-kit doc-mesh-repair` for the first safe automatic repair class: inserting missing historical-source-of-truth banners into historical-plan documents.

v0.3.5 release scope:

- Documentation mesh audit.
- Machine-readable doc-mesh JSON report output.
- Bounded doc-mesh repair planning.
- First safe automatic historical-banner repair.
- Continued documentation of the targeted-gate adoption policy.

v0.3.5 release evidence is verified:

- GitHub Release v0.3.5 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.5 version DOI: `10.5281/zenodo.20169965`.
- `agentic-kit post-release-check --version 0.3.5` passed.
- The post-release Zenodo verification is complete for v0.3.5.

Documentation-mesh audit state:

- `agentic-kit doc-mesh-audit` exists and currently checks machine-readable drift classes: version mismatch, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- The audit distinguishes current-state documents, release-history documents, governance documents, architecture/design documents, and historical-plan documents.
- The audit can write machine-readable JSON reports.
- The audit can write bounded repair plans.
- `agentic-kit doc-mesh-repair` can insert missing historical-source-of-truth banners into known historical-plan documents.
- Version, DOI, stale-state, and missing-document findings remain manual review items.
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
3. Use structured JSON reports for review and CI-friendly evidence.
4. Keep bounded repair tools limited to mechanical edits, such as historical banners or later carefully scoped version/DOI list alignment.
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

Record verified v0.3.5 DOI metadata after post-release Zenodo verification.

## Current Blockers

- Local gates must pass on `post-release/record-v0.3.5-doi`.
- `agentic-kit post-release-check --version 0.3.5` must remain PASS.
- README and CITATION DOI lists must include the verified v0.3.5 DOI only after post-release verification.

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
agentic-kit post-release-check --version 0.3.5
```

## Next Safe Step

Run the standard local gate on `post-release/record-v0.3.5-doi`. Because this records post-release DOI metadata, also run `agentic-kit doc-mesh-audit` and `agentic-kit post-release-check --version 0.3.5`. If green, open and merge the focused post-release DOI metadata PR.
