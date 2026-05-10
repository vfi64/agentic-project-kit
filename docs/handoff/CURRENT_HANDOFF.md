# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: docs/post-release-v025
Base branch: main
Current version: 0.2.5

## Current Goal

Update the repository state files after the v0.2.5 GitHub release so future agents no longer treat the release as pending.

## Current Repository State

The project has released version 0.2.5. GitHub release automation worked and attached the expected release assets.

Important released work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3 added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4 added Zenodo-backed citation and archival metadata.
- v0.2.5 released the post-v0.2.4 repository-health and visibility work, including project contracts, profiles, policy packs, policy-pack doctor checks, documentation coverage drift checks, machine-readable task gates, and the semantic quality boundary.

v0.2.5 release evidence:

- PR #33 improved release visibility and README positioning for v0.2.5.
- PR #34 raised package and citation metadata to 0.2.5 and finalized the changelog heading.
- Tag v0.2.5 was pushed.
- GitHub Release v0.2.5 was created successfully by the Release workflow.
- Release assets were attached: `agentic_project_kit-0.2.5-py3-none-any.whl` and `agentic_project_kit-0.2.5.tar.gz`.
- `agentic-kit release-check --version 0.2.5` now fails as expected because the local tag, remote tag, and GitHub release already exist. That command is a pre-release gate, not a post-release success check.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.
- The v0.2.5 version-specific DOI has not been verified in this branch. Do not add it to README.md or CITATION.cff by guessing.

Current branch work:

- docs/STATUS.md marks v0.2.5 as released.
- This handoff marks v0.2.5 as released.
- README.md and CITATION.cff are not changed on this branch because the v0.2.5 version-specific Zenodo DOI has not been verified in this branch.
- The branch explicitly avoids tags, release artifacts, publication artifacts, merges, direct main writes, and repository setting changes.

## Positioning Notes

Useful external-review signals to preserve:

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
    gh release view v0.2.5

Expected note:

    agentic-kit release-check --version 0.2.5

is expected to fail after publication because it verifies that the target tag and GitHub release are still unused.

## Latest Known Evidence

Latest validated release evidence:

- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.5
- agentic-kit release-check --version 0.2.5 -> PASS before tag creation
- python -m build -> successfully built the 0.2.5 wheel and sdist
- twine check dist/* -> passed for the 0.2.5 wheel and sdist
- Release workflow for v0.2.5 -> success
- gh release view v0.2.5 -> release exists with wheel and sdist assets

Evidence still required after the post-release status updates on this branch:

- python -m pytest -q
- ruff check .
- agentic-kit check-docs
- agentic-kit doctor
- gh release view v0.2.5

## Current Open Work

- Pull docs/post-release-v025 locally.
- Run the required local gate.
- If the gates pass, open a PR for the post-release state update.
- Verify Zenodo separately. Only after the v0.2.5 version-specific DOI is known should README.md or CITATION.cff be updated.

## Next Safe Step

Pull docs/post-release-v025 locally and run the required local gate. Expected result: tests, ruff, check-docs, and doctor pass; GitHub release v0.2.5 exists. Do not update DOI metadata by guessing.
