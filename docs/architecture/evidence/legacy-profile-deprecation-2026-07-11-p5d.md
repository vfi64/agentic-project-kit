# Legacy Profile Deprecation Evidence (P5d)

Generated: 2026-07-11
Branch: `codex/p5d-legacy-profile-deprecation`
Scope: P5d implicit legacy profile deprecation and handoff YAML subject hardening.

## Behavior

P5d keeps the implicit legacy profile available through the 1.x compatibility
window, but makes the deprecation executable:

- manifest-less workspaces emit `LegacyProfileDeprecationWarning`;
- manifest-bearing workspaces remain quiet;
- the warning is suppressible with `suppress_legacy_profile_warning=True`;
- the warning is suppressible with `AGENTIC_KIT_SUPPRESS_LEGACY_PROFILE_WARNING=1`.

This aligns the runtime behavior with the documented 2.0.0 removal of the
implicit legacy profile while keeping existing manifest-less repositories
compatible for the current line.

## Handoff YAML Hardening

The admin-refresh generator now renders injected commit subjects as YAML inline
scalars. A regression case uses a subject containing a colon:

```text
P5d: New admin refresh behavior (#2222)
```

The refreshed `.agentic/handoff_state.yaml` and
`.agentic/operational_handoff_state.yaml` remain parseable with `yaml.safe_load`,
and the parsed subject values match the original subject exactly.

## Verification

Focused branch-local verification:

```bash
./.venv/bin/python -m pytest -q tests/test_workspace_foundation.py tests/test_transfer_repo_actions.py::test_refresh_operational_handoff_docs_updates_arbitrary_previous_pr_state
./.venv/bin/ruff check src/agentic_project_kit/workspace.py src/agentic_project_kit/transfer_repo_actions.py tests/test_workspace_foundation.py tests/test_transfer_repo_actions.py
./.venv/bin/agentic-kit check-docs
./.venv/bin/agentic-kit docs-audit
```

Result:

```text
25 passed
ruff check: All checks passed
check-docs: PASS
docs-audit: PASS
```

Full branch-local verification:

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/ruff check .
./.venv/bin/agentic-kit transfer command-reference-check
./.venv/bin/agentic-kit docs-audit
./.venv/bin/agentic-kit audit-doc-currency
./.venv/bin/agentic-kit standard-gates-audit-suite
./.venv/bin/agentic-kit transfer protected-diff-plan --label p5d-legacy-profile-deprecation
```

Result:

```text
2472 passed in 90.37s
ruff check: All checks passed
command-reference-check: PASS
docs-audit: PASS
audit-doc-currency: PASS
standard-gates-audit-suite: PASS
protected-diff-plan: PASS
```

The full test run reports expected `LegacyProfileDeprecationWarning` instances
from synthetic manifest-less test fixtures. The warning category and suppression
paths are covered by focused tests.
