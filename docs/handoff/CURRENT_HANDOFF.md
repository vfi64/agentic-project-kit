Current version: 0.3.5

# Current Handoff

Status-date: 2026-05-13
Project: agentic-project-kit
Branch: post-release/record-v0.3.5-doi
Base branch: main

## Current Goal

Record verified v0.3.5 DOI metadata after post-release Zenodo verification:

- `agentic-kit doc-mesh-audit` as targeted documentation mesh drift audit;
- JSON report output for machine-readable audit evidence;
- bounded repair-plan output;
- `agentic-kit doc-mesh-repair` for the first safe automatic repair class: inserting missing historical-source-of-truth banners;
- documented adoption policy: targeted special gate first, possible later promotion to `doctor`, then possible default `ns` integration only after stabilization.

v0.3.5 post-release verification is complete. README and CITATION may now record the verified version DOI `10.5281/zenodo.20169965`.

## Current Repository State

v0.3.3 is released and post-release verified.

Completed changes included in the v0.3.3 scope:

- PR #134 documented the standard `python tools/next-step.py` terminal workflow and `done` / `d` acknowledgement pattern.
- PR #136 fixed package `__version__` drift and extended `agentic-kit doctor` to detect package-version drift.
- PR #139 added project-local environment bootstrap to `tools/next-step.py` so `.venv` and missing dev tools are created before running workflow gates.
- PR #140 documented explicit `FAILED` next-step handling as a stop-and-diagnose state and added documentation coverage.
- PR #141 prepared and released v0.3.3.

Post-v0.3.3 completed work prepared for v0.3.5:

- PR #143 added the first bounded `agentic-kit doc-mesh-audit` slice with modular core logic, CLI adapter, tests, README/TEST_GATES/DOCUMENTATION_COVERAGE coverage, README v0.3.2 DOI restoration, and the modular implementation rule.
- PR #144 documented the targeted-gate adoption policy for `doc-mesh-audit`.
- PR #145 added JSON report output for `agentic-kit doc-mesh-audit --report`.
- PR #146 added bounded repair-plan output for `agentic-kit doc-mesh-audit --repair-plan`.
- PR #147 added `agentic-kit doc-mesh-repair` for missing historical-source-of-truth banners.

v0.3.5 release evidence is verified:

- GitHub Release v0.3.5 exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified v0.3.5 version DOI: `10.5281/zenodo.20169965`.
- `agentic-kit post-release-check --version 0.3.5` passed.
- post-release Zenodo verification is complete for v0.3.5.

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
- explicit document taxonomy across current-state, release-history, governance, architecture/design, and historical-plan documents.

It can write a JSON report and a bounded repair plan. `agentic-kit doc-mesh-repair` can apply only the currently safe automatic repair class: inserting historical-source-of-truth banners into known historical-plan documents. Version, DOI, stale-state, and missing-document findings remain manual review items.

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
3. use structured reports and bounded repairs for review and maintenance;
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
agentic-kit post-release-check --version 0.3.5
```

The normal local workflow shortcut remains:

```bash
ns
```

Then reply in chat with `d` after evidence upload. If the workflow enters `FAILED`, copy the relevant terminal output because `d` alone is not sufficient for local failures unless evidence was uploaded.

## Current Branch Work

Prepared files should include:

- `pyproject.toml` and package `__version__` bumped to 0.3.5.
- `README.md` records the verified v0.3.5 version DOI.
- `CITATION.cff` records the verified v0.3.5 version DOI comment.
- `docs/STATUS.md` and this handoff reflect post-release verification.
- No release version bump or tag change is part of this branch.

## Next Safe Step

Run the standard local gate on `post-release/record-v0.3.5-doi`. Because this branch records post-release DOI metadata, also run `agentic-kit doc-mesh-audit` and `agentic-kit post-release-check --version 0.3.5`. If green, open and merge the focused post-release DOI metadata PR.
