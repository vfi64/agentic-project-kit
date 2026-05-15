Current version: 0.3.7

# Current Handoff

Status-date: 2026-05-15
Project: agentic-project-kit
Branch: main
Base branch: main

## Current Goal

v0.3.7 is fully released and post-release verified.

No release branch is active. v0.3.7 is tagged, published, archived by Zenodo, post-release verified, and DOI metadata is recorded on main.

## Current Repository State

v0.3.7 is released and post-release verified. Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`. The post-release Zenodo verification is complete for v0.3.7.

Verified release evidence:

- GitHub Release v0.3.7 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.7 version DOI: `10.5281/zenodo.20206581`.
- `agentic-kit post-release-check --version 0.3.7` passed.
- PR #163 recorded the verified v0.3.6 DOI metadata on main.

Post-release work completed after v0.3.6:

- PR #164 preserved `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md` as a curated idea note.
- PR #164 introduced `docs/ideas/LAYERED_CLI_USABILITY.md` as a non-binding usability-layer model.
- PR #164 added small `AGENTS.md` cross-references to the DCO and layered CLI usability idea notes.
- PR #165 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after the idea-note merge.
- PR #166 hardened `agentic-kit workflow cleanup` so stale `temp/workflow-evidence-*` branches can be removed even when `.agentic/workflow_state` is already `IDLE`.
- PR #167 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after workflow cleanup hardening.
- PR #168 added `docs/ideas/PATTERN_ADVISOR.md` as a non-binding idea note / architecture research track.
- PR #170 added read-only `agentic-kit workflow status --explain` guidance for common workflow states.
- PR #171 refreshed `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after PR #170.
- PR #172 completed Guided Workflow Usability v1 with read-only safety wording, `current_report` explanation, a README quick command guide, and a guided status compass.

The v0.3.7 release-preparation PR was merged on main after:

```text
0161838 Complete guided workflow status usability (#172)
a2d5e68 Update status and handoff after workflow status explain (#171)
1d0c5f4 Explain workflow status next steps (#170)
```

Latest verified local gates after v0.3.7 release preparation:

- `162 passed`
- `ruff check .` passed
- `agentic-kit check-docs` passed
- `agentic-kit doctor` passed
- `agentic-kit doc-mesh-audit` passed

## Workflow State

Expected state after the #172 merge:

- `.agentic/workflow_state` = `IDLE`
- `.agentic/current_work.yaml` = `state: READY`
- no active workflow request
- no remaining `temp/workflow-evidence-*` branches from recent slices

Normal `ns` behavior in `IDLE` plus `READY` is a no-op. A workflow starts only by explicit request.

Preferred public workflow commands:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow status --explain
agentic-kit workflow cleanup
```

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
- do not implement `patterns suggest`, `advise`, candidate capture, promotion/deprecation, or a broad catalog before a small read-only catalog MVP has proven useful;
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

## Source of Truth

Read in this order:

1. `.agentic/project.yaml`
2. `sentinel.yaml`
3. `docs/architecture/ARCHITECTURE_CONTRACT.md`
4. `docs/DOCUMENTATION_COVERAGE.yaml`
5. `AGENTS.md`
6. `README.md`
7. `docs/STATUS.md`
8. `docs/TEST_GATES.md`
9. `docs/WORKFLOW_OUTPUT_CYCLE.md`
10. `docs/handoff/CURRENT_HANDOFF.md`
11. `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`
12. `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md`
13. `docs/ideas/LAYERED_CLI_USABILITY.md`
14. `docs/ideas/PATTERN_ADVISOR.md`
15. `src/agentic_project_kit/`
16. `tests/`

## Required Local Gate

For this branch, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/agentic-kit check-docs
.venv/bin/agentic-kit doctor
.venv/bin/agentic-kit doc-mesh-audit
```

Because this branch changes current-state and handoff wording, `agentic-kit doc-mesh-audit` is required before merge even though it is not yet part of the standard `doctor` gate.

The normal local workflow shortcut remains:

```bash
ns
```

`ns` should be a no-op in `IDLE` plus `READY` until a workflow is explicitly requested.

## Coverage-sensitive wording

This handoff intentionally keeps coverage terms visible for deterministic gates: documentation coverage, policy packs, policy-pack checks, post-release Zenodo verification, workflow evidence, and semantic quality boundary.

## Current Branch Work

Prepared files should include:

- `pyproject.toml` and `src/agentic_project_kit/__init__.py` bumped to 0.3.7.
- `CITATION.cff` updated with the verified v0.3.7 version DOI.
- `CHANGELOG.md`, `README.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md` updated for post-release v0.3.7 DOI metadata.

No Pattern Advisor MVP, DCO implementation, or additional Guided CLI runtime change is part of this branch.

## Next Safe Step

v0.3.7 is complete. Start the next work only from a concrete new slice. Use `docs/ideas/PATTERN_ADVISOR.md` only as a non-binding advisory reference unless the maintainer explicitly chooses a later Pattern Advisor MVP.
