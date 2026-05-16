Current version: 0.3.13

# Current Handoff

Status-date: 2026-05-15
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

Current version: 0.3.13

v0.3.13 is released and post-release verified with version DOI `10.5281/zenodo.20241908`. It integrates document lifecycle auditing into `agentic-kit doctor`. PR #221 defined a documentation information architecture contract before UI and CLI polish. PR #224 added read-only lifecycle metadata checks. PR #228 integrated the document lifecycle audit into `agentic-kit doctor`.

Previous verified release DOI: `10.5281/zenodo.20218213`.

## Current Repository State

Current main head after PR #228:

```text
ab9a46d Include document lifecycle audit in doctor (#228)
efd0863 Refresh handoff after PR 226 (#227)
7bcbc80 Refresh handoff after document lifecycle state merge (#226)
24c7e32 Refresh state after document lifecycle audit merge (#225)
a4c88fb Add read-only document lifecycle audit (#224)
a9f9091 Classify planning roadmap strategy and idea documents (#223)
cc48093 Refresh state after documentation information architecture merge (#222)
74e0c21 Define documentation information architecture (#221)
1dea652 Add strategy roadmap alignment plan (#218)
cb36773 Record v0.3.12 DOI metadata (#217)
a760dda tag: v0.3.12, Prepare v0.3.12 release metadata (#216)
e1ea3c5 Add read-only pattern advisor catalog (#215)
```

Verified release and post-merge evidence:

- GitHub Release v0.3.9 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.9 version DOI: `10.5281/zenodo.20210345`.
- Verified v0.3.10 version DOI: `10.5281/zenodo.20214382`.
- Previous verified version DOI: `10.5281/zenodo.20215460`.
- Verified v0.3.12 version DOI: `10.5281/zenodo.20218213`.
- `agentic-kit post-release-check --version 0.3.9` passed before PR #195.
- PR #195 added `docs/ideas/DIDACTIC_GUIDANCE.md` as a documentation-only, non-binding didactic orientation note.
- PR #195 did not add runtime code, public CLI commands, deterministic gates, workflow states, Pattern Advisor implementation, or pattern catalog behavior.
- PR #197 added workflow shortcut commands for request-and-run and bounded output upload.
- PR #198 aligned status guidance with the shortcut path and clarified that `current_report` is not proof of uploadable local evidence.
- PR #200 added `docs/reports/pattern_advisor_mvp_contract.md` as a contract-only Pattern Advisor MVP planning report. It did not add runtime code, public Pattern Advisor CLI commands, pattern catalog files, deterministic gates, workflow state changes, or advisory automation.
- PR #204 added repo-local `./ns state`, `./ns list`, `./ns show`, `./ns run`, and `./ns upload` shortcuts, with one-word aliases `state`, `list`, `show`, `run`, and `up`.
- PR #206 added `./ns-menu` as an optional numbered terminal menu for the existing repo-local shortcuts.
- PR #207 fixed named workflow-item runs so `./ns run <work-item-id>` restores the original `.agentic/current_work.yaml` after the bounded workflow step.
- PR #209 refreshed state and handoff documentation after the current_work isolation fix.
- PR #221 defined `docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md` and registered it in documentation coverage and the documentation mesh.
- PR #222 refreshed current-state and handoff documentation after PR #221.
- PR #223 classified idea, planning, roadmap, and strategy documents with bounded lifecycle status headers.
- PR #224 added read-only `agentic-kit doc-lifecycle-audit` lifecycle metadata checks and raised the suite to 194 tests.
- PR #228 integrated the document lifecycle audit into `agentic-kit doctor` and raised the suite to 195 tests.

Latest verified local gates after PR #228:

- `195 passed`
- `ruff check .` passed
- `agentic-kit check-docs` passed
- `agentic-kit doctor` passed
- `agentic-kit doc-mesh-audit` passed
- `agentic-kit doc-lifecycle-audit` passed

## Workflow State

Expected state after the #228 merge:

- `.agentic/workflow_state` = `IDLE`
- `.agentic/current_work.yaml` = `state: READY`
- no active workflow request
- no remaining `temp/workflow-evidence-*` branches from recent slices

Normal `ns` behavior in `IDLE` plus `READY` is a no-op. A workflow starts only by explicit request.

Preferred public workflow commands:

```text
agentic-kit workflow go
agentic-kit workflow upload-output
agentic-kit workflow status
agentic-kit workflow status --explain
agentic-kit workflow cleanup
```

Explicit two-step control remains available through `agentic-kit workflow request` followed by `agentic-kit workflow run`.

`agentic-kit workflow cleanup` now also removes stale `temp/workflow-evidence-*` branches from `IDLE` when run inside a Git repository. It keeps the existing no-op behavior for non-Git roots.

Compatibility bridge:

```text
tools/next-step.py
```

The compatibility bridge should remain bounded and should not grow into the long-term public API surface.

## Idea Notes and Architecture Options

The current idea-note set is:

- `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
- `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
- `docs/ideas/LAYERED_CLI_USABILITY.md`
- `docs/ideas/PATTERN_ADVISOR.md`

These are non-binding idea notes. They preserve useful architecture options without making them automatic implementation requirements.

DCO guidance:

- consider DCO for complex, rule-bound generated outputs when typed cells, validation, selective repair, deterministic rendering, or auditability reduce drift;
- do not use DCO for simple Markdown, small CLI changes, or documents where direct implementation is clearer;
- no ADR is required while DCO remains an idea note.

Layered CLI usability guidance:

- keep the Golden Path small;
- keep daily usage close to `ns`, `doctor`, `check-docs`, `workflow status`, and read-only `workflow status --explain`;
- classify future public commands or options as Daily, Guided, Maintainer, or Debug before making them prominent;
- consider an ADR only if these layers become binding command policy or capability boundaries.

Pattern Advisor guidance:

- treat `docs/ideas/PATTERN_ADVISOR.md` as advisory-only and non-binding;
- use it as a reference when recurring problem classes suggest reusable patterns, anti-patterns, or candidate patterns;
- the current Pattern Advisor MVP slice adds a small read-only catalog with `patterns list` and `patterns show`; do not implement `patterns suggest`, `advise`, candidate capture, promotion/deprecation, or a broad catalog before this MVP has proven useful;
- use `docs/reports/pattern_advisor_mvp_contract.md` as the scope boundary for any later read-only Pattern Advisor catalog slice;
- keep wrapper-project lessons as evidence sources, not wrapper-specific behavior in the kit;
- consider an ADR only if public Pattern Advisor CLI, binding lifecycle, or advisory behavior becomes maintained architecture.

## AI-assisted development positioning

agentic-project-kit is best understood as a governed AI-assisted development layer, not as a promise of autonomous coding-agent correctness.

The project should continue to emphasize:

- repository state as the durable source of truth instead of chat memory;
- deterministic gates rather than model trust;
- explicit workflow states instead of blind execution;
- auditable evidence transfer for local outputs;
- release and DOI metadata that can be checked after publication;
- a clear semantic quality boundary: deterministic gates can check structure and drift, but human review owns semantic correctness unless a property is converted into a deterministic rule;
- CLI usability discipline so growing automation does not make daily use harder;
- advisory pattern work as optional support, not as a replacement for maintainer judgment.
- didactic guidance as a non-binding orientation layer documented in `docs/ideas/DIDACTIC_GUIDANCE.md`, separate from runtime behavior, deterministic gates, and Pattern Advisor implementation.

## Source of Truth

Read in this order:

1. `.agentic/project.yaml`
2. `sentinel.yaml`
3. `docs/architecture/ARCHITECTURE_CONTRACT.md`
4. `docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md`
5. `docs/DOCUMENTATION_COVERAGE.yaml`
6. `AGENTS.md`
7. `README.md`
8. `docs/STATUS.md`
9. `docs/TEST_GATES.md`
10. `docs/WORKFLOW_OUTPUT_CYCLE.md`
11. `docs/handoff/CURRENT_HANDOFF.md`
12. `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
13. `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
14. `docs/ideas/LAYERED_CLI_USABILITY.md`
15. `docs/ideas/PATTERN_ADVISOR.md`
16. `docs/reports/pattern_advisor_mvp_contract.md`
17. `src/agentic_project_kit/`
18. `src/agentic_project_kit/doc_lifecycle.py`
19. `tests/test_doc_lifecycle.py`
20. `tests/`

## Required Local Gate

For this branch, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
.venv/bin/agentic-kit doc-lifecycle-audit
```

Because state and handoff refreshes can affect repository source-of-truth wording, `agentic-kit doc-mesh-audit` should be run for post-merge state-refresh branches even though it is not yet part of the standard `doctor` gate. `agentic-kit doc-lifecycle-audit` remains useful as a direct smoke check, but it is now also covered by `agentic-kit doctor`.

The normal local workflow shortcuts are:

```bash
./ns state
./ns list
./ns show
./ns run
./ns run <work-item-id>
./ns upload
```

One-word aliases are available when installed locally: `state`, `list`, `show`, `run`, and `up`.

`ns` should be a no-op in `IDLE` plus `READY` until a workflow is explicitly requested.

## Coverage-sensitive wording

This handoff intentionally keeps coverage terms visible for deterministic gates: documentation coverage, policy packs, policy-pack checks, post-release Zenodo verification, workflow evidence, and semantic quality boundary.

## Current Branch Work

Completed post-v0.3.9 work now includes PR #195, PR #197, PR #198, PR #200, PR #204, PR #207, and PR #209: didactic guidance was added as a non-binding idea note, workflow evidence shortcuts were implemented, status guidance was aligned with the shortcut path, a contract-only Pattern Advisor MVP report was added, repo-local ns shortcuts reduce Copy-and-Paste for local workflow item selection and execution, named workflow-item runs now restore current_work after bounded execution, and state documentation was refreshed after that fix.

The current Pattern Advisor MVP slice adds public read-only `patterns list` and `patterns show` commands backed by a local catalog. No DCO implementation, deterministic gate, workflow state, automatic advice, candidate capture, or promotion behavior has been added.

## Next Safe Step

Start the next work only from a concrete slice with a one-paragraph user-facing goal, explicit command-level contract, deterministic tests, and no hidden state mutation in read-only guidance paths. Keep `docs/ideas/PATTERN_ADVISOR.md` non-binding unless the maintainer explicitly approves a separate Pattern Advisor MVP.
