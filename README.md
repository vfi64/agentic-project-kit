# Agentic Project Kit

> Handoff architecture: the deterministic Successor Handoff Package writes `successor_context.yaml`, `source_manifest.json`, `validation_report.json`, `execution_contract.json`, and `successor_prompt.md` under `docs/reports/handoff-packages/latest/` for this repo or `.agentic/state/handoff/packages/latest/` in external workspace mode. New chats verify the package and execution contract, not chat memory.


Current version: 1.0.6
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20101359.svg)](https://doi.org/10.5281/zenodo.20101359)

`agentic-project-kit` is a local Python package and CLI for governing AI-assisted repository work with explicit contracts, gates, evidence, handoffs, policy selection, task tracking, GitHub automation, and release validation.

Generated website: <https://vfi64.github.io/agentic-project-kit/>. It serves the current public projection with install, new-repo, existing-repo, command, and claim-evidence views.

## Why this exists

AI-assisted development works best when project context is explicit, current, and machine-checkable. Otherwise, agents drift into stale handoffs, unclear branch rules, missing test evidence, and unstructured logs.

This kit turns those lessons into a reusable starter system for new repositories.

The goal is not making an LLM write code better by itself; it is making repository state, handoffs, documentation coverage, tasks, release state, and policy expectations visible enough to reduce context drift.

## Why not just Cookiecutter?

Cookiecutter-style generators create initial files. `agentic-project-kit` targets the narrower problem of keeping AI-assisted repository work reviewable after the first commit.

A generated project includes machine-readable state, current handoff files, documentation coverage expectations, task gates, local health checks, release-state validation, policy-pack fixtures, and evidence conventions. These are governance aids, not semantic-completeness or production-readiness claims.

## What it generates

A generated project includes:

- professional GitHub repository structure
- `.agentic/project.yaml` as a machine-readable project contract
- recommended project profiles and policy packs
- `AGENTS.md` with stable agent rules and closeout expectations
- `docs/PROJECT_START.md` for first-run decisions
- `docs/STATUS.md` as compact current-state dashboard
- `docs/TEST_GATES.md` as evidence matrix for different change types
- `docs/handoff/CURRENT_HANDOFF.md` and `STANDARD_AGENT_PROMPT.md`
- `.agentic/todo.yaml` plus rendered `docs/TODO.md`
- GitHub Actions CI workflow
- pull request template and agent-regression issue template
- GitHub Copilot instruction file
- pre-commit configuration
- bounded diagnostic log staging script
- `sentinel.yaml` for document and task checks
- minimal package/test skeleton for Python projects

## Installation

Install the public package from PyPI in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install agentic-project-kit
agentic-kit --version
```

The first public PyPI validation confirmed that the published package installs
in an isolated Docker container. Its historical first-contact findings are
recorded in `docs/reports/V1_0_1_DOCKER_PYPI_FIRST_CONTACT_20260820.md`.

Git is a system prerequisite for `agentic-kit init` and Git-backed workflows.
`pip install agentic-project-kit` cannot install Git portably across macOS,
Linux, and Windows. Install Git with your operating-system package manager or
installer before creating a new governed repository.

For Kit development from the public source projection:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit --version
```

For Kit development from a local checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run gates:

```bash
pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit --version
agentic-kit --help
```

## Quick start

First-chat route selection is in `docs/ONBOARDING.md`. It separates creating a
new governed project, adding the Kit operating layer to an existing repository,
and working on this Kit repository. Use `agentic-kit onboarding measure` to
check that the onboarding guide still matches the command manifest and
workspace-detection message.

For the generated install and usage walkthrough, including the PyPI install
path, the source install path, a Docker-based safe package test, new
repositories, and existing repositories, see
<https://vfi64.github.io/agentic-project-kit/site/quickstart/>.

Evidence labels stay separate:

- Historical PyPI Validation: a published package was installed from
  `pypi.org`.
- Post-fix Build/Checkout Validation: a local checkout or local wheel was tested
  before publication.
- Post-release PyPI Validation: a later published package was installed from
  `pypi.org` after release.

Docker without an official registry image uses the local source image:

```bash
git clone https://github.com/vfi64/agentic-project-kit.git
cd agentic-project-kit
docker build -t agentic-project-kit:local .
docker run --rm -v "/path/to/repo:/work" agentic-project-kit:local doctor --root /work
```

Creating a new repository inside Docker also needs a Git identity for the
initial convenience commit:

```bash
docker run --rm \
  -e GIT_AUTHOR_NAME="Your Name" \
  -e GIT_AUTHOR_EMAIL="you@example.com" \
  -e GIT_COMMITTER_NAME="Your Name" \
  -e GIT_COMMITTER_EMAIL="you@example.com" \
  -v "$PWD:/work" \
  agentic-project-kit:local init my-new-project --type generic --kit-source none
```

Without that identity the project files are still created, but the initial Git
commit is skipped with an explicit warning. GitHub operations inside Docker
require explicit `gh` and SSH credentials; no secret should be baked into the
image.

Create a new project interactively:

```bash
agentic-kit init
```

Create a new Python CLI project non-interactively:

```bash
agentic-kit init my-new-project \
  --type python-cli \
  --description "My new project" \
  --license MIT \
  --github-actions \
  --pre-commit \
  --agent-docs \
  --logging-evidence
```

Then enter the generated project and run:

```bash
cd my-new-project
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
agentic-kit check
agentic-kit doctor
```

## Example workflow

See `docs/examples/minimal-python-cli.md` for a small end-to-end example showing how a generated Python CLI project gets project state files, agent instructions, documentation gates, task gates, and a local doctor check.

## Project contract, profiles, and policy packs

Generated projects contain `.agentic/project.yaml` as a machine-readable project contract and a standard `.gitignore` for local Python/tooling byproducts. The contract records the project name, description, project type, selected profiles, selected policy packs, and basic governance expectations.

Profiles describe what kind of repository the project is, for example `generic-git-repo`, `markdown-docs`, `python-cli`, `python-lib`, `git-github`, or `release-managed`.

Policy packs describe which development rules are recommended for the project goal, for example `starter`, `prototype`, `solo-maintainer`, `agentic-development`, `release-managed`, or `documentation-governed`.

By default, `agentic-kit init` recommends profiles and policy packs from the selected project type and enabled features. You can override them explicitly:

```bash
agentic-kit init my-docs-project \
  --type generic \
  --profiles generic-git-repo,markdown-docs \
  --policy-packs starter,documentation-governed
```

`agentic-kit doctor` validates the project contract when `.agentic/project.yaml` is present and reports selected profiles and policy packs.

After `agentic-kit workspace init --root PATH --execute`, `.agentic/config.yaml` enables external workspace health mode without the self-hosting Kit documentation set. `check`/`check-docs` inspect `.agentic/state/` and `.agentic/registries/`. On external workspaces, `doctor` marks not-applicable Kit checks, skips repo-local source audit, checks packaged command manifest availability, and treats Kit-specific version drift as project-owned release governance. `rules snapshot` and `rules acknowledge` use the external workspace rule sources `.agentic/config.yaml`, `.agentic/registries/rules.yaml`, `.agentic/rules/README.md`, `.agentic/state/status.md`, and `.agentic/state/handoff/README.md` instead of requiring Kit self-hosting files such as `docs/STATUS.md`. Fresh LLM-context carriers use the workspace namespace, including `.agentic/state/handoff/transfer_handoff_reports/` externally. `transfer pr-merge-safe` may run externally after fresh-context passes, external rule acknowledgement is current, and the worktree is clean except known transient carriers.

## Policy-pack doctor checks

`agentic-kit doctor` also activates lightweight policy-pack checks from `.agentic/project.yaml`.

They verify structural prerequisites:

- `solo-maintainer` expects status, handoff, sentinel, and task gate files.
- `agentic-development` expects agent instructions, test gates, handoff, and the architecture contract.
- `release-managed` expects changelog, citation metadata, and Zenodo metadata.
- `documentation-governed` expects the documentation coverage matrix and architecture contract.
- `starter` and `prototype` expect basic README/status scaffolding.

The policy-pack checks are structural. They prove that the selected policy pack has its required fixtures, not prose completeness or release readiness.

## Project health check

Use `agentic-kit doctor` as the compact repository health check:

```bash
agentic-kit doctor
```

It reports project files, workspace manifest status, project contract status,
policy-pack checks, documentation gates, task validation, and version drift.
`SKIP` means not applicable; `WARN` means advisory. The command exits non-zero
only when required checks fail.

`agentic-kit check` and `agentic-kit doctor` treat a directory with no Kit
markers as `not an Agentic Project Kit workspace` and exit non-zero with the
next safe setup command instead of an internal traceback. A freshly generated
project uses `.agentic/project.yaml`; `doctor` reports the operating-layer
`.agentic/config.yaml` checks as `SKIP` there instead of warning that the new
project is implicitly legacy.

## Clean handoff / chat switch

Use the deterministic successor handoff package before switching chats or continuing in another LLM:

```bash
agentic-kit transfer chat-switch-complete --render-prompt
```

For local development in this repository, run it through the project environment:

```bash
./.venv/bin/agentic-kit transfer chat-switch-complete --render-prompt
```

The command writes a machine-readable successor context, source manifest, validation report, and copy/paste successor prompt under:

```text
docs/reports/handoff-packages/latest/
```

In external workspace mode the default package path is `.agentic/state/handoff/packages/latest/`. It updates canonical chat-switch projections, including the initial `START_NEW_CHAT_PROMPT.md` when missing. A successor chat uses `successor_prompt.md`, runs `agentic-kit transfer repo-status`, `agentic-kit check --root .`, and `agentic-kit doctor --root .`, and stops unless `validation_report.json` is `PASS`.

After a PR merge, run `agentic-kit transfer post-merge-settle --after-pr PR_NUMBER`; it stops at READY/NOOP and blocks repeated generated/admin refresh loops.

## Planning-documentation slice gate

`agentic-kit slice gate --kind planning-doc` emits `SLICE_GATE_RESULT` and `slice_result=PASS|BLOCKED`. helper-local PASS is not a slice PASS; `planning-doc` runs targeted tests plus `agentic-kit handoff check`, `agentic-kit check-docs`, `agentic-kit docs-audit`, and `agentic-kit doctor`. Dirty state reports `merge_pr_ready=NO`.

## Project direction

`agentic-kit direction validate`, `agentic-kit direction render`, and `agentic-kit direction audit-drift` guard `docs/planning/PROJECT_DIRECTION.yaml`.
`meta.updated_after_pr` is a strategic direction refresh marker, not a current-main freshness claim; validation requires `updated_after_pr_semantics` and keeps `updated_after_pr_current_main_claimed=false` when the marker is set.
Open Direction items whose `target_release` passed the current package version require revalidation.

## Govern an existing repository (operating layer)

For an existing Git repo, add `.agentic/` governance; use `agentic-kit init` only for new scaffolds.

```bash
python -m pip install "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit workspace dpa-intake --root PATH
agentic-kit workspace adopt --root PATH
agentic-kit dpa repo-adoption-assessment --root PATH
agentic-kit workspace init --root PATH --execute [--inject-ci|--inject-pre-commit]
agentic-kit workspace remove --root PATH
agentic-kit-gui --root PATH
```

`workspace dpa-intake` is the one-shot DPA intake orchestrator for takeover or
new-workspace planning. It resolves the target repo exact Git ref when possible,
runs `workspace adopt`, runs the DPA repo-adoption assessment, groups surfaces
into an `adjudication_plan`, and can write bounded intake evidence with
`--write-evidence --execute`. It remains read-only by default and keeps
`external_repo_conformance_claimed=false`,
`automatic_migration_performed=false`, and `production_mutation_performed=false`;
`READY_FOR_DPA_INTAKE_ADJUDICATION` means the repo is ready for Maintainer
adjudication, not automatically conformant.

`workspace adopt` is read-only: it proposes `.agentic/config.yaml`, reports the private/public boundary, a documentation age baseline, a DPA repo-adoption assessment, and foreign `.agentic/` directory. `agentic-kit dpa repo-adoption-assessment --root PATH` is the same DPA intake gate as a standalone command: it inventories candidate surfaces, including top-level architecture/specification files and common specification directories such as `JSON/`, records source authority and target identity, classifies `specification_authority`, generated, or command-updated outputs, records DPA-600/DPA-700 evidence requirements, requires exact-ref evidence before adoption readiness, and keeps `external_repo_conformance_claimed=false`. `workspace init` is dry-run by default; `--execute` creates `.agentic/state/status.md`, `.agentic/state/handoff/`, `.agentic/DOC_LIFECYCLE.md`, `docs/archive/README.md`, transfer/CI/prompt files, and a `hygiene` manifest block with warn-mode doc lifecycle defaults. It appends `.agentic/tmp/`; versioned `.agentic/` must not hold secrets, chat fragments, or logs.

`agentic-kit workspace upgrade --root PATH` is also a dry-run by default. It
plans deterministic manifest schema migrations step by step, prints the
manifest diff, reports when a workspace is already at schema v2, and with
`--execute` writes `.agentic/config.yaml.bak.v<N>` before each migration step.
The first real schema migration upgrades v1 manifests to v2 by materializing
`hygiene`. Manifest-less repositories should run `workspace init`;
newer-schema repositories should upgrade the kit.

After updating the Kit package in an already managed repository, run the bounded
upgrade path from inside or against the target repository:

```bash
python -m pip install --upgrade "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit doctor --root PATH
agentic-kit workspace upgrade --root PATH
agentic-kit workspace upgrade --root PATH --execute
agentic-kit check --root PATH
agentic-kit doctor --root PATH
```

`doctor` reports an actionable warning when the workspace manifest schema is
older than the schema supported by the installed Kit.

Brownfield path: `docs/guides/BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md`.

`agentic-kit workspace remove --root PATH` is the bounded rollback path for an
unmodified Kit operating layer. It is dry-run by default. With `--execute` it
removes only exact Kit-generated `.agentic/` workspace files and managed injected
CI/pre-commit files; generated successor handoff package files are recognized.
Rule: unknown or modified `.agentic/` paths block execution; project docs/source files are preserved.

Manifest-less repositories still use the implicit legacy profile for the 1.x
line, but that fallback is deprecated. The resolver emits a suppressible
legacy profile deprecation warning for compatibility repositories that have Kit
governance markers but no `.agentic/config.yaml`; empty non-workspaces and
fresh generator-mode projects have explicit public CLI states instead. Set
`AGENTIC_KIT_SUPPRESS_LEGACY_PROFILE_WARNING=1` for temporary quiet
compatibility while planning `workspace init`.

## Documentation registry

`agentic-kit docs-registry` shows the read-only documentation registry summary.
Reviewed single-entry additions use `agentic-kit doc-registry register --path PATH
--class CLASS --json`; `agentic-kit doc-registry check-unregistered --json`
warns without broad migration. `docs/DOC_REGISTRY_SCOPE.yaml` declares required
files, required paths, and exemptions; `agentic-kit doc-registry check-unregistered --strict-scope`
fails only on declared required scope violations.

## Rule registry

`agentic-kit rule-registry check` validates the governed rule mechanism registry.
`agentic-kit rule-registry report --json` summarizes direct coverage and follow-up
state. Reviewed additive rule entries use `agentic-kit rule-registry register`
with direct source and test evidence; it does not edit or deactivate existing
rules and fails closed when the registry would no longer validate.

## Deterministic quality heuristics

`agentic-kit check-docs` includes deterministic document-quality heuristics for machine-checkable problems such as unresolved placeholder markers, stale handoff markers, missing required sections, missing coverage terms, and documentation drift.

These checks are intentionally limited. They are useful hard gates for known bad patterns, but they do not prove semantic perfection. A passing check does not prove that an architecture is globally optimal, a README is persuasive for every audience, or a handoff is sufficient for every future agent.

Future commands such as `review-docs` or `review-architecture` may provide advisory review for clarity, didactic quality, audience fit, missing rationale, overclaims, architecture drift, or review questions. Such advisory review must remain separate from `doctor` and must not be treated as merge authority.

## Runtime validation workflow

`agentic-project-kit` includes a small deterministic validation path for generated governance artifacts.

The current workflow is intentionally narrow:

```bash
agentic-kit validate-sections output.md -s "Plan" -s "Solution" -s "Check" -s "Final Answer"
agentic-kit validate-contract --root .
agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml
agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --report validation-report.json
agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --repair-output output.repaired.md --repair-report repair-report.json
```

The optional `--report` flag writes machine-readable validation evidence as JSON with `ok`, `contract`, `contract_version`, `checked_file`, and `findings`.

Validation report schema:

```json
{
  "ok": false,
  "contract": "default-answer",
  "contract_version": 1,
  "checked_file": "output.md",
  "findings": [
    {
      "severity": "error",
      "code": "missing_required_section",
      "message": "Missing required section: Solution"
    }
  ]
}
```

The report schema is intentionally small and structural. `findings` entries use stable string fields so CI, wrappers, and review scripts can consume them without parsing human console output.

What these commands do:

- `validate-sections` checks literal required section markers in a text file.
- `validate-contract` checks the machine-readable `.agentic/project.yaml` project contract.
- `validate-output-contract` loads a machine-readable output-contract YAML file and validates an output text file using the same required-section semantics.
- `validate-output-contract --repair-output ... --repair-report ...` can write a deterministic structural repair for missing required sections and a machine-readable repair report. The repair inserts missing section markers with explicit TODO text only; it does not invent semantic content.

Boundary: these checks do not repair content, infer missing facts, or prove semantic correctness. They are deterministic structural gates for known contract requirements.

Generated `governance-wrapper` projects include a sample output contract at:

```text
docs/output-contracts/default-answer.yaml
```

## Release planning and validation

Use `agentic-kit release-plan` before preparing a release:

```bash
agentic-kit release-plan --version 0.3.4
```

Use `agentic-kit release-check` before tagging:

```bash
agentic-kit release-check --version 0.3.4
```

These commands help prevent release-state drift between `pyproject.toml`, `CHANGELOG.md`, project state files, local tags, remote tags, GitHub releases, and citation metadata.

This post-release command is separate from release-check: release-check is a pre-release gate, while post-release-check verifies the already-published release and its Zenodo archive state.

Use `agentic-kit post-release-check` after publishing a GitHub release:

```bash
agentic-kit post-release-check --version 0.3.4
```

This command checks that the GitHub release exists and then looks for a verified Zenodo version record derived from the DOI in `CITATION.cff`. If Zenodo has not archived the release yet, the command reports `WAITING` and leaves README/CITATION DOI metadata unchanged. It is intentionally separate from `release-check`, because `release-check` is a pre-release gate that expects the tag and GitHub release to be unused.

## TODO workflow

Generated projects contain a machine-readable TODO file and a rendered Markdown view.

```bash
agentic-kit todo list
agentic-kit todo complete BOOT-001 --evidence "LICENSE reviewed"
agentic-kit todo render
agentic-kit check-todo
```

The intended pattern is simple: bootstrap tasks are explicit, evidence is recorded, and the human-readable TODO file is regenerated from the YAML source.

## Workflow Output Cycle

For local LLM handoff, prefer the package CLI:

```bash
agentic-kit workflow status
agentic-kit workflow status --explain
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow cleanup
agentic-kit workflow fail-report
```

Use `workflow status --explain` when you are unsure what to do next. It is read-only and explains the current state before recommending a safe command. This guided path is intentionally conservative: dirty working trees and failed workflow states point to evidence upload or inspection first instead of hidden state changes.

Quick command guide:

- `agentic-kit audit-command-authority`: verify that agent-facing chat/handoff entrypoints carry the current command manifest ACK, `command-for` guidance to choose the most specific available Kit workflow command, and the no-memory-reconstruction contract.
- `agentic-kit instruction lint --file PATH` or `--stdin`: lint LLM instruction text against the current command manifest before applying transfer orders.
- `agentic-kit chat refresher --mode copy-paste`: print the six-line command-manifest refresher for chat replies that may include commands.
- `agentic-kit chat session-start --mode copy-paste`: print the refresher plus the full inline command manifest for a new session.
- `agentic-kit commands sync-entrypoints --execute`: synchronize command reference files and command-manifest entrypoint headers.

Command manifest surface classes are role metadata, not stability metadata. `orchestrator` marks primary task/lifecycle operations, `diagnostic` marks inspection and readiness operations, and `primitive` marks public low-level command building blocks. Surface classification is intent-oriented: read-only session start or dry-run maintenance workflows may be primary, while highly parameterized evidence/log/file helpers may remain low-level even when implemented as mini-workflows. Surface classification does not by itself change command safety, compatibility, or deprecation status; primitive does not mean unstable.
`agentic-kit command-for` uses the same surface classes as a tie-breaker after semantic task matching and safety checks: equally suitable task matches prefer orchestrator, diagnostic task tags may prefer diagnostic, and exact primitive matches are not displaced by broader orchestrators. GUI and website projections must consume this same generated `surface` field: Primary (`orchestrator`), Diagnostics (`diagnostic`), and Expert / Low-level (`primitive`).
GUI and website projections may add presentation-only guidance over that surface: `diagnostic_priority` separates Guided Diagnostics common blockers from specialized audits, `safety_review` highlights bounded commands without dry-run as manual-review items, and `claim_evidence` marks commands whose readiness, release, PR, or DPA claims require gate output, exact refs, or remote/release evidence.

## Generated website foundation

`site/scripts/build.py` uses `agentic_project_kit.site_generator` for ignored
`site/dist/`: package version, Python requirement, command
count, `meta.manifest_sha`, `manifest_sha(commands)`, and build commit. The
site is not a second hand-maintained technical truth surface.

Pages: <https://vfi64.github.io/agentic-project-kit/>. Workflow
chooser: <https://vfi64.github.io/agentic-project-kit/site/workflows/>
(`workflows/index.html`, `workflows/workflows.json`). `Choose How You Want To Work`:
File Transfer, Copy and Paste, Agent Direct, and
experimental early GUI surface. Brownfield evidence:
`docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json`; status
`B1_EVALUABLE`; general Brownfield portability is not claimed.

legacy `main` `/docs`: `python site/scripts/build.py --docs-pages-fallback --json`
writes `docs/index.html`, `docs/.nojekyll`, and `docs/site/`; `site/dist/`
stays ignored. `site/` and `/docs` Pages fallback files are excluded from Python sdist and wheel artifacts.

- `agentic-kit workspace dpa-intake`: run the deterministic one-shot DPA intake for a target repository by resolving exact-ref evidence, running workspace adoption analysis and DPA repo-adoption assessment, generating an adjudication plan, and optionally writing bounded intake evidence without migration or external-repo conformance claims.
- `agentic-kit workspace remove`: plan or execute bounded removal of exact Kit-generated workspace files while preserving modified, unknown, source, and project-documentation paths.
- `agentic-kit dpa readiness`: validate the staged DPA DP1 Assessment readiness record, report the deterministic DP2 selected self-hosting target-scope implementation percentage, and keep that separate from Kit-wide DPA conformance.
- `agentic-kit dpa repo-adoption-assessment`: assess a foreign or new repository for DPA-governed adoption without mutation; it records fresh per-repo inventory, source authority, target identity, DPA-600/DPA-700 evidence requirements, exact-ref readiness and no external-repo conformance claim.
- `agentic-kit dpa post-dp2-scope-assessment`: inventory post-DP2 DP3 rollout candidates, DP4 status-authority candidates and DP5 strict lifecycle-gate stage blockers without claiming Kit-wide DPA completion.
- `agentic-kit dpa dp3-dp4-adjudication-check`: validate the bounded DP3/DP4 adjudication record without authorizing DP5 strict lifecycle gates.
- `agentic-kit dpa dp5-stage-check`: validate the bounded DP5 stage record; the current default is strict for the accepted post-DP2 DP3/DP4 scope.
- `agentic-kit dpa dp5-block-new-gate`: fail when current DPA scope nonconformance introduces items outside the accepted warn-stage baseline.
- `agentic-kit dpa dp5-strict-gate`: fail when any configured noncompliance remains in the accepted DPA scope before final closeout.
- `agentic-kit dpa final-closeout-check`: validate the final DP1-DP5 closeout record that owns the bounded Kit-wide DPA conformance claim.
- `agentic-kit dpa stable-readiness-check`: validate Stable-DPA readiness and the bounded Stable Promotion record; foreign repositories still require fresh per-repo inventory, DPA-600/DPA-700 evidence and Maintainer-authorized scope.
- `agentic-kit dpa dp2-decision-readiness`: prepare the DP2 decision package without recording Maintainer Assessment or authorization.
- `agentic-kit dpa maintainer-record-check`: validate a DP2 Maintainer Assessment record or blocked template without authorizing DP2.
- `agentic-kit dpa probe-002-readiness`: inspect PROBE-002 lifecycle and selected-writer readiness, optionally writing bounded DPA probe evidence under `docs/architecture/evidence/dpa/probes/`.
- `agentic-kit dpa probe-003-readiness`: inspect PROBE-003 workflow serialization readiness, optionally writing bounded DPA probe evidence without workflow mutation.
- `agentic-kit dpa renderer-readiness`: inspect Renderer Probe readiness, optionally writing bounded DPA probe evidence without renderer conformance claims.
- `agentic-kit dpa probe-004-readiness`: inspect PROBE-004 migration and rollback readiness, optionally writing bounded DPA probe evidence without migration or rollback execution.
- `agentic-kit dpa wrt-ch001-evidence`: observe a WRT-CH-001 administrative handoff refresh PR without claiming disposable fixture PASS.
- `agentic-kit work start --from-ref REF`: create a fresh work branch based on a selected release tag or branch.
- `agentic-kit work discard-changes`: preview the explicitly destructive feature-branch discard flow; `--execute` requires a deliberate confirmation path.
- `agentic-kit transfer list-refs --json`: list local release tags and branches for the guided work-start picker.
- `workflow status --explain`: inspect the current state and next safe step.
- `workflow request`: mark a concrete local workflow slice as requested.
- `workflow run`: run one bounded workflow state-machine step.
- `workflow cleanup`: clean uploaded temporary evidence after review.
- `workflow fail-report`: upload preserved FAILED-state evidence for diagnosis without cleanup or retry.


Legacy compatibility remains available through:

```bash
agentic-kit workflow request
agentic-kit workflow
```

Prefer the package CLI for normal use; the legacy command is kept visible for compatibility and documentation coverage.

The legacy cycle uses `IDLE`, `TEST`, `UPLOAD`, and `CLEANUP`. Details are documented in `docs/WORKFLOW_OUTPUT_CYCLE.md`.

## Workflow guard

Use `agentic-kit workflow-guard check` before mutation-oriented workflow repair or protected control-file changes. The workflow guard diagnoses recurring workflow failures such as governance YAML parse errors, missing protected anchors, weakened no-hard-length-limit preservation policy, and missing workflow guard policy documentation.

The guard is conservative by design: it diagnoses first and requires a repair plan for semantic rule loss, release-state conflict, broad document rewrites, and unclear YAML recovery. It is a workflow guard, not an autonomous semantic fixer.


## Pattern Advisor read-only catalog

The Pattern Advisor MVP is a local, read-only catalog for recurring project patterns and anti-patterns. It is advisory-only: no gates, no automatic architecture choice, no workflow-state mutation, and no candidate promotion.

```bash
agentic-kit patterns list
agentic-kit patterns show bounded-workflow-evidence
```


## Local Cockpit Foundation

The local cockpit foundation exposes a conservative control surface for local project operation. Use `agentic-kit cockpit`, `agentic-kit actions`, `agentic-kit cockpit status`, `agentic-kit cockpit actions`, and `agentic-kit cockpit run <action-id>` to inspect state, read the structured action inventory, and execute registered read-only actions. For `agentic-kit` actions, inventory output includes `manifest_surface` and `gui_layer` from the command manifest: Primary layer, Diagnostics layer, and Expert / Low-level layer. It also includes `gui_diagnostic_priority`, `claim_evidence`, and `safety_review` so GUI and website views can show Guided Diagnostics common blockers before specialized audits and avoid prose-only readiness or release claims.

The action inventory classifies by category, safety, and Access level. Access level is a Tkinter cockpit visibility convenience, not permission. Execution allows `read_only` by default, blocks `bounded` without an allow path, and blocks general `destructive` actions. The experimental `agentic-kit-gui` entry point starts a local Tkinter cockpit skeleton and may guide `agentic-kit release ready` before confirmed `agentic-kit release prepare`; it must not publish releases, push tags, merge PRs, or run remote cleanup. The GUI button catalog is a Bedienprojektion, not a second taxonomy: `agentic-kit` wrappers must resolve to generated command-reference entries with valid `surface`, and stale wrappers fail tests. The bounded Upload Result Log button uses `agentic-kit work-order upload`.

Architecture details are documented in `docs/architecture/LOCAL_COCKPIT_FOUNDATION.md`.

## Planner-Kit-Executor Contract

`agentic-kit executor plan INTENT` and `agentic-kit executor run INTENT` expose the governed Planner-Kit-Executor surface. The intent may name `hermes` as the first executor adapter, but every runnable step must still resolve through the generated command manifest or the cockpit/action registry. This keeps Kit authority in one place instead of creating a parallel planner or workflow taxonomy.

`agentic-kit executor run` is dry-run by default. Read-only manifest and cockpit steps may run with `--execute`; bounded cockpit actions also require step-level `allow_bounded: true` and CLI `--allow-bounded`; destructive actions remain blocked. The contract, failure states, and evidence rules are documented in `docs/architecture/PLANNER_KIT_EXECUTOR_CONTRACT.md`.

## CLI command package structure

The root CLI module is intentionally a thin root command registry. Command implementations live under `src/agentic_project_kit/cli_commands/`.

```text
src/agentic_project_kit/
  cli.py
  cli_commands/
    checks.py
    github.py
    init.py
    profiles.py
    release.py
    todo.py
    validation.py
    workflow.py
```

Boundary tests keep `cli.py` from regrowing into a monolith.

## GitHub integration

Create a GitHub repository from inside a generated project:

```bash
agentic-kit github-create --owner YOUR_GITHUB_NAME --visibility private
```

This command uses the official GitHub CLI `gh`. It does not ask for or store GitHub tokens.

The generated CI workflow runs the basic project gate on push and pull request. The generated pull request template asks for intended outcome, required evidence, tests, and remaining risks.

## Agentic development model

Generated projects separate:

- stable rules from volatile status
- current handoff from historical notes
- output from outcome
- logs from committed source state
- agent instructions from project overview
- project profiles from policy packs

Agents should start with `AGENTS.md`, `.agentic/project.yaml`, `docs/PROJECT_START.md`, `docs/STATUS.md`, and `docs/TEST_GATES.md`. They should not infer current state from memory or stale prose.

## Documentation coverage and drift checks

`docs/DOCUMENTATION_COVERAGE.yaml` is the machine-checkable documentation coverage matrix.

`agentic-kit check-docs` validates that important commands, workflows, governance concepts, safety rules, release commands, and evidence expectations remain visible.

When adding a public command, workflow, gate, profile, policy pack, generated file, architecture concept, or release-visible feature, update the coverage matrix and the affected documentation in the same change.

## Documentation mesh audit

`agentic-kit doc-mesh-audit` checks machine-readable drift across the project documentation mesh. It is bounded and does not claim semantic proof.

The first audit slice distinguishes four document classes:

- current-state documents, such as README, CITATION, pyproject, package `__version__`, STATUS, and CURRENT_HANDOFF;
- release-history documents, currently CHANGELOG.md, which remain required and may feed release DOI synchronization without being treated as live project state;
- governance documents, such as AGENTS, TEST_GATES, DOCUMENTATION_COVERAGE, sentinel, and project contract files;
- architecture/design documents, such as ARCHITECTURE_CONTRACT, WORKFLOW_OUTPUT_CYCLE, and optional DESIGN.md;
- historical-plan documents, such as roadmap summaries, status reports, and v0.3.0 output-repair planning files.

The hard checks currently cover version mismatches, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches.

`agentic-kit doc-mesh-audit --report doc-mesh-report.json` writes a machine-readable JSON report for CI, review tools, or later workflow evidence.

`agentic-kit doc-mesh-audit --repair-plan doc-mesh-repair-plan.json` writes a bounded repair plan. `agentic-kit doc-mesh-repair` currently applies only one safe automatic repair class: inserting missing historical-source-of-truth banners into known historical-plan documents. Version, DOI, stale-state, and missing-document findings remain manual review items.

Future repair tools should stay bounded to mechanical edits and must not rewrite semantics.

`agentic-kit doc-lifecycle-audit --json`; `agentic-kit doc-lifecycle-audit --strict`; `agentic-kit doc-lifecycle-audit --suggest-review-after`; `agentic-kit audit-doc-orphans`; `agentic-kit docs lifecycle sweep --dry-run`; `agentic-kit docs lifecycle bootstrap --dry-run`; `agentic-kit docs lifecycle propose-delete`.

## Status current-state audit

`agentic-kit audit-status-current-state` checks that `docs/STATUS.md` Current verified main, the handoff validation report, `release-status`, `origin/main`, and the current `CHANGELOG.md` release block agree. It allows bounded admin-refresh lag, but blocks stale current-state claims, including a pending DOI line after STATUS records a verified Zenodo version DOI for the same current version and active Current governed slice / Next safe step instructions that still tell maintainers to publish, prepare, or verify an already verified current release.

## Path literal audit

`agentic-kit audit-path-literals` is report-only. `agentic-kit audit-path-literals --enforce-active`
runs in the standard gate suite and blocks active path/repository identity
literals outside resolver exceptions. Evidence:
`docs/architecture/evidence/path-literal-audit-2026-07-04.md`.

## Mutation-lock coverage audit

`agentic-kit audit-mutation-lock-coverage` runs in the standard gate suite. It
blocks unlocked core runtime git or GitHub mutators; others stay
non-blocking review data. Evidence:
`docs/architecture/evidence/mutation-lock-coverage-2026-07-11-post-lc3.md`.

## Documentation system audit

Use `agentic-kit docs-audit` as the umbrella documentation-system audit command. It reports Aktualität, Vollständigkeit, Korrektheit, Redundanzfreiheit, Stringenz der Dokumentenordnung, and Konsistenz in one ordered result.

The command aggregates deterministic findings from `agentic-kit check-docs`, `agentic-kit doc-mesh-audit`, and `agentic-kit doc-lifecycle-audit`. It also marks full semantic redundancy review as review-only instead of pretending to prove what deterministic gates cannot prove.

```bash
agentic-kit docs-audit
agentic-kit docs-audit --report docs-audit.json
```

## Logging and evidence

The generated `scripts/stage_recent_logs.py` script is intentionally bounded. It stages only a recent diagnostic window from known log folders into `tmp/agent-evidence`.

Logs are diagnostic evidence, not automatic source material. Do not commit secrets, local credentials, broad raw logs, or private runtime state.

## Citation and archiving

Citation metadata is provided in `CITATION.cff`; Zenodo metadata is provided in `.zenodo.json`.

For citation across versions, prefer the all-versions DOI: `10.5281/zenodo.20101359`.

Historical verified version-specific DOI notes are maintained in `docs/releases/VERIFIED_RELEASES.md`.

## Governance wrapper projects

Use the `governance-wrapper` profile for strict human-AI wrapper projects that need explicit output contracts, validation, bounded repair, and auditability.

```bash
agentic-kit init demo-governance \
  --type governance-wrapper \
  --description "Governance wrapper demo" \
  --github-actions \
  --agent-docs \
  --logging-evidence
```

This profile is intended for projects where generated answers or tool outputs must be checked against explicit contracts before they are accepted. The related `output-contracts` policy pack emphasizes schemas, validators, repair boundaries, and evidence-oriented failure handling.

To inspect available profiles and policy packs, run:

```bash
agentic-kit profile-explain
```

## Safety rule

Do not generate a public project from a private repository history.

This kit creates a fresh repository from generic templates. It does not copy a private `.git` history.

## Project scope boundary

`agentic-project-kit` is a generic open repository governance and agentic-development kit. It is not tied to a specific private legacy refactoring project, and examples should stay generic unless they describe generated files or this repository itself.

## GitHub discovery suggestions

Suggested GitHub description:

```text
Reproducible AI-assisted repository work through project contracts, documentation gates, release checks, task gates, and policy packs.
```

Suggested topics:

```text
agentic-development
ai-agents
developer-tools
github
project-template
software-engineering
documentation
release-management
python
cli
```

These repository settings are maintainer-owned and are not changed by the package.

## Current status

Prepared release: `v1.0.6`; GitHub Release, tag publication, and Zenodo version DOI verification are pending.
Version `1.0.6` is the current release line prepared as a safety baseline after the pre-GUI transfer-wrapper, output-discipline, GUI wrapper-gating, PR diagnostics, and release-plan guard hardening work.
Current verified release: `v1.0.5` with Zenodo version DOI `10.5281/zenodo.22090891`.
Earlier verified version-specific DOI notes are maintained in `docs/releases/VERIFIED_RELEASES.md`; historical release records remain in this section and the verified release archive.

Archived GUI/cockpit release notes: v0.3.22 verified DOI `10.5281/zenodo.20256637`; v0.3.19 verified DOI `10.5281/zenodo.20246121`.

Archived release v0.3.10 covers workflow shortcut commands, bounded workflow-output upload, aligned shortcut guidance, and the contract-only Pattern Advisor MVP report with DOI `10.5281/zenodo.20214382`. Compatibility coverage anchor: Version `0.3.10`.

Archived release v0.3.9 remains the previous post-release verified archived release before v0.3.10. Compatibility coverage anchor: Version `0.3.9`.

Verified version-specific DOI history is maintained in `docs/releases/VERIFIED_RELEASES.md`.

### Workflow CLI coverage

- `agentic-kit workflow go`
- `agentic-kit workflow upload-output`
- `agentic-kit workflow state`
- `agentic-kit workflow list`
- `agentic-kit workflow show`
- `agentic-kit workflow upload`
- `.agentic/workflow_state`
Supported cockpit status check: `agentic-kit cockpit status`.
