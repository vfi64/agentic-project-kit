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
