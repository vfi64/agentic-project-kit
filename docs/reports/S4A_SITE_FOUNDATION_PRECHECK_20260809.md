# S4a Site Foundation Precheck

Date: 2026-08-09

Current base before S4a: `fabd18da349ef87676e6313d1c5782e04b8a208b`
(`Refresh handoff state after PR2026 (#2027)`).

## Findings

- No `site/` tree existed before this slice.
- No `.openai/hosting.json` file exists, so the OpenAI Sites connector is not
  the repository authority for this work.
- GitHub Pages is not currently configured for `vfi64/agentic-project-kit`; the
  GitHub Pages REST endpoint returned HTTP 404.
- Existing workflows are `.github/workflows/ci.yml` and
  `.github/workflows/release.yml`; no Pages workflow exists before S4c.
- `site/dist/` is generated output and must not become a committed truth
  surface.
- `site/` is outside the governed `docs/` registry scope. The website needs its
  own README, tests and coverage anchors, not documentation-registry enrollment.
- `pyproject.toml` is the source for package name, package version, Python
  requirement and entry points.
- The command manifest identity authority is
  `docs/reference/agentic-kit-commands.json` field `meta.manifest_sha`, currently
  `3d20e7338c12`.
- The manifest identity is reproducible through
  `agentic_project_kit.command_manifest.manifest_sha(commands)`.
- There is no top-level `manifest_hash` field.

## S4a Decision

S4a adds only the local foundation:

- importable generator core in `agentic_project_kit.site_generator`;
- thin local script adapter at `site/scripts/build.py`;
- minimal template and static CSS;
- generated output ignored under `site/dist/`;
- tests that prove version, command count and manifest identity are derived from
  current repository sources.

S4a does not add claim-evidence evaluation, command catalog pages, GitHub Pages
deployment or presentation-layer claims. Those remain S4b, S4b.2, S4c and S4d.
