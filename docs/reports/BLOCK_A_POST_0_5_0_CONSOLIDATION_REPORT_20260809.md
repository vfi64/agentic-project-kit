# Block A Post-0.5.0 Consolidation Report

Date: 2026-08-09

Status: Block A complete and refreshed after the post-report hardening slices. Block B has not started.

Current admin main ref: `a0229a9eecd8483d3930b01d72d4a2b8c8f72f0c` (`a0229a9e`, `Refresh handoff state after PR2024 (#2025)`).
Current substantive main ref: `539fc9699a256754d76aa63522ed53b1810c3d63` (`539fc969`, `Harden freshness and guided diagnostics (#2024)`).

## Scope

Block A covered post-0.5.0 consolidation only:

- status/direction drift analysis and repair;
- command surface evidence and manifest classification;
- command surface compatibility documentation;
- command-for surface preference;
- GUI/cockpit projection from manifest surfaces;
- intent-oriented surface refinement after review;
- status current-state freshness hardening;
- guided diagnostic prioritization and initial claim/safety review projection.

This report is not a DPA-stable or kit-wide DPA-conformance claim.

DP2 implementation status remains `100%` for `DP2_SELECTED_SELF_HOSTING_CURRENT_HANDOFF_SCOPE`.
Kit-wide DPA status must not be inferred from the DP2 readiness percentage.

## PRs

Block A and required administrative closeout merged through:

- #2002 `70fa831b` Analyze status direction drift after 0.5.0.
- #2003 `8d97afe1` Refresh handoff state after PR2002.
- #2004 `a18e831d` Fix post release status next step drift.
- #2005 `717dc451` Refresh handoff state after PR2004.
- #2006 `800ad500` Record command surface evidence.
- #2007 `a83468b8` Refresh successor package after PR2006.
- #2008 `22c33481` Refresh handoff state after PR2007.
- #2009 `41dd0028` Classify command manifest surfaces.
- #2010 `4ebfa0cd` Refresh handoff state after PR2009.
- #2011 `9cefd514` Document command surface compatibility contract.
- #2012 `5ee13cab` Refresh handoff state after PR2011.
- #2013 `6b074259` Prefer command surfaces in command-for.
- #2014 `e3509718` Refresh handoff state after PR2013.
- #2015 `9eb75b58` Project GUI commands from manifest surfaces.
- #2016 `79280d21` Refresh handoff state after PR2015.
- #2017 `f559f1eb` Accept handoff state refresh merge subjects.
- #2018 `58491226` Refresh handoff state after PR2017.
- #2019 `53dcc34a` Record Block A consolidation report.
- #2020 `17b393c7` Refresh successor package after PR2019.
- #2021 `136c08ef` Refresh handoff state after PR2020.
- #2022 `71e072a9` Refine intent-oriented command surfaces.
- #2023 `0de34d2f` Refresh handoff state after PR2022.
- #2024 `539fc969` Harden freshness and guided diagnostics.
- #2025 `a0229a9e` Refresh handoff state after PR2024.

## Current Gate Evidence

Current local evidence on branch start from `a0229a9e`:

- `agentic-kit transfer sync-main`: PASS.
- `agentic-kit audit-command-manifest`: PASS, finding count 0.
- `agentic-kit audit-status-current-state`: PASS, finding count 22, blocker count 0.
- `docs/reference/agentic-kit-commands.json`: 251 commands.
- `build_gui_command_projection(...)`: finding count 0.

Most recent complete post-merge validation after PR #2025 recorded:

- `pytest -q`: 2772 passed.
- `ruff check .`: PASS.
- `agentic-kit check-docs`: PASS.
- `agentic-kit docs-audit`: PASS.
- `agentic-kit doctor`: PASS with report-only lifecycle warnings.
- DPA readiness: `DP2_AUTHORIZED`, DP2 selected scope 100%, kit-wide DPA not assessed by that command.
- DPA post-DP2 and stable readiness: final/stable records valid for their recorded exact refs; external repo conformance remains explicitly unclaimed.

## Surface Distribution

Current generated command manifest:

- `orchestrator`: 31.
- `diagnostic`: 119.
- `primitive`: 101.
- total commands: 251.

Current manifest acknowledgement: `COMMAND_MANIFEST_ACK 3d20e7338c12`.

The acknowledgement value comes from `docs/reference/agentic-kit-commands.json` field `meta.manifest_sha`. The value is reproduced by `agentic_project_kit.command_manifest.manifest_sha(commands)` over the committed command list. There is no top-level `manifest_hash` field.

## Orchestrators

- `agentic-kit artifact-gc`
- `agentic-kit chat session-start`
- `agentic-kit docs lifecycle sweep`
- `agentic-kit dpa final-closeout-check`
- `agentic-kit github-create`
- `agentic-kit init`
- `agentic-kit post-release-doi-closeout`
- `agentic-kit release prepare`
- `agentic-kit release ready`
- `agentic-kit release-prep`
- `agentic-kit release-publish`
- `agentic-kit transfer admin-refresh-pr`
- `agentic-kit transfer chat-switch-complete`
- `agentic-kit transfer evidence-pr-complete`
- `agentic-kit transfer post-merge-complete`
- `agentic-kit transfer post-merge-settle`
- `agentic-kit transfer pr-closeout-complete`
- `agentic-kit transfer pr-complete`
- `agentic-kit transfer pr-create-complete`
- `agentic-kit transfer remote-next`
- `agentic-kit transfer remote-work-start`
- `agentic-kit transfer sync-main`
- `agentic-kit work finish`
- `agentic-kit work recover`
- `agentic-kit work start`
- `agentic-kit workflow go`
- `agentic-kit workspace adopt`
- `agentic-kit workspace dpa-intake`
- `agentic-kit workspace init`
- `agentic-kit workspace remove`
- `agentic-kit workspace upgrade`

## Diagnostic Projection

The manifest still contains 119 diagnostic commands, but GUI-facing guidance is not a flat list of 119 entries.

Current diagnostic priority projection:

- `common_blocker`: 6.
- `reference_lookup`: 11.
- `claim_evidence`: 12.
- `specialized_audit`: 20.
- `advanced_diagnostic`: 70.

Current guided diagnostic count: 6.

The six common-blocker diagnostics are the first-line "why is this blocked?" surface. Specialized audits and advanced diagnostics remain available without being promoted as the normal diagnostic starting point.

## Command-For Result

`agentic-kit command-for` uses surface as a preference after task matching, safety and prerequisite filtering.

Evidence:

- PR #2013 added surface-aware resolver behavior and tests.
- Equally suitable matches prefer `orchestrator`.
- A more precise primitive is not displaced by a broad orchestrator.
- Diagnostic intent may prefer `diagnostic`.
- Safety and prerequisite rules remain ahead of surface preference.

This is a selection aid, not a second command taxonomy.

## GUI Result

GUI/cockpit no longer carries an independent command surface taxonomy.

- Full command projection is derived from the generated manifest `surface` field:
  - Primary = `orchestrator`.
  - Diagnostics = `diagnostic`.
  - Expert / low-level = `primitive`.
- Current GUI command projection:
  - `primary`: 31.
  - `diagnostics`: 119.
  - `expert`: 101.
- Current GUI button manifest bindings:
  - total bound agentic-kit wrappers: 17.
  - `diagnostic`: 5.
  - `orchestrator`: 4.
  - `primitive`: 8.
  - binding findings: 0.
- Cockpit action registry remains a Bedienprojektion with labels, gates and access-level visibility. It is not a second surface authority.

## Claim And Safety Projection

PR #2024 added initial command-level projection fields for later public evidence work:

- `claim_evidence_for_command(...)`
- `safety_review_for_command(...)`
- `diagnostic_priority_for_command(...)`

These are derived projections, not proof that a website claim is verified. Block B must still evaluate claim evidence from executable checks before presenting a technical claim as verified.

Safety remains separate from surface. No S2-safety PR was opened, because Block A did not find a material safety reclassification that should be changed without additional review. The notable current follow-up is presentation and review guidance for bounded commands without dry-run, not a bulk safety rewrite.

Current review note from PR #2024 evidence:

- destructive diagnostics: 0.
- bounded commands without dry-run are exposed as `manual_safety_review` where applicable.

## Remaining Second Truths And Drift Surfaces

No second command surface authority remains for command role classification.

Remaining hand-curated or projected operational state surfaces still exist and must stay governed:

- `docs/STATUS.md` remains a concise manual status pointer with freshness gates.
- `docs/planning/PROJECT_DIRECTION.yaml` keeps strategic direction metadata; `updated_after_pr` now has explicit `strategic_direction_refresh` semantics and is not a current-main claim.
- `.agentic/handoff_state.yaml` and `.agentic/operational_handoff_state.yaml` remain command-updated state surfaces.
- Successor handoff package files remain generated projections.
- Historical planning and evidence reports remain historical records, not current control-plane sources.

Block B must not add a new hand-maintained technical truth surface. Any public technical claim must be generated from repository sources or evaluated through claim evidence.

## Website Canonical Sources

Block B should derive technical truth from:

- `pyproject.toml` for package version, Python requirement and entry points;
- `docs/reference/agentic-kit-commands.json` for command metadata and `meta.manifest_sha`;
- `docs/reference/AGENTIC_KIT_COMMANDS.md` only as generated human projection;
- release metadata and DOI sources already governed by release commands;
- `docs/planning/PROJECT_DIRECTION.yaml` for roadmap state, with the documented `updated_after_pr` boundary;
- `docs/STATUS.md` as concise current-state pointer, with its manual boundary visible;
- DPA records and readiness commands for DPA status;
- executable evidence and gate outputs, not stored `verified` prose.

No GitHub Pages site or Pages workflow exists at this refreshed checkpoint. There is no existing `site/` tree.

## Block B Decision

No new maintainer decision point is created by the refreshed Block A evidence.

Block B can proceed unchanged if it follows these constraints:

- use the current manifest `surface` field for guided, diagnostic and complete command views;
- derive manifest identity from `meta.manifest_sha`, reproducing it from committed commands when validating;
- calculate website claim status from evidence bindings;
- never store a derived `verified` truth value in curated claim content;
- let optional claims degrade visibly instead of blocking unrelated website publication;
- block required claim regressions.
