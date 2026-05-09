# Agentic Project Kit

`agentic-project-kit` is a local Python package for generating GitHub-ready projects with built-in support for human-AI software development workflows.

It creates not only files, but a reusable development process:

- professional GitHub repository structure
- agent onboarding documentation
- status and handoff documents
- test gate matrix
- interactive bootstrap TODOs
- logging and evidence conventions
- optional GitHub repository creation through the GitHub CLI
- local quality checks for docs and TODO state

## Why this exists

AI-assisted development works best when the project context is explicit, current, and machine-checkable.

This kit helps prevent stale handoff files, unclear branch rules, missing test evidence, undocumented technical debt, unstructured logs that agents cannot use, overloaded README files with volatile status, and copied private project history in new public repositories.

## Installation for local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## CLI

```bash
agentic-kit --help
```

Create a new project interactively:

```bash
agentic-kit init
```

Create a new project non-interactively:

```bash
agentic-kit init my-new-project --type python-cli --license MIT --github-actions --pre-commit --agent-docs --logging-evidence
```

Run checks inside a generated project:

```bash
agentic-kit check
agentic-kit check-docs
agentic-kit check-todo
```

Optionally create and push a GitHub repository:

```bash
agentic-kit github-create --owner YOUR_GITHUB_NAME --visibility private
```

This command uses the official GitHub CLI `gh`. It does not ask for or store GitHub tokens.

## Generated project philosophy

Generated projects separate stable rules from volatile status, current handoff from historical archive, output from outcome, logs from committed source state, and agent instructions from project overview.

## Safety rule

Do not generate a public project from a private repository history.

This kit creates a fresh repository from generic templates. It does not copy a private `.git` history.
