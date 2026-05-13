Current version: 0.3.3

# Current Handoff

Status-date: 2026-05-13
Project: agentic-project-kit
Branch: docs/doc-mesh-gate-policy
Base branch: main

## Current Goal

Document the adoption policy for `agentic-kit doc-mesh-audit` after PR #143:

- keep it as a targeted special gate first;
- require it for documentation-mesh, release, handoff, governance, roadmap, DOI/version, documentation-coverage, and cross-document drift-rule changes;
- do not add it immediately to every default `ns` workflow run;
- reassess later for integration into `agentic-kit doctor` after several successful PRs without false positives;
- reassess default `ns` integration only after the `doctor` integration decision.

This branch must not implement a code change. It records the policy decision and the next safe evaluation path.

## Current Repository State

v0.3.3 is released and post-release verified.

Completed changes included in the v0.3.3 scope:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` to detect package-version drift.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage.
- PR #141 prepared and released v0.3.3.

Post-v0.3.3 completed work:

- PR #143 added the first bounded `agentic-kit doc-mesh-audit` slice with modular core logic, CLI adapter, tests, README/TEST_GATES/DOCUMENTATION_COVERAGE coverage, README v0.3.2 DOI restoration, and the modular implementation rule.

Release evidence:

- GitHub Release v0.3.3 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.3 version DOI: `10.5281/zenodo.20151924`.
- `agentic-kit post-release-check --version 0.3.3` passed.
- post-release Zenodo verification is complete for v0.3.3.

Current project-health baseline:

- `agentic-kit doctor` checks required project files, documentation gates, task gates, version drift, package `__version__` drift, and policy-pack checks.
- The selected policy packs remain visible in the project contract and documentation coverage.
- `agentic-kit doc-mesh-audit` is currently a targeted special gate, not yet a default doctor check.

Documentation-mesh audit state:

The project now has `agentic-kit doc-mesh-audit`. It is a deterministic bounded audit for machine-readable documentation drift classes. It currently covers:

- current-state document version mismatch;
- stale current-state wording;
- missing historical-source-of-truth banners;
- release DOI list mismatches;
- explicit document taxonomy across current-state, governance, architecture/design, and historical-plan documents.

It does not prove semantic completeness or overall documentation quality.

Adoption policy:

Use `agentic-kit doc-mesh-audit` as a targeted special gate when changing:

- README, CHANGELOG, CITATION, pyproject, package `__version__`, STATUS, or CURRENT_HANDOFF;
- AGENTS, TEST_GATES, DOCUMENTATION_COVERAGE, sentinel, or project contract files;
- ARCHITECTURE_CONTRACT, WORKFLOW_OUTPUT_CYCLE, DESIGN, or architecture/design docs;
- roadmap summaries, historical planning files, status reports, or output-repair planning files;
- release DOI lists, version lists, post-release archive state, next-safe-step wording, or cross-document drift rules.

Do not add the audit immediately to every default current-branch local gate. It is still young and could block unrelated code changes through documentation-taxonomy or historical-plan rules. The safer promotion path is:

1. targeted gate use across a few PRs;
2. collect real failures and false positives;
3. consider structured report output and bounded repairs;
4. integrate into `agentic-kit doctor` if stable;
5. only then consider unconditional default `ns` workflow integration.

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

Then reply in chat with `d` after evidence upload. If the workflow enters `FAILED`, copy the relevant terminal output because `d` alone is not sufficient for local failures unless evidence was uploaded.

## Current Branch Work

Prepared files should include:

- `docs/STATUS.md` with the post-PR #143 documentation-mesh audit state and targeted-gate adoption policy.
- `docs/handoff/CURRENT_HANDOFF.md` with the same next-safe-step context.

No code change is intended in this slice.

## Next Safe Step

Run the standard local gate on `docs/doc-mesh-gate-policy`. Because this branch changes documentation-mesh policy, also run `agentic-kit doc-mesh-audit`. If green, open and merge the focused documentation policy PR.
