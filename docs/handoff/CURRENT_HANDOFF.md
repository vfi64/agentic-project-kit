# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: docs/update-state-after-doctor-mvp
Base branch: main
Current version: 0.2.4

## Current Goal

Record the merged doctor MVP in STATUS and CURRENT_HANDOFF.

## Current Repository State

The project has released version 0.2.4. GitHub release automation and Zenodo archival are both working.

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
- PR #16 added Zenodo and citation metadata after v0.2.3 had already been released.
- PR #17 prepared v0.2.4 as the first Zenodo-backed release.
- v0.2.4 was tagged and released successfully.
- Release workflow for v0.2.4 passed.
- CI workflow for v0.2.4 passed.
- GitHub Release v0.2.4 exists with wheel and source distribution assets.
- Zenodo archived v0.2.4.
- PR #18 fixed README status drift after v0.2.4.
- PR #19 added the assigned Zenodo DOI to README.md, CITATION.cff, STATUS, and CURRENT_HANDOFF.
- PR #20 added the first agentic-kit doctor MVP.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.

Doctor state:

- agentic-kit doctor exists on main after PR #20.
- It checks required README.md, optional pyproject.toml, optional sentinel.yaml, optional .github/workflows/ci.yml, documentation gates, and TODO gates when sentinel.yaml is present.
- In the kit repository root, sentinel.yaml is currently absent and therefore reported as WARN, not FAIL.
- The latest validated doctor run reported Overall: PASS.

Current branch work:

- docs/STATUS.md records the merged doctor MVP and latest validation evidence.
- docs/handoff/CURRENT_HANDOFF.md records the current doctor state and next safe step.

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
    agentic-kit doctor

## Latest Known Evidence

Last known successful checks after PR #20:

- python -m pytest -q -> 30 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS

## Current Open Work

- Pull docs/update-state-after-doctor-mvp locally.
- Run the required local gate.
- Merge the branch after validation.

## Next Safe Step

Pull docs/update-state-after-doctor-mvp locally and run the required local gate. If it passes, open and merge the state update PR.

After this branch is merged, the next functional development block should extend agentic-kit doctor to detect version drift, README/status drift, citation metadata drift, TODO render staleness, and generated-project health issues.
