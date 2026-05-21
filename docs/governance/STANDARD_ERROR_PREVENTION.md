# Standard Error Prevention

Audit and release-preparation workflows must avoid fragile shell argument construction.

Rules:

- Do not run discovered pytest matrices through `xargs PATH=...` or equivalent shell pipelines.
- Do not hard-code test files in executable workflows unless existence is checked first.
- Prefer Python argument lists for discovered test matrices.
- Failed audit logs should be committed as evidence when a repair slice succeeds, but the stable path should use one deterministic runner.
- Release branches must be rebuilt from current `origin/main` after any pre-release hardening merge.

The reusable audit-test matrix code lives in `agentic_project_kit.audit_test_matrix` and `agentic_project_kit.audit_test_matrix_cli`.
