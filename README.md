# Agentic Project Kit


Current version: 0.4.2
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20101359.svg)](https://doi.org/10.5281/zenodo.20101359)
Latest verified version DOI: `10.5281/zenodo.20376095`

`agentic-project-kit` is a local Python package for generating GitHub-ready project skeletons for human-AI software development workflows.

It creates not only files, but a reusable development process: agent onboarding, project contract, profile and policy pack selection, status discipline, test gates, task tracking, bounded logging conventions, optional GitHub automation, workflow evidence capture, and release-state validation.

In one sentence: `agentic-project-kit` is an early, dogfooded attempt to make AI-assisted repository work more reproducible through project contracts, documentation gates, release-state checks, task gates, policy expectations, workflow evidence, and bounded auditability.

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

## Example workflow

See `docs/examples/minimal-python-cli.md` for a small end-to-end example showing how a generated Python CLI project gets project state files, agent instructions, documentation gates, task gates, and a local doctor check.

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