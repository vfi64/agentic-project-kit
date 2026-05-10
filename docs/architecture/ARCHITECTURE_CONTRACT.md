# Architecture Contract and Roadmap

Status: Draft contract  
Date: 2026-05-10  
Project: agentic-project-kit  
Audience: maintainers, human developers, AI coding agents

## 1. Purpose

`agentic-project-kit` is a language- and toolchain-open governance and development assistance system for Git-based software and documentation repositories.

The project must not be defined as a Python-only repository generator. Python remains the first reference implementation because it provides a concrete, testable toolchain for validating the core architecture.

The long-term product boundary is:

- create and maintain repository skeletons;
- encode project contracts and development rules;
- check architecture, documentation, tests, release state, and workflow health;
- detect drift between code, documentation, metadata, and project state;
- guide human and AI-assisted development iterations with explicit evidence;
- propose controlled changes instead of silently applying architectural rewrites.

## 2. Architectural Contract

### 2.1 Core Principle

The core of `agentic-project-kit` must be independent of any specific programming language, test runner, package manager, hosting provider, or user interface.

The core may know that checks exist. It must not need to know that a Python project uses `pytest`, a TypeScript project uses `tsc`, or a Rust project uses `cargo`.

### 2.2 Required Layering

The architecture shall be organized around the following conceptual layers:

```text
Interfaces
  CLI today; later optional TUI, web UI, or service API

Application Services
  init, check, doctor, release-plan, release-check, project extension flows

Core Engine
  project contract loading, policy selection, diagnostic aggregation, report model

Policy Engine
  universal rules, profile rules, severity handling, recommendation logic

Profile Packs
  Python, Markdown/docs, Git/GitHub, release/citation, later TypeScript, Rust, LaTeX, etc.

Adapters
  filesystem, Git, GitHub CLI/API, subprocess execution, package/tool runners
```

The dependency direction is inward:

```text
interfaces -> application services -> core engine -> policy model
adapters   -> application services -> core engine -> policy model
```

The core must not import concrete adapters, UI code, or language-specific tooling.

### 2.3 Forbidden Couplings

The following couplings are architectural violations:

- core modules importing concrete GitHub, CLI, filesystem, or subprocess implementations;
- generic diagnostics depending directly on `pytest`, `ruff`, `mypy`, `npm`, `cargo`, or similar tools;
- project-type decisions hard-coded across unrelated modules;
- policy behavior hidden in prose-only documentation without a machine-checkable representation;
- automatic structural rewrites without a visible plan, rationale, risk note, and explicit approval path.

## 3. Project Contract Model

Generated and maintained repositories should converge on a machine-readable project contract, for example `agentic.toml` or an equivalent future format.

The contract should describe at least:

```toml
[project]
type = "software"
primary_profile = "python-library"
secondary_profiles = ["markdown-docs", "git-github"]

[governance]
plan_before_code = true
architecture_note_for_structural_change = true
doctor_before_merge = true
record_evidence = true

[profiles.python-library]
enabled = true
test_command = "python -m pytest -q"
lint_command = "ruff check ."
typecheck_command = "mypy src"

[profiles.markdown-docs]
enabled = true
check_required_state_docs = true
check_stale_handoff_markers = true

[profiles.git-github]
enabled = true
feature_branch_required = true
pull_request_template_required = true
```

The exact format may evolve, but the separation between universal governance and profile-specific checks is mandatory.

## 4. Profile and Policy Pack Model

### 4.1 Profiles

A profile describes a repository kind, not merely a programming language.

Examples:

- `python-library`
- `python-cli`
- `typescript-webapp`
- `rust-cli`
- `markdown-docs`
- `latex-docs`
- `mixed-repo`
- `generic-git-repo`

Profiles may be combined. A Python library with Markdown documentation and GitHub release automation is a multi-profile project.

### 4.2 Policy Packs

A policy pack is a selectable group of development principles and checks. Policy packs should be recommended by the system during `agentic-kit init` and during substantial project extensions.

Policy packs should not be one-size-fits-all. They should be chosen according to application domain, risk level, team maturity, and maintenance goal.

Initial recommended policy packs:

| Policy pack | Intended use | Typical strictness |
| --- | --- | --- |
| `starter` | small local projects, early experiments | low |
| `teaching` | educational repositories and didactic material | low to medium |
| `solo-maintainer` | single-user development repositories | medium |
| `agentic-development` | human-AI assisted development workflows | medium to high |
| `research-reproducible` | research code, datasets, papers, citations | high |
| `release-managed` | projects with tags, releases, artifacts, changelogs | high |
| `safety-critical-inspired` | projects that benefit from stricter reliability constraints | high, but not a safety certification |
| `documentation-governed` | documentation-heavy repositories | medium to high |

The `safety-critical-inspired` pack may draw on ideas such as NASA/JPL Power of 10 style constraints, but it must be adapted realistically to the target language and project type. It must not claim formal safety certification.

### 4.3 Principle Categories

Policy packs may combine principles from these categories:

#### Universal governance principles

- explicit project purpose;
- explicit current status;
- current handoff or continuation state;
- test and evidence gates;
- no stale release/citation/version metadata;
- bounded diagnostic logs;
- no secrets in generated or staged artifacts.

#### Architecture principles

- small modules with clear responsibility;
- controlled dependency direction;
- no cyclic imports or equivalent dependency cycles;
- public interfaces separated from concrete adapters;
- structural changes require an architecture note or ADR;
- core logic separated from UI and provider-specific integration.

#### Reliability principles

- small functions where practical;
- explicit error handling;
- no broad silent exception swallowing;
- deterministic checks where possible;
- assertions or invariants for internal assumptions;
- reproducible local gate commands;
- failure severity must be visible.

#### Documentation principles

- generated project state must remain current;
- command examples in documentation should match implemented CLI behavior;
- handoff documents must not contain stale placeholder markers;
- TODO state must have one machine-readable source of truth;
- release/citation metadata must be consistent.

#### Agentic workflow principles

- agents start from stable rules and current state files, not memory;
- every substantial change has intended outcome, changed files, tests, and remaining risks;
- automatic fixes are proposed as reviewable patches;
- generated evidence must be bounded and inspectable;
- diagnosis, recommendation, and action are separate concepts.

## 5. Advisory Selection Dialog

`agentic-kit init` should eventually guide the user through profile and policy selection instead of asking only for a project type.

The dialog should ask for practical intent, then recommend a profile set and policy pack.

Example questions:

1. What kind of repository is this?
   - software library
   - CLI tool
   - web application
   - documentation repository
   - teaching material
   - research/reproducibility project
   - mixed repository

2. Which toolchains should be active now?
   - Python
   - Markdown/docs
   - Git/GitHub
   - release/citation metadata
   - other/later

3. How strict should the governance be?
   - lightweight starter
   - normal solo-maintainer discipline
   - agentic development with stronger evidence gates
   - release-managed
   - research-reproducible
   - safety-critical-inspired constraints

4. Will the repository be single-user or team-oriented?
   - single-user now
   - team later possible
   - team from start

5. Should architecture changes require a documented decision?
   - no, only warnings
   - yes, for structural changes
   - yes, for every public interface change

The system should then produce a recommendation:

```text
Recommended profiles:
- python-library
- markdown-docs
- git-github

Recommended policy packs:
- solo-maintainer
- agentic-development
- release-managed

Reason:
The project is a Python package with GitHub releases and AI-assisted development.
It needs test gates, documentation state checks, release-state validation, and drift checks.
```

The user may accept, modify, or reject the recommendation. The final selection must be recorded in the project contract.

## 6. Extension and Change Dialog

For significant changes after initialization, the system should re-open a focused advisory dialog.

Trigger examples:

- adding a new programming language;
- adding release automation;
- adding citation/archival metadata;
- adding a web UI or service mode;
- enabling multiuser workflows;
- changing architecture style;
- introducing LLM/agent automation that writes files.

The dialog should ask:

```text
This change expands the project boundary. Should the project contract be updated?

Detected change:
- new profile candidate: release-managed
- affected files: CHANGELOG.md, CITATION.cff, .zenodo.json, GitHub workflow

Recommended action:
- enable release-managed policy pack
- require release-check before tagging
- add version drift checks to doctor
```

A structural change without contract update should at least produce a warning. For strict policy packs it may be a failing diagnostic.

## 7. Diagnostics and Severity Model

All checks should return a structured diagnostic model:

```text
id: stable rule identifier
severity: INFO | WARN | FAIL | CRITICAL
location: file, section, command, or repository state
finding: what is wrong
rule: which rule applies
rationale: why it matters
recommendation: what to do next
automation: none | can-generate-stub | can-propose-patch | can-apply-after-approval
```

Severity expectations:

- `INFO`: useful context;
- `WARN`: should be reviewed but does not block ordinary work;
- `FAIL`: blocks the relevant gate;
- `CRITICAL`: indicates corrupted state, unsafe automation, or a violation of fundamental architecture boundaries.

## 8. Automation Boundary

The system may automatically perform low-risk mechanical actions after explicit user command, such as:

- formatting generated files;
- rendering TODO Markdown from YAML;
- creating missing documentation stubs;
- generating ADR templates;
- staging bounded diagnostic evidence;
- updating generated indices.

The system must not silently perform high-risk actions, such as:

- multi-module architecture refactoring;
- semantic code rewrites;
- changing release history;
- weakening tests or policy gates;
- committing broad logs or secrets;
- changing repository visibility or access policy.

High-risk actions require a proposed plan, reviewable diff, test evidence, and explicit approval path.

## 9. Single-User Now, Multiuser Later

The first implementation may assume a single local maintainer and no rights management.

However, the architecture must not prevent later multiuser operation. Therefore:

- project state should be represented explicitly instead of being implicit in local memory;
- roles should be modelable even if only `owner` exists initially;
- audit logs should be append-friendly;
- policy decisions should be attributable;
- adapters should be replaceable;
- GitHub-specific assumptions should remain outside the core.

Potential future roles:

- `viewer`
- `developer`
- `maintainer`
- `owner`
- `automation-agent`

## 10. Roadmap

### Phase 1: Contract and Profile Foundation

- document this architecture contract;
- introduce or draft the `agentic.toml` project contract format;
- define the diagnostic result model;
- separate universal checks from Python-specific checks;
- keep Python as the reference implementation.

### Phase 2: Policy Pack MVP

- implement selectable policy packs for `starter`, `solo-maintainer`, `agentic-development`, and `release-managed`;
- expose recommendations during `agentic-kit init`;
- record the selected profiles and policies in the generated project contract;
- make `doctor` report active profiles and policy packs.

### Phase 3: Drift and Architecture Fitness Functions

- add import/dependency boundary checks where feasible;
- add README/CLI drift checks;
- add release/citation/version drift checks to doctor;
- add architecture-note or ADR checks for structural changes;
- support baseline mode for existing repositories.

### Phase 4: Additional Profiles

- add `markdown-docs` as a first-class profile;
- add `generic-git-repo` profile;
- evaluate `latex-docs`, `typescript`, and `rust` profiles only after the profile interface is stable.

### Phase 5: Controlled Change Proposals

- generate reviewable plans for contract changes;
- generate low-risk stubs and templates;
- produce patch proposals for selected rule violations;
- require explicit approval for applying changes.

## 11. Acceptance Criteria for Future Work

Future implementation work must preserve the following invariants:

- Python support is a profile, not the core identity of the project.
- The core does not import concrete language tool runners.
- Policy packs are selectable and recorded.
- Diagnostics separate finding, rule, rationale, recommendation, and action.
- Init and major extension flows recommend policies instead of silently choosing strictness.
- Automatic changes remain bounded, reviewable, and reversible.
- Multiuser support is not implemented prematurely, but future roles and attribution are not blocked.

## 12. Open Questions

- Should the project contract be named `agentic.toml`, `.agentic/project.toml`, or another path?
- Should policy packs be built into the package, loaded from files, or both?
- How strict should `doctor` be for repositories without a project contract?
- Which checks belong to `check`, which to `doctor`, and which to release-specific commands?
- Should baseline mode be implemented before or after the first policy pack MVP?
