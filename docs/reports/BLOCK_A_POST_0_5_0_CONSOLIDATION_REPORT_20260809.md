# Block A Post-0.5.0 Consolidation Report

Date: 2026-08-09

Status: Block A complete. Block B has not started.

Current main ref: `5849122639e87b3563f1e04d2eb27df7dcf6aa5e` (`58491226`, `Refresh handoff state after PR2017 (#2018)`).

## Scope

Block A covered post-0.5.0 consolidation only:

- status/direction drift analysis and repair;
- command surface evidence and manifest classification;
- command-for surface preference;
- GUI/cockpit projection from manifest surfaces;
- post-merge lifecycle repair needed to settle the S3 merge.

This report is not a DPA-stable or kit-wide DPA-conformance claim.

DP2 implementation status remains `100%` for `DP2_SELECTED_SELF_HOSTING_CURRENT_HANDOFF_SCOPE`.

Kit-wide DPA status remains `NOT_ASSESSED_BY_DP2_READINESS`.

## PRs

Block A and required administrative closeout merged through:

- #2002 `70fa831b` Analyze status direction drift after 0.5.0.
- #2003 `8d97afe1` Refresh handoff state after PR2002.
- #2004 `a18e831d` Fix post-release status next-step drift.
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

## Gates

Final local evidence on main `58491226`:

- `pytest -q`: 2765 passed.
- `ruff check .`: PASS.
- `agentic-kit check-docs`: PASS.
- `agentic-kit docs-audit`: PASS.
- `agentic-kit doctor`: PASS.
- `agentic-kit audit-command-manifest`: PASS.
- `agentic-kit audit-command-authority`: PASS, manifest SHA `2eea21bea1cd`.
- `agentic-kit command-taxonomy-check`: PASS, command count 251.
- `agentic-kit transfer post-merge-check --json`: PASS, `refresh_required=False`, `result=NOOP`, `successor_package_head_status=refresh_only_descendant`.
- DPA readiness: `DP2_AUTHORIZED`, DP2 selected scope 100%, kit-wide DPA `NOT_ASSESSED_BY_DP2_READINESS`.
- DPA probe-002, renderer, probe-003 and probe-004 readiness: `SATISFIED_FOR_CURRENT_KIT_REF`.

## Surface Distribution

Current generated command manifest:

- `orchestrator`: 27.
- `diagnostic`: 121.
- `primitive`: 103.
- total commands: 251.

Current manifest acknowledgement: `COMMAND_MANIFEST_ACK 2eea21bea1cd`.

The acknowledgement value comes from `docs/reference/agentic-kit-commands.json` `meta.manifest_sha`, regenerated from the Typer/Click command registry and synchronized into agent entrypoints.

## Orchestrators

- `agentic-kit dpa final-closeout-check`
- `agentic-kit evidence commit-paths`
- `agentic-kit evidence finalize-log`
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
- `agentic-kit workflow go`
- `agentic-kit workspace adopt`
- `agentic-kit workspace dpa-intake`
- `agentic-kit workspace init`
- `agentic-kit workspace remove`
- `agentic-kit workspace upgrade`

## Command-For Result

`agentic-kit command-for` uses surface as a preference after task matching and safety filtering. Evidence:

- PR #2013 added the tie-breaker and tests.
- Final transfer-task output still lists read-only diagnostic transfer commands first because safety filtering precedes surface preference.
- Resolver tests prove equally suitable task matches prefer orchestrator, diagnostic intent can prefer diagnostic, and exact primitive matches are not displaced by broader orchestrators.

## GUI Result

GUI/cockpit no longer carries an independent command surface taxonomy.

- Full command projection is derived from the generated manifest `surface` field:
  - Primary = `orchestrator`.
  - Diagnostics = `diagnostic`.
  - Expert / Low-level = `primitive`.
- Cockpit action JSON exposes `manifest_surface` and `gui_layer`.
- Current cockpit action inventory:
  - `manifest_surface`: diagnostic 9, orchestrator 2, primitive 6, external 1.
  - `gui_layer`: diagnostics 9, primary 2, expert 6, external 1.
- GUI button wrappers that start with `agentic-kit` are validated against the command manifest.
- The stale `agentic-kit work-order upload` GUI wrapper is now backed by a registered `agentic-kit work-order upload` command that reuses the existing bounded result-log uploader core.

The GUI action registry remains a Bedienprojektion with labels, gates and access-level visibility. It is not a second surface authority.

## Remaining Second Truths And Drift Surfaces

No second command surface authority remains for command role classification.

Remaining hand-curated or projected operational state surfaces still exist and must stay governed:

- `docs/STATUS.md` remains a concise manual status pointer with freshness gates.
- `.agentic/handoff_state.yaml` and `.agentic/operational_handoff_state.yaml` remain command-updated state surfaces.
- Successor handoff package files remain generated projections.
- Historical planning and evidence reports remain historical records, not current control-plane sources.

Block A also fixed a lifecycle mismatch where the post-merge refresh gate accepted `Refresh successor handoff after PR...` but not the current `Refresh handoff state after PR...` admin refresh subject.

## Safety Follow-Up

No S2-safety PR was opened in Block A. S2a did not require a bulk safety reclassification slice.

Known review note: surface classification is not safety classification. Some cockpit actions intentionally have cockpit-local safety labels for GUI execution gating while manifest safety describes the public command wrapper. That split is documented and tested; it is not a DPA or stable-conformance claim.

## Website Canonical Sources

If Block B proceeds unchanged, the website should derive technical truth from:

- `pyproject.toml`;
- `docs/reference/agentic-kit-commands.json`;
- `docs/reference/AGENTIC_KIT_COMMANDS.md` as generated human projection only;
- release metadata and DOI sources already governed by release commands;
- `docs/planning/PROJECT_DIRECTION.yaml` for roadmap state;
- `docs/STATUS.md` as concise current-state pointer, with its manual boundary visible;
- DPA records and readiness commands for DPA status;
- executable evidence and gate outputs, not stored `verified` prose.

## Recommendation For Block B

Block B can proceed without changing the high-level scope, but it must honor the S4b.2 rule: public technical claims need computed evidence status, not hand-stored `verified` fields.

The website must consume the manifest surface field and must not create a new hand-maintained command taxonomy.
