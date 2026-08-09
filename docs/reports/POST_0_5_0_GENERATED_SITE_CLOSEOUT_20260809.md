# Post-0.5.0 Generated Site Closeout

Date: 2026-08-09

Status: Block A and Block B are complete for the post-0.5.0 consolidation and
generated website scope. This is not a global DPA-stable or arbitrary
external-repository conformance claim.

Post-S4d main ref before this reporting slice:
`8227f304bbc5cf5dc3aa5c0cbb5db838c992007f`
(`Refresh handoff state after PR2037 (#2038)`).

## Scope Boundary

This closeout covers:

- post-0.5.0 drift consolidation;
- command surface classification and projection;
- `command-for` surface preference;
- GUI/cockpit manifest-driven progressive disclosure;
- generated website foundation, repository projections, claim evidence, Pages
  workflow and presentation layer.

It does not claim:

- kit-wide DPA strict enforcement for every possible future scope;
- DPA conformance for arbitrary foreign repositories without fresh scope
  evidence;
- full GUI parity with every CLI command;
- live public GitHub Pages publication before the repository Pages source is set
  to GitHub Actions.

DP2 implementation remains `100%` only for the
`DP2_SELECTED_SELF_HOSTING_CURRENT_HANDOFF_SCOPE`. That percentage must not be
read as whole-kit DPA completion.

## Main Refs

- Release 0.5.0 starting assumption from the assignment: `01b21325`.
- Refreshed Block A start for this continuation: `a0229a9e`.
- Block B start after refreshed Block A report: `fabd18da`.
- S4b.2 start: `0d1070b3`.
- S4c start: `b145064a`.
- S4d start: `30de3c23`.
- Post-S4d admin main before this closeout report: `8227f304`.

## PRs

Block A was completed earlier and refreshed for this continuation:

- #2002 `70fa831b` Analyze status direction drift after 0.5.0.
- #2004 `a18e831d` Fix post release status next step drift.
- #2006 `800ad500` Record command surface evidence.
- #2009 `41dd0028` Classify command manifest surfaces.
- #2011 `9cefd514` Document command surface compatibility contract.
- #2013 `6b074259` Prefer command surfaces in command-for.
- #2015 `9eb75b58` Project GUI commands from manifest surfaces.
- #2017 `f559f1eb` Accept handoff state refresh merge subjects.
- #2019 `53dcc34a` Record Block A consolidation report.
- #2022 `71e072a9` Refine intent-oriented command surfaces.
- #2024 `539fc969` Harden freshness and guided diagnostics.
- #2026 `2f321aa1` Refresh Block A consolidation report.

Administrative handoff refresh PRs for Block A were #2003, #2005, #2007,
#2008, #2010, #2012, #2014, #2016, #2018, #2020, #2021, #2023, #2025 and
#2027.

Block B PRs:

- #2028 `e2f78baf` Add generated site foundation.
- #2029 `97b61145` Refresh handoff state after PR2028.
- #2030 `8cb5d04e` Generate site repository content.
- #2031 `0d1070b3` Refresh handoff state after PR2030.
- #2032 `e9fcfa09` Bind site claims to executable evidence.
- #2033 `b145064a` Refresh handoff state after PR2032.
- #2034 `c210890d` Add generated site Pages workflow.
- #2035 `926a3b90` Guard Pages deploy until Actions source is enabled.
- #2036 `30de3c23` Refresh handoff state after PR2035.
- #2037 `19d1fc32` Build generated site presentation layer.
- #2038 `8227f304` Refresh handoff state after PR2037.

## Gate Evidence

Latest local full validation before merging S4d:

- `.venv/bin/python -m pytest -q`: 2785 passed.
- `.venv/bin/ruff check .`: PASS.
- `.venv/bin/agentic-kit check-docs`: PASS.
- `.venv/bin/agentic-kit doctor`: PASS.
- `.venv/bin/agentic-kit docs-audit`: PASS.
- `.venv/bin/python site/scripts/build.py --output tmp/site-build --json`: PASS.
- Playwright file-url smoke test for the generated homepage: PASS on desktop and
  mobile screenshots.

Latest post-merge evidence after #2038:

- `agentic-kit transfer post-merge-check --json`: PASS / NOOP at `8227f304`.
- GitHub CI run `31308777521`: success.
- GitHub Pages run `31308777543`: success.
- S4d PR #2037 CI run `31308450612`: success.
- S4d PR #2037 Pages run `31308450606`: success.
- `agentic-kit transfer pr-closeout-complete --after-pr 2037`: PASS.

## Drift Result

S1 selected Option A: a minimal freshness gate for current status markers rather
than a DP4 migration of all status authority surfaces. That path was appropriate
because the stale release/current-state wording was real, but the
`updated_after_pr` field in `PROJECT_DIRECTION.yaml` is a strategic-direction
refresh marker rather than a current-main claim.

Current drift protections:

- `STATUS.md` current-state markers are checked by
  `audit-status-current-state`.
- `PROJECT_DIRECTION.yaml` carries explicit
  `updated_after_pr_semantics: strategic_direction_refresh`.
- `updated_after_pr_current_main_claimed: false` prevents treating the field as
  a current-main freshness assertion.

Remaining curated state surfaces are intentional and gated, not eliminated:

- `docs/STATUS.md`;
- `docs/planning/PROJECT_DIRECTION.yaml`;
- `.agentic/handoff_state.yaml`;
- `.agentic/operational_handoff_state.yaml`;
- generated successor handoff package projections;
- historical planning and evidence reports.

## Command Surface

Current command manifest identity:

- source: `docs/reference/agentic-kit-commands.json`;
- field: `meta.manifest_sha`;
- value: `3d20e7338c12`;
- reproduced by `agentic_project_kit.command_manifest.manifest_sha(commands)`;
- no top-level `manifest_hash` field exists.

Current command distribution:

- total commands: 251;
- `orchestrator`: 31;
- `diagnostic`: 119;
- `primitive`: 101;
- `BOUNDED`: 165;
- `DESTRUCTIVE`: 9;
- `READ_ONLY`: 77.

Normal users typically need the 31 orchestrators as the primary lifecycle
surface, not all 251 registered commands. Expert and CI use still retain the
complete reference.

Current orchestrators:

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

Surface edge cases from the review were resolved by #2022. For example,
`pr-closeout` remains a primitive because `agentic-kit transfer
pr-closeout-complete` is the user-facing orchestrator.

No second command-surface truth remains. `command-for`, GUI/cockpit and the
website consume the same manifest surface values.

## Diagnostics

The manifest still has 119 diagnostics. The user-facing blocker path is reduced
by a derived diagnostic-priority projection rather than by changing the surface
taxonomy.

First-line common-blocker diagnostics:

- `agentic-kit audit-status-current-state`
- `agentic-kit check-docs`
- `agentic-kit docs-audit`
- `agentic-kit doctor`
- `agentic-kit workflow status`
- `agentic-kit workflow-guard check`

Specialized audits and advanced diagnostics remain reachable through the
complete reference.

## Safety

Safety remains separate from surface. No S2-safety PR was opened because the
review did not establish a material safety reclassification that should be
changed without a dedicated safety slice.

Current follow-up risk:

- 165 commands remain `BOUNDED`;
- bounded commands without dry-run should continue to be reviewed before any
  autonomy-policy expansion;
- there are no destructive diagnostics after the intent-oriented surface
  refinement.

## Resolver And GUI

`command-for` uses surface as a preference after task matching, safety and
prerequisite filtering:

- equally suitable matches prefer `orchestrator`;
- a more precise primitive is not displaced by a broad orchestrator;
- diagnostic intent may prefer `diagnostic`;
- safety and prerequisites remain ahead of surface preference.

GUI/cockpit projection is manifest-driven:

- Primary = `surface: orchestrator`;
- Diagnostics = `surface: diagnostic`;
- Expert / Low-level = `surface: primitive`;
- action registry labels and access controls remain Bedienprojektion, not a
  second command taxonomy.

## Website Result

The generated website now has:

- deterministic local build via `site/scripts/build.py`;
- generated metadata from `pyproject.toml`, release/status sources and the
  command manifest;
- guided command view from `surface: orchestrator`;
- diagnostic command view from `surface: diagnostic`;
- complete command reference for all 251 commands;
- computed claim-evidence status;
- GitHub Actions workflow for Pages artifact generation and deployment when
  Pages is configured for Actions;
- presentation-layer homepage with Repository Memory, Runtime Structure, CLI,
  GUI, Communication and Claims sections;
- generated static output count: 10 files.

Automatically generated technical website values include:

- package version;
- Python requirement;
- release tag;
- concept DOI;
- version DOI;
- manifest identity;
- command count;
- command surfaces;
- command safety values;
- dry-run availability;
- command groups;
- status projection;
- roadmap projection;
- computed claim status.

Consciously curated content remains limited to:

- motivation and explanatory prose;
- examples and didactic framing;
- architecture narrative;
- `not claimed` boundaries;
- the static runtime-map illustration.

## Claim Evidence

Claim truth is computed at build time. `site/content/claims.yaml` stores claim
text, requirement level and evidence bindings; it does not store `verified` or
other derived truth values.

Current claim status:

- verified: 10;
- unverified: 0;
- planned: 0;
- required: 5;
- optional: 5.

Verified claims:

- `cli-entry-point`
- `gui-entry-point`
- `python-requirement`
- `package-version`
- `command-manifest-synchronization`
- `artifact-gc-dry-run`
- `workspace-adopt-read-only`
- `workspace-init-preview-execute`
- `successor-handoff-package`
- `generated-command-catalog`

Required claims that protect deployment integrity:

- `cli-entry-point`
- `python-requirement`
- `package-version`
- `command-manifest-synchronization`
- `generated-command-catalog`

Optional claims degrade visibly if their evidence stops passing; they do not
block unrelated text or layout fixes.

## Pages Status

The Pages workflow is present and current runs are green. It builds the site and
runs site tests on `main`.

Live publication is still pending repository configuration. Earlier remote
inspection returned HTTP 404 for the repository Pages API, so the workflow now
guards configure/upload/deploy steps until GitHub Pages is enabled and the Pages
source is set to GitHub Actions. This prevents a missing repository setting from
making `main` red.

Required manual or external action before public deployment:

- set repository Pages source to GitHub Actions;
- re-run or wait for the Pages workflow;
- verify the first live deployment URL.

## Final Answers

1. A normal user should usually know the 31 orchestrators, and in practice the
   homepage highlights a smaller lifecycle subset first. The complete set of
   251 commands remains available for experts, agents and CI.
2. Normal lifecycle coverage is provided by `work start`, `work finish`,
   `work recover`, `workspace init`, `workspace adopt`, `docs lifecycle sweep`,
   `artifact-gc`, release orchestrators and the `transfer ... complete`
   closeout chain.
3. Typical blocker diagnostics are covered by the six common-blocker commands:
   status audit, docs gate, docs audit, doctor, workflow status and
   workflow-guard check.
4. There is no remaining second command-surface truth. The manifest is the
   source for command surface; GUI and website are projections.
5. Hand-curated drift surfaces remain for status and direction, but they are
   bounded and gated instead of silently treated as generated truth.
6. Safety follow-up remains focused on bounded commands without dry-run and any
   future autonomy-policy expansion. No current safety anomaly blocks the site
   closeout.
7. Website command catalog, metadata, status projection, roadmap projection and
   claim status are generated from repository sources or executable evidence.
8. Motivation, teaching copy, visual framing and public `not claimed` limits
   remain curated.
9. Public claim status is currently 10 verified, 0 unverified and 0 planned.
10. Required deployment-integrity claims are the CLI entry point, Python
    requirement, package version, command manifest synchronization and generated
    command catalog.
11. Manifest identity comes from
    `docs/reference/agentic-kit-commands.json` `meta.manifest_sha` and is
    reproduced from the command list as `3d20e7338c12`.
12. Useful pre-0.6.0 work is: enable and verify live GitHub Pages, continue
    safety review for bounded commands where autonomy matters, broaden external
    repository adoption/DPA evidence, and avoid turning DP2 scope completion
    into a global DPA-conformance claim.

## Closeout Judgment

The assignment's structural goal is met: existing command complexity is ordered
through one manifest-backed surface model, the GUI and website project that
model without owning a second taxonomy, and public technical claims are bound to
computed evidence rather than stored prose truth.

The remaining work is operational publication and future scope expansion, not a
blocker for the post-0.5.0 consolidation or generated evidence-bound website
implementation.
