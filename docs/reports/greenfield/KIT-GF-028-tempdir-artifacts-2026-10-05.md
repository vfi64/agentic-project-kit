# KIT-GF-028 — TMPDIR-aware temporary Kit artifacts

Source: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` at commit `684a696b45dbc3af0c0b819d178f05c0e43933aa`.

## Finding

GF-028 observed hard-coded `/tmp` paths for Kit-owned local artifacts. The Cockpit could not redirect those files with `TMPDIR`, and `artifact-gc --tmp-logs` only collected `agentic-project-kit-*.log` files, not protected-diff artifacts.

## Fix

Kit-owned OS-temp artifacts now use Python `tempfile.gettempdir()` unless the caller explicitly selects the repository-local temp root with `--local-tmp`.

- `agentic-kit artifact-gc --tmp-logs` defaults to the OS temp directory returned by `tempfile.gettempdir()`.
- `agentic-kit transfer protected-diff-plan` writes `agentic-project-kit-<label>.diff` into the same OS temp directory.
- The communication artifact GC collects expired `agentic-project-kit-*.log` and `agentic-project-kit-*.diff` artifacts.
- The legacy `communication_artifact_gc.main()` route uses the same default instead of a literal `/tmp`.

The change has no remote side effect. `artifact-gc --tmp-logs` remains dry-run by default; deletion still requires `--execute`.

## Regression coverage

- `tests/test_communication_artifact_gc.py::test_tmp_log_gc_collects_only_expired_local_tmp_artifacts` proves expired protected-diff artifacts are collected with the existing temp-log class.
- `tests/test_communication_artifact_gc.py::test_artifact_gc_cli_tmp_logs_uses_os_tempdir` proves the public CLI respects `tempfile.gettempdir()` and finds the protected-diff artifact there.
- `tests/test_communication_artifact_gc.py::test_communication_gc_legacy_main_tmp_logs_uses_os_tempdir` proves the legacy module entrypoint no longer falls back to literal `/tmp`.
- `tests/test_transfer_repo_actions.py::test_transfer_protected_diff_plan_runs_diff_and_python_planner` proves `protected-diff-plan` writes the diff under `tempfile.gettempdir()`.

## Validation

Focused validation:

- `tests/test_communication_artifact_gc.py`
- `tests/test_transfer_repo_actions.py::test_transfer_protected_diff_plan_runs_diff_and_python_planner`
- command-reference refresh/check after CLI help changes

