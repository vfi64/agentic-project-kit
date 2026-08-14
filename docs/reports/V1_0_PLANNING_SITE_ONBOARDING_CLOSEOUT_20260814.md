# v1.0 Planning and Site Onboarding Closeout

Status: complete
Date: 2026-08-14
Branch: `codex/v1-direction-site-onboarding`
Base main: `eaa92f6f`
Command manifest SHA: `2bb560ebe587`

## Scope

This slice closes the post-release consistency gap found after the verified
v1.0.0 release:

- bring `docs/planning/PROJECT_DIRECTION.yaml` in line with the v1.0.0 release
  and DOI closeout;
- ensure no GUI dependency can be read as a retroactive 1.0 release blocker;
- add a report-only planning drift record for open Direction items that carry
  current-release evidence or a passed target release;
- expose the public generated website from the README;
- add a generated quickstart page for local install, Docker-contained pip usage,
  new repositories, and existing repositories;
- regenerate the `/docs` GitHub Pages fallback.

## Result

`v1-0-milestone` is now `done` with release evidence:

- GitHub release: `https://github.com/vfi64/agentic-project-kit/releases/tag/v1.0.0`
- Zenodo version DOI: `10.5281/zenodo.21925421`
- DOI closeout: `docs/reports/release/post-release-doi-closeout-1.0.0.json`
- release closeout PR: `#2090`, merge commit `52a72628`

The remaining 1.0 dependencies are completed Direction items:

- `post-0-5-0-phases-a-b-c`
- `v1-0-schema-readiness`

`p6-gui-project-selection-and-ci-recipe` is retained only as related prior work.
The item now states explicitly that GUI workbench capability is not a 1.0
release prerequisite. The accepted 1.0 basis remains deterministic CLI
operating-layer evidence, schema migration evidence, external repository
evidence, release publication, and DOI closeout.

## Drift Guard

`agentic-kit direction audit-drift` now emits report-only records for two
release-planning drift classes:

- `OPEN_ITEM_REFERENCES_CURRENT_RELEASE`
- `OPEN_ITEM_TARGET_RELEASE_PASSED`

These records do not change `direction validate` into a release-history gate.
They make the stale-planning pattern visible during audits without blocking
ordinary validation.

## Website and README

The README now links to the published generated website:

- `https://vfi64.github.io/agentic-project-kit/`
- `https://vfi64.github.io/agentic-project-kit/site/quickstart/`

The generated site now includes:

- `quickstart/index.html`
- `quickstart/quickstart.json`

The quickstart projection is generated from package metadata, command-manifest
entries, and canonical documentation links. It covers:

- local pip install in a virtual environment;
- local Kit checkout development;
- a Docker-contained Python path using pip, without claiming an official Docker
  image;
- `agentic-kit init` for new repositories;
- `workspace dpa-intake`, `workspace adopt`, `workspace init`, health gates,
  successor handoff, and `workspace remove` for existing repositories.

`sentinel.yaml` raises the README word cap from 4500 to 5200 words so the public
website pointer and short onboarding link do not create artificial churn.

## Full-Suite Follow-ups

The first full local test run exposed two local consistency follow-ups, both
fixed in this slice:

- `tests/test_site_claims.py` used a site fixture without the new
  `quickstart.html` template.
- `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` still counted
  `docs/reports/` as 88 Markdown files after this report was added; it now
  records 89.

## Known Limits Preserved

- No official Docker image is claimed.
- Remote target-CI validation remains limited by the neutral fork having no
  reported checks.
- Broader unrelated repository evidence is not expanded by this slice; the
  previously recorded Comm-SCI and neutral `sampleproject` evidence remain the
  current basis.

## Evidence

- `pytest tests/test_project_direction.py tests/test_site_generator.py tests/test_readme_release_history_extraction.py`: 34 passed.
- `pytest tests/test_documentation_registry.py::test_decision_template_counts_match_filesystem tests/test_site_claims.py::test_optional_unverified_claim_does_not_block_site_build tests/test_site_claims.py tests/test_site_generator.py`: 16 passed.
- `pytest -q`: 2813 passed, 632 warnings.
- `ruff check .`: PASS.
- `python -m py_compile src/agentic_project_kit/project_direction.py src/agentic_project_kit/site_generator.py`: PASS.
- `agentic-kit check`: PASS.
- `agentic-kit check-docs`: PASS.
- `agentic-kit doctor`: Overall PASS; document lifecycle findings remain report-only WARN.
- `agentic-kit docs-registry`: PASS, 296 registered documents and 90 unregistered candidates.
- `agentic-kit standard-gates-audit-suite`: PASS, 17 checks, 0 blockers.
- `python site/scripts/build.py --docs-pages-fallback --json`: PASS, 14 files.
- `agentic-kit direction validate --root .`: PASS.
- `agentic-kit direction audit-drift --root .`: PASS; no open current-release
  Direction records after the v1.0 milestone update.
- `git diff --check`: PASS.

PR lifecycle, CI, merge, post-merge settle, and successor handoff closeout remain
required before this branch is considered fully closed on `main`.
