Status: analysis
Status-date: 2026-08-09
Scope: S1 status/direction drift analysis only
Branch: codex/s1-status-direction-drift-analysis

# S1 Status and Direction Drift Analysis

## Executive Summary

This S1 slice is read-only analysis. It does not repair `docs/STATUS.md`,
`docs/handoff/CURRENT_HANDOFF.md`, generated successor projections, or
`docs/planning/PROJECT_DIRECTION.yaml`.

Current repository evidence confirms the known post-0.5.0 drift class:

- Release metadata is current and verified for version `0.5.0`.
- `origin/main` is `01b21325fbdb5ffa76b7c5dad9a86ffc056ceb59`, after PR #2001
  (`Refresh handoff state after PR2000`).
- `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`,
  `.agentic/handoff_state.yaml`, `.agentic/operational_handoff_state.yaml`, and
  the latest successor validation report still anchor the operational/substantive
  safe state to `fa1f8cccd83a1904ad2f6be32445326f3db5308c`, after PR #2000
  (`Close out release 0.5.0 DOI metadata`).
- The checked-in status audit currently treats this as valid bounded
  administrative lag: `handoff_validation_head_not_too_far_behind_origin_main`
  reports `lag_count=1`, `max_origin_lag=3`.
- `docs/STATUS.md` still contains stale active prose:
  `codex/claude-followup-hardening` is described as the current governed slice
  and the active next step still says to regenerate and publish release `0.5.0`
  from fresh main.
- `docs/planning/PROJECT_DIRECTION.yaml` remains structurally valid, but its
  `meta.updated_after_pr` is `1860` while current main has merged through PR
  #2001. No current gate compares this field with latest main or latest PR.

The root cause is not a simple missing gate failure. It is a deliberately
preserved hybrid authority model: current-state documents remain partly
manual/curated dashboards and partly command-updated/generated projections. The
existing gates validate selected invariants, not complete semantic currency.

## Current Evidence

| Evidence | Result |
|---|---|
| Local branch at analysis start | `codex/s1-status-direction-drift-analysis` |
| Local base HEAD | `01b21325fbdb5ffa76b7c5dad9a86ffc056ceb59` |
| `origin/main` | `01b21325fbdb5ffa76b7c5dad9a86ffc056ceb59` |
| Release lifecycle | `release-status --version 0.5.0 --include-remote --json`: `PASS`, `current_verified` |
| Release DOI | `10.5281/zenodo.21850952` |
| Post-merge handoff status | `handoff post-merge-refresh-status`: `result=NOOP` |
| Status current-state audit | `audit-status-current-state --json`: `PASS`, 0 blockers |
| Direction validation | `direction validate --json`: `PASS`, 0 findings |
| Direction drift audit | `direction audit-drift --json`: `PASS`, 13 records |
| Successor validation report | `PASS`, generated head `fa1f8ccc` |

## Reverified Drift Findings

### STATUS.md

Confirmed current-state release facts:

- `Current version: 0.5.0`
- `Current verified release: 0.5.0.`
- `Current release tag: v0.5.0.`
- `Verified Zenodo version DOI: 10.5281/zenodo.21850952.`

Confirmed stale or ambiguous active prose:

- `Current verified main` is `fa1f8ccc`, not current `origin/main`
  `01b21325`.
- `Latest substantive work` is PR #2000, while the latest merged PR is
  administrative PR #2001.
- `Current governed slice` still names `codex/claude-followup-hardening` and
  says it closes small Claude follow-ups before release `0.5.0`.
- The active next step says: continue from fresh main with the next planned
  governed slice, handoff closeout, then regenerate and publish release `0.5.0`
  from fresh main. That publishing step is stale because `0.5.0` is already
  published and DOI-verified.

### CURRENT_HANDOFF.md

The generated operational handoff block is consistent with the bounded
substantive safe-state model:

- Current verified main/admin HEAD: `fa1f8ccc`
- Last substantive work state: `fa1f8ccc`

However, the non-generated and compact-history areas still contain older
operational slices and historical anchors. This is expected for a hybrid
document, but it increases cognitive drift risk when active readers skim beyond
the generated block.

### PROJECT_DIRECTION.yaml

`docs/planning/PROJECT_DIRECTION.yaml` remains the canonical direction file and
passes its structural validator. Its `meta.updated_after_pr` is `1860` and
`updated_after_pr_url` points to PR #1860. The value is rendered by
`agentic_project_kit.project_direction`, but current searches found no gate that
compares it to latest merged PR, current main, or latest completed release.

The field currently functions as a coarse "last strategic direction refresh"
marker, not as a current main freshness claim.

## Historical DPA / DP4 Decision

The bounded DP3/DP4 adjudication record is
`docs/architecture/evidence/dpa/assessment/DP3_DP4_ADJUDICATION_RECORD_20260801.json`.

Relevant decisions:

- `DP4-CURRENT-HANDOFF`: `NO_MIGRATION_HYBRID_STATUS_AUTHORITY`; generated
  operational block remains command-owned, while non-lifecycle-owned prose
  remains manually preserved.
- `DP4-STATUS`: `NO_MIGRATION_MANUAL_STATUS_DASHBOARD`; `docs/STATUS.md`
  remains a concise manual dashboard and DPA does not become a full-document
  source authority for it in that bounded slice.
- `DP4-SUCCESSOR-PROJECTIONS`: no full migration; generated successor
  projection boundary remains command-owned.

Was the old decision correct then?

Yes, for the bounded DP4 exit it was conservative and governance-compliant. It
avoided converting broad manual status prose into generated output without full
reader/writer/generator evidence.

Is it still sufficient today?

Only partially. It remains correct as a no-migration boundary, but the current
runtime has accumulated enough repeated status/handoff refresh pressure that
manual preservation alone no longer gives maintainers a clear freshness model.
The recurring drift now warrants either a narrow freshness gate or a renewed DP4
status-authority design slice.

## Operational Truth Inventory

| Path | Authority | Writers | Readers | Write frequency | Automated | Freshness gate | Semantic gate | Projection | DPA-managed | Drift risk |
|---|---|---|---|---|---|---|---|---|---|---|
| `docs/STATUS.md` | Manual current-state dashboard with bounded command-updated release/admin lines | Maintainer/manual edits; release prep/DOI closeout; transfer admin refresh | AGENTS required read; doctor/version checks; docs-audit; status-current-state audit; successor context; humans | Release, post-release closeout, admin refresh, manual state update | Partly | Partial: `audit-status-current-state`, docs-audit headroom | Partial: release/version/DOI/current-main subset only | No full projection | DP4 no-migration/manual preservation | High |
| `docs/handoff/CURRENT_HANDOFF.md` | Hybrid handoff document | Generated operational block via transfer/DPA lifecycle; manual prose; release DOI closeout for bounded lines | AGENTS; handoff/package tools; agents; docs-audit | Post-merge/admin refresh, handoff refresh, release closeout | Partly | Partial: post-merge refresh status and successor validation | Partial: generated block contract and DPA lifecycle scope | Generated block only | DP2/DP4 bounded | High |
| `docs/reports/handoff-packages/latest/*` | Generated successor handoff package | `transfer chat-switch-complete`, post-merge settle/admin refresh | AGENTS; successor chats; validation tools | Handoff/admin refresh | Yes | Validation report `PASS`; post-merge refresh status | Stronger structural validation | Yes | DP4 generated-output boundary | Low |
| `.agentic/handoff_state.yaml` | Machine-readable handoff state, partly stale historical release fields | Handoff/admin refresh commands | Handoff tools, tests, agents | Handoff/admin refresh | Yes | Handoff freshness/status gates | Partial | Source-like state | Not full-DPA for status | Medium |
| `.agentic/operational_handoff_state.yaml` | Machine-readable operational handoff state | Operational handoff projection/update commands | `CURRENT_HANDOFF.md` generator, tests, agents | Admin refresh | Yes | Generated block validation | Partial | Source for generated block | DPA current-handoff lifecycle related | Medium |
| `docs/planning/PROJECT_DIRECTION.yaml` | Canonical strategic direction | Manual maintainer/codex planning updates | Direction renderer, direction validator, direction drift audit, successor package | Strategic slice/release/decision | No full auto update | Structural validation only | Drift audit for source references, not main PR freshness | No | Not selected for DP4 migration | Medium |
| `docs/planning/PROJECT_DIRECTION.md` | Rendered readable projection / canonical direction view | Direction renderer/manual refresh path | Humans, docs coverage, command docs | Direction render/update | Partly | Direction tests/coverage | Partial | Yes in practice | Not selected | Medium |
| `CHANGELOG.md` | Release history | Release prep, DOI closeout, manual release notes | release-status, release-check, docs-audit, humans | Release and DOI closeout | Partly | Release gates | Version/DOI subset | No | Release lifecycle governed | Low |
| `CITATION.cff` | Citation/release metadata | Release prep, DOI closeout | release-status, post-release-check, humans | Release and DOI closeout | Partly | Release gates | Version/DOI subset | No | Release lifecycle governed | Low |
| `docs/releases/VERIFIED_RELEASES.md` | Release DOI history | DOI closeout | release-status/history readers | Post-release DOI closeout | Yes for current append/update | Release metadata authority gate | DOI/release subset | No | Release lifecycle governed | Low |
| `.agentic/current_work.yaml` | Workflow control state | Workflow commands | Workflow commands, agents | Per workflow request/run | Yes | Workflow guard/state checks | State-machine scoped | No | No | Medium |
| `.agentic/todo.yaml` | TODO task state | TODO commands/manual | TODO commands/check-todo | Task updates | Partly | check-todo | Task schema | Render source for TODO view | No | Medium |

## STATUS.md Reference Classification

The current repository contains many references to `docs/STATUS.md`. The
important classification is:

- `read-current-state`: `AGENTS.md`, chat/bootstrap governance contracts,
  `doctor.py`, `handoff_freshness.py`, `audit-status-current-state`, successor
  package creation/validation, active tests.
- `write-current-state`: manual edits, release prep/DOI closeout paths, transfer
  admin refresh paths.
- `validate`: `audit-status-current-state`, docs-audit, doctor version checks,
  handoff freshness tests, current-state doc currency tests.
- `render/copy/project`: generated operational handoff projections and successor
  package prompts refer to or copy selected current-state markers.
- `historical-reference`: old status snapshots inside `docs/STATUS.md`,
  `docs/handoff/CURRENT_HANDOFF.md`, archives, and long historical reports.
- `test-only`: many fixtures write minimal `docs/STATUS.md` files.
- `documentation-only`: README, TEST_GATES, governance docs describe how the
  status file should be read.

The decisive pattern is multiple readers plus more than one semantic writer.
There is no single full-document writer. That is the root of the recurring
semantic freshness risk.

## updated_after_pr Analysis

| Question | Finding |
|---|---|
| Who sets it? | Manual planning/direction updates; historical instructions in `MASTER_IMPLEMENTATION_Q.md` describe setting it after PR numbers are known. |
| Who renders it? | `agentic_project_kit.project_direction` renders `Updated after PR` into text/Markdown output. |
| Who checks it? | Structural direction validation accepts the field; current search found no gate comparing it to latest PR/main. |
| Does it have current-state authority? | Not reliably. Current value `1860` is older than current merged PR #2001 and should be treated as strategic-direction currency only. |
| Is it still needed? | Yes as a direction-refresh marker, but it should be renamed/clarified or separately gated if expected to mean current repository freshness. |

## Cause Model

1. DPA DP4 deliberately preserved `STATUS.md` and most handoff prose as manual
   current-state surfaces.
2. Release and handoff commands update bounded subsets, creating a hybrid
   document rather than a single generated projection.
3. Existing gates validate bounded invariants: release version/DOI, validation
   head reachability, admin lag, duplicate live markers, and pending DOI lines.
4. No current gate validates the semantic content of `Current governed slice`,
   `Next safe step`, or `PROJECT_DIRECTION.meta.updated_after_pr` against
   current main/release state.
5. Therefore release-critical facts can be correct while active prose remains
   stale.

## Options

### Option A: Minimal Freshness Gate

Add a narrow deterministic gate for obvious stale active-state markers:

- `updated_after_pr` too far behind latest merged PR when presented as current.
- active next-step text that tells maintainers to publish an already verified
  release.
- active governed-slice text that refers to a completed pre-release branch after
  release lifecycle is `current_verified`.

Benefits: small, reversible, fast to test; catches the current failure class.

Risks: can become a collection of pattern checks; will not solve all semantic
status drift.

Effort: small to medium.

Architecture impact: extends existing current-state audit rather than changing
document authority.

Drift reduction: medium.

Reversibility: high.

### Option B: Reopen DP4 Status Authority

Treat current state as a typed source model and render `STATUS.md`,
`CURRENT_HANDOFF.md`, and successor projections from that model.

Benefits: strongest long-term reduction of duplicate truth surfaces.

Risks: larger migration; requires careful preservation of manual/historical
prose; can conflict with the DP4 no-migration boundary unless explicitly
adjudicated.

Effort: medium to large.

Architecture impact: significant; should be its own DP4 follow-up design and
implementation sequence.

Drift reduction: high.

Reversibility: medium.

### Option C: Explicit Manual Curation Boundary

Keep status and direction manual, and make their limited freshness guarantee
visible. Tighten wording so current facts are only release/current-head subsets
that gates actually check.

Benefits: minimal implementation risk and compatible with prior DP4 decision.

Risks: does not materially reduce operational drift; agents may continue to
over-read manual prose.

Effort: small.

Architecture impact: low.

Drift reduction: low to medium.

Reversibility: high.

## Recommendation

Use Option A immediately for post-0.5.0: add a minimal current-state freshness
gate after the S1-fix symptom repair. Keep Option B as the likely better
post-0.6.0 architecture direction if drift recurs. Option C alone is
insufficient because the current failure affected active next-step guidance, not
just explanatory wording.

## S1-fix Scope Recommendation

The next slice should only repair current stale symptoms:

- Update the active `docs/STATUS.md` current slice/next-step lines to remove
  pre-release `0.5.0` publication instructions.
- Refresh current verified main wording only if the repository chooses to treat
  PR #2001 as current admin head rather than preserving PR #2000 as the last
  substantive state.
- Do not manually patch generated successor package files.
- Use existing handoff/admin refresh commands for generated handoff surfaces.
- Leave `PROJECT_DIRECTION.meta.updated_after_pr` unchanged unless a safe
  current authority is established for what the field means.

## Maintainer Decision Point

S1 exposes one real decision:

Recommended decision: proceed with S1-fix and Option A minimal freshness gate in
follow-up slices. Do not start a full DP4 generated status migration yet.

No Block-B website work should begin before S1-fix and the command-surface
slices clarify which command/manifest projections are canonical.
