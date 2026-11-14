# KIT-GF-111: Pip cache key of generated project CI

Date: 2026-11-14

Scope: CI template of `agentic-kit init --github-actions` (`templates.py`).

Status: fixed on Kit `main` in PR #2786 (`25a27560`); not released.

## Finding

The generator wrote the same `cache: "pip"` setup without a
`cache-dependency-path` as the workspace CI before KIT-GF-109. `python-cli` and
`python-lib` projects have a `pyproject.toml`, but `generic` and
`governance-wrapper` projects have neither a requirements file nor a
`pyproject.toml`, so their generated CI failed in setup-python.

## Change

The generated CI keys the pip cache on `.github/workflows/ci.yml`, which every
generated project with GitHub Actions has, and on `**/pyproject.toml`.

## Regression evidence

`test_generated_ci_pip_cache_key_exists_for_every_project_type`
(`tests/test_generator.py`) generates all four project types and requires a
literal cache key that names an existing file. The machine contract generates a
`governance-wrapper` project with the installed wheel; with only the template
change of PR #2786 reverted, its `cache-dependency-path` step fails. (Against the
whole tree before #2786 the contract cannot run, because `init --json` came
later with PR #2802.)

## Boundaries

The contract checks the generated workflow; it does not run GitHub Actions.
Consumer `VERIFIED_FIXED` and the release are separate.
