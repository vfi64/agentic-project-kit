Status: analysis
Status-date: 2026-08-11
Scope: Phase A3 CLI version and Phase A4 quickstart synchronization
Branch: codex/post-050-planning-reconciliation

# Post-0.5.0 CLI Version And Quickstart Sync

## A3 CLI Version

Pre-change evidence:

- `agentic-kit --help` did not list `--version`.
- `agentic-kit --version` failed with `No such option: --version`.
- Canonical package runtime version source exists at
  `src/agentic_project_kit/__init__.py` as `__version__ = "0.5.0"`.

Change:

- added a root Typer callback registered from `agentic_project_kit.cli_commands.version`;
- `agentic-kit --version` prints `agentic-kit 0.5.0`;
- the callback reads `agentic_project_kit.__version__`, so the CLI does not keep
  an independent version literal.

Post-change evidence:

- `agentic-kit --version`: `agentic-kit 0.5.0`.
- `python -m pytest -q tests/test_cli.py tests/test_release_version_source_contract.py`:
  15 passed.

## A4 Quickstart Synchronization

The README already has a Quick start. This slice did not replace it.

Current README path:

- local development gate now includes `agentic-kit --version`;
- Quick start uses `agentic-kit init` for new projects;
- generated-project follow-up uses `pytest -q`, `agentic-kit check`, and
  `agentic-kit doctor`;
- the existing "Govern an existing repository" section uses
  `agentic-kit workspace dpa-intake --root PATH` for operating-layer intake.

Current generated website path:

- `site/scripts/build.py --output tmp/site-build-a2-after --json`: `PASS`.
- Homepage "Normal Lifecycle" is generated from `surface: orchestrator`.
- The generated Guided view includes `agentic-kit init` as an orchestrator.
- Common blocker diagnostics are generated separately from the manifest and GUI
  projection, not as a second hand-maintained Quickstart truth.

Decision:

- No broad README Quickstart rewrite is needed in Phase A.
- Adding `agentic-kit --version` to the local gate is enough to expose the new
  version surface.
- Brownfield/Greenfield details should be recorded in Phase B evidence, not
  pre-written into the Quickstart before the probes run.
