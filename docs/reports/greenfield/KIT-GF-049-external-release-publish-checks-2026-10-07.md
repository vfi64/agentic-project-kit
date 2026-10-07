# KIT-GF-049 — External release-publish checks

Source ledger: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read from `origin/main` commit `daf630d38481b42e5819a1e6fa27e0a681292386` on 2026-10-07.

## Finding

`release-publish` ran Kit self-hosting checks for every non-private publication. In an external workspace without the Kit documentation system, `docs-audit` and `transfer command-reference-check` could block the GitHub publication route even though those checks were not applicable to that workspace.

## Repair

For public publication policies, `release-publish` now runs the Kit-only publish checks only when the workspace declares the relevant system:

- Kit development checkouts still run both checks.
- External workspaces with `docs/DOCUMENTATION_REGISTRY.yaml` still run `docs-audit` and block on a failure.
- External workspaces with `docs/reference/agentic-kit-commands.json` still run `transfer command-reference-check`.
- Otherwise each check is reported as `SKIP` with a reason, and `SKIP` does not count as a blocker or enter the approval signature.

An explicit `release.publish_checks` config can still opt in or out of the Kit publish checks.

## Regression coverage

- `tests/test_release_publish_orchestration.py::test_release_publish_external_workspace_skips_kit_self_hosting_checks`
- `tests/test_release_publish_orchestration.py::test_release_publish_external_workspace_with_registry_blocks_failing_docs_audit`

## Expected external retest

In an external workspace with publication `github` and no Kit documentation registry or command reference, `agentic-kit release-publish --dry-run --json` should list `docs audit` and `command reference check` as `SKIP` and should not include them in `blockers`. If the workspace declares `docs/DOCUMENTATION_REGISTRY.yaml`, a failing `docs-audit` must still block publication.
