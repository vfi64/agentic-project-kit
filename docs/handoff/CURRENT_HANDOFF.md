# Current Handoff

Status-date: 2026-05-09
Project: agentic-project-kit
Branch: feature/zenodo-metadata
Base branch: main
Current version: 0.2.3

## Current Goal

Add citation and Zenodo metadata, then validate the branch locally before merging. The next release after this branch should be used to trigger Zenodo archival and DOI assignment.

## Current Repository State

The project has released version 0.2.3.

Important completed work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.2 was tagged, released on GitHub, uploaded to TestPyPI, installed from TestPyPI in a fresh virtual environment, and used to generate a test project.
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

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- v0.2.3 was released before Zenodo integration was enabled, so the next release is expected to be the first automatically archived Zenodo release.
- This branch adds CITATION.cff.
- This branch adds .zenodo.json.
- This branch updates README.md with citation and archiving notes, but no DOI badge yet.

Current branch work:

- CITATION.cff added.
- .zenodo.json added.
- README.md documents citation and archiving metadata.
- docs/STATUS.md updated after v0.2.3 release and Zenodo setup.
- docs/handoff/CURRENT_HANDOFF.md updated for this branch.

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

For package validation, also run:

    rm -rf dist build
    find . -maxdepth 3 -name "*.egg-info" -type d -prune -exec rm -rf {} +
    python -m build
    twine check dist/*
    ls -lh dist/

## Latest Known Evidence

Last known successful checks before this Zenodo metadata branch:

- python -m pytest -q -> 28 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit release-plan -> target v0.2.3 before tagging
- agentic-kit release-check --version 0.2.3 -> PASS before tagging
- python -m build -> passed for v0.2.3
- twine check dist/* -> passed for v0.2.3
- GitHub Release workflow for v0.2.3 -> passed
- GitHub CI workflow for v0.2.3 -> passed
- GitHub Release v0.2.3 -> exists with wheel and source distribution assets

## Current Open Work

- Pull feature/zenodo-metadata locally.
- Run the required local gate.
- Merge the branch after validation.
- Prepare the next release so Zenodo can archive it and assign a DOI.
- Add the DOI badge only after Zenodo has assigned the DOI.

## Next Safe Step

Pull feature/zenodo-metadata locally and run the required local gate. If it passes, open and merge the metadata PR.
