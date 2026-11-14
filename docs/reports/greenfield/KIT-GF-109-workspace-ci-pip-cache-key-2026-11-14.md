# KIT-GF-109: Pip cache key of the injected workspace CI

Date: 2026-11-14

Scope: managed workspace CI written by `workspace init --inject-ci`, `workspace ci-update` and `kit update` (`workspace_ci_template.py`).

Status: fixed on Kit `main` in PR #2782 (`0bd0ad5d`); not released.

## Finding

The injected workflow used `actions/setup-python` with `cache: "pip"` and no
`cache-dependency-path`. setup-python then looks for `requirements.txt` or
`pyproject.toml` and fails the job when neither exists. A generic workspace has
neither, so its first CI run failed before any Kit gate ran (G4 live-run
preflight, 2026-11-13).

## Change

The template keys the pip cache on `.agentic/ci/agentic-gate.yaml`, the managed
source that every workspace with injected CI has and that carries the Kit pin.
The previous template hash stays registered as Kit-written, so `kit update` and
`workspace ci-update` refresh an existing workflow.

## Regression evidence

`test_injected_ci_pip_cache_key_exists_in_a_generic_workspace`
(`tests/test_workspace_init.py`) initializes a generic workspace with injected
CI and requires every setup-python cache key to name an existing file;
`test_workspace_ci_template_hash_registry_covers_the_current_template` keeps
the previous template refreshable. The machine contract runs the same check
with the installed wheel; against the code before PR #2782 its `git grep` step
fails because the workflow has no `cache-dependency-path`.

## Boundaries

The contract proves the cache key names an existing file; it does not run
GitHub Actions. Consumer `VERIFIED_FIXED` and the release are separate.
