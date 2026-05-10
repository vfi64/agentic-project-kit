# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/project-contract-policy-packs
Current version: 0.2.4

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, and policy packs.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4: added Zenodo-backed citation and archival metadata.

v0.2.4 release evidence:

- Git tag v0.2.4 was pushed.
- GitHub Release v0.2.4 exists.
- Release workflow for v0.2.4 passed.
- CI workflow for v0.2.4 passed.
- Release assets are attached: wheel and source distribution.
- Zenodo archived v0.2.4.
- Zenodo all-versions DOI: 10.5281/zenodo.20101359.
- Zenodo v0.2.4 version DOI: 10.5281/zenodo.20101360.

Citation and archival state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- CITATION.cff provides citation metadata and the all-versions Zenodo DOI.
- .zenodo.json provides Zenodo deposit metadata.
- README.md includes the Zenodo DOI badge and citation guidance.

Project-level state documentation is present on main:

- docs/STATUS.md
- docs/TEST_GATES.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/architecture/ARCHITECTURE_CONTRACT.md
- docs/architecture/AGENTIC_CODING_RESEARCH_INPUTS.md
- docs/architecture/references.bib
- docs/DOCUMENTATION_COVERAGE.yaml

Project-level state documentation is machine-checkable:

- agentic-kit check-docs checks the state gate documents.
- sentinel.yaml is optional for check-docs, so the kit repository root can be checked directly.
- stale handoff markers are detected in docs/handoff/CURRENT_HANDOFF.md.
- docs/architecture/ARCHITECTURE_CONTRACT.md is a required state gate document.
- docs/DOCUMENTATION_COVERAGE.yaml is a documentation coverage matrix.
- documentation coverage checks that public commands, workflows, governance concepts, safety rules, release/citation topics, evidence conventions, and state-doc expectations remain visible in the expected documents.

Release preparation is CLI-supported:

- agentic-kit release-plan prints a release preparation checklist for the target version.
- The plan includes local gates, package validation, state-file checks, local tag lookup, remote tag lookup, GitHub release lookup, and release verification commands.
- The plan checks for an existing target tag and release before suggesting tag creation.

Release state validation is CLI-supported:

- agentic-kit release-check validates release state for a target version.
- It checks semantic version shape, CHANGELOG version text, STATUS version text, CURRENT_HANDOFF version text, local tag availability, remote tag availability, and GitHub release availability.
- It treats unavailable remote/GitHub tooling as WARN, while existing local tags, remote tags, or GitHub releases are FAIL.
- It exits with code 1 when a required release-state check fails.

Project health diagnostics are CLI-supported:

- PR #20 added agentic-kit doctor.
- The first doctor MVP checks required README.md, optional pyproject.toml, optional sentinel.yaml, optional .github/workflows/ci.yml, documentation gates, and TODO gates when sentinel.yaml is present.
- PR #22 extended doctor with version-drift detection across project state and citation files.
- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks.
- On this branch, doctor reports and validates `.agentic/project.yaml` when it is present.
- The doctor command reports PASS, WARN, and FAIL entries and exits non-zero only when required checks fail.

Project contract and policy-pack work on this branch:

- `src/agentic_project_kit/contract.py` defines the project contract schema helpers, known profiles, known policy packs, defaults, recommendations, validation, and summary rendering.
- `agentic-kit init` now writes `.agentic/project.yaml`.
- `agentic-kit init` accepts `--profiles` and `--policy-packs` for explicit selection.
- The repository now contains its own `.agentic/project.yaml` so doctor can validate the kit's active profiles and policy packs instead of warning that the contract is absent.
- Generated projects point agents to `.agentic/project.yaml` in README, AGENTS, PROJECT_START, STATUS, TEST_GATES, and handoff files.
- README.md documents project contract, profiles, and policy packs.
- docs/DOCUMENTATION_COVERAGE.yaml now protects project contract, profile, and policy-pack visibility.

Latest validated gates before this branch:

- python -m pytest -q -> 37 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS
- agentic-kit doctor version drift -> project state matches version 0.2.4

## Current Goal

Implement the first project-contract/profile/policy-pack MVP without turning the kit into a Python-only system. The first cut must stay language-neutral at the architecture level and treat Python as one selectable profile.

## Current Blockers

- Local gate still required after pulling this branch.

## Live Status Commands

Run:

git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor

## Next Safe Step

Pull feature/project-contract-policy-packs locally and run the local gate. If it passes, review the generated `.agentic/project.yaml` behavior and open/merge the PR after maintainer approval.
