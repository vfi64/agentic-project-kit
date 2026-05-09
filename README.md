# Agentic Project Kit

`agentic-project-kit` is a local Python package for generating GitHub-ready project skeletons for human-AI software development workflows.

It creates not only files, but a reusable development process: agent onboarding, status discipline, test gates, TODO tracking, bounded logging conventions, and optional GitHub automation.

## Why this exists

AI-assisted development works best when project context is explicit, current, and machine-checkable. Without that, agents tend to rely on stale handoffs, copied project history, unclear branch rules, missing test evidence, and unstructured logs.

This kit turns those lessons into a reusable starter system for new repositories.

## What it generates

A generated project includes:

- professional GitHub repository structure
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
- `sentinel.yaml` for document and TODO checks
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
```

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

Agents should start with `AGENTS.md`, `docs/PROJECT_START.md`, `docs/STATUS.md`, and `docs/TEST_GATES.md`. They should not infer current state from memory or stale prose.

## Logging and evidence

The generated `scripts/stage_recent_logs.py` script is intentionally bounded. It stages only a recent diagnostic window from known log folders into `tmp/agent-evidence`.

Logs are diagnostic evidence, not automatic source material. Do not commit secrets, local credentials, broad raw logs, or private runtime state.

## Citation and archiving

Citation metadata is provided in `CITATION.cff`.

Zenodo metadata is provided in `.zenodo.json`. The repository is intended to be archived through the Zenodo GitHub integration starting with the first release after that integration is enabled.

A DOI badge should be added here only after Zenodo has archived a release and assigned the DOI.

## Safety rule

Do not generate a public project from a private repository history.

This kit creates a fresh repository from generic templates. It does not copy a private `.git` history.

## Current status

Version `0.2.4` is an early MVP with release-state validation and Zenodo-ready citation metadata. It is suitable for local use, generating new starter repositories, validating release state before tagging, and archiving releases through the Zenodo GitHub integration.
