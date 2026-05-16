# Agentic Project Kit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20101359.svg)](https://doi.org/10.5281/zenodo.20101359)

`agentic-project-kit` is a local Python package for generating GitHub-ready project skeletons for human-AI software development workflows.

It creates not only files, but a reusable development process: agent onboarding, project contract, profile and policy pack selection, status discipline, test gates, task tracking, bounded logging conventions, optional GitHub automation, workflow evidence capture, and release-state validation.

In one sentence: `agentic-project-kit` is an early, dogfooded attempt to make AI-assisted repository work more reproducible through project contracts, documentation gates, release-state checks, task gates, policy expectations, workflow evidence, and bounded auditability.

## Why this exists

AI-assisted development works best when project context is explicit, current, and machine-checkable. Without that, agents tend to rely on stale handoffs, copied project history, unclear branch rules, missing test evidence, and unstructured logs.

This kit turns those lessons into a reusable starter system for new repositories.

The goal is not to make an LLM write code better by itself. The goal is to make repository state, handoffs, documentation coverage, task state, release state, and policy expectations visible enough that humans and coding agents can work with less context drift.

## Why not just Cookiecutter?

Cookiecutter-style generators are useful for creating initial files. `agentic-project-kit` is aimed at a narrower problem: keeping AI-assisted repository work reviewable after the first commit.

A generated project therefore includes machine-readable state, current handoff files, documentation coverage expectations, task gates, local health checks, release-state validation, policy-pack fixtures, and evidence conventions. These are governance aids, not a claim that the repository is semantically complete or production-ready.

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

## Installation for local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the local gate:

```bash
pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit --help
```

## Quick start

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

Generated projects contain `.agentic/project.yaml` as a machine-readable project contract. It records the project name, description, project type, selected profiles, selected policy packs, and basic governance expectations.

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

## Policy-pack doctor checks

`agentic-kit doctor` also activates lightweight policy-pack checks from `.agentic/project.yaml`.

These checks currently verify structural prerequisites:

- `solo-maintainer` expects status, handoff, sentinel, and task gate files.
- `agentic-development` expects agent instructions, test gates, handoff, and the architecture contract.
- `release-managed` expects changelog, citation metadata, and Zenodo metadata.
- `documentation-governed` expects the documentation coverage matrix and architecture contract.
- `starter` and `prototype` expect basic README/status scaffolding.

The policy-pack checks are deliberately structural. They prove that the selected policy pack has its required repository fixtures. They do not prove that the prose is complete or that release readiness has already been achieved.

## Project health check

Use `agentic-kit doctor` as the compact repository health check:

```bash
agentic-kit doctor
```

It reports required project files, project contract status, policy-pack checks, documentation gates, task validation when configured, and version-drift checks. The command exits non-zero only when required checks fail.

Example output shape:

```text
Agentic project doctor report for /path/to/project

[PASS] pyproject.toml: present
[PASS] README.md: present
[PASS] sentinel.yaml: present
[PASS] project contract: my-project; profiles: generic-git-repo, python-cli; policy packs: starter, solo-maintainer
[PASS] policy pack checks: active: starter, solo-maintainer
[PASS] documentation gates: passed
[PASS] todo gates: passed
[PASS] version drift: project state matches version 0.3.4

Overall: PASS
```

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

This post-release command is separate from release-check: `release-check` is the pre-release gate, while `post-release-check` verifies the already-published release and its Zenodo archive state.

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

- `workflow status --explain`: inspect the current state and next safe step.
- `workflow request`: mark a concrete local workflow slice as requested.
- `workflow run`: run one bounded workflow state-machine step.
- `workflow cleanup`: clean uploaded temporary evidence after review.
- `workflow fail-report`: upload preserved FAILED-state evidence for diagnosis without cleanup or retry.

The workflow uses `.agentic/workflow_state` and `.agentic/current_work.yaml`. `IDLE` with `current_work.yaml` state `READY` is a safe no-op. A run starts only after an explicit request. The explicit two-step form is `agentic-kit workflow request`, followed by `agentic-kit workflow run`. The shortcut `agentic-kit workflow go` performs the same request-and-run handoff for one bounded workflow step. Guided inspection commands include `agentic-kit workflow state`, `agentic-kit workflow list`, and `agentic-kit workflow show`. A requested run captures bounded local evidence, resets the request to `READY`, updates `docs/reports/CURRENT_WORKFLOW_OUTPUT.md`, uploads a temporary evidence branch, and waits for explicit cleanup. When bounded local output already exists and should be uploaded without pasted terminal output, use `agentic-kit workflow upload-output`, `agentic-kit workflow upload`, or the repo-local shortcut `./ns upload` / `./ns up`. For daily local use, `./ns state`, `./ns list`, `./ns show`, `./ns run`, `./ns go`, `./ns up`, and `./ns fail` provide the short workflow surface. The optional `./ns-menu` helper wraps the same repo-local shortcuts in a simple numbered terminal menu for interactive local use.

Legacy compatibility remains available through:

```bash
./ns --request
./ns
```

Prefer the package CLI for normal use; the legacy command is kept visible for compatibility and documentation coverage.

The legacy cycle uses `IDLE`, `TEST`, `UPLOAD`, and `CLEANUP`. Details are documented in `docs/WORKFLOW_OUTPUT_CYCLE.md`.


## Pattern Advisor read-only catalog

The Pattern Advisor MVP is a local, read-only catalog for recurring project patterns and anti-patterns. It is advisory-only: no gates, no automatic architecture choice, no workflow-state mutation, and no candidate promotion.

```bash
agentic-kit patterns list
agentic-kit patterns show bounded-workflow-evidence
```


## Local Cockpit Foundation

The local cockpit foundation exposes a read-only control surface for local project operation. Use `agentic-kit cockpit status` to inspect the current project root, Git branch, dirty-tree state, workflow state, and current-work request state. Use `agentic-kit cockpit actions` to list the structured action inventory.

The cockpit action inventory classifies actions by category and safety, including `read_only`, `bounded`, and future `destructive` classes. In the v0.3.14 foundation, cockpit commands inspect status and action metadata only; they do not execute destructive Git, release, tag, merge, cleanup, or remote operations.

Repo-local shortcuts are available through `./ns cockpit` and `./ns actions`. The optional `./ns-menu` helper includes the same cockpit entries. The long-term direction is a shared action layer that can be reused by CLI, shell/menu adapters, and a later Tkinter cockpit without assembling fragile shell snippets.

Architecture details are documented in `docs/architecture/LOCAL_COCKPIT_FOUNDATION.md`.

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

The repository uses `docs/DOCUMENTATION_COVERAGE.yaml` as a machine-checkable documentation coverage matrix.

`agentic-kit check-docs` validates that important public commands, workflows, governance concepts, safety rules, release commands, and evidence expectations remain visible in the expected documents. This prevents features such as `agentic-kit doctor` from being implemented but invisible to new users.

When adding a public command, workflow, gate, profile, policy pack, generated file, architecture concept, or release-visible feature, update the coverage matrix and the affected documentation in the same change.

## Documentation mesh audit

`agentic-kit doc-mesh-audit` checks machine-readable drift across the project documentation mesh. It is stricter than plain term coverage, but it is still deliberately bounded and does not claim semantic proof.

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

## Logging and evidence

The generated `scripts/stage_recent_logs.py` script is intentionally bounded. It stages only a recent diagnostic window from known log folders into `tmp/agent-evidence`.

Logs are diagnostic evidence, not automatic source material. Do not commit secrets, local credentials, broad raw logs, or private runtime state.

## Citation and archiving

Citation metadata is provided in `CITATION.cff`.

Zenodo metadata is provided in `.zenodo.json`. The project is archived through the Zenodo GitHub integration.

For citation across versions, prefer the all-versions DOI: `10.5281/zenodo.20101359`.

The archived v0.2.5 release has the verified version-specific DOI: `10.5281/zenodo.20111119`.

The archived v0.2.6 release has the verified version-specific DOI: `10.5281/zenodo.20119102`.

The archived v0.2.7 release has the verified version-specific DOI: `10.5281/zenodo.20125518`.

The archived v0.2.8 release has the verified version-specific DOI: `10.5281/zenodo.20126270`.

The archived v0.2.9 release has the verified version-specific DOI: `10.5281/zenodo.20126490`.

The archived v0.2.10 release has the verified version-specific DOI: `10.5281/zenodo.20127028`.

The archived v0.3.0 release has the verified version-specific DOI: `10.5281/zenodo.20140467`.

The archived v0.3.1 release has the verified version-specific DOI: `10.5281/zenodo.20144969`.

The archived v0.3.2 release has the verified version-specific DOI: `10.5281/zenodo.20145114`.

The archived v0.3.3 release has the verified version-specific DOI: `10.5281/zenodo.20151924`.

The archived v0.3.4 release has the verified version-specific DOI: `10.5281/zenodo.20162214`.

The archived v0.3.5 release has the verified version-specific DOI: `10.5281/zenodo.20169965`.

The archived v0.3.6 release has the verified version-specific DOI: `10.5281/zenodo.20183888`.

The archived v0.3.7 release has the verified version-specific DOI: `10.5281/zenodo.20206581`.

The archived v0.3.8 release has the verified version-specific DOI: `10.5281/zenodo.20208638`.

The archived v0.3.9 release has the verified version-specific DOI: `10.5281/zenodo.20210345`.
The archived v0.3.10 release has the verified version-specific DOI: `10.5281/zenodo.20214382`.
The archived v0.3.11 release has the verified version-specific DOI: `10.5281/zenodo.20215460`.

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

Version `0.3.13` is the current release line covering document lifecycle auditing in `agentic-kit doctor` with verified DOI `10.5281/zenodo.20241908`. Version `0.3.11` remains the previous archived release covering repo-local workflow-item shortcuts, stored work-item execution, and current-work isolation for named workflow-item runs.

Version `0.3.10` remains the previous archived release covering workflow shortcut commands, bounded workflow-output upload, aligned shortcut guidance, and the contract-only Pattern Advisor MVP report with DOI `10.5281/zenodo.20214382`.

Version `0.3.9` remains the previous post-release verified archived release before v0.3.10.

This repository has maintainer-owned GitHub releases and verified Zenodo archive records. Verified version-specific DOIs:

- v0.2.5: `10.5281/zenodo.20111119`
- v0.2.6: `10.5281/zenodo.20119102`
- v0.2.7: `10.5281/zenodo.20125518`
- v0.2.8: `10.5281/zenodo.20126270`
- v0.2.9: `10.5281/zenodo.20126490`
- v0.2.10: `10.5281/zenodo.20127028`
- v0.3.0: `10.5281/zenodo.20140467`
- v0.3.1: `10.5281/zenodo.20144969`
- v0.3.2: `10.5281/zenodo.20145114`
- v0.3.3: `10.5281/zenodo.20151924`
- v0.3.4: `10.5281/zenodo.20162214`
- v0.3.5: `10.5281/zenodo.20169965`
- v0.3.6: `10.5281/zenodo.20183888`
- v0.3.7: `10.5281/zenodo.20206581`
- v0.3.8: `10.5281/zenodo.20208638`
- v0.3.9: `10.5281/zenodo.20210345`
- v0.3.10: `10.5281/zenodo.20214382`
- v0.3.11: `10.5281/zenodo.20215460`
- Verified v0.3.12 version DOI: `10.5281/zenodo.20218213`

Near-term documentation-governance work: stabilize `agentic-kit doc-mesh-audit` as a targeted special gate, collect false positives, then decide whether to promote it into `agentic-kit doctor` before any unconditional default `ns` integration.
