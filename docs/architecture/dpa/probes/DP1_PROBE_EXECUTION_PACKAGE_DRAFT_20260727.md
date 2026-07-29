# DP1 Probe Execution Package Draft

Status: prepared-provisional

Status-date: 2026-07-27

Authority: DPA-300 through DPA-900; current Kit validation record
`evidence/repo-facts/CURRENT-MAIN-VALIDATION-C788A8C5-20260727.md`
and current `CURRENT_HANDOFF.md` reader/writer graph record
`evidence/repo-facts/CURRENT-HANDOFF-READER-WRITER-GRAPH-C788A8C5-20260727.md`
plus selected-writer fixture plan
`integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`; prepared fixture
manifest
`integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`; cleanup
and Assessment plan
`integration/probe-fixtures/DP1_PROBE_CLEANUP_AND_ASSESSMENT_PLAN_20260727.md`

## 1. Scope

This draft converts the current DPA Probe manuals into a concrete execution
package shape for later local work in `vfi64/agentic-project-kit`.

It is not Probe execution, not Kit import, not production mutation, not
implementation evidence and not main-repository conformance evidence. Existing
Kit commands and tests named here are command-surface and fixture-planning
inputs only. A future Probe run MUST freeze a fresh exact ref and may replace
any command here when the command manifest or repository state has changed.

## 2. Current planning anchor

| Field | Value |
|---|---|
| Kit planning ref | `c788a8c530eb0984d088a86e8e7951145581abbe` |
| Historical DP1 Discovery baseline | `6a9da7d363ae3f97f347b79a2679f6f848d8cdf3` |
| Command manifest acknowledgement | `COMMAND_MANIFEST_ACK 8610cfd2990a` |
| Current Kit branch state | local `main` equals `origin/main`; ahead 0, behind 0 |
| Current Kit worktree | clean |
| Current package freshness | `PASS_REFRESH_ONLY`: checked-in `validation_report.generated_head=70403d...`; the diff from `70403d...` to `c788a8c5...` changes only administrative handoff refresh artifacts |
| Refresh candidate | resolved by Kit PR #1877 on `main` |

## 3. Common preflight commands

Before any Probe run, the operator MUST rerun the command-reference check and
record the current manifest acknowledgement. Commands below are current planning
candidates only:

```bash
git fetch origin main --prune
git switch main
git status --short
git rev-parse HEAD
git rev-parse origin/main
./.venv/bin/agentic-kit transfer divergence-status --json
./.venv/bin/agentic-kit transfer repo-status --json
./.venv/bin/agentic-kit transfer command-reference-check --json
./.venv/bin/agentic-kit check-docs
./.venv/bin/agentic-kit doctor
./.venv/bin/agentic-kit handoff check
```

`agentic-kit handoff post-merge-refresh-status` is manifest-classified as
`DESTRUCTIVE` at the current planning ref and is not part of the read-only
preflight package.

## 4. Evidence package layout

A later Probe run SHOULD write a bounded evidence package using this shape, or
record why the selected Kit evidence policy requires a different shape:

```text
docs/architecture/evidence/dpa/probes/<probe-id>-<validation-short>-<date>/
  README.md
  command-manifest.md
  preflight.json
  fixture-plan.md
  results.json
  terminal.log
  cleanup.md
  assessment-input.md
```

The Lab-side mirror, if needed before controlled import, is:

```text
evidence/probes/<probe-id>-<validation-short>-<date>/
```

Evidence MUST be narrow enough to review, must not include credentials or
private runtime state, and must preserve cleanup/rollback status for every
mutable fixture.

For selected-writer cases, the evidence package SHOULD also include
`selected-writers.json`, `writer-dispositions.md` and
`writer-fixture-results.json`, as defined by
`integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`.

Prepared fixture IDs, mutation scopes, authorization requirements and cleanup
plan IDs are materialized in
`integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`. That
manifest remains `NOT_RUN` evidence until a later authorized Probe execution
records results.

Read-only baseline execution evidence is recorded in
`evidence/probes/dp1-readonly-c788a8c5-20260727/` with result
`PASS_WITH_LIMITATIONS`. It exercises read-only and bounded baseline commands
only. Mutation-scoped fixture cases remain `NOT_RUN`, and the evidence must not
be cited as full Probe PASS or main-repository conformance.

Sandbox-only selected-writer mutation evidence is recorded in
`evidence/probes/dp1-mutation-sandbox-c788a8c5-20260727/` with result
`PARTIAL`. It exercises bounded writer-adjacent commands only in a temporary
local Kit clone or temporary generated-output root. It covers WRT-CH-001
component handoff-state refresh, WRT-CH-002 release metadata writes,
WRT-CH-004 release-authority surfaced mutations, WRT-CH-005 external workspace
initialization and WRT-CH-006 generated successor-package routes. WRT-CH-003
and the full WRT-CH-001 administrative refresh PR flow remain unexecuted. This
evidence must not be cited as full Probe PASS, Kit import, production mutation
or main-repository conformance.

## 5. Probe command matrix

### PROBE-001 - Registry compatibility

Current source/test candidates:

- `src/agentic_project_kit/documentation_registry.py`;
- `src/agentic_project_kit/cli_commands/doc_registry.py`;
- `docs/DOCUMENTATION_REGISTRY.yaml`;
- `tests/test_documentation_registry.py`;
- `tests/test_doc_mesh.py`.

Current executable preflight candidates:

```bash
./.venv/bin/agentic-kit docs-registry
./.venv/bin/agentic-kit doc-registry check-unregistered --json
./.venv/bin/python -m pytest -q tests/test_documentation_registry.py tests/test_doc_mesh.py
```

Missing before execution:

- fixture entries for optional `ProjectionContract`;
- fixture entries for parent-entry `PartitionContract`;
- negative fixtures for unknown schema version, unknown field, missing required
  fields and dangling registered-region references;
- exact assertion that existing manual entries remain accepted.

### PROBE-002 - Lifecycle, acceptance and writer routing

Current source/test candidates:

- `src/agentic_project_kit/doc_lifecycle.py`;
- `src/agentic_project_kit/doc_lifecycle_sweep.py`;
- `src/agentic_project_kit/cli_commands/docs.py`;
- `src/agentic_project_kit/workspace.py`;
- `src/agentic_project_kit/workspace_lock.py`;
- `src/agentic_project_kit/transfer_repo_actions.py`;
- `src/agentic_project_kit/release_prepare.py`;
- `src/agentic_project_kit/post_release_closeout.py`;
- `src/agentic_project_kit/action_specs.py`;
- `src/agentic_project_kit/dpa_workspace_init_projection.py`;
- `src/agentic_project_kit/templates.py`;
- `src/agentic_project_kit/workspace_init.py`;
- `tests/test_doc_lifecycle.py`;
- `tests/test_docs_lifecycle_*.py`;
- `tests/test_transfer_repo_actions.py`;
- `tests/test_release_prepare_command.py`;
- `tests/test_release_command_authority.py`;
- `tests/test_release_prep_core.py`;
- `tests/test_post_release.py`;
- `tests/test_post_release_doi_closeout_atomicity.py`;
- `tests/test_action_specs.py`;
- `tests/test_generator.py`;
- `tests/test_workspace_init.py`.

Current executable preflight candidates:

```bash
./.venv/bin/agentic-kit docs lifecycle plan --scope docs/handoff --json
./.venv/bin/agentic-kit docs lifecycle triage --json
./.venv/bin/agentic-kit docs lifecycle report --scope docs/handoff --json
./.venv/bin/python -m pytest -q tests/test_doc_lifecycle.py tests/test_docs_lifecycle_cli.py tests/test_docs_lifecycle_apply_cli.py tests/test_docs_lifecycle_plan_cli.py tests/test_docs_lifecycle_report_cli.py tests/test_transfer_repo_actions.py
./.venv/bin/python -m pytest -q tests/test_release_prepare_command.py tests/test_release_command_authority.py tests/test_release_prep_core.py tests/test_post_release.py tests/test_post_release_doi_closeout_atomicity.py tests/test_action_specs.py tests/test_generator.py tests/test_workspace_init.py
```

Missing before execution:

- DPA lifecycle plan fixtures with source, target, base, contract, renderer,
  partition and ownership fingerprints;
- stale-plan rejection fixtures for Write, under-lock and acceptance-bearing
  evidence publication;
- acceptance-state, tamper, recovery, re-acceptance and layered-acceptance
  fixtures;
- selected-writer fixtures or explicit out-of-scope adjudication for the
  current static `CURRENT_HANDOFF.md` writer graph, including administrative
  post-PR refresh, release preparation, post-release DOI closeout,
  action-spec surfaced release/finalize mutations and generated workspace
  initialization template behavior. The current planning matrix is
  `integration/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md`.

The workspace-initialization template writer is not a current self-hosting
handoff refresh writer, but it remains a namespace/profile and
external-habitability concern.

### Renderer Probes

Current source/test candidates:

- `src/agentic_project_kit/gui_tkinter_renderer.py`;
- `src/agentic_project_kit/gui_action_renderer.py`;
- `tests/test_v040_gui_tkinter_renderer.py`;
- `tests/test_v040_gui_dry_run_renderer_integration.py`;
- `tests/test_v040_gui_action_renderer.py`.

Current executable boundary-smoke candidates:

```bash
./.venv/bin/python -m pytest -q tests/test_v040_gui_tkinter_renderer.py tests/test_v040_gui_dry_run_renderer_integration.py tests/test_v040_gui_action_renderer.py
```

Missing before execution:

- approved DPA renderer-map location;
- DPA renderer identity and interface-version fixtures;
- semantic-version mismatch fixtures;
- implementation-evidence-only change fixtures;
- immutable lifecycle-resolved input snapshot fixtures;
- deterministic repeat-output fixtures;
- output type and target-scope fixtures;
- side-effect prohibition fixtures for filesystem, network, subprocess,
  workflow, state, evidence and nested-renderer behavior.
- deterministic semantic resource bound, operational abort and bounded failure
  diagnostic fixtures.

The observed GUI renderer tests are not DPA renderer conformance tests.

### PROBE-003 - Workflow serialization

Current source/test candidates:

- `src/agentic_project_kit/transfer_repo_actions.py`;
- `src/agentic_project_kit/gatekeeper_core.py`;
- `src/agentic_project_kit/local_feature_gate.py`;
- `src/agentic_project_kit/workspace_lock.py`;
- `src/agentic_project_kit/handoff_freshness.py`;
- `tests/test_transfer_repo_actions.py`;
- `tests/test_gatekeeper_core.py`;
- `tests/test_local_feature_gate_contract.py`;
- `tests/test_handoff_freshness.py`.

Current executable preflight candidates:

```bash
./.venv/bin/agentic-kit transfer divergence-status --json
./.venv/bin/agentic-kit transfer repo-status --json
./.venv/bin/python -m pytest -q tests/test_transfer_repo_actions.py tests/test_gatekeeper_core.py tests/test_local_feature_gate_contract.py tests/test_handoff_freshness.py
```

Missing before execution:

- disposable branch/worktree/ref identity fixtures;
- branch switch and rebase/reset stale-plan rejection fixtures;
- pull-request head/base and required-check identity fixtures;
- integration-time revalidation fixtures;
- acceptance-bearing evidence publication stale-identity rejection fixtures;
- competing projection refresh conflict fixtures.

Any fixture that creates branches, opens PRs, pushes or mutates repository state
requires Maintainer authorization and rollback instructions before execution.

### PROBE-004 - Migration and rollback

Current source/test candidates:

- Git exact-ref history;
- `src/agentic_project_kit/successor_handoff_package.py`;
- `src/agentic_project_kit/transfer_repo_actions.py`;
- `docs/reports/handoff-packages/latest/execution_contract.json`;
- `docs/reports/handoff-packages/latest/source_manifest.json`;
- `docs/reports/handoff-packages/latest/validation_report.json`;
- `tests/test_successor_handoff_package.py`;
- `tests/test_transfer_repo_actions.py`.

Current executable preflight candidates:

```bash
./.venv/bin/agentic-kit handoff check
./.venv/bin/python -m pytest -q tests/test_successor_handoff_package.py tests/test_transfer_repo_actions.py
```

Missing before execution:

- migration-form selection fixtures, including `no migration`;
- rollback package capture fixtures;
- exact-byte rollback fixtures before Write, after Write and after acceptance;
- acceptance invalidation fixtures when renderer reproducibility is unavailable;
- renderer semantic-version rollback fixtures;
- interrupted migration recovery fixtures;
- generated or command-updated output fixtures that prove source/generator or
  command-contract handling.

No public read-only command was identified that emits the same detailed
successor-package freshness notes as the internal helper used during current
validation. A future Probe package should either rely on an existing public
command with sufficient output, add a reviewed read-only wrapper before Probe
execution, or record Maintainer authorization for the internal helper as
diagnostic evidence.

## 6. Current diagnostic command observations

The following commands were run read-only at Kit ref
`c788a8c530eb0984d088a86e8e7951145581abbe` while refreshing this package:

| Command | Result | Notable output |
|---|---|---|
| `agentic-kit transfer divergence-status --json` | PASS | branch `main`; `HEAD` equals `origin/main`; ahead 0; behind 0 |
| `agentic-kit transfer repo-status --json` | PASS | worktree clean |
| `agentic-kit transfer command-reference-check --json` | PASS | underlying command-reference tests: 2 passed |
| `agentic-kit handoff check` | PASS | persistent handoff state check passed; registry has 100 documents; `broad_migration_allowed: False` |
| `agentic-kit docs-registry` | PASS | 100 registered documents; 3 generated artifacts; 66 unregistered candidates exempted by policy |
| `agentic-kit doc-registry check-unregistered --json` | PASS | `candidate_count: 0`; `scope_violation_count: 0` |
| `agentic-kit docs lifecycle plan --scope docs/handoff --json` | PASS | dry-run only; advisory/header/manual-review findings remain non-mutating |
| `agentic-kit docs lifecycle report --scope docs/handoff --json` | PASS | dry-run only; `mutation: none`; `safe_to_continue: true`; would write only with `--execute` |

These results support command-package preparation only. They do not satisfy
PROBE-001 through PROBE-004 or renderer Probe obligations.
They record that the generated successor-package freshness blocker observed at
`70403d...` is resolved on Kit `main`.

The later read-only baseline run in
`evidence/probes/dp1-readonly-c788a8c5-20260727/` re-executed the prepared
baseline command set and records 21 passing commands, exact ref preservation and
clean Kit worktree before and after.

## 7. Stop states

Return `BLOCKED` rather than executing a Probe when:

- current `origin/main`, local `HEAD` or command manifest differs from the
  recorded execution package and the package has not been refreshed;
- the checked-in generated successor package is not exact or accepted as
  refresh-only-fresh for the selected Probe validation ref;
- a required fixture file does not exist;
- a command is absent from the current manifest or its safety class changed;
- an existing command would mutate non-disposable state;
- a generated or command-updated output would need manual target-byte patching;
- cleanup cannot return the repository to a clean state;
- evidence cannot be bounded to the exact validation ref and selected Probe
  family.

## 8. Remaining package work

Before full DP1 Probe execution can begin, the Lab or Kit must still provide:

1. Maintainer adjudication of the sandbox-only mutation evidence;
2. final exact execution-ref confirmation for any remaining non-sandbox
   mutation-scoped fixture execution;
3. exact evidence path selection for remaining mutation-scoped fixture families;
4. Maintainer authorization for any additional mutable/disposable Probe;
5. Maintainer out-of-scope adjudication for any selected writer not executed;
6. Probe execution and Assessment entries for every PASS, FAIL, PARTIAL or
   BLOCKED result.
