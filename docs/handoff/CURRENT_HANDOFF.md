Current version: 0.3.3

# Current Handoff

Status-date: 2026-05-13
Project: agentic-project-kit
Branch: docs/plan-documentation-drift-audit
Base branch: main

## Current Goal

Record the verified v0.3.3 Zenodo DOI and add a focused planning item for a full documentation-mesh drift audit.

This branch must not implement the full audit/refactor yet. It only makes the next work item explicit and keeps release metadata current.

## Current Repository State

v0.3.3 is released and post-release verified.

Completed changes included in the v0.3.3 scope:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` to detect package-version drift.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage.
- PR #141 prepared and released v0.3.3.

Release evidence:

- GitHub Release v0.3.3 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.3 version DOI: `10.5281/zenodo.20151924`.
- `agentic-kit post-release-check --version 0.3.3` passed.

Documentation-mesh concern:

The project has many interacting documentation files: README, CHANGELOG, STATUS, CURRENT_HANDOFF, TEST_GATES, DOCUMENTATION_COVERAGE, WORKFLOW_OUTPUT_CYCLE, architecture contract, generated-project guidance, and release/citation metadata. The current `check-docs` coverage matrix is useful, but it mainly checks terms and structural visibility. It does not fully prove that the whole documentation mesh is current, non-redundant, and semantically consistent.

Next focused implementation work should inspect the documentation mesh for:

A. Aktualität / current release, roadmap, state, handoff, README, architecture, and workflow accuracy.
B. Redundanzen / duplicated status, DOI, release, roadmap, workflow, and gate explanations.
C. Konsistenz / agreement between state files, release metadata, handoff, changelog, README, coverage matrix, architecture contract, and generated-project guidance.
D. automatische Aktualisierung und sichernder automatischer Test / deterministic checks and bounded repair tools for known drift classes.

Candidate implementation direction:

- Add a deterministic documentation-mesh audit command before adding broad repair behavior.
- Start with machine-checkable invariants: current version, verified DOI list, stale release-candidate wording after publication, stale branch/current-work labels, pre-release vs post-release wording, repeated but inconsistent release/version/DOI lists, and stale next-safe-step text.
- Produce structured findings before repair.
- Add tests for every detected drift class.
- Add bounded repair only for mechanical edits, not semantic rewriting.
- Keep semantic review advisory and separate from `doctor`.

Release and governance context:

- The project remains governed by `.agentic/project.yaml`, `sentinel.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and the architecture contract.
- Active profiles include generic Git repository, Markdown docs, Python CLI, Git/GitHub, and release-managed workflows.
- Active policy packs include solo-maintainer, agentic-development, release-managed, and documentation-governed.
- `agentic-kit doctor` must continue to report policy-pack checks and policy packs.
- `agentic-kit check-docs` must continue to enforce documentation coverage.
- The post-release Zenodo workflow remains active; use `agentic-kit post-release-check --version X.Y.Z` before updating DOI metadata.

## Source of Truth

Read in this order:

1. .agentic/project.yaml
2. sentinel.yaml
3. docs/architecture/ARCHITECTURE_CONTRACT.md
4. docs/DOCUMENTATION_COVERAGE.yaml
5. AGENTS.md
6. README.md
7. docs/STATUS.md
8. docs/TEST_GATES.md
9. docs/WORKFLOW_OUTPUT_CYCLE.md
10. docs/handoff/CURRENT_HANDOFF.md
11. src/agentic_project_kit/
12. tests/

## Required Local Gate

For this branch, run:

```bash
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

The normal local workflow shortcut remains:

```bash
ns
```

Then reply in chat with `d` after evidence upload. If the workflow enters `FAILED`, copy the relevant terminal output because `d` alone is not sufficient for local failures unless evidence was uploaded.

## Current Branch Work

Prepared files should include:

- `CITATION.cff` with the verified v0.3.3 version DOI comment.
- `README.md` with the v0.3.3 DOI and a near-term documentation-governance work note.
- `docs/STATUS.md` with the v0.3.3 post-release state and the documentation-mesh drift audit plan.
- `docs/handoff/CURRENT_HANDOFF.md` with the same next-safe-step context.
- `CHANGELOG.md` with the v0.3.3 verified DOI recorded.

## Next Safe Step

Run the local gate on `docs/plan-documentation-drift-audit`. If green, open and merge this planning/DOI update. Then start a separate implementation branch for the documentation-mesh audit command, tests, and bounded repair-tool design.
