# KIT-GF-117: remote effects of init --github

Date: 2026-11-15

Scope: command manifest (`command_manifest.infer_remote_effects`),
`greenfield_retest_release_check.release_effects`.

Status: fixed in this change; not released.

## Finding

The manifest listed `init` with remote effects `none`. With `--github`, init
creates the GitHub repository and pushes the first commit (`gh repo create
--source --push`), like `github-create`, which listed only `release_publish`.
`journey_contracts.needs_consent` therefore did not count `init --github` as
an owner consent. Observed in the evaluation of order 0107.

## Change

`init` and `github-create` list `push` and `release_publish`.
`release_effects` narrows `init` without `--github` to `none`, so the machine
contracts that generate projects locally (for example KIT-GF-111) stay local
and need no consent.

## Regression evidence

`test_init_remote_effects_follow_the_github_flag`
(`tests/test_g3_init_github_routes.py`) checks the manifest entries, the
narrowing and `needs_consent` for both forms; it fails against the previous
manifest.

## Boundaries

The route creates a GitHub repository, so it has no local machine contract.
No release or consumer `VERIFIED_FIXED` is claimed.
