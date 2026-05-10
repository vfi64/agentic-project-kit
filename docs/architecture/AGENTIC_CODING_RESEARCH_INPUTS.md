# Agentic Coding Research Inputs

Status: planning input  
Date: 2026-05-10  
Related document: `docs/architecture/ARCHITECTURE_CONTRACT.md`  
Bibliography: `docs/architecture/references.bib`

## 1. Purpose

This document records external research and practitioner signals used to refine the `agentic-project-kit` architecture plan.

The goal is not to chase hype around agentic coding or vibe coding. The goal is to extract usable design constraints for a repository governance tool that supports human-AI software development without weakening engineering discipline.

## 2. Source Themes

### 2.1 Repository-level software engineering is harder than code completion

SWE-bench frames real-world issue resolution as a repository-level task: agents must understand issue descriptions, edit code across files, and validate patches against execution-based tests. This supports the `agentic-project-kit` decision to treat repository context, project state, and test gates as first-class concepts rather than optional documentation.

Planning implication:

- keep generated `STATUS`, `TEST_GATES`, handoff, TODO, and release-state documents machine-checkable;
- make repository health a `doctor` concern, not merely a README convention;
- prefer execution-backed diagnostics over prose-only agent instructions.

### 2.2 Agent-computer interfaces matter

SWE-agent argues that agents need purpose-built interfaces for repository navigation, file editing, and running tests. The important lesson for `agentic-project-kit` is that agent productivity depends on the surrounding interface and command contract, not only on the model.

Planning implication:

- generated repositories should expose stable commands for checks and evidence collection;
- `agentic-kit` should document canonical commands in project state files;
- agent instructions should point to exact commands and expected evidence;
- future tool integrations should treat agents as users with constrained capabilities.

### 2.3 Repository maps and code graphs are useful context infrastructure

RepoGraph shows that repository-level structural guidance can improve AI software engineering systems. `agentic-project-kit` should not implement a full code graph prematurely, but the architecture should leave room for repository maps, dependency graphs, and architecture boundary checks.

Planning implication:

- introduce a future `repo-map` or `architecture-map` concept;
- preserve a profile-independent diagnostic model that can later consume dependency graphs;
- add architecture fitness functions before attempting autonomous structural refactoring;
- separate navigation/context generation from patch generation.

### 2.4 Multi-language evaluation argues against Python-only identity

SWE-PolyBench evaluates repository-level coding agents across Java, JavaScript, TypeScript, and Python. This reinforces the architecture decision that Python should be the first reference profile, not the product boundary.

Planning implication:

- keep `python-library` and `python-cli` as profiles;
- keep the core language-neutral;
- add `markdown-docs` and `generic-git-repo` before adding more programming languages;
- design profile packs so TypeScript, Rust, LaTeX, and mixed repositories can be added later.

### 2.5 Vibe coding highlights flow, but also exposes governance gaps

Qualitative work on vibe coding identifies co-creation, flow, trust, specification, reliability, debugging, code review burden, and collaboration as central themes. Practitioner discussions on Reddit show similar concerns: review burden increases when code is cheap to generate, and maintainability/convention violations can be harder to detect than syntax errors.

Planning implication:

- support fast experimentation, but require explicit policy selection;
- add a lightweight `prototype` or `starter` policy pack that can later be tightened;
- add stronger `agentic-development` and `release-managed` packs for durable projects;
- make review burden visible through diagnostics and evidence expectations;
- require specs or architecture notes for structural changes.

### 2.6 Agentic pull requests need review infrastructure

GitHub Copilot coding agent now works by creating or updating pull requests and requesting review. This validates the project direction toward PR templates, evidence gates, and reviewer-facing state. It also means `agentic-project-kit` should optimize not just for generation, but for reviewability.

Planning implication:

- generated PR templates should ask for intent, affected areas, tests, risks, and remaining uncertainty;
- `doctor` should detect missing or stale review infrastructure;
- future policy packs should distinguish prototype changes from production/release changes;
- agent-created changes should be auditable by default.

### 2.7 Benchmarks can overestimate real interactive capability

Recent benchmark-mutation work argues that formal GitHub issue benchmarks can overestimate how well agents handle realistic user-style requests. This supports a conservative design: `agentic-project-kit` should not rely on benchmark claims alone when deciding how much autonomy to allow.

Planning implication:

- keep high-risk changes behind explicit approval;
- prefer deterministic checks over model self-assessment;
- treat LLM recommendations as advisory unless backed by tests, static checks, or explicit human review;
- record assumptions and uncertainty in generated plans.

### 2.8 Skills and prompts are not enough without deterministic constraints

Emerging SWE-skills evaluation suggests that procedural agent skills may have limited marginal benefit in real tasks. Practitioner reports also suggest that instructions and subagents can be ignored or misapplied. The architectural conclusion is that durable quality must be encoded in deterministic checks, contracts, and gates.

Planning implication:

- every repeated agent failure should become a check, template, or policy rule where feasible;
- `AGENTS.md` is necessary but not sufficient;
- `agentic-kit doctor` should grow into the authoritative health check;
- policy packs should prefer executable checks over long instruction prose.

### 2.9 Secret leakage and local authority are major risks

Reports on AI-assisted development and secret sprawl indicate that agents and generated code can increase accidental exposure of credentials or overprivileged configuration. `agentic-project-kit` should keep secrets and broad logs out of generated/staged artifacts by design.

Planning implication:

- generated projects should include secret-safety guidance;
- bounded evidence staging must remain strict;
- future `doctor` checks should detect risky committed evidence folders, `.env` files, tokens, and unbounded logs;
- automation agents should operate with least practical privilege.

## 3. Planning Additions to Adopt

The following ideas should be folded into the architecture roadmap.

### 3.1 Add an `agentic-development` policy pack

Purpose: durable human-AI development workflows.

Required checks and conventions:

- stable `AGENTS.md`;
- current state file;
- handoff file;
- test gate matrix;
- PR template with intent/tests/risks;
- bounded evidence staging;
- `doctor` check before merge;
- warnings for structural changes without architecture note.

### 3.2 Add a `prototype` or `starter` policy pack

Purpose: fast experimentation without pretending to be production-ready.

Required behavior:

- lower strictness;
- visible warnings that governance is intentionally light;
- easy migration path to `solo-maintainer` or `agentic-development`;
- no release/citation claims unless release-managed policy is enabled.

### 3.3 Add reviewability as a first-class quality dimension

Diagnostics should not only ask whether code builds. They should ask whether a human can review the change efficiently.

Potential checks:

- PR template exists;
- changed files are summarized;
- test evidence is present;
- architecture impact is stated;
- generated evidence is bounded;
- no broad log dumps are staged.

### 3.4 Add future repository map support

Do not build a full graph engine now. Instead define a future extension point:

```text
repo-map provider -> architecture diagnostics -> policy engine -> doctor report
```

Early implementation can start with simple import/dependency checks where feasible.

### 3.5 Make specification-before-code selectable

For strict policy packs, structural or feature changes should require a brief spec before implementation.

Example requirement:

```text
For policy packs `agentic-development`, `release-managed`, and `research-reproducible`, a non-trivial feature change should record:
- intended outcome;
- affected areas;
- acceptance checks;
- rollback/risk note.
```

### 3.6 Separate tests from implementation authorship

When an agent writes both implementation and tests, tests can mirror the implementation instead of validating the intent. The kit cannot fully solve this, but it can improve the workflow.

Recommended rule:

- tests should be derived from the stated spec or acceptance criteria;
- for important changes, PR evidence should say whether tests were written before, during, or after implementation;
- strict policy packs may warn when tests are added without corresponding acceptance criteria.

### 3.7 Add security and secret hygiene checks to the roadmap

Future `doctor` expansions should include:

- known secret file names;
- accidental `.env` staging;
- broad diagnostic log staging;
- token-like strings in staged evidence;
- risky MCP or agent configuration files when detectable.

## 4. Non-Adopted Ideas

The following ideas are intentionally not adopted:

- fully autonomous architecture rewrites;
- accepting benchmark leaderboard performance as proof of production reliability;
- treating vibe coding as a replacement for software engineering process;
- letting an LLM decide merge readiness without deterministic checks;
- adding multiuser server architecture before local contracts and profiles are stable;
- adding every language profile before the profile interface is proven.

## 5. Immediate Repository Actions

Recommended next implementation steps:

1. Keep `ARCHITECTURE_CONTRACT.md` as the governing architecture plan.
2. Add `references.bib` with research and practitioner sources.
3. Update the contract roadmap with research-derived additions.
4. Implement a first draft of a project contract format.
5. Implement policy-pack selection in `agentic-kit init`.
6. Make `doctor` report active profiles and policy packs.
7. Add `agentic-development` and `starter` policy packs before adding new programming-language profiles.

## 6. Summary

The strongest external signal is consistent:

```text
Agentic coding needs less unconstrained autonomy and more explicit context, deterministic checks, review infrastructure, and auditability.
```

That matches the planned direction of `agentic-project-kit`. The project should therefore become a governance layer for human-AI development, not merely a scaffold generator and not a vibe-coding accelerator.
