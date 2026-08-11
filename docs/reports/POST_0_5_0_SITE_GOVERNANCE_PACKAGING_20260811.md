Status: analysis
Status-date: 2026-08-11
Scope: Phase A2 site governance and packaging
Branch: codex/post-050-planning-reconciliation

# Post-0.5.0 Site Governance And Packaging

## Decision

`site/` remains outside `DOC_REGISTRY_SCOPE`.

The current `site/` tree is a repository-native generated website projection
surface, not a governed document tree under `docs/` and not Python package
runtime data. It should not be registered merely because it exists.

## Evidence

Checked current sources:

- `site/README.md` defines the site as a generated projection of repository
  sources and states that `site/dist/` is ignored.
- `docs/DOC_REGISTRY_SCOPE.yaml` declares required/exempt paths under `docs/`
  only. `site/` is outside that scope model.
- `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` records
  `docs/reports/` and `docs/examples/` exemptions, not a general rule that every
  non-docs tree must enter the registry.
- `agentic-kit doc-registry check-unregistered --strict-scope --json`: `PASS`,
  0 scope violations.
- `python site/scripts/build.py --output tmp/site-build-a2 --json`: `PASS`,
  10 generated files, 10 verified claims, command catalog derived from the
  command manifest.
- `python -m pytest -q tests/test_site_generator.py tests/test_site_claims.py tests/test_pages_workflow.py`:
  13 passed.

Packaging check before this slice:

- `python -m build --sdist --wheel --outdir tmp/package-check-build-20260811`:
  `PASS`.
- Built wheel `agentic_project_kit-0.5.0-py3-none-any.whl`: `site_count=0`.
- Built sdist `agentic_project_kit-0.5.0.tar.gz`: `site_count=9`.

The wheel was already clean. The sdist included the checked-in `site/` source
tree because Hatchling's default source-distribution behavior included tracked
repository files not excluded by `[tool.hatch.build].exclude`.

## Chosen Change

Add `/site` to `[tool.hatch.build].exclude`.

This is the smallest clean architecture change because:

- it does not expand documentation registry scope;
- it does not move or delete the website sources;
- it preserves the generated-site workflow and GitHub Pages build path;
- it aligns sdist and wheel behavior with the stated product boundary that
  `site/` is not package runtime data.

## Non-Goals

This slice does not:

- register `site/` in `docs/DOCUMENTATION_REGISTRY.yaml`;
- include `site/` in Python package data;
- alter `site/dist/` ignore behavior;
- change GitHub Pages deployment semantics;
- exclude `docs/reports/` or any other tree from distribution artifacts beyond
  the specific `site/` finding.

## Post-Change Evidence

After adding `/site` to `[tool.hatch.build].exclude`:

- `python -m build --sdist --wheel --outdir tmp/package-check-build-20260811-after`:
  `PASS`.
- Built wheel `agentic_project_kit-0.5.0-py3-none-any.whl`: `site_count=0`.
- Built sdist `agentic_project_kit-0.5.0.tar.gz`: `site_count=0`.
- `python -m pytest -q tests/test_packaging_config.py tests/test_site_generator.py tests/test_site_claims.py tests/test_pages_workflow.py`:
  14 passed.
- `python site/scripts/build.py --output tmp/site-build-a2-after --json`:
  `PASS`, 10 generated files, 10 verified claims.
