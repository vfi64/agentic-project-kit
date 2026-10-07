# KIT-GF-055/056 — Release run C3/C4 hardening

Source ledger: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read from `origin/main` commit `daf630d38481b42e5819a1e6fa27e0a681292386` on 2026-10-07.

## Findings

- KIT-GF-055: `agentic-kit release run` C3 could dispatch the package-index workflow without the PyPI publish input when `release.package_index_workflow` was absent, and it selected the latest workflow run after dispatch instead of the specific run it had created.
- KIT-GF-056: C4 called `agentic-kit post-release-check --json`, but `post-release-check` did not expose `--json`, so public release runs stopped at C4 before the DOI phase.

## Repair

`post-release-check` now accepts `--json` and emits one JSON result with `result_status`, `blocker_count`, `blockers`, and per-check details. Waiting Zenodo version records are blockers in JSON mode so release-run C4 keeps retrying instead of treating a pending DOI as complete. Text output is unchanged.

`release run` now derives `publish_target=pypi` from a `github+pypi` or `github+pypi+zenodo` publication policy when no explicit package-index workflow input is configured. C3 records the dispatch time and current head SHA, then selects only a `workflow_dispatch` run created after dispatch for that head SHA. If the workflow declares a required input that is neither configured nor derivable, C3 blocks before dispatch.

## Regression coverage

- `tests/test_release_run.py::test_release_run_agentic_argv_options_exist_in_typer_cli`
- `tests/test_release_run.py::test_release_run_derives_pypi_dispatch_input_without_config_section`
- `tests/test_release_run.py::test_release_run_watches_dispatched_workflow_run_not_stale_latest`
- `tests/test_release_run.py::test_release_run_blocks_when_required_workflow_input_cannot_be_derived`
- `tests/test_post_release.py::test_post_release_check_command_json_reports_pass`
- `tests/test_post_release.py::test_post_release_check_command_json_blocks_waiting_zenodo`

## Expected external retest

In a public `github+pypi` or `github+pypi+zenodo` workspace without `release.package_index_workflow`, C3 should dispatch `release.yml` with `publish_target=pypi`, watch the workflow-dispatch run for the release head, and C4 should parse `post-release-check --json`. If Zenodo has not indexed the release version yet, C4 should report a bounded wait/block instead of entering the DOI closeout phase.
