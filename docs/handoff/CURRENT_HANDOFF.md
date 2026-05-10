# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: feature/release-visibility-v025
Base branch: main
Current version: 0.2.4

## Current Goal

Prepare a small release-visibility and positioning cut for a maintainer-owned v0.2.5 release decision. The branch should make the post-v0.2.4 health-check, policy-pack, documentation-coverage, machine-readable task-gate, and semantic-boundary work visible without performing release-owned actions.

## Current Repository State

The project has released version 0.2.4. GitHub release automation and Zenodo archival are both working.

Important released work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3 added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4 added Zenodo-backed citation and archival metadata.

Important merged post-v0.2.4 work on main:

- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks and Remote Work Authorization.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and machine-readable task gates.
- PR #31 activated policy-pack checks in doctor.
- PR #32 defined the semantic quality boundary and added deterministic document-quality heuristics.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.

Current branch work:

- CHANGELOG.md has an Unreleased section preparing the v0.2.5 release narrative without raising the package version.
- README.md now foregrounds the purpose, the difference from a simple skeleton generator, the doctor/check-docs workflow, project scope boundary, and GitHub discovery suggestions.
- docs/STATUS.md and this handoff now point to feature/release-visibility-v025 instead of the old semantic-boundary branch.
- The branch explicitly avoids version bumps, tags, release artifacts, publication artifacts, merges, direct main writes, and repository setting changes.

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

Optional release-preparation smoke command before a later release branch or release PR:

    agentic-kit release-plan --version 0.2.5

## Latest Known Evidence

Branch creation baseline:

- git branch --show-current -> feature/release-visibility-v025
- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.4

Evidence still required after the documentation updates on this branch:

- python -m pytest -q
- ruff check .
- agentic-kit check-docs
- agentic-kit doctor

## Current Open Work

- Pull feature/release-visibility-v025 locally.
- Run the required local gate.
- If the gate passes, open a PR for README, CHANGELOG, STATUS, and handoff visibility updates.
- After merge, a separate maintainer-approved release-preparation step may update version metadata, CHANGELOG release heading, tags, release artifacts, and publication state.

## Next Safe Step

Pull feature/release-visibility-v025 locally and run the required local gate. Expected result: tests, ruff, check-docs, and doctor pass. Do not merge or release without maintainer approval.
