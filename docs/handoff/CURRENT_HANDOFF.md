# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: feature/documentation-coverage-drift
Base branch: main
Current version: 0.2.4

## Current Goal

Add a comprehensive documentation coverage drift check so public commands, workflows, governance concepts, safety rules, release/citation topics, and evidence expectations cannot silently disappear from the documentation set.

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
- PR #22 extended agentic-kit doctor with version-drift detection.
- PR #25 added research-informed architecture planning inputs, the architecture contract, and bibliography.
- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.

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
- It now also detects version drift across project state and citation files.
- PR #26 made docs/architecture/ARCHITECTURE_CONTRACT.md a required state gate document and added agent/PR contract-review rules.
- On this branch, docs/DOCUMENTATION_COVERAGE.yaml is added as a required state gate document.
- On this branch, agentic-kit check-docs validates coverage terms across README, AGENTS.md, TEST_GATES, STATUS, CURRENT_HANDOFF, and architecture docs.
- In the kit repository root, sentinel.yaml is currently absent and therefore reported as WARN, not FAIL.
- The latest validated doctor run before this branch reported Overall: PASS.
- Version-drift validation reports: project state matches version 0.2.4.

Current branch work:

- docs/DOCUMENTATION_COVERAGE.yaml added as a documentation coverage matrix.
- src/agentic_project_kit/checks.py updated to validate documentation coverage terms.
- tests/test_checks.py updated to cover documentation coverage validation.
- README.md updated with release planning and documentation coverage sections.
- AGENTS.md updated with a Documentation Coverage Rule and Remote Work Authorization.
- docs/TEST_GATES.md updated with a Documentation Coverage Gate, Remote Work Authorization Gate, and doctor in the Standard Local Gate.
- docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md updated for this branch.

## Remote Work Authorization

For this repository, assistants and coding agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.

Maintainer approval is still required before merging pull requests, writing directly to main, creating release tags, creating release or publication artifacts, raising release versions, changing repository access settings, or choosing a new architecture direction when multiple plausible options exist.

## Source of Truth

Read in this order:

1. docs/architecture/ARCHITECTURE_CONTRACT.md
2. docs/DOCUMENTATION_COVERAGE.yaml
3. AGENTS.md
4. README.md
5. CITATION.cff
6. .zenodo.json
7. CHANGELOG.md
8. docs/STATUS.md
9. docs/TEST_GATES.md
10. docs/handoff/CURRENT_HANDOFF.md
11. src/agentic_project_kit/
12. tests/

## Required Local Gate

Run:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor

## Latest Known Evidence

Last known successful checks before this branch:

- python -m pytest -q -> 33 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS
- agentic-kit doctor version drift -> project state matches version 0.2.4

Branch evidence still required locally after pulling feature/documentation-coverage-drift.

## Current Open Work

- Pull feature/documentation-coverage-drift locally.
- Run the required local gate.
- Inspect docs/DOCUMENTATION_COVERAGE.yaml for useful coverage without overfitting.
- Merge the branch after validation.

## Next Safe Step

Pull feature/documentation-coverage-drift locally and run the required local gate. If it passes, review docs/DOCUMENTATION_COVERAGE.yaml and merge the documentation coverage drift PR.

After this branch is merged, the next functional development block can start the project-contract and policy-pack implementation.
