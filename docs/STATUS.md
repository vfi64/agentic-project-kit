# Project Status

Status-date: 2026-05-10
Project: agentic-project-kit
Primary branch: main
Current work branch: feature/policy-pack-doctor-checks
Current version: 0.2.4

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, TODO tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, and policy-pack doctor checks.

The project itself has a current state layer so work can be continued from the repository state files.

## Current State

Released versions:

- v0.2.0: first GitHub release workflow with build artifacts.
- v0.2.1: fixed generated CI to install agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2: added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3: added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4: added Zenodo-backed citation and archival metadata.

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
- Documentation coverage checks that public commands, workflows, governance concepts, release topics, evidence conventions, state-doc expectations, and policy-pack doctor checks remain visible.
- sentinel.yaml and .agentic/todo.yaml are present so the repository validates its own TODO gate configuration.

Project health diagnostics are CLI-supported:

- PR #20 added agentic-kit doctor.
- PR #22 extended doctor with version-drift detection across project state and citation files.
- PR #26 enforced architecture contract review gates.
- PR #27 documented agentic-kit doctor in README.md.
- PR #28 added documentation coverage drift checks.
- PR #29 added project contract, profiles, and policy packs.
- PR #30 added self sentinel and TODO gates.
- On this branch, Policy-pack checks are activated in doctor.
- Policy-pack checks currently verify structural prerequisites for starter, prototype, solo-maintainer, agentic-development, release-managed, and documentation-governed.

Latest validated gates before this branch:

- python -m pytest -q -> 46 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS

## Current Goal

Make selected policy packs operational in doctor by activating structural policy-pack checks from .agentic/project.yaml.

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

Pull feature/policy-pack-doctor-checks locally and run the local gate. Expected result: tests, ruff, check-docs, and doctor pass with policy pack checks active.
