# Contributing

Thank you for improving Agentic Project Kit.

This project is built around a simple rule: changes should be traceable, testable, and useful for human-AI software development workflows.

## Development setup

```bash
git clone git@github.com:vfi64/agentic-project-kit.git
cd agentic-project-kit
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Local quality gate

Run this before opening a pull request or claiming completion:

```bash
python -m pytest -q
ruff check .
agentic-kit --help
agentic-kit todo --help
```

## Pull request expectations

A useful pull request should state:

- intended outcome
- files changed
- tests run
- risks or remaining gaps
- whether generated-project behavior changed

Do not describe a patch as successful only because files were produced. Success means the intended behavior is verified by tests, CLI smoke checks, generated-project smoke checks, or other concrete evidence.

## Agentic workflow rules

When an AI agent works on this repository, it should:

1. read `README.md`, `CHANGELOG.md`, and this file first
2. inspect the current code and tests rather than relying on remembered state
3. make small, focused commits
4. add or update tests for behavior changes
5. run the local quality gate
6. report remaining uncertainty explicitly

Generated project templates are part of the product. If a change modifies generated files, add or update a generator test and run a demo generation smoke test when appropriate.

## Commit hygiene

Do not commit:

- `.venv/` or other virtual environments
- `__pycache__/` or `*.pyc`
- local credentials, tokens, or private configuration
- broad raw logs
- generated temporary demo folders

Bounded diagnostic evidence is acceptable only when it is needed to reproduce or verify a problem and has been inspected for secrets.

## Dependency updates

Dependabot may open pull requests for GitHub Actions and Python dependencies. Merge only after CI passes and the change is plausibly safe.

## Release policy

Early MVP releases are GitHub Releases only. PyPI publishing is intentionally not enabled yet.

A release should include:

- updated version in `pyproject.toml`
- updated `CHANGELOG.md`
- passing CI on `main`
- a tag like `v0.2.0`
