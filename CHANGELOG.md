# Changelog

All notable changes to this project are documented here.

This project uses a pragmatic semantic versioning scheme while it is in early MVP development.

## 0.2.1

- Fix generated CI to install `agentic-project-kit` from the package index instead of a private GitHub repository.
- Keep generated project CI usable without repository-specific GitHub credentials.

## 0.2.0 - 2026-05-09

### Added

- TODO management CLI:
  - `agentic-kit todo list`
  - `agentic-kit todo complete <ID> --evidence ...`
  - `agentic-kit todo render`
- Generated `.agentic/todo.yaml` as machine-readable bootstrap TODO source.
- Generated `docs/TODO.md` as human-readable TODO view.
- CI quality gate for the kit repository.
- Regression test for Rich markup escaping in the generated install hint.

### Changed

- Generated CLI next-step output now prints `pip install -e ".[dev]"` literally.
- README expanded to explain generated structure, TODO workflow, GitHub integration, logging/evidence conventions, and current MVP status.

### Fixed

- Removed an unused import flagged by Ruff.

## 0.1.0 - 2026-05-09

### Added

- Initial MVP package.
- Project generator for GitHub-ready agentic development skeletons.
- Documentation and TODO checks.
- Optional GitHub repository creation through the GitHub CLI.
- Initial tests for checks and project generation.
