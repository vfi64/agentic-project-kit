# S4c GitHub Pages Deployment

Date: 2026-08-09

Base before S4c: `b145064a6f997acd47cb69dde32ebf4bbcb80efd`
(`Refresh handoff state after PR2032 (#2033)`).

## Scope

S4c adds a GitHub Actions Pages workflow for the generated website. It does not
change repository Pages settings through the GitHub API and does not maintain a
`gh-pages` branch.

## Current Pages State

Current remote inspection returned `404` for `GET /repos/vfi64/agentic-project-kit/pages`.
That means GitHub Pages is not currently enabled for the repository through the
available API view.

## Workflow Contract

`.github/workflows/pages.yml` now:

- runs on pushes to `main` and on manual dispatch;
- installs the package with development dependencies;
- runs `python site/scripts/build.py --output site/dist --json`;
- runs `python -m pytest tests/test_site_generator.py tests/test_site_claims.py -q`;
- uploads `site/dist` with `actions/upload-pages-artifact`;
- deploys with `actions/deploy-pages` only when the repository Pages API reports
  `build_type: workflow`.

If Pages is not enabled or is not configured for GitHub Actions deployment, the
workflow skips deployment after a successful build. This keeps `main` from
turning red because of a missing repository setting while still making the
deployment path ready.

## Required Maintainer Action

To make publication live, the repository Pages source must be set to GitHub
Actions. After that setting is active, the workflow can deploy the uploaded
Pages artifact.
