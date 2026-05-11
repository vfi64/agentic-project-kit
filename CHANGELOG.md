# Changelog

## Unreleased

- Document the runtime validation workflow in `README.md`.
- Surface `validate-sections`, `validate-contract`, and `validate-output-contract` as deterministic structural validation commands.
- Clarify that output-contract validation currently checks required literal sections and does not claim semantic validation or repair.

## v0.2.6

- Add a minimal generated-project example workflow.
- Fix generated Python CLI projects so their initial state passes documentation and doctor gates.
- Reduce Zenodo post-release lookup timeout and keep timeout failures non-fatal.

All notable changes to this project are documented here.

This project uses a pragmatic semantic versioning scheme while it is in early MVP development.

## v0.2.5

- Document the post-v0.2.4 repository-health work as a visible release instead of leaving it only in merged pull requests.
- Emphasize `agentic-kit doctor` and `agentic-kit check-docs` as the main user-facing health and documentation gates.
- Clarify that project contracts, profiles, policy packs, documentation coverage, machine-readable task gates, version-drift checks, and deterministic document-quality heuristics are machine-checkable governance aids.
- Preserve the semantic quality boundary: deterministic gates are hard checks for known structural and drift problems, not proof of semantic perfection.
- Improve README positioning with a clearer purpose statement, generator-boundary explanation, project scope boundary, and maintainer-owned GitHub discovery suggestions.
- Update project state and handoff documents for the v0.2.5 release-preparation branch.

## v0.2.4

- Add citation metadata through `CITATION.cff`.
- Add Zenodo deposit metadata through `.zenodo.json`.
- Document citation and archiving setup in `README.md`.
- Prepare the first release after Zenodo GitHub integration was enabled so Zenodo can archive the project and assign a DOI.

## v0.2.3

- Add machine-checkable release-state validation for local tags, remote tags, and GitHub releases.
- Extend `agentic-kit release-plan` with remote tag and GitHub release checks before tag creation.
- Keep unavailable remote or GitHub tooling as WARN while treating existing release artifacts as FAIL.
- Update repository state and handoff documentation after remote release validation.

## 0.2.2

- Add `--kit-source` option for generated CI.
- Support `pypi`, `testpypi`, and `none` as generated CI install sources for `agentic-project-kit`.
- Add generator tests for configurable kit install source behavior.

## 0.2.1

- Fix generated CI to install `agentic-project-kit` from the package index instead of a private GitHub repository.
- Keep generated project CI usable without repository-specific GitHub credentials.

## 0.2.0 - 2026-05-09

### Added

- TODO management CLI:
  - `agentic-kit todo list`
  - `agentic-kit todo complete <ID> --evidence ...`
  - `agentic-kit todo render`
- Generated `.agentic/todo.yaml` as machine-readable bootstrap TODO source.
- Generated `docs/TODO.md` as human-readable TODO view.
- CI quality gate for the kit repository.
- Regression test for Rich markup escaping in the generated install hint.

### Changed

- Generated CLI next-step output now prints `pip install -e \".[dev]\"` literally.
- README expanded to explain generated structure, TODO workflow, GitHub integration, logging/evidence conventions, and current MVP status.

### Fixed

- Removed an unused import flagged by Ruff.

## 0.1.0 - 2026-05-09

### Added

- Initial MVP package.
- Project generator for GitHub-ready agentic development skeletons.
- Documentation and TODO checks.
- Optional GitHub repository creation through the GitHub CLI.
- Initial tests for checks and project generation.
