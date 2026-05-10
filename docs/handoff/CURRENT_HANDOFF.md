# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: feature/release-v025
Base branch: main
Current version: 0.2.5

## Current Goal

Prepare the v0.2.5 release metadata and state files so a maintainer can review, merge, and then perform the separate tag and publication steps.

## Current Repository State

The project has released version 0.2.4. GitHub release automation and Zenodo archival are both working.

Important released work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3 added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4 added Zenodo-backed citation and archival metadata.

Important work prepared for v0.2.5:

- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks and Remote Work Authorization.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and machine-readable task gates.
- PR #31 activated policy-pack checks in doctor.
- PR #32 defined the semantic quality boundary and added deterministic document-quality heuristics.
- PR #33 improved release visibility and README positioning for v0.2.5.
- This branch raises package and citation metadata to 0.2.5 and finalizes the changelog heading.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.
- The v0.2.5 version-specific DOI must not be stated until the v0.2.5 GitHub release has been published and archived by Zenodo.

Current branch work:

- pyproject.toml version is set to 0.2.5.
- CITATION.cff version is set to 0.2.5.
- CHANGELOG.md has a v0.2.5 section.
- README.md current status describes v0.2.5 as a release candidate and avoids promising a version-specific Zenodo DOI before publication.
- docs/STATUS.md and this handoff now point to feature/release-v025.
- The branch explicitly avoids tags, release artifacts, publication artifacts, merges, direct main writes, and repository setting changes.

## Positioning Notes

Useful external-review signals to preserve:

- The most important near-term issue is release visibility: post-v0.2.4 governance work exists on main but is not yet represented by a published v0.2.5 release.
- The strongest value proposition is reproducible AI-assisted repository work through explicit context, machine-checkable gates, bounded evidence, handoff discipline, release-state validation, and dogfooding.
- Avoid overclaims such as production ready, de-facto standard, semantic perfection, or LLM-proven quality.
- Treat mechanized trust as a useful concept, but express it through concrete checked project state rather than marketing claims.
- Do not let examples or wording blur agentic-project-kit with Comm-SCI-Control-private or any private legacy refactoring project.

## Remote Work Authorization

For this repository, assistants and coding agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.

Maintainer approval is still required before merging pull requests, writing directly to main, creating release tags, creating release or publication artifacts, raising release versions, changing repository access settings, or choosing a new architecture direction when multiple plausible options exist.

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
9. docs/handoff/CURRENT_HANDOFF.md
10. src/agentic_project_kit/
11. tests/

## Required Local Gate

Run:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor
    agentic-kit release-plan --version 0.2.5
    agentic-kit release-check --version 0.2.5

## Latest Known Evidence

Latest validated main gate before this branch:

- git branch --show-current -> main
- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.4

Evidence still required after the release-preparation updates on this branch:

- python -m pytest -q
- ruff check .
- agentic-kit check-docs
- agentic-kit doctor
- agentic-kit release-plan --version 0.2.5
- agentic-kit release-check --version 0.2.5

## Current Open Work

- Pull feature/release-v025 locally.
- Run the required local gate and release-state checks.
- If the gates pass, open a PR for the v0.2.5 release-preparation changes.
- After merge, separate maintainer-approved release steps may create the tag, trigger release artifacts, publish package artifacts, and allow Zenodo archival.

## Next Safe Step

Pull feature/release-v025 locally and run the required local gate plus release-plan and release-check for 0.2.5. Expected result: tests, ruff, check-docs, doctor, and release-check pass, with release-plan printing the intended release commands. Do not tag or publish without maintainer approval.
