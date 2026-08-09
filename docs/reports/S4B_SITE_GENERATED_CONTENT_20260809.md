# S4b Site Generated Repository Content

Date: 2026-08-09

Base before S4b: `97b611453a971f6343258f0d7b2033556b6b849a`
(`Refresh handoff state after PR2028 (#2029)`).

## Scope

S4b extends the S4a foundation with generated repository projections. It does
not add claim-evidence evaluation, GitHub Pages deployment or the final
presentation layer.

## Generated Sources

- `pyproject.toml`: package name, version and Python requirement.
- `docs/reference/agentic-kit-commands.json`: command catalog, command count,
  surface, safety, dry-run, help, when-to-use and parameters.
- `docs/STATUS.md`: current release tag, Zenodo DOI markers, current verified
  main and next-safe-step summary.
- `CITATION.cff`: concept DOI fallback when STATUS does not carry one.
- `docs/planning/PROJECT_DIRECTION.yaml`: roadmap and strategy status counts.
- `git rev-parse HEAD`: build commit.

## Generated Outputs

The local build writes these generated files under the selected output
directory:

- `index.html`
- `site.json`
- `commands/guided.html`
- `commands/diagnostics.html`
- `commands/index.html`
- `commands/commands.json`
- `static/site.css`

The checked-in repository still does not commit `site/dist/`.

## Gate Behavior

The build blocks when:

- the command manifest is unreadable;
- `meta.manifest_sha` is missing or does not reproduce from `commands`;
- a command lacks `qualified_name`, `group`, valid `surface`, valid `safety`,
  boolean `dry_run_available`, `when_to_use` or list-shaped `params`;
- the guided view has no `orchestrator` commands;
- the diagnostics view has no `diagnostic` commands;
- package version or Python requirement is missing.

S4b intentionally keeps technical claim verification for S4b.2. No generated
claim is represented as `verified` by this slice.
