# KIT-GF-011 — Successor handoff final-head identity

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-011), read from `origin/main` commit `148255313dafee2425b28f954a05d2d882df4a8c`.

## Change

The successor handoff execution contract now records an explicit final-head identity model. A committed successor package records the generation head in `validation_report.generated_head`; after the refresh commit exists, `post-merge-check` supplies the exact final repository identity with `successor_package_current_head` when `successor_package_head_status=refresh_only_descendant` proves that the diff since the generation head is limited to generated handoff refresh/projection paths.

This prevents the self-staling loop where a refresh commit makes its own tracked projection files stale and forces another rerender/commit cycle.

## Regression

- The execution contract must define the committed-package/final-HEAD boundary.
- Successor-output validation fails if that boundary is missing.
- The post-merge freshness evidence reports `successor_package_current_head` and the identity model for `refresh_only_descendant`.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own disposable-clone retest.

## Validation

- `.venv/bin/python -m pytest -q` — 3110 passed.
- `.venv/bin/ruff check .` — pass.
- `.venv/bin/agentic-kit check-docs` — pass.
- `.venv/bin/agentic-kit doctor` — Overall: PASS.
