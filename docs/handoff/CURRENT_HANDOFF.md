# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: feature/prepare-v0.2.4-zenodo-release
Base branch: main
Current version: 0.2.4

## Current Goal

Prepare and validate v0.2.4 so the next tag can trigger GitHub Release automation and Zenodo archival.

## Current Repository State

The project has released version 0.2.3. The current branch prepares version 0.2.4.

Important completed work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- Project-level state documentation is present in docs/STATUS.md, docs/TEST_GATES.md, and docs/handoff/CURRENT_HANDOFF.md.
- PR #7 made project-level state documentation machine-checkable through agentic-kit check-docs.
- check-docs can run in the kit repository root without sentinel.yaml.
- PR #9 added agentic-kit release-plan for release preparation.
- PR #11 added agentic-kit release-check for release state validation.
- PR #13 extended release-check and release-plan with remote release state validation.
- PR #15 prepared v0.2.3.
- v0.2.3 was tagged and released successfully.
- Release workflow for v0.2.3 passed.
- CI workflow for v0.2.3 passed.
- GitHub Release v0.2.3 exists with wheel and source distribution assets.
- PR #16 added Zenodo and citation metadata after v0.2.3 had already been released.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- v0.2.3 was released before Zenodo integration was enabled, so v0.2.4 is expected to be the first automatically archived Zenodo release.
- CITATION.cff is present.
- .zenodo.json is present.
- README.md documents citation and archiving notes, but no DOI badge yet.

Current branch work:

- pyproject.toml bumped to 0.2.4.
- CITATION.cff bumped to 0.2.4.
- CHANGELOG.md documents v0.2.4.
- docs/STATUS.md updated for v0.2.4.
- docs/handoff/CURRENT_HANDOFF.md updated for v0.2.4.

## Source of Truth

Read in this order:

1. README.md
2. CITATION.cff
3. .zenodo.json
4. CHANGELOG.md
5. docs/STATUS.md
6. docs/TEST_GATES.md
7. docs/handoff/CURRENT_HANDOFF.md
8. src/agentic_project_kit/
9. tests/

## Required Local Gate

Run:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit release-plan
    agentic-kit release-check --version 0.2.4

For package validation, also run:

    rm -rf dist build
    find . -maxdepth 3 -name "*.egg-info" -type d -prune -exec rm -rf {} +
    python -m build
    twine check dist/*
    ls -lh dist/

## Latest Known Evidence

Last known successful checks before this branch:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- python -m build -> passed for v0.2.3
- twine check dist/* -> passed for v0.2.3
- GitHub Release workflow for v0.2.3 -> passed
- GitHub CI workflow for v0.2.3 -> passed
- GitHub Release v0.2.3 -> exists with wheel and source distribution assets

## Current Open Work

- Pull feature/prepare-v0.2.4-zenodo-release locally.
- Run the required local gate.
- Merge the branch after validation.
- Tag v0.2.4.
- Verify GitHub Release v0.2.4.
- Verify Zenodo archival and DOI assignment.
- Add the DOI badge only after Zenodo has assigned the DOI.

## Next Safe Step

Pull feature/prepare-v0.2.4-zenodo-release locally and run the required local gate. If it passes, open and merge the release preparation PR.
