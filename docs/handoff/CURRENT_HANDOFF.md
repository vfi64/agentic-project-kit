Current version: 0.3.6

# Current Handoff

Status-date: 2026-05-13
Project: agentic-project-kit
Branch: docs/ai-development-roadmap
Base branch: main

## Current Goal

Prepare v0.3.6 release metadata after PR #158, PR #159, PR #160, and PR #161.

Update project roadmap and handoff after v0.3.5 so the next development slice is explicit: move the explicit workflow request mechanism from the internal `tools/next-step.py --request` path to the public `agentic-kit workflow request` CLI path.

This branch is documentation-only. It records the post-v0.3.5 direction and does not implement the public command yet.

## Current Repository State

v0.3.5 is released and post-release verified.

v0.3.5 release evidence is verified:

- GitHub Release v0.3.5 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.5 version DOI: `10.5281/zenodo.20169965`.
- `agentic-kit post-release-check --version 0.3.5` passed.
- Post-release Zenodo verification is complete for v0.3.5.
- PR #157 recorded the verified v0.3.5 DOI metadata on main.

Recent completed workflow hardening:

- PR #153 made the `ns` idle state require an explicit workflow request.
- PR #154 added explicit `ns` workflow request mode.
- PR #155 documented explicit `ns` workflow request mode.

Current workflow behavior:

- `.agentic/workflow_state` should be `IDLE` after the v0.3.5 release and DOI metadata cycle.
- `.agentic/current_work.yaml` may exist with `state: READY`.
- A normal `ns` run in `IDLE` plus `READY` is intentionally a no-op.
- A workflow run now requires an explicit request.
- The current compatibility path is `tools/next-step.py --request` followed by `ns`.
- The next product step is to expose equivalent behavior through `agentic-kit workflow request`.

## AI-assisted development positioning

agentic-project-kit is best understood as a governed AI-assisted development layer, not as a promise of autonomous coding-agent correctness.

The project should continue to emphasize:

- repository state as the durable source of truth instead of chat memory;
- deterministic gates rather than model trust;
- explicit workflow states instead of blind execution;
- auditable evidence transfer for local outputs;
- release and DOI metadata that can be checked after publication;
- a clear semantic quality boundary: deterministic gates can check structure and drift, but human review owns semantic correctness unless a property is converted into a deterministic rule.

## Roadmap now recorded in docs/STATUS.md

The updated roadmap is split into three near-term tracks:

1. Public workflow CLI:
   - add `agentic-kit workflow request` as the public equivalent of `tools/next-step.py --request`;
   - keep `tools/next-step.py` as a compatibility bridge;
   - test READY/IDLE no-op and explicit request activation;
   - document the public `agentic-kit workflow request/run/status/cleanup` path;
   - add `workflow status` and `workflow cleanup` in later slices.

2. Documentation governance:
   - keep `doc-mesh-audit` as a targeted special gate for current-state, handoff, roadmap, release, governance, and documentation-mesh changes;
   - keep documentation coverage visible in handoff and status documents;
   - keep policy packs and policy-pack checks visible as part of the public doctor contract;
   - collect failure classes and false positives before promoting it to `doctor` or default `ns`.

3. Product positioning:
   - explain the problem solved by the project: chat-context drift, branch drift, unclear handoff state, local-output transfer, and release-state drift;
   - keep onboarding simple despite the governance vocabulary;
   - provide a compact example flow: request workflow, run gate, upload evidence, inspect status, cleanup evidence.

## Source of Truth

Read in this order:

1. .agentic/project.yaml
2. sentinel.yaml
3. docs/architecture/ARCHITECTURE_CONTRACT.md
4. docs/DOCUMENTATION_COVERAGE.yaml
5. AGENTS.md
6. README.md
7. docs/STATUS.md
8. docs/TEST_GATES.md
9. docs/WORKFLOW_OUTPUT_CYCLE.md
10. docs/handoff/CURRENT_HANDOFF.md
11. src/agentic_project_kit/
12. tests/

## Required Local Gate

For this branch, run:

```bash
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
agentic-kit doc-mesh-audit
```

The normal local workflow shortcut remains:

```bash
ns
```

`ns` should be a no-op in `IDLE` plus READY until a workflow is explicitly requested.

## Coverage-sensitive wording

This handoff intentionally keeps coverage terms visible for deterministic gates: documentation coverage, policy packs, policy-pack checks, and post-release Zenodo verification.

## Current Branch Work

Prepared files should include:

- `docs/STATUS.md` updated with the AI-assisted development assessment and near-term roadmap.
- `docs/handoff/CURRENT_HANDOFF.md` updated with the post-v0.3.5 next slice.

No package version bump, release metadata change, or implementation change is part of this branch.

## Next Safe Step

Run local gates on `docs/ai-development-roadmap`. Because this changes current-state and roadmap wording, include `agentic-kit doc-mesh-audit`. If green, open and merge a focused documentation PR. After merge, create `feature/workflow-request-cli` and implement `agentic-kit workflow request` as the public equivalent of `tools/next-step.py --request`.
