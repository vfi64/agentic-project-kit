# Changelog

## v0.3.6 - 2026-05-14

- Aligned the public `agentic-kit workflow request` command with the explicit `.agentic/current_work.yaml` request mechanism.
- Kept `.agentic/workflow_state` at `IDLE` for workflow requests and added `current_work_state` status reporting.
- Added governed workflow design rules, including DCO, state models, contract-first CLI design, idempotency, stop states, typed intermediate artifacts, bounded repair, capability matrices, and ADR guidance.
- Added `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` as an idea note for Event-Sourcing Light, capability matrices, ADR policy, and state-model templates.

## v0.3.5 - 2026-05-13

- Classify CHANGELOG.md as a release-history document in the documentation mesh instead of live current-state.
- Document the release-history documentation mesh category across README, test gates, coverage, status, and handoff docs.
- Assert the release-history category in the documentation mesh JSON report shape.
- Make the next-step workflow safe by default: IDLE with current_work.yaml state READY now no-ops.
- Add explicit next-step request mode through tools/next-step.py --request.
- Document the explicit ns/request workflow and add smoke-test expectations for READY no-op and REQUESTED execution.

## v0.3.4 - 2026-05-13

Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `agentic-kit doc-mesh-audit` as a targeted documentation mesh drift audit for current-state, governance, architecture/design, and historical-plan documents.
- Added deterministic checks for version mismatches, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.
- Added README, TEST_GATES, AGENTS, STATUS, handoff, and documentation coverage visibility for the documentation mesh audit.
- Documented the adoption policy: targeted special gate first, possible later promotion to `doctor`, and only then possible default `ns` integration after stabilization.
- Added JSON report output for `agentic-kit doc-mesh-audit --report`.
- Added bounded documentation mesh repair planning through `agentic-kit doc-mesh-audit --repair-plan`.
- Added the first safe automatic documentation mesh repair through `agentic-kit doc-mesh-repair`, limited to inserting missing historical-source-of-truth banners.
- Preserved the bounded repair boundary: version, DOI, stale-state, and missing-document findings remain manual review items.

## v0.3.3 - 2026-05-13

Zenodo v0.3.3 DOI: 10.5281/zenodo.20151924
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Fixed package `__version__` drift and extended `agentic-kit doctor` so package-version drift is detected.
- Documented the standard `python tools/next-step.py` / `done` / `d` terminal workflow for chat-assisted local gates.
- Added project-local environment bootstrap to `tools/next-step.py` so it can create `.venv` and install missing dev tools before running the workflow.
- Documented the `ns` shell shortcut pattern while keeping shell configuration outside the normal workflow side effects.
- Documented explicit `FAILED` next-step handling as a stop-and-diagnose workflow state and added coverage so the rule does not drift.
- Planned a follow-up documentation-mesh drift audit for currency, redundancy, consistency, deterministic tests, and bounded repair tools.

## v0.3.2 - 2026-05-12

Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `IDLE` as the safe no-op workflow state.
- Added declarative workflow runner support for bounded local evidence capture.
- Added `agentic-kit workflow request`, `agentic-kit workflow run`, `agentic-kit workflow status`, and `agentic-kit workflow cleanup`.
- Updated v0.3.0 Zenodo DOI metadata.
- Documented `done` and `d` as local terminal acknowledgement wording.
- Modularized CLI command registration and moved command groups into `src/agentic_project_kit/cli_commands/`.
- Added boundary tests to keep `cli.py` as a thin root command registry.

## v0.3.0

Zenodo v0.3.0 DOI: 10.5281/zenodo.20140467
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added generated repair-report schema support for governance-wrapper projects.
- Added a repair report model for machine-readable bounded repair evidence.
- Added a minimal deterministic output repairer for missing required section markers.
- Added validate-output-contract --repair-output and --repair-report CLI support.
- Documented bounded structural repair behavior with explicit TODO text and without invented semantic content.


## v0.2.11 - 2026-05-12

Zenodo v0.2.11 DOI: 10.5281/zenodo.20139103
Zenodo Concept DOI: 10.5281/zenodo.20101359


### Added

- Added optional `--report-schema` support to `agentic-kit validate-output-contract` so generated JSON validation reports can be checked against `docs/schemas/validation-report.schema.json` before they are written.
- Added an end-to-end smoke-test report for the `--report --report-schema` governance-wrapper workflow.
- Added `docs/reports/CURRENT_WORKFLOW_OUTPUT.md` as an overwriteable current workflow handoff bridge for app-based agent workflows.

### Changed

- Documented terminal feedback, diagnostic-output transfer, and diagnostic-report hygiene rules in `AGENTS.md`.
- Updated generated governance-wrapper validation documentation to show `--report-schema` usage.
- Recorded a concise post-v0.2.10 roadmap summary for the v0.2.11 direction.

### Removed

- Removed transient raw workflow reports from `docs/reports/`, keeping only the overwriteable current workflow output and concise longer-term reports.


## v0.2.10 - 2026-05-11

- Generate `docs/schemas/validation-report.schema.json` for governance-wrapper projects.
- Reference the validation-report schema file from generated validation guidance so wrappers and CI can consume a stable machine-readable contract.

## v0.2.9 - 2026-05-11

- Document the validation-report JSON schema in `README.md` and generated governance-wrapper validation guidance.
- Clarify that report findings use stable string fields so CI, wrappers, and review scripts can consume them without parsing human console output.

## v0.2.8 - 2026-05-11

- Add deterministic JSON report export for `agentic-kit validate-output-contract --report`.
- Document validation reports as bounded audit evidence while keeping report creation explicit and avoiding auto-staging by default.

## v0.2.7 - 2026-05-11

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

- Fix generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
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
