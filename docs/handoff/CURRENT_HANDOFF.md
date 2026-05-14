Current version: 0.3.6

# Current Handoff

Status-date: 2026-05-14
Project: agentic-project-kit
Branch: docs/status-handoff-after-164
Base branch: main

## Current Goal

Update `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` after PR #164 so the repository state no longer points future agents to stale pre-v0.3.6 or pre-#164 branch goals.

This branch is documentation-only. It records the post-#164 state and does not change CLI behavior, workflow behavior, release metadata, package version, or implementation code.

## Current Repository State

v0.3.6 is released and post-release verified.

Verified v0.3.6 release evidence:

- GitHub Release v0.3.6 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.6 version DOI: `10.5281/zenodo.20183888`.
- `agentic-kit post-release-check --version 0.3.6` passed.
- PR #163 recorded the verified v0.3.6 DOI metadata on main.

Post-release documentation work completed after v0.3.6:

- PR #164 preserved `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md` as a curated idea note.
- PR #164 introduced `docs/ideas/LAYERED_CLI_USABILITY.md` as a non-binding usability-layer model.
- PR #164 added small `AGENTS.md` cross-references to the DCO and layered CLI usability idea notes.

Current main head before this branch:

```text
ff28c43 Preserve DCO and layered CLI usability ideas (#164)
```

Latest verified local gates after PR #164:

- `155 passed`
- `ruff check .` passed
- `agentic-kit check-docs` passed
- `agentic-kit doctor` passed

## Workflow State

Expected state after the #164 cleanup:

- `.agentic/workflow_state` = `IDLE`
- `.agentic/current_work.yaml` = `state: READY`
- no active workflow request
- no remaining `temp/workflow-evidence-*` branches from the #164 slice

Normal `ns` behavior in `IDLE` plus `READY` is a no-op. A workflow starts only by explicit request.

Preferred public workflow commands:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

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

These are non-binding idea notes. They preserve useful architecture options without making them automatic implementation requirements.

DCO guidance:

- consider DCO for complex, rule-bound generated outputs when typed cells, validation, selective repair, deterministic rendering, or auditability reduce drift;
- do not use DCO for simple Markdown, small CLI changes, or documents where direct implementation is clearer;
- no ADR is required while DCO remains an idea note.

Layered CLI usability guidance:

- keep the Golden Path small;
- keep daily usage close to `ns`, `doctor`, `check-docs`, and workflow status;
- classify future public commands or options as Daily, Guided, Maintainer, or Debug before making them prominent;
- consider an ADR only if these layers become binding command policy or capability boundaries.

## AI-assisted development positioning

agentic-project-kit is best understood as a governed AI-assisted development layer, not as a promise of autonomous coding-agent correctness.

The project should continue to emphasize:

- repository state as the durable source of truth instead of chat memory;
- deterministic gates rather than model trust;
- explicit workflow states instead of blind execution;
- auditable evidence transfer for local outputs;
- release and DOI metadata that can be checked after publication;
- a clear semantic quality boundary: deterministic gates can check structure and drift, but human review owns semantic correctness unless a property is converted into a deterministic rule;
- CLI usability discipline so growing automation does not make daily use harder.

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
14. `src/agentic_project_kit/`
15. `tests/`

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

- `docs/STATUS.md` updated with the post-#164 state, idea-note set, workflow request state, and next possible slices.
- `docs/handoff/CURRENT_HANDOFF.md` updated with the post-#164 handoff and source-of-truth reading order.

No package version bump, release metadata change, CLI behavior change, or implementation change is part of this branch.

## Next Safe Step

Run local gates on `docs/status-handoff-after-164`, including `agentic-kit doc-mesh-audit`. If green, open and merge a focused documentation PR.

After merge, reassess the next slice. Plausible options are:

1. harden `workflow cleanup` behavior for stale temporary evidence branches when local state is already `IDLE`;
2. keep `doc-mesh-audit` as a special manual gate for more PRs before considering any promotion toward `doctor`;
3. design a small guided-usability CLI slice, such as a status or explanation command, only if it keeps the Golden Path simple.
