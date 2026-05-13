Current version: 0.3.3

# Current Handoff

Status-date: 2026-05-13
Project: agentic-project-kit
Branch: release/prepare-v0.3.3
Base branch: main

## Current Goal

Prepare v0.3.3 as a patch release for workflow usability, package-version drift hardening, project-local next-step environment bootstrap, and explicit `FAILED` next-step handling.

## Current Repository State

The project has released v0.3.2. The current release-preparation branch updates metadata and state files for v0.3.3.

Completed changes included in the v0.3.3 scope:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` to detect package-version drift.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage.

Release and governance context:

- The project remains governed by `.agentic/project.yaml`, `sentinel.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and the architecture contract.
- Active profiles include generic Git repository, Markdown docs, Python CLI, Git/GitHub, and release-managed workflows.
- Active policy packs include solo-maintainer, agentic-development, release-managed, and documentation-governed.
- `agentic-kit doctor` must continue to report policy-pack checks and policy packs.
- `agentic-kit check-docs` must continue to enforce documentation coverage.
- `agentic-kit release-check --version 0.3.3` must pass before tagging.
- The post-release Zenodo workflow remains active; use `agentic-kit post-release-check --version 0.3.3` only after the GitHub Release exists.

Important release discipline:

- Do not add a v0.3.3 version-specific DOI during release preparation.
- Keep `CITATION.cff` on the Zenodo concept DOI during pre-release checks.
- Add a v0.3.3 version-specific DOI only after `agentic-kit post-release-check --version 0.3.3` verifies the Zenodo record.

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

For this release-preparation branch, run:

```bash
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit release-plan --version 0.3.3
agentic-kit release-check --version 0.3.3
```

The normal local workflow shortcut remains:

```bash
ns
```

Then reply in chat with `d` after evidence upload. If the workflow enters `FAILED`, copy the relevant terminal output because `d` alone is not sufficient for local failures unless evidence was uploaded.

## Current v0.3.3 Release Work

Prepared files should include:

- `pyproject.toml` version `0.3.3`
- `src/agentic_project_kit/__init__.py` version `0.3.3`
- `CITATION.cff` version `0.3.3` and release date `2026-05-13`
- `CHANGELOG.md` v0.3.3 section
- `README.md` current status and release-command examples for `0.3.3`
- `docs/STATUS.md` current version `0.3.3`
- `docs/handoff/CURRENT_HANDOFF.md` current version `0.3.3`

## Next Safe Step

Run the local gate and release-check on `release/prepare-v0.3.3`. If green, open the release-preparation PR. After merge to main, tag `v0.3.3`, wait for the GitHub Release workflow, then run post-release verification.
