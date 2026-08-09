# Generated Website

This directory contains the repository-native public website generator.

The generated output is a projection of current repository sources, not a manual
technical truth surface. `site/scripts/build.py` calls
`agentic_project_kit.site_generator` and writes the static artifact to
`site/dist/` by default. The generated `site/dist/` tree is ignored; GitHub
Pages deployment must build a fresh artifact from the checked-in sources.

S4a foundation sources:

- `pyproject.toml` supplies package name, version and Python requirement.
- `docs/reference/agentic-kit-commands.json` supplies command count and
  `meta.manifest_sha`.
- `agentic_project_kit.command_manifest.manifest_sha(commands)` reproduces the
  manifest identity from the committed command list.
- `git rev-parse HEAD` supplies the build commit.

Later website slices add generated command views, claim-evidence evaluation, the
GitHub Pages workflow and the presentation layer. Technical claim status must be
computed from evidence bindings; curated content must not store a derived
`verified` value.

S4b generated content adds the command catalog projections:

- `commands/guided.html` contains only `surface: orchestrator` entries.
- `commands/diagnostics.html` contains only `surface: diagnostic` entries.
- `commands/index.html` and `commands/commands.json` contain the complete
  reference.
- The build fails when command entries lack valid `surface`, `safety`,
  `dry_run_available`, `when_to_use` or `params` metadata, or when guided and
  diagnostic views would be empty.
- Release, status and roadmap summaries are derived from `docs/STATUS.md`,
  `CITATION.cff` and `docs/planning/PROJECT_DIRECTION.yaml`.

S4b.2 claim evidence adds `site/content/claims.yaml`. Claim content stores
`id`, `text`, `required`, optional `planned`, and evidence bindings only. It
must not store derived `status` or `verified` fields. The build computes
`verified`, `unverified`, or `planned` in `claims/claims.json` and
`claims/index.html`. Required claims block the build when they are not verified;
optional claims degrade visibly to unverified.

Supported evidence types:

- `pyproject-entrypoint`
- `pyproject-value`
- `command-manifest`
- `pytest-node`
- `command-probe`
- `generated-artifact`

S4c Pages deployment adds `.github/workflows/pages.yml`. The GitHub Pages
workflow builds a fresh `site/dist/` artifact and runs the site tests on `main`.
It configures Pages, uploads with `actions/upload-pages-artifact`, and deploys
with `actions/deploy-pages` only after the repository Pages API reports
`build_type: workflow`. When Pages is not enabled or not set to GitHub Actions deployment,
the workflow records that state and skips the Pages-specific steps after a
successful build rather than turning `main` red for a missing repository setting.
