# Generated Website

This directory contains the repository-native public website generator.

The generated output is a projection of current repository sources, not a manual
technical truth surface. `site/scripts/build.py` calls
`agentic_project_kit.site_generator` and writes the static artifact to
`site/dist/` by default. The generated `site/dist/` tree is ignored; GitHub
Pages deployment must build a fresh artifact from the checked-in sources.
`site/` and the generated `/docs` Pages fallback files are excluded from Python sdist and wheel artifacts
because they are repository-native projection surfaces, not package runtime data.

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

W0a evidence integrity keeps the same three computed statuses. Claims additionally
carry an evidence scope: `technical` (default), `documentation`, or
`historical-observation` with a mandatory `scope_note`. A presentation template
cannot verify its own technical or historical claim. Documentation assertions
verify documentation only; historical observations do not establish current release
installability. These scopes classify the assertion's boundary, not its maturity.

Direct evidence inputs are derived from claim bindings and checked against the
Pages input manifest. Conservative `src/agentic_project_kit/`, `tools/`, `tests/`
and report prefixes cover transitive source changes; this can cause extra builds.
A new evidence path outside those inputs blocks the build until the manifest is
updated. This does not add a YAML dependency to the pre-install Pages classifier.
The existing literal selections are unchanged, but a missing selected command now
blocks the build instead of rendering an empty metadata row. Unsupported workflow
maturity rankings are omitted; preferred-command reselection belongs to W0b.

Supported evidence types:

- `pyproject-entrypoint`
- `pyproject-value`
- `command-manifest`
- `pytest-node`
- `command-probe`
- `generated-artifact`

S4c Pages deployment adds `.github/workflows/pages.yml`. The GitHub Pages
workflow builds a fresh `site/dist/` artifact and runs the site tests on `main`.
Pages builds on every push to main and explicit dispatch. The former Pages path gate
is no longer part of the workflow. Its legacy diagnostic classifier and
`site/pages_input_manifest.json` retain `BUILD_REQUIRED` / `BUILD_SKIPPED` for
compatibility, including release/version projection state and deterministically
irrelevant main-push changes; those results cannot skip builds.
The workflow configures Pages, uploads with `actions/upload-pages-artifact`, and
deploys with `actions/deploy-pages` only after the repository Pages API reports
`build_type: workflow`. When Pages is not enabled or not set to GitHub Actions deployment,
the workflow records that state and skips the Pages-specific steps
after a successful build rather than turning `main` red for a missing repository
setting.
When Pages is served from the Actions artifact, public links use the deployment
root, for example `/quickstart/` and `/workflows/`. The `/site/` prefix belongs
only to the legacy docs-source fallback.

Legacy GitHub Pages source `/docs` is supported as a generated fallback, not as a
new manual website source. `python site/scripts/build.py --docs-pages-fallback --json`
writes `docs/index.html`, `docs/.nojekyll`, and `docs/site/` from the same
generator. This lets `https://vfi64.github.io/agentic-project-kit/` open the
generated website while preserving `site/` as the canonical source and
`site/dist/` as ignored fresh-build output.
The fallback intentionally renders volatile current-state details as pointers to
`docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md`; this keeps the committed
Pages projection idempotent across post-merge handoff/status refreshes.
CI enforces the docs Pages fallback pytest staleness check through
`tests/test_site_fallback_staleness.py`. The test builds the fallback-equivalent
`docs/site/` projection into a temporary directory and performs a byte-for-byte comparison
against `docs/index.html`, `docs/.nojekyll`, and committed
`docs/site/` files. No comparison exceptions are currently needed: the fallback
uses the stable `docs-pages-fallback` internal projection label and pointer text for volatile
repository state, so a mismatch means the generated docs output needs to be
rebuilt and committed.

S4d presentation keeps the public homepage generated from the same sources while
adding clearer explanatory sections:

- `static/runtime-map.svg` visualizes repository truth flowing into the
  deterministic site builder.
- Repository Memory, Runtime Structure, CLI, GUI, Communication, and Claims
  sections are rendered from templates plus generated metadata.
- Guided lifecycle examples come from `surface: orchestrator` and are ordered
  by `lifecycle_rank` metadata in the generated command manifest, with
  deterministic grouping as fallback.
- common blocker diagnostics come from the existing GUI command projection, not
  a separate website taxonomy.
- Status categories use computed claim status and declared scope: required evidence
  checks, optional evidence checks, planned, and not claimed. Optional is not a
  maturity ranking.

S4e quickstart projection adds `quickstart/index.html` and
`quickstart/quickstart.json`:

- install paths cover local pip, local Kit checkout development, and a
  Docker-based Python container path without claiming an official Kit image.
- new-repository and existing-repository flows are rendered beside command
  metadata projected from `docs/reference/agentic-kit-commands.json`.
- documentation links point back to canonical repository docs, including the
  Brownfield external repository guide and generated command reference.

S4f workflow projection adds `workflows/index.html` and
`workflows/workflows.json`:

- the public entry point is `Choose How You Want To Work`, not a raw command
  list.
- File Transfer, Copy and Paste, Agent Direct, and the experimental early GUI surface
  are generated from one projection, with manifest-backed command
  metadata where commands exist.
- the page explains that the Kit complements Git and CI; it does not replace them.
- Executor Is Replaceable; Repository Governance Persists is rendered as a
  workflow boundary, not as a claim for one required runtime.
- YAML/JSON state is documented as versioned, diffable, reviewable, and
  portable, with file-volume and projection-refresh tradeoffs.
- Brownfield evidence is read from
  `docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json`; the current
  status is `B1_EVALUABLE`, and general Brownfield portability is explicitly not
  claimed from one familiar private repository.

## Explanation and public evidence

`agentic_project_kit.site_explanation` generates `understand/index.html` and
`understand/evidence.json`. Audience, architecture, benefits, limits and local
controller boundaries are curated explanations of existing contracts. Current
release bullets come from the matching CHANGELOG section. Brownfield observation
counts come from canonical planning records with existing public reports; the
historical B1 threshold window remains separately labelled. Greenfield evidence
retains its tested package, date and scope; missing or invalid evidence is
`unverified`, never a fresh PASS. PAA remains planning, not an implemented engine.

Only selected public fields are projected; private repository identities, raw
reports and local runtime paths are not copied. `tool_comparison.yaml` contains
dated official-source descriptions, not automatic external product monitoring,
rankings or measured superiority claims. Invalid comparison URLs/dates block the
build. Builds require no network access for those descriptions.

`tests/test_site_explanation.py` checks derivation, evidence degradation, release
isolation, escaping and publication boundaries. `static/kit-architecture.svg`
shows Kit responsibilities; `static/runtime-map.svg` describes the site build.


## W0b public entry contract

The visible product name comes from the single README H1, checked against
`project.name` and `CITATION.cff` title. Normalization trims leading/trailing
whitespace, lowercases, and replaces each whitespace run with one hyphen;
other characters are preserved. Missing or contradictory sources block the build.
No website-only rename or Formerly claim is allowed.

The overview keeps purpose, the everyday workflow, audience, limits and a short
release card. Technical provenance is labelled separately: Pages fallback is a
projection type, not a Git commit; a deterministic source SHA that is not supplied
is shown as not provided. Claim counts are computed per scope and status; an
unqualified total of verified claims is not shown. Aggregate JSON counts remain
compatible. Neither scope nor optional status is a maturity ranking.

The release card counts **entries in the CHANGELOG section**: every top-level
`- ` bullet line in the exact version section, including zero and more than eight.
Subheadings do not end a section; Unreleased and neighboring versions are excluded.
A missing date is not recorded. Nested, numbered or alternate bullet syntax blocks
rather than silently changing the meaning of the count. Fenced code is excluded.
This is a line count, not a measure of change size.

The first existing-repository path contains four editorial command families:
workspace adopt, workspace init (preview and explicit execute), check, doctor.
The manifest supplies safety and availability, not this editorial ordering.
D1 remains deferred as the future shared task-to-preferred-command authority.
The generator path remains separate; removal is not an onboarding step.
The fixture runs the actual local sequence with no models or remote actions and
checks read-only previews, preservation of project files, bounded writes and gates.
The four communication paths do not claim equal maturity or test coverage; GUI/CLI
parity and automatic recovery are not promised.

`release-pypi-workflow` is a scoped optional evidence binding. For the version from
pyproject.toml it reads `docs/reports/release/release-run-<version>.json`, requires
matching version/tag, PyPI publication policy, release.yml PyPI target and C3 PASS
with returncode zero and no blockers. This proves successful workflow completion,
not index visibility or installability. Missing evidence is unverified and removes
PyPI assurances from the quickstart. No network or installation test runs in the
site build, and no historical archive is rewritten.

The GF-078 case separates the finding/repair, regression coverage, recorded release
steps and a bounded archive merge observation captured from GitHub and local Git.
That observation is a build input, so shallow checkouts reproduce the same card.
It does not claim every recovery path was executed or consumer VERIFIED_FIXED.
E freshness policy, N4 Pages simplification, D1, lock triage and new graphics remain
outside W0b.
