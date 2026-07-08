# Kit as Operating Layer Master Plan

Document class: archive/historical
Status-date: 2026-07-08
Moved-from: docs/archive/KIT_AS_OS_MASTERPLAN.md
Superseded-by: docs/architecture/KIT_AS_OS_ARCHITECTURE.md
Archive note: This plan is not discarded. Its normative architecture content has been centralized in docs/architecture/KIT_AS_OS_ARCHITECTURE.md, and residual follow-up work is tracked in docs/planning/PROJECT_DIRECTION.yaml. This file is retained as historical source and planning evidence.

Status: active
Decision status: accepted
Review policy: required
Scope: planning authority for turning `agentic-project-kit` into an operating layer for arbitrary GitHub repositories.  
Implementation status: no code is authorized by this document itself. Implementation starts only through later separately reviewed slices.  
Language: English, following the active planning-document policy.

## 1. Purpose

This master plan defines the controlled path from the current dogfooded `agentic-project-kit` repository toward a reusable local operating layer for arbitrary GitHub repositories.

The goal is not to create an autonomous coding agent. The goal is to create a local, deterministic, repository-backed governance layer that keeps human control over AI-assisted work.

The kit should let a maintainer install the kit once, point it at a target repository, and obtain a governed work surface there:

- project manifest;
- rules;
- registries;
- transfer protocol;
- work-cycle state;
- handoff packages;
- gates;
- audits;
- evidence reports;
- optional GUI cockpit;
- optional CI recipe.

The kit must not be copied into every target repository. The kernel stays outside the target repository as an installed tool. The target repository gets a reserved `.agentic/` workspace.

## 2. Non-goals

This plan does not authorize immediate implementation.

The planning slice that adopts this document must not include:

- resolver implementation;
- manifest parser implementation;
- workspace commands;
- GUI changes;
- package installer changes;
- migration of existing governance files;
- physical movement of `docs/STATUS.md`;
- physical movement of handoff package trees;
- release work;
- broad documentation rewrites;
- automatic migration of historical documents.

The adopting PR is documentation and registry work only.

## 3. Current ordering constraint

Before implementation work starts from this plan, the administrative handoff refresh after PR #1681 must be resolved.

At the time this plan was prepared, that refresh was tracked as PR #1682.

This constraint protects the project from starting a new architecture line from a stale post-release handoff state.

Allowed before that refresh is resolved:

- review of this plan;
- wording edits to this plan;
- local draft preparation.

Not allowed before that refresh is resolved:

- resolver implementation;
- workspace command implementation;
- self-hosting attempt;
- migration of governance files;
- new operating-layer implementation branch.

## 4. Core architecture decision

The kit will have two operating modes.

### 4.1 Generator mode

Generator mode exists today.

It creates a new project skeleton. By design, it may write outside `.agentic/` because creating the project structure is its purpose.

This mode includes the existing `agentic-kit init` meaning space and related scaffold behavior.

Generator mode may create files such as:

- `AGENTS.md`;
- `docs/PROJECT_START.md`;
- `docs/STATUS.md`;
- `docs/TEST_GATES.md`;
- CI workflows;
- PR templates;
- pre-commit configuration;
- package/test skeleton;
- initial project contract;
- initial handoff documentation.

This meaning space must be protected. `agentic-kit init` must not be silently redefined as operating-layer onboarding.

### 4.2 Operating-layer mode

Operating-layer mode is new.

It governs an existing repository through a reserved `.agentic/` workspace without rewriting the target repository's code or documents.

By default, this mode writes only inside:

- `.agentic/`;
- narrowly documented setup files such as `.gitignore`.

Optional explicit exceptions may write outside `.agentic/`, for example CI or pre-commit injection, but only through dry-run-first bounded commands.

The intended command namespace is:

- `agentic-kit workspace adopt`;
- `agentic-kit workspace init`;
- `agentic-kit workspace upgrade`;
- later optionally `agentic-kit workspace evidence`.

## 5. Kernel model

The kit kernel is the installed project-agnostic engine.

The right mental model is not a literal operating system that owns the machine. The kit is a guest inside a repository it does not own.

The more accurate class of tool is:

- `git`;
- `pre-commit`;
- `tox`;
- similar installed toolchains.

The tool lives outside the repository and leaves inside the repository only a reserved namespace and a declarative manifest.

## 6. Layer model

```text
L3  Interfaces
    CLI · GUI cockpit · LLM transfer · copy/paste · optional CI

L2  Modules and profiles
    gate profiles · feature toggles · project-type adapters

L1  Workspace inside the target repository
    .agentic/config.yaml · registries · rules · state · transfer · tmp

L0  Kernel outside the target repository
    resolver · gates · audits · transfer engine · work cycle · safety model
```

Hard rules:

1. L0 contains no target-repository-specific knowledge.
2. L0 may ship generic profile defaults and an implicit legacy profile.
3. Target-specific paths and toggles resolve from the manifest.
4. L2 is configuration, not forks.
5. L3 must use the same public CLI/API surface as every other consumer.
6. The GUI must not acquire private bypasses.
7. The existing READ_ONLY / BOUNDED / DESTRUCTIVE safety model remains.
8. Access levels are visibility, not permission.
9. Dry-run-before-confirm remains mandatory for mutating flows.
10. Activity logs are UI/evidence views, not semantic project state.
11. Mutations are serialized per workspace.

## 7. Target `.agentic/` workspace

Target layout:

```text
.agentic/
├── config.yaml
├── registries/
│   ├── documentation.yaml
│   └── rules.yaml
├── rules/
├── ci/
│   ├── github-actions/
│   └── pre-commit/
├── state/
│   ├── status.md
│   └── handoff/
├── transfer/
│   ├── inbox/
│   └── outbox/
└── tmp/
    ├── workspace.lock
    ├── wrapper-status.json
    ├── gui-panel-state.json
    └── audit/
```

Versioned by default:

- `config.yaml`;
- registries;
- rules;
- CI templates;
- project-governance status;
- validated handoff packages when intentionally committed.

Always git-ignored:

- `.agentic/tmp/`;
- workspace lock;
- GUI panel state;
- wrapper live status;
- local activity logs;
- local audit exports.

Mode-dependent:

- `.agentic/transfer/inbox/`;
- `.agentic/transfer/outbox/`.

## 8. Transfer visibility

Transfer visibility is not absolute. It is mode-dependent.

Manifest field:

```yaml
transfer:
  visibility: repo
```

`repo` means that file-transfer mode uses a versioned, pushed carrier as the communication channel.

Alternative:

```yaml
transfer:
  visibility: local
```

`local` means that remote/copy-paste-only projects keep transfer files local and git-ignored.

Regardless of mode, no secrets, credentials, private chat fragments, personal logs, or broad local output belong in any versioned `.agentic/` area.

## 9. Manifest

Initial target manifest:

```yaml
kit_schema_version: 1

project:
  name: my-project
  type: python

profile: python-default

modules:
  release_governance: true
  doc_registry: true
  rule_registry: true
  transfer: true

transfer:
  visibility: repo

paths:
  docs_root: docs/

gates:
  extra: []
  skip: []
```

Rules:

- unknown schema versions fail loudly;
- failure messages name the next action;
- newer kernel against older manifest points to `workspace upgrade`;
- older kernel against newer manifest says to upgrade the kit;
- gate skips are audited;
- profile defaults are explicit;
- target-specific paths never become hardcoded kernel knowledge.

## 10. Workspace lock

Because CLI, GUI, and transfer wrappers may operate as separate processes over the same workspace, mutating operations must be serialized.

Lock path:

```text
.agentic/tmp/workspace.lock
```

Lock content:

```json
{
  "pid": 12345,
  "command": "agentic-kit ...",
  "acquired_at": "..."
}
```

Rules:

- mutating operations take the lock;
- read-only operations never take the lock;
- a live lock causes fail-fast;
- a stale lock may be taken over with a warning;
- lock creation is atomic;
- the lock is local and git-ignored;
- the lock complements but does not replace wrapper live-status.

For manifest-less legacy-profile repositories, lock creation must not create versioned workspace artifacts. The resolver must define the legacy runtime lock path explicitly.

## 11. Adoption and lifecycle commands

### 11.1 `workspace adopt`

Safety class: READ_ONLY.

Purpose: analyze an existing repository and propose how it could be placed under kit governance.

It must detect:

- project type;
- documentation tree;
- existing CI;
- existing `.agentic/`;
- possible foreign `.agentic/`;
- candidate profile;
- candidate manifest;
- candidate documentation registration;
- private/public boundary risks.

It must not write anything.

### 11.2 `workspace init`

Safety class: BOUNDED.

Default: dry-run.

With `--execute`, it may write:

- `.agentic/config.yaml`;
- `.agentic/registries/`;
- `.agentic/rules/`;
- `.agentic/state/`;
- `.agentic/ci/`;
- `.agentic/tmp/` ignore rule;
- initial repository-parameterized LLM prompt;
- minimal `.gitignore` patch for `.agentic/tmp/`.

It must not overwrite existing files silently.

It must not write into `.github/workflows/` unless explicit CI injection is requested.

### 11.3 CI and hook entry points

Default: instruct, do not inject.

`workspace init` writes CI and hook templates into `.agentic/ci/` and prints copy/paste instructions.

Optional commands:

- `workspace init --inject-ci`;
- `workspace init --inject-pre-commit`.

Rules:

- dry-run first;
- `--execute` required;
- no silent overwrite;
- injected files carry a generated-from header pointing to `.agentic/ci/`;
- a later audit should detect drift between `.agentic/ci/` templates and injected copies.

### 11.4 `workspace upgrade`

Safety class: BOUNDED.

Purpose: migrate manifest schema versions deterministically.

Rules:

- one documented transformation per schema bump;
- dry-run prints exact manifest diff;
- `--execute` writes the new manifest;
- previous manifest is kept as `.agentic/config.yaml.bak.v<N>`;
- downgrade is out of scope;
- schema-gate failure messages name the upgrade path.

## 12. Workspace resolver

The technical keystone is a central resolver.

Target API shape:

```python
class Workspace:
    root: Path
    config: KitConfig

    def status_path(self) -> Path: ...
    def doc_registry_path(self) -> Path: ...
    def rule_registry_path(self) -> Path: ...
    def transfer_inbox(self) -> Path: ...
    def transfer_outbox(self) -> Path: ...
    def tmp(self) -> Path: ...
    def lock_path(self) -> Path: ...

def load_workspace(root: Path = Path(".")) -> Workspace:
    ...
```

Behavior:

- if `.agentic/config.yaml` exists: manifest mode;
- if not: implicit legacy profile;
- invalid manifest never silently falls back;
- no target-repository-specific hardcoding;
- no versioned artifacts created in legacy mode.

## 13. Implicit legacy profile

The implicit legacy profile represents today's historical layout.

It is compatibility machinery, not target-specific knowledge.

Lifetime:

- supported through the entire 1.x line;
- removed in 2.0.0;
- from 2.0.0 onward, `.agentic/config.yaml` is required.

The removal must be documented before 2.0.0.

## 14. Version strategy

### 0.5.x

Introduces:

- workspace resolver;
- workspace lock;
- manifest;
- schema gate;
- `workspace adopt`;
- `workspace init`;
- `workspace upgrade` skeleton;
- CI templates;
- first namespace-completion work.

### 1.0.0 criteria

Required before 1.0.0:

- self-hosting litmus passed;
- `workspace adopt/init` stable on at least one real external project;
- schema upgrade path tested;
- too-old and too-new schema failures tested;
- transfer modes tested;
- private/public documentation present;
- GUI root/workspace handling at least safe and explicit;
- implicit legacy profile still works.

### 2.0.0

Changes:

- implicit legacy profile removed;
- manifest required;
- migration from 1.x documented and tested.

## 15. Migration roadmap

### P0 — Architecture and evidence preparation

Adopt this master plan as planning authority.

No code.

Tasks:

- add this planning document;
- register it in the documentation registry;
- run documentation gates;
- define evidence logs needed before P1.

Required evidence before P1:

1. command inventory dump;
2. path-literal audit;
3. test-list extract;
4. generated artifact baseline;
5. GUI/CLI process-boundary evidence;
6. transfer-carrier evidence;
7. current-state audit baseline.

### P1 — Resolver foundation and workspace lock

Implement:

- `workspace.py`;
- `KitConfig`;
- implicit legacy profile;
- resolver methods;
- workspace lock;
- migration of the first highest-literal modules.

Acceptance:

- public behavior unchanged for manifest-less repos;
- generated artifacts unchanged for manifest-less repos;
- no versioned `.agentic/` artifacts created before `workspace init`;
- lock tests cover busy and stale paths;
- read-only remains lock-free.

### P2 — Manifest and schema gate

Implement:

- manifest parser;
- schema validation;
- profiles `python-default` and `generic`;
- transfer visibility;
- module toggles;
- gate extras/skips;
- loud failures.

Acceptance:

- valid manifests pass;
- invalid manifests block;
- version mismatch text gives the next action;
- legacy fallback only applies when no manifest exists.

### P3 — Adopt, init, upgrade skeleton, CI templates

Implement:

- `workspace adopt`;
- `workspace init`;
- `workspace upgrade` skeleton;
- `.agentic/ci/` templates;
- optional CI/pre-commit injection.

Acceptance:

- adopt is read-only;
- init is bounded;
- dry-run writes nothing;
- execute writes only expected files;
- injection refuses overwrite;
- injected files carry generated-from headers.

### P4 — Namespace completion for manifest-bearing repos

Implement:

- registries resolved into `.agentic/`;
- rules resolved into `.agentic/`;
- state resolved into `.agentic/`;
- transfer resolved according to visibility;
- tmp remains git-ignored;
- legacy repos continue unchanged.

### P5 — Kit self-hosting

Split:

- P5a: manifest only, physical paths stable;
- P5b: resolver-backed aliases;
- P5c: optional physical migration only after all references are resolver-based;
- P5d: deprecation decision aligned with 2.0.0.

Public files such as `docs/STATUS.md` may remain projections instead of moving physically.

### P6 — Interface follow-ups

Implement:

- GUI project/root selection;
- visible workspace mode;
- visible lock status;
- workspace-specific prompts;
- CI recipe hardening;
- documentation and troubleshooting;
- installer/onboarding/migration assistants later.

## 16. Packaging and installation distinction

There are two separate installation problems.

### 16.1 Installing the kit

This concerns the user's machine.

Future work:

- stable `pip` packaging;
- dependency checks;
- Git/GitHub CLI checks;
- Tk/GUI notes;
- optional launcher;
- optional npm/helper packaging only if it solves a real cross-platform problem.

### 16.2 Onboarding a repository

This concerns the target repository.

Tools:

- `workspace adopt`;
- `workspace init`;
- `workspace upgrade`;
- registry commands;
- CI templates;
- handoff generation;
- audits;
- doctor checks.

Installing the kit is not the same as putting a repository under kit governance.

## 17. Documentation plan

Required documentation after implementation begins:

- workspace manifest reference;
- workspace adopt guide;
- workspace init guide;
- workspace upgrade guide;
- transfer visibility guide;
- private/public boundary;
- CI integration guide;
- GUI/cockpit workspace guide;
- migration guide;
- troubleshooting;
- glossary;
- installation guide;
- repository onboarding guide.

Active documentation should remain concise and avoid duplicating current state that belongs in generated or machine-readable sources.

## 18. Website plan

The future public website should be English.

It must not claim that operating-layer mode is complete before P3/P4 are actually stable.

The website should explain:

1. what the kit is;
2. why it exists;
3. prompt-to-contract transition;
4. human control;
5. generator mode versus operating-layer mode;
6. two installation paths;
7. `.agentic/` workspace;
8. communication modes;
9. CLI/GUI/transfer/CI;
10. maturity and roadmap;
11. limitations;
12. quickstart;
13. glossary.

## 19. Risk register

### Risk: legacy fallback becomes permanent

Mitigation: define it as implicit legacy profile and remove it in 2.0.0.

### Risk: GUI becomes a second workflow engine

Mitigation: GUI uses public CLI/API only.

### Risk: private data enters `.agentic/`

Mitigation: private/public boundary, transfer visibility, tests, warnings.

### Risk: CI copies drift from templates

Mitigation: generated-from header and later drift audit.

### Risk: physical migration breaks public docs

Mitigation: projections before moves; moves late or never.

### Risk: schema gate locks users out

Mitigation: `workspace upgrade` before schema bumps.

### Risk: P1 becomes too large

Mitigation: resolver foundation first, minimal module migration.

### Risk: current-state prose becomes fake evidence

Mitigation: current-state claims require machine-generated evidence logs.

## 20. Definition of done for the operating-layer transformation

The transformation is complete when:

1. the kit can be installed outside a target repo;
2. an existing repo can be analyzed with `workspace adopt`;
3. an existing repo can be initialized with `workspace init`;
4. `.agentic/config.yaml` governs workspace behavior;
5. profiles and modules resolve deterministically;
6. governance paths run through the resolver;
7. manifest-less repos remain supported through 1.x;
8. mutating operations are serialized per workspace;
9. GUI and CLI safely share the same workspace;
10. transfer `repo` and `local` are tested;
11. CI templates are present and optionally injectable;
12. schema upgrades are supported;
13. the kit self-hosts through `.agentic/config.yaml`;
14. at least one real external repository has been successfully adopted;
15. docs clearly distinguish kit installation from repository onboarding;
16. private data is not stored in versioned `.agentic/` areas;
17. tests, audits, and handoff gates are green.

## 21. Conflict-resolution rule

If implementation choices conflict, use this priority order:

1. do not publish private data;
2. do not surrender control to agents;
3. do not mutate silently;
4. do not rely on unsupported current-state prose;
5. do not bypass the kernel through the GUI;
6. do not perform broad rewrite PRs;
7. do not physically migrate before semantic decoupling;
8. do not implement without tests;
9. do not continue after BLOCK/FAIL without diagnosis;
10. do not work from chat memory when repo/log evidence is required.

## 22. Closing principle

The operating-layer architecture succeeds only if it makes the kit stricter, not more magical.

The target shape is:

- one installed kernel;
- one workspace per target repository;
- one manifest;
- explicit profiles;
- testable gates;
- bounded mutations;
- repo-readable evidence;
- human control.
