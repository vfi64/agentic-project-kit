# KIT-GF-043 / KIT-GF-044 — Release publish and lifecycle header scope

Source for KIT-GF-043: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` at commit `773fa414d7fd3c07d1d0ac8efbd2497ecb68d208`.

Source for KIT-GF-044: new maintainer finding from 2026-10-05, observed in agp-Cockpit `docs/planning/ULTRA_REVIEW_REMEDIATION.md`. The family will be recorded in the Cockpit ledger with the same ID; this Kit report is the fix evidence and does not replace that Cockpit-side ledger entry.

## KIT-GF-043

`release-publish --execute` now uses the same annotated tag command for GitHub publication policies that the private `publication: none` path already used: `git tag -a <tag> -m "Release <tag>"`. If a local tag already exists, the command now verifies `git cat-file -t refs/tags/<tag>` and blocks lightweight tags instead of accepting them as idempotent success. If the remote tag already exists, it must be peelable as an annotated tag before the run can continue.

External workspaces can set a GitHub Release title template in `.agentic/config.yaml`:

```yaml
release:
  github_release_title_template: AGP Cockpit {version} (privat)
```

Allowed placeholders are `{version}` and `{tag}`. Without the setting, the title remains the tag for compatibility.

Regression coverage:

- `tests/test_release_publish_orchestration.py::test_release_publish_execute_capability_runs_ordered_live_plan_with_fake_runner` uses a manifest-bearing external workspace with `publication: github`, proves annotated tag creation, and checks the configured GitHub Release title.
- `tests/test_release_publish_orchestration.py::test_release_publish_invalid_release_title_template_blocks_before_tagging` proves a malformed title template blocks before tag, push, or release creation.
- `tests/test_release_publish_orchestration.py::test_release_publish_blocks_existing_lightweight_local_tag` proves an existing lightweight local tag blocks before push or GitHub Release creation.
- `tests/test_release_publish_orchestration.py::test_release_publish_blocks_existing_lightweight_remote_tag` proves an existing lightweight remote tag at the same commit still blocks instead of being accepted as publish success.

## KIT-GF-044

The suspected cause was confirmed in `src/agentic_project_kit/doc_lifecycle.py`: `_audit_document` already used `_first_header_value(...)` for `Status` and `Decision status`, but accepted `Review policy` through a full-file substring check. `_first_header_value(...)` also scanned the full document.

The documentation lifecycle audit now treats lifecycle metadata as a head-block contract. `Status`, `Decision status`, `Status-date`, `Superseded-by`, and `Review policy` are read only before the first `##` section. Lines with those labels in later prose no longer satisfy the lifecycle sweep.

Regression coverage:

- `tests/test_doc_lifecycle.py::test_doc_lifecycle_ignores_lifecycle_headers_after_first_section` reproduces the agp-Cockpit shape: status labels in the body are ignored and the document reports missing lifecycle headers.
- `tests/test_doc_lifecycle.py::test_doc_lifecycle_requires_review_policy_in_header_block` keeps `Status` and `Decision status` valid in the head while proving a body-only `Review policy` is still reported missing.

Focused validation after the patch: `53 passed` for `tests/test_doc_lifecycle.py` and `tests/test_release_publish_orchestration.py`. Full local gate validation also passed: `3123 passed` for `python -m pytest -q`; `ruff check .`; `agentic-kit check-docs`; `agentic-kit doctor` Overall PASS.
