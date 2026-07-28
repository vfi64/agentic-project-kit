# DP1 Probe Manuals

Status: prepared-provisional

Status-date: 2026-07-27

Authority: DPA-300 through DPA-900; DPA-ADR-015, DPA-ADR-016, DPA-ADR-017,
DPA-ADR-019, DPA-ADR-021

## 1. Scope

This file prepares execution manuals for the Probe families required by DPA-800
and DPA-900:

- PROBE-001;
- PROBE-002;
- Renderer Probes;
- PROBE-003;
- PROBE-004.

The manuals are prepared for later exact-ref local execution. They are not
Probe execution, not evidence, not implementation, not controlled import and not
main-repository conformance.

The current Kit ref, candidate command families, candidate source/test surfaces
and generated-output source contracts are recorded in
`evidence/repo-facts/CURRENT-MAIN-VALIDATION-C788A8C5-20260727.md`.
The current static `CURRENT_HANDOFF.md` reader/writer graph is recorded in
`evidence/repo-facts/CURRENT-HANDOFF-READER-WRITER-GRAPH-C788A8C5-20260727.md`.
The current selected-writer fixture and out-of-scope planning matrix is
`integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`.
The prepared fixture manifest and cleanup/Assessment plan are
`integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json` and
`integration/probe-fixtures/DP1_PROBE_CLEANUP_AND_ASSESSMENT_PLAN_20260727.md`.
The executable Probe command package is drafted; final command freeze, manifest
revision freeze, evidence paths and authorization records remain open until a
later Probe package refreshes them at the selected Probe validation ref.

The current execution-package draft is
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.

## 2. Common ref sheet

Every Probe execution record MUST fill this sheet before any command is run:

| Field | Value |
|---|---|
| Repository | `vfi64/agentic-project-kit` |
| Historical evidence ref | `6a9da7d363ae3f97f347b79a2679f6f848d8cdf3` |
| Current remote revalidation ref | `c788a8c530eb0984d088a86e8e7951145581abbe` |
| Local confirmation ref | `c788a8c530eb0984d088a86e8e7951145581abbe` |
| Probe validation ref | `NEEDS_PROBE_EXECUTION_REF` |
| Fixture revision | `NEEDS_PROBE_FIXTURE_COMMIT` |
| Evidence path | `evidence/probes/NEEDS_PROBE_RUN_ID/` |
| Cleanup path | `NEEDS_PROBE_CLEANUP_PLAN` |
| Operator | `NEEDS_MAINTAINER_OR_OPERATOR_RECORD` |

One exact commit MAY carry multiple roles only when the execution record names
every role, scope and limitation explicitly.

## 2A. Current Kit command and generated-output evidence

The current read-only validation at
`c788a8c530eb0984d088a86e8e7951145581abbe` records:

- Kit command-manifest acknowledgement
  `COMMAND_MANIFEST_ACK 8610cfd2990a`;
- `agentic-kit check-docs` passed;
- `agentic-kit doctor` returned `Overall: PASS`, with 45 report-only document
  lifecycle audit warnings and version drift matching `0.4.13`;
- successor handoff package validation status is `PASS`, with
  `generated_head=70403d1906ce4788dca0c72b2ea133aa78a74f3b`;
- the diff from `70403d...` to `c788a8c5...` touches only administrative
  handoff refresh artifacts, so the generated package is refresh-only current
  for Kit `main`;
- generated handoff projections and latest successor package files are governed
  by `successor_handoff_package.py`, machine-readable package files and the
  generator command contract.

Generated or command-updated Kit output relevant to DPA MUST be treated as
source/generator/command-contract work. Durable manual target-byte patching is
blocked unless the Maintainer records an explicit temporary repair and later
source-of-truth correction.

At the same ref, `docs/handoff/CURRENT_HANDOFF.md` is not a generated successor
package projection, but it is command-updated. Static source inspection
identifies write-capable paths through administrative post-PR handoff refresh,
release preparation, post-release DOI closeout, action-spec surfaced
release/finalize mutations and generated workspace initialization templates.
PROBE-002 must turn the selected subset of those writer paths into executable
fixtures or record explicit out-of-scope adjudication. The current matrix
prepares those obligations but does not execute or approve them.

## 2B. Candidate source and test surfaces

These current-ref paths may be used to prepare executable Probe fixtures. They
are not sufficient evidence until a later Probe run freezes exact commands,
fixture revisions, evidence paths and cleanup.

| Probe | Candidate sources | Candidate tests or checks |
|---|---|---|
| PROBE-001 | `src/agentic_project_kit/documentation_registry.py`; `src/agentic_project_kit/cli_commands/doc_registry.py`; `docs/DOCUMENTATION_REGISTRY.yaml` | `tests/test_documentation_registry.py`; `tests/test_doc_mesh.py`; `agentic-kit docs-registry`; `agentic-kit doc-registry check-unregistered` |
| PROBE-002 | `src/agentic_project_kit/doc_lifecycle.py`; `src/agentic_project_kit/doc_lifecycle_sweep.py`; `src/agentic_project_kit/cli_commands/docs.py`; `src/agentic_project_kit/workspace.py`; `src/agentic_project_kit/workspace_lock.py`; `src/agentic_project_kit/transfer_repo_actions.py`; `src/agentic_project_kit/release_prepare.py`; `src/agentic_project_kit/post_release_closeout.py`; `src/agentic_project_kit/action_specs.py`; `src/agentic_project_kit/workspace_init.py` | `tests/test_doc_lifecycle.py`; `tests/test_docs_lifecycle_*.py`; `tests/test_transfer_repo_actions.py`; `tests/test_release_prepare_command.py`; `tests/test_release_command_authority.py`; `tests/test_release_prep_core.py`; `tests/test_post_release.py`; `tests/test_post_release_doi_closeout_atomicity.py`; `tests/test_action_specs.py`; `agentic-kit docs lifecycle plan`; `agentic-kit docs lifecycle triage`; `agentic-kit docs lifecycle report` |
| Renderer Probes | `src/agentic_project_kit/gui_tkinter_renderer.py`; `src/agentic_project_kit/gui_action_renderer.py`; any later DPA renderer map | `tests/test_v040_gui_tkinter_renderer.py`; `tests/test_v040_gui_dry_run_renderer_integration.py`; `tests/test_v040_gui_action_renderer.py` |
| PROBE-003 | `src/agentic_project_kit/transfer_repo_actions.py`; `src/agentic_project_kit/gatekeeper_core.py`; `src/agentic_project_kit/local_feature_gate.py`; `src/agentic_project_kit/workspace_lock.py`; `src/agentic_project_kit/handoff_freshness.py` | `tests/test_transfer_repo_actions.py`; `tests/test_gatekeeper_core.py`; `tests/test_local_feature_gate_contract.py`; `tests/test_handoff_freshness.py`; `agentic-kit transfer divergence-status`; `agentic-kit transfer repo-status` |
| PROBE-004 | Git exact-ref history; `src/agentic_project_kit/transfer_repo_actions.py`; successor-package freshness helpers; generated-output contracts | `tests/test_transfer_repo_actions.py` successor-package freshness cases; later disposable rollback fixtures |

Observed GUI renderers are candidate boundary evidence only. They are not
approved DPA renderer identities.

## 3. Common stop states

Return `BLOCKED` rather than continuing when:

- the current remote ref cannot be recorded;
- local confirmation does not match the intended validation ref;
- a required command, parser, writer, renderer or fixture path cannot be
  identified from repository evidence;
- a Probe would mutate production state;
- a generated or command-updated Kit output would need a durable manual patch;
- cleanup or rollback cannot be bounded;
- evidence would be broader than the exact ref under test.

## 4. Common result vocabulary

| Result | Meaning |
|---|---|
| PASS | All required cases for the bounded Probe family match expected behavior at the exact validation ref. |
| FAIL | At least one required case contradicts the governing DPA contract. |
| PARTIAL | Some cases ran, but coverage is incomplete or a non-blocking fixture limitation remains. |
| BLOCKED | Execution could not start or continue without violating a precondition. |

Every non-PASS result requires Assessment classification before implementation
or import decisions rely on it.

## 5. PROBE-001 manual - Registry compatibility

Purpose: test registry parser and validator compatibility for optional
projection and partition contracts.

Required fixture groups:

1. existing manual registry entries unchanged;
2. valid optional `ProjectionContract`;
3. valid parent-entry `PartitionContract`;
4. unknown projection schema version;
5. unknown projection field;
6. missing required projection field;
7. missing, dangling or inconsistent registered-region reference;
8. unsupported target-semantics and partition combination.

Candidate current-ref Kit surfaces:

- `src/agentic_project_kit/documentation_registry.py`;
- `src/agentic_project_kit/cli_commands/doc_registry.py`;
- `docs/DOCUMENTATION_REGISTRY.yaml`;
- `tests/test_documentation_registry.py`;
- `tests/test_doc_mesh.py`.

Candidate preflight commands are listed in
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.

PASS requires valid fixtures to parse and validate as expected, invalid fixtures
to fail loud, and existing manual entries to remain accepted.

## 6. PROBE-002 manual - Lifecycle, acceptance and writer routing

Purpose: test lifecycle-owned planning, writing, verification, acceptance,
recovery, re-acceptance, layered acceptance, finding and gate behavior without a
parallel DPA runtime authority.

Required fixture groups:

1. immutable plan capture;
2. source, target, base, contract, renderer, partition and ownership guards;
3. local Workspace lock and same-process reentrancy rejection;
4. stale-plan rejection before Write and under lock;
5. atomic complete-target or partition-preserving replacement;
6. post-Write verification;
7. acceptance-state creation, tamper detection and scope validation;
8. conditional accepted-base persistence;
9. base-independent post-acceptance evaluation;
10. gate-set re-acceptance without renderer invocation or target mutation;
11. layered acceptance for registered-region projections;
12. lifecycle finding and severity compatibility;
13. every then-known selected writer for selected targets;
14. explicit out-of-scope adjudication for write-capable paths not covered by
    the first DP2 target.

Candidate current-ref Kit surfaces:

- `src/agentic_project_kit/doc_lifecycle.py`;
- `src/agentic_project_kit/doc_lifecycle_sweep.py`;
- `src/agentic_project_kit/cli_commands/docs.py`;
- `src/agentic_project_kit/workspace.py`;
- `src/agentic_project_kit/workspace_lock.py`;
- `src/agentic_project_kit/transfer_repo_actions.py`;
- `src/agentic_project_kit/release_prepare.py`;
- `src/agentic_project_kit/post_release_closeout.py`;
- `src/agentic_project_kit/action_specs.py`;
- `src/agentic_project_kit/workspace_init.py`;
- `tests/test_doc_lifecycle.py`;
- `tests/test_docs_lifecycle_*.py`;
- `tests/test_transfer_repo_actions.py`;
- `tests/test_release_prepare_command.py`;
- `tests/test_release_command_authority.py`;
- `tests/test_release_prep_core.py`;
- `tests/test_post_release.py`;
- `tests/test_post_release_doi_closeout_atomicity.py`;
- `tests/test_action_specs.py`.

Candidate preflight commands are listed in
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.
Selected-writer fixture obligations are mapped in
`integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`.

PASS requires every selected lifecycle case to satisfy DPA-300 and DPA-500
without a quick writer patch, parallel acceptance source or unbounded evidence
claim.

## 7. Renderer Probe manual

Purpose: test renderer identity, deterministic output, immutable inputs, purity
and failure diagnostics.

Required fixture groups:

1. static renderer-map resolution;
2. unknown renderer identifier;
3. duplicate or ambiguous renderer identifier;
4. interface-version incompatibility;
5. semantic-version mismatch;
6. immutable lifecycle-resolved input snapshot;
7. deterministic repeat execution;
8. output type and target scope;
9. filesystem, network, subprocess, lock, workflow, state and evidence write
   prohibition;
10. nested-renderer prohibition;
11. deterministic resource bounds;
12. non-semantic operational abort;
13. bounded failure diagnostics.

Candidate current-ref Kit surfaces:

- `src/agentic_project_kit/gui_tkinter_renderer.py`;
- `src/agentic_project_kit/gui_action_renderer.py`;
- `tests/test_v040_gui_tkinter_renderer.py`;
- `tests/test_v040_gui_dry_run_renderer_integration.py`;
- `tests/test_v040_gui_action_renderer.py`.

The current Kit GUI renderer paths do not by themselves define an approved DPA
renderer map.

Candidate boundary-smoke commands are listed in
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.

PASS requires renderer-boundary evidence only. It does not prove registry,
lifecycle, migration, strict-gate or production conformance.

## 8. PROBE-003 manual - Workflow serialization

Purpose: test DPA-600 branch, pull-request, integration and post-integration
serialization behavior.

Required fixture groups:

1. branch/worktree/ref identity capture;
2. branch switch stale-plan rejection;
3. rebase/reset stale-plan rejection;
4. pull-request head/base identity comparison;
5. required-check evidence bound to the exact PR head;
6. merge eligibility blocked by stale source, target, contract, renderer,
   ownership, partition, gate-set or base-context dependency;
7. integration-time revalidation before acceptance-bearing workflow completion;
8. clean textual Git merge rejected as projection-freshness evidence;
9. deterministic regeneration from current validation ref after stale-plan
   detection;
10. competing projection refresh conflict across shared targets or registered
   partitions;
11. post-integration refresh bound to the accepted integration ref.

Candidate current-ref Kit surfaces:

- `src/agentic_project_kit/transfer_repo_actions.py`;
- `src/agentic_project_kit/gatekeeper_core.py`;
- `src/agentic_project_kit/local_feature_gate.py`;
- `src/agentic_project_kit/workspace_lock.py`;
- `src/agentic_project_kit/handoff_freshness.py`;
- `tests/test_transfer_repo_actions.py`;
- `tests/test_gatekeeper_core.py`;
- `tests/test_local_feature_gate_contract.py`;
- `tests/test_handoff_freshness.py`.

Candidate preflight commands are listed in
`integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.

PASS requires workflow serialization evidence only. It does not prove that a
production merge queue already implements DPA-600.

## 9. PROBE-004 manual - Migration and rollback

Purpose: test DPA-700 migration-form selection, rollback-package recoverability
and renderer semantic-version rollback consequences.

Required fixture groups:

1. migration-form precondition evaluation, including `no migration`;
2. lower-risk migration-form rejection before hybrid or managed-head selection;
3. migration plan identity and rollback-package capture;
4. target bytes, registry/contracts, acceptance state, gate-set identity,
   writer/reader routing and exact-ref recoverability;
5. rollback before Write;
6. rollback after Write before acceptance;
7. rollback after acceptance with acceptance invalidation when renderer
   reproducibility is unavailable;
8. renderer semantic-version rollback with retained prior renderer;
9. fail-closed unavailable-renderer rollback paths;
10. interrupted migration recovery without inferring success from markers,
    historical prose or evidence alone;
11. no new canonical history source;
12. generated or command-updated candidate documents changed only through source
    authority, generator or command contract.

Candidate current-ref Kit surfaces:

- `src/agentic_project_kit/successor_handoff_package.py`;
- `src/agentic_project_kit/transfer_repo_actions.py`;
- `docs/reports/handoff-packages/latest/execution_contract.json`;
- `docs/reports/handoff-packages/latest/source_manifest.json`;
- `docs/reports/handoff-packages/latest/validation_report.json`;
- `tests/test_successor_handoff_package.py`;
- `tests/test_transfer_repo_actions.py`.

Candidate preflight commands and the public-readonly freshness-note gap are
listed in `integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.

PASS requires recoverability and fail-closed evidence for the bounded migration
scope. It does not select a production migration target without Assessment and
Maintainer adjudication.

## 10. Assessment handoff

After execution, each Probe family MUST hand off:

- exact refs and fixture identities;
- case-by-case results;
- discrepancy classification;
- evidence and bounded logs;
- cleanup/rollback confirmation;
- limitation statement;
- required architecture, implementation, fixture or evidence follow-up.

Assessment, not Probe execution alone, decides whether evidence supports DP2
entry, amendment, rerun, blocked status or no adoption.
