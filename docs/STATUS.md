# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: docs/roadmap-after-grok-review
Current version: 0.2.6

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, and deterministic document-quality heuristics.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4: added Zenodo-backed citation and archival metadata.
- v0.2.5: released the post-v0.2.4 repository-health and visibility work, including project contracts, profiles, policy packs, policy-pack doctor checks, documentation coverage drift checks, machine-readable task gates, and the semantic quality boundary.

v0.2.5 release evidence:

- PR #33 improved release visibility and README positioning for v0.2.5.
- PR #34 raised package and citation metadata to 0.2.5 and finalized the changelog heading.
- Tag v0.2.5 was pushed.
- GitHub Release v0.2.5 was created successfully by the Release workflow.
- Release assets were attached: `agentic_project_kit-0.2.5-py3-none-any.whl` and `agentic_project_kit-0.2.5.tar.gz`.
- `agentic-kit post-release-check --version 0.2.5` verified the v0.2.5 Zenodo version DOI: `10.5281/zenodo.20111119`.
- `agentic-kit release-check --version 0.2.5` now fails as expected because the local tag, remote tag, and GitHub release already exist. That command is a pre-release gate, not a post-release success check.

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

Project-level state documentation is machine-checkable:

- agentic-kit check-docs checks the state gate documents.
- docs/architecture/ARCHITECTURE_CONTRACT.md is a required state gate document.
- docs/DOCUMENTATION_COVERAGE.yaml is a documentation coverage matrix.
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, policy-pack doctor checks, and semantic quality boundary language remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own machine-readable task gate configuration.

Project health diagnostics are CLI-supported:

- agentic-kit doctor checks required project files, project contract status, policy-pack checks, documentation gates, machine-readable task gates, and version drift.
- agentic-kit check-docs checks documentation coverage and deterministic document-quality heuristics.
- agentic-kit release-plan and agentic-kit release-check support release-state validation before maintainer-owned tagging and publication.

Post-v0.2.5 external review signal:

- External review characterizes v0.2.5 as a useful late-early MVP with unusually strong dogfooding and machine-checkable repository state.
- Treat that as a planning signal, not as proof of production readiness.
- Preserve the conservative positioning: strong early governance tooling, not a de-facto standard, not production-ready, and not proof of semantic perfection.
- Keep agentic-project-kit generic. Do not rename generic roadmap items after private projects or private legacy-refactoring work.

Post-v0.2.5 roadmap:

1. Add a post-release Zenodo verification command.
   - Candidate command names: `agentic-kit post-release-check --version X.Y.Z` or `agentic-kit zenodo-check --version X.Y.Z`.
   - The command must check GitHub release state and Zenodo archive state after publication.
   - It must only recommend or prepare README.md or CITATION.cff DOI follow-up when a verified Zenodo record for the requested release version exists.
   - If no version-specific DOI exists yet, it must report WAITING or WARN and leave DOI metadata unchanged.
   - This must remain separate from `release-check`, because `release-check` is a pre-release gate.
2. Add advisory review commands after the post-release check exists.
   - Candidate commands: `agentic-kit review-docs` and `agentic-kit review-architecture`.
   - These should be advisory only and must not become merge authority.
   - They may flag clarity, audience fit, missing rationale, overclaims, architecture drift, or review questions.
3. Add generic output-contract-oriented scaffolding after the advisory review layer is stable.
   - Prefer generic names such as `structured-output`, `governed-output`, `response-contracts`, `repairable-output`, and `audit-evidence`.
   - Avoid private-project-specific names in the open kit.
   - Start with fixtures, documentation, and minimal gates before adding any large enforcement pipeline.
4. Consider a later v0.3.0 milestone for minimal response-contract gates.
   - This should be based on generic structured-output needs, not on a single private wrapper implementation.

Current roadmap branch work:

- STATUS.md records the post-v0.2.5 external-review planning signal and roadmap.
- CURRENT_HANDOFF.md should point future agents to the same roadmap.
- No code, README, CITATION, tag, release artifact, publication artifact, merge, or direct main write is part of this branch.

Latest validated release gates:

- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.5
- agentic-kit release-check --version 0.2.5 -> PASS before tag creation
- python -m build -> successfully built the 0.2.5 wheel and sdist
- twine check dist/* -> passed for the 0.2.5 wheel and sdist
- Release workflow for v0.2.5 -> success
- gh release view v0.2.5 -> release exists with wheel and sdist assets

## Current Goal

Record the verified v0.2.5 Zenodo DOI in documentation and citation guidance without changing code, tags, releases, or package metadata.

## Current Blockers

- Local gate must be rerun after documenting the verified v0.2.5 Zenodo DOI.
- The v0.2.5 version-specific Zenodo DOI has been verified by `agentic-kit post-release-check --version 0.2.5`: `10.5281/zenodo.20111119`.
- Maintainer approval is required before merge, publication changes, or GitHub repository setting changes.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
gh release view v0.2.5

Expected note:

agentic-kit release-check --version 0.2.5 is expected to fail after publication because it verifies that the target tag and GitHub release are still unused.

## Next Safe Step

Pull docs/roadmap-after-grok-review locally and run the standard local gate. If it passes, open a PR for the roadmap-only update. After that, the next implementation branch should be feature/post-release-zenodo-check.

Current documentation usability work:

- docs/examples/minimal-python-cli.md documents a small end-to-end generated-project workflow.
- README.md points new users to the example workflow.

Current v0.2.6 release-preparation work:

- v0.2.6 released the post-v0.2.5 documentation usability, generated-project doctor-gate, and Zenodo timeout improvements.

- `agentic-kit post-release-check --version 0.2.6` verified the v0.2.6 Zenodo version DOI: `10.5281/zenodo.20119102`.
- Local release preparation must verify tests, ruff, documentation gates, doctor, release-check, build, and twine check before tagging.

Current profile explain work:

- `agentic-kit profile-explain` is available and lists project profiles and policy packs with descriptions.
- This makes profile/policy selection more inspectable before adding specialized governance-wrapper profiles.

Current governance-wrapper profile work:

- `agentic-kit profile-explain` lists project profiles and policy packs.
- `governance-wrapper` is available as a project profile for strict human-AI wrapper projects.
- `output-contracts` is available as a policy pack for schema/validator/repair-boundary oriented projects.
- `agentic-kit init --type governance-wrapper` generates a project whose initial doctor gate passes.
- Next safe step: add generated output-contract skeleton files only after documenting the intended contract shape and acceptance tests.

Governance-wrapper generated-project guidance:

- PR #51 added generated output-contract skeleton docs for governance-wrapper projects.
- PR #52 fixed `agentic-kit init --type governance-wrapper` next-step guidance so non-Python governance projects are directed to `agentic-kit check-docs`, `agentic-kit check`, and `agentic-kit doctor`.
- PR #54 tightened generated validation/repair guidance so repair wording is singular, bounded, and auditable.
- PR #55 added a small deterministic runtime-validator skeleton in `src/agentic_project_kit/runtime_validator.py` with tests in `tests/test_runtime_validator.py`.
- PR #57 wired the runtime-validator skeleton into a separate `agentic-kit validate-sections` CLI command without changing `doctor` or `check` behavior.
- PR #59 added optional `validate-sections` guidance to generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` files.
- Next safe step: decide whether to add a higher-level contract validator command beyond literal section checks, or keep the current runtime validator deliberately small.
