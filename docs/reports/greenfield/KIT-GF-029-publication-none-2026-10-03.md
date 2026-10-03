# KIT-GF-029 — Publication policy `none`

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` at commit `7f2e421de8f453fb3c32aab54f740eec5aa0885f`.

## Result

The Kit now supports a workspace manifest publication policy:

- `none`
- `github`
- `github+pypi`
- `github+pypi+zenodo` (default)

For external workspaces with `publication: none`, release validation and closeout paths stay private and local:

- `release-plan` renders local tag steps only.
- `release-check` and release preflight skip remote tag and GitHub Release checks.
- `post-release-check` returns a policy PASS without invoking GitHub or Zenodo checks.
- `post-release-doi-closeout` is a no-op PASS and does not query Zenodo.
- CHANGELOG quality checks no longer require a Zenodo DOI or pending marker.
- `release-publish` returns a disabled publication plan and does not run tag push, GitHub Release, PyPI, or Zenodo actions.

## Regression evidence

The regression uses temporary manifest-bearing external workspaces, not the Kit checkout as the target workspace. The tests assert that forbidden GitHub/Zenodo/remote command runners are not called under `publication: none`.

Targeted validation run:

```text
132 passed, 3 warnings
ruff check selected files: passed
agentic-kit check-docs: passed
```

Covered tests include:

- `tests/test_release.py::test_build_release_plan_publication_none_uses_local_tag_only`
- `tests/test_release.py::test_build_release_state_report_publication_none_skips_remote_checks`
- `tests/test_release.py::test_build_release_preflight_report_publication_none_skips_remote_checks`
- `tests/test_post_release.py::test_publication_none_post_release_skips_github_and_zenodo`
- `tests/test_post_release.py::test_publication_none_doi_closeout_is_noop_without_zenodo_lookup`
- `tests/test_checks.py::test_changelog_quality_skips_zenodo_marker_for_publication_none`
- `tests/test_release_publish_orchestration.py::test_release_publish_publication_none_does_not_run_remote_checks`

## Notes

This slice does not set `VERIFIED_FIXED` in the agp-Cockpit ledger. That status remains owned by the external workspace retest.
