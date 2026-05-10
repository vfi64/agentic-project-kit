# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: feature/policy-pack-doctor-checks
Base branch: main
Current version: 0.2.4

## Current Goal

Make selected policy packs operational in doctor by activating structural policy-pack checks from `.agentic/project.yaml`.

## Current Repository State

The project has released version 0.2.4. GitHub release automation and Zenodo archival are both working.

Important completed work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- PR #20 added the first agentic-kit doctor MVP.
- PR #22 extended agentic-kit doctor with version-drift detection.
- PR #25 added research-informed architecture planning inputs, the architecture contract, and bibliography.
- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks and Remote Work Authorization.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and TODO gates.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.

Current branch work:

- Doctor now reads selected policy packs from `.agentic/project.yaml`.
- Doctor now emits a `policy pack checks` row.
- Policy pack checks currently verify structural prerequisites for starter, prototype, solo-maintainer, agentic-development, release-managed, and documentation-governed.
- README.md documents policy-pack doctor checks.
- docs/DOCUMENTATION_COVERAGE.yaml protects visibility of policy-pack doctor checks.
- docs/STATUS.md updated for this branch.
- docs/handoff/CURRENT_HANDOFF.md updated for this branch.
- tests/test_doctor.py covers passing and failing policy-pack checks.

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

## Latest Known Evidence

Last known successful checks before this branch:

- python -m pytest -q -> 46 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS

Branch evidence still required locally after pulling feature/policy-pack-doctor-checks.

## Current Open Work

- Pull feature/policy-pack-doctor-checks locally.
- Run the required local gate.
- If the gate passes, open/merge the PR after maintainer approval.

## Next Safe Step

Pull feature/policy-pack-doctor-checks locally and run the required local gate. Expected result: tests, ruff, check-docs, and doctor pass with policy pack checks active.
