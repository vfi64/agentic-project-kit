# Agentic Project Kit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20101359.svg)](https://doi.org/10.5281/zenodo.20101359)

`agentic-project-kit` is a local Python package for generating GitHub-ready project skeletons for human-AI software development workflows.

It creates not only files, but a reusable development process: agent onboarding, project contract, profile and policy pack selection, status discipline, test gates, task tracking, bounded logging conventions, and optional GitHub automation.

In one sentence: `agentic-project-kit` is an early, dogfooded attempt to make AI-assisted repository work more reproducible through project contracts, documentation gates, release-state checks, task gates, policy expectations, and bounded evidence.

## Why this exists

AI-assisted development works best when project context is explicit, current, and machine-checkable. Without that, agents tend to rely on stale handoffs, copied project history, unclear branch rules, missing test evidence, and unstructured logs.

This kit turns those lessons into a reusable starter system for new repositories.

The goal is not to make an LLM write code better by itself. The goal is to make repository state, handoffs, documentation coverage, task state, release state, and policy expectations visible enough that humans and coding agents can work with less context drift.

## Why not just Cookiecutter?

Cookiecutter-style generators are useful for creating initial files. `agentic-project-kit` is aimed at a narrower problem: keeping AI-assisted repository work reviewable after the first commit.

A generated project therefore includes machine-readable state, current handoff files, documentation coverage expectations, task gates, local health checks, release-state validation, policy-pack fixtures, and evidence conventions. These are governance aids, not a claim that the repository is semantically complete or production-ready.

## What it generates

A generated project includes:

- professional GitHub repository structure
- `.agentic/project.yaml` as a machine-readable project contract
- recommended project profiles and policy packs
- `AGENTS.md` with stable agent rules and closeout expectations
- `docs/PROJECT_START.md` for first-run decisions
- `docs/STATUS.md` as compact current-state dashboard
- `docs/TEST_GATES.md` as evidence matrix for different change types
- `docs/handoff/CURRENT_HANDOFF.md` and `STANDARD_AGENT_PROMPT.md`
- `.agentic/todo.yaml` plus rendered `docs/TODO.md`
- GitHub Actions CI workflow
- pull request template and agent-regression issue template
- GitHub Copilot instruction file
- pre-commit configuration
- bounded diagnostic log staging script
- `sentinel.yaml` for document and task checks
- minimal package/test skeleton for Python projects

## Installation for local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the local gate:

```bash
pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit --help
```

## Quick start

Create a new project interactively:

```bash
agentic-kit init
```

Create a new Python CLI project non-interactively:

```bash
agentic-kit init my-new-project \
  --type python-cli \
  --description "My new project" \
  --license MIT \
  --github-actions \
  --pre-commit \
  --agent-docs \
  --logging-evidence
```

Then enter the generated project and run:

```bash
cd my-new-project
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
agentic-kit check
agentic-kit doctor
```

## Project contract, profiles, and policy packs

Generated projects contain `.agentic/project.yaml` as a machine-readable project contract. It records the project name, description, project type, selected profiles, selected policy packs, and basic governance expectations.

Profiles describe what kind of repository the project is, for example `generic-git-repo`, `markdown-docs`, `python-cli`, `python-lib`, `git-github`, or `release-managed`.

Policy packs describe which development rules are recommended for the project goal, for example `starter`, `prototype`, `solo-maintainer`, `agentic-development`, `release-managed`, or `documentation-governed`.

By default, `agentic-kit init` recommends profiles and policy packs from the selected project type and enabled features. You can override them explicitly:

```bash
agentic-kit init my-docs-project \
  --type generic \
  --profiles generic-git-repo,markdown-docs \
  --policy-packs starter,documentation-governed
```

`agentic-kit doctor` validates the project contract when `.agentic/project.yaml` is present and reports selected profiles and policy packs.

## Policy-pack doctor checks

`agentic-kit doctor` also activates lightweight policy-pack checks from `.agentic/project.yaml`.

These checks currently verify structural prerequisites:

- `solo-maintainer` expects status, handoff, sentinel, and task gate files.
- `agentic-development` expects agent instructions, test gates, handoff, and the architecture contract.
- `release-managed` expects changelog, citation metadata, and Zenodo metadata.
- `documentation-governed` expects the documentation coverage matrix and architecture contract.
- `starter` and `prototype` expect basic README/status scaffolding.

The policy-pack checks are deliberately structural. They prove that the selected policy pack has its required repository fixtures. They do not prove that the prose is complete or that release readiness has already been achieved.

## Project health check

Use `agentic-kit doctor` as the compact repository health check:

```bash
agentic-kit doctor
```

It reports required project files, project contract status, policy-pack checks, documentation gates, task validation when configured, and version-drift checks. The command exits non-zero only when required checks fail.

Example output shape:

```text
Agentic project doctor report for /path/to/project

[PASS] pyproject.toml: present
[PASS] README.md: present
[PASS] sentinel.yaml: present
[PASS] project contract: my-project; profiles: generic-git-repo, python-cli; policy packs: starter, solo-maintainer
[PASS] policy pack checks: active: starter, solo-maintainer
[PASS] documentation gates: passed
[PASS] todo gates: passed
[PASS] version drift: project state matches version 0.2.5

Overall: PASS
```

## Deterministic quality heuristics

`agentic-kit check-docs` includes deterministic document-quality heuristics for machine-checkable problems such as unresolved placeholder markers, stale handoff markers, missing required sections, missing coverage terms, and documentation drift.

These checks are intentionally limited. They are useful hard gates for known bad patterns, but they do not prove semantic perfection. A passing check does not prove that an architecture is globally optimal, a README is persuasive for every audience, or a handoff is sufficient for every future agent.

Future commands such as `review-docs` or `review-architecture` may provide advisory review for clarity, didactic quality, audience fit, missing rationale, or possible architecture drift. Such advisory review must remain separate from `doctor` and must not be treated as merge authority.

## Release planning and validation

Use `agentic-kit release-plan` before preparing a release:

```bash
agentic-kit release-plan --version 0.2.5
```

Use `agentic-kit release-check` before tagging:

```bash
agentic-kit release-check --version 0.2.5
```

These commands help prevent release-state drift between `pyproject.toml`, `CHANGELOG.md`, project state files, local tags, remote tags, GitHub releases, and citation metadata.

## TODO workflow

Generated projects contain a machine-readable TODO file and a rendered Markdown view.

```bash
agentic-kit todo list
agentic-kit todo complete BOOT-001 --evidence "LICENSE reviewed"
agentic-kit todo render
agentic-kit check-todo
```

The intended pattern is simple: bootstrap tasks are explicit, evidence is recorded, and the human-readable TODO file is regenerated from the YAML source.

## GitHub integration

Create a GitHub repository from inside a generated project:

```bash
agentic-kit github-create --owner YOUR_GITHUB_NAME --visibility private
```

This command uses the official GitHub CLI `gh`. It does not ask for or store GitHub tokens.

The generated CI workflow runs the basic project gate on push and pull request. The generated pull request template asks for intended outcome, required evidence, tests, and remaining risks.

## Agentic development model

Generated projects separate:

- stable rules from volatile status
- current handoff from historical notes
- output from outcome
- logs from committed source state
- agent instructions from project overview
- project profiles from policy packs

Agents should start with `AGENTS.md`, `.agentic/project.yaml`, `docs/PROJECT_START.md`, `docs/STATUS.md`, and `docs/TEST_GATES.md`. They should not infer current state from memory or stale prose.

## Documentation coverage and drift checks

The repository uses `docs/DOCUMENTATION_COVERAGE.yaml` as a machine-checkable documentation coverage matrix.

`agentic-kit check-docs` validates that important public commands, workflows, governance concepts, safety rules, release commands, and evidence expectations remain visible in the expected documents. This prevents features such as `agentic-kit doctor` from being implemented but invisible to new users.

When adding a public command, workflow, gate, profile, policy pack, generated file, or architecture concept, update the coverage matrix and the affected documentation in the same change.

## Logging and evidence

The generated `scripts/stage_recent_logs.py` script is intentionally bounded. It stages only a recent diagnostic window from known log folders into `tmp/agent-evidence`.

Logs are diagnostic evidence, not automatic source material. Do not commit secrets, local credentials, broad raw logs, or private runtime state.

## Citation and archiving

Citation metadata is provided in `CITATION.cff`.

Zenodo metadata is provided in `.zenodo.json`. The project is archived through the Zenodo GitHub integration.

For citation, prefer the all-versions DOI: `10.5281/zenodo.20101359`.

The latest prepared release in this repository is `v0.2.5`. Zenodo assigns the version-specific DOI after the GitHub release is published and archived.

## Safety rule

Do not generate a public project from a private repository history.

This kit creates a fresh repository from generic templates. It does not copy a private `.git` history.

## Project scope boundary

`agentic-project-kit` is a generic open repository governance and agentic-development kit. It is not tied to a specific private legacy refactoring project, and examples should stay generic unless they describe generated files or this repository itself.

## GitHub discovery suggestions

Suggested GitHub description:

```text
Reproducible AI-assisted repository work through project contracts, documentation gates, release checks, task gates, and policy packs.
```

Suggested topics:

```text
agentic-development
ai-agents
developer-tools
github
project-template
software-engineering
documentation
release-management
python
cli
```

These repository settings are maintainer-owned and are not changed by the package.

## Current status

Version `0.2.5` is an early MVP release candidate with release-state validation, project-health diagnostics, policy-pack doctor checks, deterministic document-quality heuristics, documentation coverage checks, generated project contracts, project profiles, policy packs, and Zenodo-backed citation metadata. It is suitable for local use, generating new starter repositories, validating repository health, validating documentation coverage, validating release state before tagging, and archiving releases through the Zenodo GitHub integration.

This repository is prepared for maintainer-owned v0.2.5 release validation. Tag creation, GitHub release publication, package publication, and Zenodo archival remain separate maintainer-approved steps.
