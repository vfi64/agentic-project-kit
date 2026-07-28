# DP1 Probe Backlog

Status: active

Status-date: 2026-07-27

Authority: DPA-300 through DPA-900; DPA-ADR-015, DPA-ADR-016, DPA-ADR-017,
DPA-ADR-021

## 1. Purpose

This backlog records the Probe families that remain to be executed against the
actual `vfi64/agentic-project-kit` repository before DPA implementation,
controlled import, stable promotion or production conformance can be claimed.

Discovery evidence is non-normative. Probe evidence may confirm or falsify an
implementation mapping, but it MUST NOT silently create architecture.

This file is synchronized to the DPA-800 Probe family names. The older
2026-07-15 backlog labels for finding, gate, concurrency and rollback probes
are superseded. Their concerns are preserved under the current DPA-800 Probe
families below.

## 2. Entry conditions

A Probe item may execute only when:

- its governing specification is `review-ready` or later;
- the exact main-repository validation ref is recorded;
- the local confirmation ref is recorded when execution is local;
- proposed serialized contracts and expected results are explicit;
- the Probe is bounded and reproducible;
- mutation is absent or separately authorized by the implementation phase;
- output is committed as evidence;
- cleanup and rollback are explicit.

Probe preparation may occur remotely. Probe execution requires a suitable local
environment and exact refs.

## 3. Canonical active Probe families

| Probe | Current DPA-800 scope | Preserved older backlog concerns |
|---|---|---|
| PROBE-001 | Registry, projection-contract and partition-contract compatibility | registry parser, validator, manual-entry compatibility |
| PROBE-002 | Lifecycle, plan, lock, Write, Verify, acceptance-state, recovery, re-acceptance, layered acceptance and writer routing | lifecycle findings, gate identity, CI compatibility, writer inventory |
| Renderer Probes | Renderer-map resolution, deterministic output, purity, capability restrictions, semantic versions, operational aborts and bounded failure diagnostics | renderer behavior and side-effect boundaries |
| PROBE-003 | DPA-600 branch-context, pull-request, integration and post-integration serialization behavior | former concurrency and serialization compatibility |
| PROBE-004 | DPA-700 migration-form, rollback-package and renderer semantic-version rollback behavior | former rollback-input sufficiency and generated-output handling |

`integration/DP1_PROBE_MANUALS_20260727.md` owns the current execution-manual
detail for these Probe families.
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md` owns the current
execution-package draft for preflight commands, evidence layout and missing
fixture gates.

Current read-only Kit validation for candidate source/test surfaces and
generated-output command contracts is recorded in
`evidence/repo-facts/CURRENT-MAIN-VALIDATION-C788A8C5-20260727.md` at
`vfi64/agentic-project-kit@c788a8c530eb0984d088a86e8e7951145581abbe`.
It supports Probe preparation only. It is not Probe execution and does not close
writer-set completeness. It records refresh-only successor-package freshness for
current Kit `main`. The current
static `CURRENT_HANDOFF.md` reader/writer
graph is recorded in
`evidence/repo-facts/CURRENT-HANDOFF-READER-WRITER-GRAPH-C788A8C5-20260727.md`.
It identifies source-level write-capable paths for planning, but still requires
Probe-selected fixture coverage or explicit out-of-scope adjudication.
The current planning matrix for that conversion is
`integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`.
Sandbox-only selected-writer mutation evidence is recorded in
`evidence/probes/dp1-mutation-sandbox-c788a8c5-20260727/` with result
`PARTIAL`. It is feasibility evidence only. It does not close full Probe PASS,
Kit import, production mutation or main-repository conformance, and WRT-CH-003
plus the full administrative refresh PR flow remain open for Maintainer
adjudication or later fixture execution.

## 4. Active backlog items

### PROBE-001 - Registry projection and partition compatibility

Evidence source:

- `evidence/repo-facts/DP1-DISC-001-REGISTRY-6A9DA7D.md`

Governing contracts:

- DPA-300;
- DPA-800 §10 and §11;
- ADR-017.

Question: Can the real registry parser and validator represent optional
`ProjectionContract` and parent-entry `PartitionContract` structures without
breaking manual entries or weakening validation?

Current candidate surfaces are recorded in the current-main validation record.
Executable fixtures remain pending.

### PROBE-002 - Lifecycle, acceptance and writer-routing compatibility

Evidence sources:

- DISC-002 reader graph;
- DISC-003 writer graph;
- DISC-003 correction and DISC-003b resolution;
- DISC-004 authority inputs;
- DISC-005 lifecycle findings;
- DISC-006 lifecycle mutation;
- DISC-007 Workspace;
- DISC-008 locking/concurrency;
- DISC-009 gates and CI;
- DISC-010 history/rollback.

Mandatory writer revalidation:

Current static evidence at `c788a8c5...` identifies write-capable
`CURRENT_HANDOFF.md` paths through:

- administrative post-PR handoff refresh:
  `transfer_repo_actions._refresh_operational_handoff_docs()`;
- release preparation:
  `release_prepare.prepare_release(..., dry_run=False)`;
- post-release DOI metadata closeout:
  `post_release_closeout.post_release_doi_closeout(..., write=True)`;
- action-spec surfaced release/finalize mutations:
  `action_specs.py`;
- generated workspace initialization templates:
  `workspace_init.execute_workspace_init()`.

DISC-003b establishes that the inspected `transfer chat-switch-complete` path
does not write `CURRENT_HANDOFF.md` at the recorded Discovery ref. The Probe
MUST rebuild the writer inventory at its own validation ref and include every
then-known selected writer, or record why a writer class is outside the first
DP2 target scope. The workspace-initialization template writer is not a current
self-hosting handoff refresh writer, but remains relevant to namespace/profile
and external-habitability planning.

Governing contracts:

- DPA-300;
- DPA-500;
- DPA-800 §10 and §12;
- ADR-016;
- ADR-021.

Question: Can the main repository lifecycle, Workspace, writer, acceptance-state
and gate mechanisms carry DPA-owned projection behavior without a parallel DPA
writer, state store, evidence authority or gate system?

Current candidate lifecycle, Workspace and writer-routing surfaces are recorded
in the current-main validation record and the current handoff reader/writer
graph record. Converting that graph into executable selected-writer fixtures
remains open; the current selected-writer fixture plan records the required
writer dispositions and fixture families.

### Renderer Probes - Renderer boundary and determinism

Evidence sources:

- DPA-400 renderer boundary;
- current main-repository renderer-map discovery at the Probe validation ref.

Governing contracts:

- DPA-400;
- DPA-800 §10 and §13;
- ADR-019.

Question: Can renderer identity, immutable input snapshots, deterministic output
and capability restrictions be tested without granting the renderer write,
network, subprocess, workflow, state or evidence authority?

Current GUI renderer-like paths are candidate boundary evidence only; no DPA
renderer identity is approved.

### PROBE-003 - Workflow serialization compatibility

Evidence source:

- DISC-008 locking/concurrency.

Governing contracts:

- DPA-600;
- DPA-800 §10 and §14.

Question: Can branch, pull-request, integration and post-integration workflows
implement DPA-600 freshness and serialization without conflating local locks
with cross-PR or integration authority?

Current transfer, gatekeeper, local-feature-gate, lock and freshness candidate
surfaces are recorded in the current-main validation record.

### PROBE-004 - Migration and rollback sufficiency

Evidence source:

- DISC-010 history/rollback.

Governing contracts:

- DPA-700;
- DPA-800 §10 and §15.

Question: Are Git and repository inputs sufficient for migration and rollback
without a new canonical history source, automatic historical-prose merge or
durable manual patching of command-generated or command-updated Kit outputs?

Current successor-handoff generated-output and freshness contracts are recorded
in the current-main validation record. Disposable rollback fixtures remain
pending.

## 5. Review boundary

The Discovery set is complete for the recorded historical scope after
DISC-003b. Current static writer graph preparation is recorded at `c788a8c5...`,
but global dynamic writer-set completeness is not claimed and must be
revalidated at Probe time.

This backlog is not Probe evidence, not implementation evidence, not a Kit
import plan and not a main-repository conformance claim.
