# Agentic-kit command reference

GENERATED FROM agentic-kit-commands.json — do not edit; manifest_sha: da49759e8d28

> Successor handoff contract note: the machine-readable successor execution contract is written to `docs/reports/handoff-packages/latest/execution_contract.json`. This generated command reference points to the contract instead of duplicating local-command rules.

- Schema version: `2`
- Source: `generated_from_typer_click_registry`
- Command count: `221`

## Commands

### `agentic-kit actions list`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit actions list.
- Dry-run available: `False`

_No parameters._

### `agentic-kit actions show`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit actions show.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `action_id` | `TyperArgument` | action_id | `True` |  |  |

### `agentic-kit artifact-gc`

- Safety: `BOUNDED`
- When to use: Dry-run by default garbage collector for transient communication artifacts.
- Dry-run available: `True`

Dry-run by default garbage collector for transient communication artifacts.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `tmp_logs` | `TyperOption` | --tmp-logs | `False` | `False` | Collect expired local tmp logs. |
| `local_tmp` | `TyperOption` | --local-tmp | `False` | `False` | Use repository-local tmp/ instead of /tmp for --tmp-logs. |
| `local_tmp_contents` | `TyperOption` | --local-tmp-contents | `False` | `False` | Collect expired untracked files and empty directories under repository-local tmp/. |
| `transfer_runs` | `TyperOption` | --transfer-runs | `False` | `False` | Collect expired docs/reports/transfer_runs files. |
| `report_retention` | `TyperOption` | --report-retention | `False` | `False` | Collect expired report-like files and generated successor-handoff Markdown under selected docs/report surfaces. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Actually delete candidates. Default is dry-run. |
| `ttl_seconds` | `TyperOption` | --ttl-seconds | `False` | `86400` | Retention age in seconds for age-gated modes. |
| `older_than` | `TyperOption` | --older-than | `False` | `` | ISO date/datetime cutoff. Overrides --ttl-seconds for age-gated modes. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit audit-absolute-path-portability`

- Safety: `READ_ONLY`
- When to use: Audit absolute local paths that may break portability.
- Dry-run available: `False`

Audit absolute local paths that may break portability.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-command-manifest`

- Safety: `READ_ONLY`
- When to use: Audit command manifest hash, CLI coverage, safety metadata, and MD sync.
- Dry-run available: `False`

Audit command manifest hash, CLI coverage, safety metadata, and MD sync.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit audit-doc-currency`

- Safety: `READ_ONLY`
- When to use: Audit current release/documentation currency across handoff and release docs.
- Dry-run available: `False`

Audit current release/documentation currency across handoff and release docs.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-mutation-lock-coverage`

- Safety: `READ_ONLY`
- When to use: Audit mutating entrypoints for workspace mutation-lock coverage.
- Dry-run available: `False`

Audit mutating entrypoints for workspace mutation-lock coverage.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit JSON output. |

### `agentic-kit audit-ns-legacy-references`

- Safety: `READ_ONLY`
- When to use: Audit remaining legacy ./ns/ns-menu/ns_release references.
- Dry-run available: `False`

Audit remaining legacy ./ns/ns-menu/ns_release references.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-patch-failure-discipline`

- Safety: `READ_ONLY`
- When to use: Audit whether repeated patch failures were followed by diagnosis evidence.
- Dry-run available: `False`

Audit whether repeated patch failures were followed by diagnosis evidence.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `include_tmp` | `TyperOption` | --include-tmp | `False` | `False` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-path-literals`

- Safety: `READ_ONLY`
- When to use: Report hardcoded docs/tmp path literals in source modules.
- Dry-run available: `False`

Report hardcoded docs/tmp path literals in source modules.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |
| `enforce_active` | `TyperOption` | --enforce-active | `False` | `False` | Fail when active path or repository identity literals remain. |

### `agentic-kit audit-planning-docs-consolidation`

- Safety: `READ_ONLY`
- When to use: Audit planning and handoff docs for consolidation candidates.
- Dry-run available: `False`

Audit planning and handoff docs for consolidation candidates.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-program-redundancy`

- Safety: `READ_ONLY`
- When to use: Audit source for risky bug/redundancy patterns.
- Dry-run available: `False`

Audit source for risky bug/redundancy patterns.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit audit-status-current-state`

- Safety: `READ_ONLY`
- When to use: Audit STATUS.md current-state claims against handoff, release, and origin/main state.
- Dry-run available: `False`

Audit STATUS.md current-state claims against handoff, release, and origin/main state.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `max_origin_lag` | `TyperOption` | --max-origin-lag | `False` | `3` | Maximum commits the validated substantive safe-state may trail origin/main. |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit boot check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit boot check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `.` |  |

### `agentic-kit boot closeout`

- Safety: `BOUNDED`
- When to use: Run agentic-kit boot closeout.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `.` |  |

### `agentic-kit boot prompt`

- Safety: `BOUNDED`
- When to use: Run agentic-kit boot prompt.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `.` |  |

### `agentic-kit boot report`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit boot report.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `.` |  |
| `path` | `TyperOption` | --path | `False` | `` |  |

### `agentic-kit boot write`

- Safety: `BOUNDED`
- When to use: Run agentic-kit boot write.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `docs/handoff/NEXT_CHAT_BOOTSTRAP.md` |  |
| `root` | `TyperOption` | --root | `False` | `.` |  |
| `include_state` | `TyperOption` | --include-state, --no-include-state | `False` | `False` |  |

### `agentic-kit chat refresher`

- Safety: `READ_ONLY`
- When to use: Render the compact six-line command manifest refresher.
- Dry-run available: `False`

Render the compact six-line command manifest refresher.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `mode` | `TyperOption` | --mode | `False` | `copy-paste` | copy-paste, remote, or file-transfer. |

### `agentic-kit chat session-start`

- Safety: `READ_ONLY`
- When to use: Render the session-start refresher and full inline command list.
- Dry-run available: `False`

Render the session-start refresher and full inline command list.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `mode` | `TyperOption` | --mode | `False` | `copy-paste` | copy-paste, remote, or file-transfer. |

### `agentic-kit check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit check-docs`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit check-docs.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit check-todo`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit check-todo.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit cockpit actions`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit cockpit actions.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON action inventory. |

### `agentic-kit cockpit gatekeeper-status`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit cockpit gatekeeper-status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON GUI gatekeeper status. |

### `agentic-kit cockpit run`

- Safety: `BOUNDED`
- When to use: Run agentic-kit cockpit run.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `action_id` | `TyperArgument` | action_id | `True` |  |  |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `allow_bounded` | `TyperOption` | --allow-bounded | `False` | `False` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON action result. |

### `agentic-kit cockpit select`

- Safety: `BOUNDED`
- When to use: Run agentic-kit cockpit select.
- Dry-run available: `False`

_No parameters._

### `agentic-kit cockpit status`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit cockpit status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit command-for`

- Safety: `READ_ONLY`
- When to use: Select the deterministic wrapper command for a raw command or task tag.
- Dry-run available: `False`

Select the deterministic wrapper command for a raw command or task tag.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `raw` | `TyperOption` | --raw | `False` |  | Raw command line to map to a wrapper. |
| `task` | `TyperOption` | --task | `False` |  | Task tag to list matching commands. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit command-taxonomy-check`

- Safety: `READ_ONLY`
- When to use: Check that public commands have stable GUI-usable taxonomy.
- Dry-run available: `False`

Check that public commands have stable GUI-usable taxonomy.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit commands render-md`

- Safety: `READ_ONLY`
- When to use: Render docs/reference/AGENTIC_KIT_COMMANDS.md from the JSON manifest.
- Dry-run available: `True`

Render docs/reference/AGENTIC_KIT_COMMANDS.md from the JSON manifest.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Write generated Markdown. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit commands sync-entrypoints`

- Safety: `BOUNDED`
- When to use: Synchronize command reference files and command-manifest entrypoint headers.
- Dry-run available: `True`

Synchronize command reference files and command-manifest entrypoint headers.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Write synchronized entrypoint files. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit dev local-feature-gate`

- Safety: `BOUNDED`
- When to use: Run the local feature gate through the supported agentic-kit CLI.
- Dry-run available: `False`

Run the local feature gate through the supported agentic-kit CLI.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `include_pr_hygiene` | `TyperOption` | --include-pr-hygiene | `False` | `False` | Also run PR hygiene after the local feature gate. |

### `agentic-kit direction audit-drift`

- Safety: `READ_ONLY`
- When to use: Report planning files that are not yet represented in project direction.
- Dry-run available: `False`

Report planning files that are not yet represented in project direction.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit direction render`

- Safety: `BOUNDED`
- When to use: Render project direction without overwriting committed projections.
- Dry-run available: `False`

Render project direction without overwriting committed projections.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `section` | `TyperOption` | --section | `False` | `all` | all, strategy, roadmap, plans, ideas, done, or discarded. |
| `output_format` | `TyperOption` | --format | `False` | `text` | text, markdown, or json. |
| `output` | `TyperOption` | --output | `False` |  | Optional tmp/*.md, tmp/*.txt, or tmp/*.json output path. |

### `agentic-kit direction validate`

- Safety: `READ_ONLY`
- When to use: Validate docs/planning/PROJECT_DIRECTION.yaml.
- Dry-run available: `False`

Validate docs/planning/PROJECT_DIRECTION.yaml.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `strict_planning_files` | `TyperOption` | --strict-planning-files | `False` | `False` | Fail when free docs/planning files are not canonical files or listed sources. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit doc-lifecycle-audit`

- Safety: `READ_ONLY`
- When to use: Audit lifecycle status headers for planning, roadmap, strategy, and idea documents.
- Dry-run available: `False`

Audit lifecycle status headers for planning, roadmap, strategy, and idea documents.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `report_path` | `TyperOption` | --report | `False` |  |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit doc-mesh-audit`

- Safety: `READ_ONLY`
- When to use: Audit cross-document state, governance, architecture, and historical-plan drift.
- Dry-run available: `False`

Audit cross-document state, governance, architecture, and historical-plan drift.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `report_path` | `TyperOption` | --report | `False` |  |  |
| `repair_plan_path` | `TyperOption` | --repair-plan | `False` |  |  |

### `agentic-kit doc-mesh-repair`

- Safety: `BOUNDED`
- When to use: Apply safe automatic documentation mesh repairs.
- Dry-run available: `False`

Apply safe automatic documentation mesh repairs.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `result_path` | `TyperOption` | --result | `False` |  |  |

### `agentic-kit doc-registry check-unregistered`

- Safety: `BOUNDED`
- When to use: List unregistered docs candidates with optional strict declared-scope failure.
- Dry-run available: `False`

List unregistered docs candidates with optional strict declared-scope failure.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `strict_scope` | `TyperOption` | --strict-scope | `False` | `False` | Fail when unregistered Markdown files violate declared required scope paths. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit doc-registry reconcile`

- Safety: `BOUNDED`
- When to use: Reconcile documentation registry, declared scope, and decision projection.
- Dry-run available: `True`

Reconcile documentation registry, declared scope, and decision projection.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Reserved for a later slice; current implementation is dry-run only. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit doc-registry register`

- Safety: `BOUNDED`
- When to use: Add one reviewed document entry to the documentation registry.
- Dry-run available: `False`

Add one reviewed document entry to the documentation registry.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `document_path` | `TyperOption` | --path | `True` |  | Repository-relative document path. |
| `document_class` | `TyperOption` | --class | `True` |  | Allowed documentation registry class. |
| `owner` | `TyperOption` | --owner | `False` | `maintainers` | Document owner recorded in the registry. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs lifecycle apply`

- Safety: `BOUNDED`
- When to use: Apply one safe documentation lifecycle plan step.
- Dry-run available: `True`

Apply one safe documentation lifecycle plan step.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `scope` | `TyperOption` | --scope | `False` | `docs` | Repository-relative documentation scope. |
| `only` | `TyperOption` | --only | `False` | `` | Plan step id to apply. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Required explicit execution flag. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs lifecycle plan`

- Safety: `READ_ONLY`
- When to use: Build a dry-run lifecycle plan for one documentation scope.
- Dry-run available: `False`

Build a dry-run lifecycle plan for one documentation scope.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `scope` | `TyperOption` | --scope | `False` | `docs` | Repository-relative documentation scope. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs lifecycle report`

- Safety: `READ_ONLY`
- When to use: Build or write one documentation lifecycle evidence report.
- Dry-run available: `True`

Build or write one documentation lifecycle evidence report.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `scope` | `TyperOption` | --scope | `False` | `docs` | Repository-relative documentation scope. |
| `output` | `TyperOption` | --output | `False` | `PosixPath('docs/architecture/evidence/doc-lifecycle-report.json')` | Evidence JSON output path. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Write the evidence report. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs lifecycle triage`

- Safety: `READ_ONLY`
- When to use: Propose safe documentation lifecycle actions without applying changes.
- Dry-run available: `False`

Propose safe documentation lifecycle actions without applying changes.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs removed-source-audit`

- Safety: `READ_ONLY`
- When to use: Fail if removed documentation sources still have live refs or registry refs.
- Dry-run available: `False`

Fail if removed documentation sources still have live refs or registry refs.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `path` | `TyperOption` | --path | `False` |  | Repository-relative removed source path to audit. May be supplied multiple times. Defaults to removed_source paths in PROJECT_DIRECTION.yaml. |
| `central_target` | `TyperOption` | --central-target | `False` | `docs/planning/PROJECT_DIRECTION.yaml` | Repository-relative central document that may retain removed_source metadata. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit docs-audit`

- Safety: `READ_ONLY`
- When to use: Run the umbrella documentation-system audit.
- Dry-run available: `False`

Run the umbrella documentation-system audit.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `report_path` | `TyperOption` | --report | `False` |  |  |

### `agentic-kit docs-registry`

- Safety: `BOUNDED`
- When to use: Show a read-only summary of the documentation registry.
- Dry-run available: `False`

Show a read-only summary of the documentation registry.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `report_path` | `TyperOption` | --report | `False` |  |  |

### `agentic-kit doctor`

- Safety: `READ_ONLY`
- When to use: Run a compact project health check.
- Dry-run available: `False`

Run a compact project health check.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit evidence classify-log`

- Safety: `BOUNDED`
- When to use: Classify a terminal/evidence log for deterministic gatekeeper decisions.
- Dry-run available: `False`

Classify a terminal/evidence log for deterministic gatekeeper decisions.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `False` |  |  |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `require_summary` | `TyperOption` | --require-summary | `False` | `False` |  |
| `ignore_git_status` | `TyperOption` | --ignore-git-status | `False` | `False` |  |

### `agentic-kit evidence clean`

- Safety: `BOUNDED`
- When to use: Clean local evidence according to repo policy.
- Dry-run available: `False`

Clean local evidence according to repo policy.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit evidence clean-check`

- Safety: `BOUNDED`
- When to use: Pass when git status is clean except one expected in-progress log.
- Dry-run available: `False`

Pass when git status is clean except one expected in-progress log.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `expected_log` | `TyperArgument` | expected_log | `True` |  |  |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit evidence commit-paths`

- Safety: `BOUNDED`
- When to use: Commit an explicit evidence path set and verify the worktree is clean afterwards.
- Dry-run available: `False`

Commit an explicit evidence path set and verify the worktree is clean afterwards.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `[]` | Repository-relative path to commit. Repeat for multiple paths. |
| `message` | `TyperOption` | --message | `True` |  |  |
| `log_path` | `TyperOption` | --log-path | `False` |  |  |
| `push` | `TyperOption` | --push | `False` | `False` |  |
| `required_branch` | `TyperOption` | --branch | `False` | `` | Expected branch for evidence commit-paths commits. |
| `allow_main` | `TyperOption` | --allow-main | `False` | `False` | Allow evidence commit-paths to commit on main. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit evidence finalize-log`

- Safety: `BOUNDED`
- When to use: Append a canonical summary, require strict inspection, then upload the evidence log.
- Dry-run available: `False`

Append a canonical summary, require strict inspection, then upload the evidence log.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `run_log` | `TyperOption` | --run-log | `True` |  |  |
| `remote_log` | `TyperOption` | --remote-log | `True` |  |  |
| `slice_name` | `TyperOption` | --slice | `True` |  |  |
| `scope` | `TyperOption` | --scope | `True` |  |  |
| `mode_check` | `TyperOption` | --mode-check | `True` |  |  |
| `work` | `TyperOption` | --work | `False` | `PASS` |  |
| `evidence` | `TyperOption` | --evidence | `False` | `PASS` |  |
| `overall` | `TyperOption` | --overall | `False` | `PASS` |  |
| `remote_evidence` | `TyperOption` | --remote-evidence | `False` | `NOT_REQUIRED` |  |
| `pr` | `TyperOption` | --pr | `False` | `NONE` |  |
| `ci` | `TyperOption` | --ci | `False` | `not-required` |  |
| `merge` | `TyperOption` | --merge | `False` | `not-required` |  |
| `command_report` | `TyperOption` | --command-report | `True` |  |  |
| `interpretation` | `TyperOption` | --interpretation | `True` |  |  |
| `safe_step` | `TyperOption` | --safe-step | `True` |  |  |
| `chat_reply` | `TyperOption` | --next | `False` | `d` |  |
| `origin` | `TyperOption` | --origin | `False` | `local` |  |
| `state_mode` | `TyperOption` | --state-mode | `False` | `local` |  |
| `comm_id` | `TyperOption` | --comm-id | `False` | `COMM-LOCAL` |  |
| `commit_message` | `TyperOption` | --commit-message | `False` |  |  |
| `push` | `TyperOption` | --push | `False` | `False` |  |
| `required_branch` | `TyperOption` | --branch | `False` | `` | Expected branch for finalize-log commits. |
| `allow_main` | `TyperOption` | --allow-main | `False` | `False` | Allow finalize-log to commit on main. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |

### `agentic-kit evidence guard`

- Safety: `BOUNDED`
- When to use: Fail if a terminal evidence log has contradictory final state.
- Dry-run available: `False`

Fail if a terminal evidence log has contradictory final state.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `logfile` | `TyperArgument` | logfile | `True` |  |  |

### `agentic-kit evidence inspect`

- Safety: `READ_ONLY`
- When to use: Inspect explicit or latest terminal evidence before continuing after chat control signals.
- Dry-run available: `False`

Inspect explicit or latest terminal evidence before continuing after chat control signals.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `False` |  |  |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `require_summary` | `TyperOption` | --require-summary | `False` | `False` |  |

### `agentic-kit evidence scope-check`

- Safety: `BOUNDED`
- When to use: Fail if expected target paths are missing from a change set.
- Dry-run available: `False`

Fail if expected target paths are missing from a change set.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `changed` | `TyperOption` | --changed | `False` | `[]` | Changed repository path. Repeat for multiple paths. |
| `expected` | `TyperOption` | --expected | `False` | `[]` | Expected target path. Repeat for multiple paths. |

### `agentic-kit github-create`

- Safety: `BOUNDED`
- When to use: Run agentic-kit github-create.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `owner` | `TyperOption` | --owner | `False` |  |  |
| `visibility` | `TyperOption` | --visibility | `False` | `private` |  |

### `agentic-kit governance check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit governance check.
- Dry-run available: `False`

_No parameters._

### `agentic-kit gui initial-llm-prompt`

- Safety: `BOUNDED`
- When to use: Run agentic-kit gui initial-llm-prompt.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root whose GUI prompt should be rendered. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit gui-readiness-gate`

- Safety: `BOUNDED`
- When to use: Run the pre-GUI readiness gate.
- Dry-run available: `False`

Run the pre-GUI readiness gate.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` | `0.4.12` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit handoff check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit handoff check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `.agentic/handoff_state.yaml` |  |

### `agentic-kit handoff post-merge-refresh-status`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit handoff post-merge-refresh-status.
- Dry-run available: `False`

_No parameters._

### `agentic-kit handoff prompt`

- Safety: `BOUNDED`
- When to use: Run agentic-kit handoff prompt.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `.agentic/handoff_state.yaml` |  |

### `agentic-kit handoff refresh`

- Safety: `BOUNDED`
- When to use: Run agentic-kit handoff refresh.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `False` | `.agentic/handoff_state.yaml` |  |
| `write` | `TyperOption` | --write | `False` | `False` | Write refreshed safe_state to YAML. |

### `agentic-kit handoff show`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit handoff show.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `.agentic/handoff_state.yaml` |  |

### `agentic-kit init`

- Safety: `BOUNDED`
- When to use: Run agentic-kit init.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `name` | `TyperArgument` | name | `False` |  | Project directory/name. |
| `project_type` | `TyperOption` | --type | `False` | `python-cli` | python-cli, python-lib, generic, governance-wrapper |
| `description` | `TyperOption` | --description | `False` |  |  |
| `license_name` | `TyperOption` | --license | `False` | `MIT` |  |
| `github_actions` | `TyperOption` | --github-actions, --no-github-actions | `False` | `True` |  |
| `pre_commit` | `TyperOption` | --pre-commit, --no-pre-commit | `False` | `True` |  |
| `agent_docs` | `TyperOption` | --agent-docs, --no-agent-docs | `False` | `True` |  |
| `logging_evidence` | `TyperOption` | --logging-evidence, --no-logging-evidence | `False` | `True` |  |
| `profiles` | `TyperOption` | --profiles | `False` |  | Comma-separated profile ids. Defaults are recommended from project type. |
| `policy_packs` | `TyperOption` | --policy-packs | `False` |  | Comma-separated policy pack ids. Defaults are recommended from project type. |
| `github` | `TyperOption` | --github, --no-github | `False` | `False` |  |
| `github_owner` | `TyperOption` | --owner | `False` |  |  |
| `visibility` | `TyperOption` | --visibility | `False` | `private` | private or public |
| `kit_source` | `TyperOption` | --kit-source | `False` | `pypi` | agentic-kit install source for generated CI: pypi, testpypi, or none |

### `agentic-kit instruction lint`

- Safety: `READ_ONLY`
- When to use: Lint instruction text against the current command manifest.
- Dry-run available: `False`

Lint instruction text against the current command manifest.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `file_path` | `TyperOption` | --file | `False` |  | Instruction text file to lint. |
| `stdin_input` | `TyperOption` | --stdin | `False` | `False` | Read instruction text from stdin. |
| `require_ack` | `TyperOption` | --require-ack, --no-require-ack | `False` | `True` | Require the current COMMAND_MANIFEST_ACK line. |
| `strict_unknown` | `TyperOption` | --strict-unknown | `False` | `False` | Treat unknown raw git/gh commands as blocking. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit pass-already-done classify`

- Safety: `BOUNDED`
- When to use: Run agentic-kit pass-already-done classify.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `True` |  |  |
| `exit_code` | `TyperOption` | --exit-code | `True` |  |  |
| `target_verified` | `TyperOption` | --target-verified | `False` | `False` |  |
| `target_state` | `TyperOption` | --target-state | `False` |  | Already-done target class. One of: branch-exists, git-clean, pull-request-exists, remote-sync |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON output. |

### `agentic-kit pass-already-done report`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit pass-already-done report.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `True` |  |  |
| `exit_code` | `TyperOption` | --exit-code | `True` |  |  |
| `target_verified` | `TyperOption` | --target-verified | `False` | `False` |  |
| `target_state` | `TyperOption` | --target-state | `False` |  | Already-done target class. One of: branch-exists, git-clean, pull-request-exists, remote-sync |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON output. |

### `agentic-kit patch-preflight`

- Safety: `BOUNDED`
- When to use: Run agentic-kit patch-preflight.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `paths` | `TyperArgument` | paths | `False` |  |  |
| `require_slice_gate` | `TyperOption` | --require-slice-gate | `False` |  | Require a clean passing slice gate before accepting preflight. |

### `agentic-kit patch-scope-preflight`

- Safety: `BOUNDED`
- When to use: Diagnose patch size, protected paths, and diff-risk before closeout.
- Dry-run available: `False`

Diagnose patch size, protected paths, and diff-risk before closeout.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `label` | `TyperOption` | --label | `False` | `patch` |  |
| `base_ref` | `TyperOption` | --base-ref | `False` | `HEAD` |  |
| `max_files` | `TyperOption` | --max-files | `False` | `6` |  |
| `max_diff_lines` | `TyperOption` | --max-diff-lines | `False` | `400` |  |
| `strict` | `TyperOption` | --strict | `False` | `False` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit patterns list`

- Safety: `READ_ONLY`
- When to use: List known local patterns and anti-patterns.
- Dry-run available: `False`

List known local patterns and anti-patterns.

_No parameters._

### `agentic-kit patterns show`

- Safety: `READ_ONLY`
- When to use: Show one local pattern catalog entry by stable ID.
- Dry-run available: `False`

Show one local pattern catalog entry by stable ID.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pattern_id` | `TyperArgument` | pattern_id | `True` |  |  |

### `agentic-kit post-release-check`

- Safety: `BOUNDED`
- When to use: Validate post-release GitHub and Zenodo state without guessing DOI metadata.
- Dry-run available: `False`

Validate post-release GitHub and Zenodo state without guessing DOI metadata.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` |  | Release version without leading v. |

### `agentic-kit post-release-doi-closeout`

- Safety: `BOUNDED`
- When to use: Run agentic-kit post-release-doi-closeout.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `True` |  | Release version without leading v. |
| `write` | `TyperOption` | --write | `False` | `False` | Write verified DOI metadata updates. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print a machine-readable result. |

### `agentic-kit pr closeout-check`

- Safety: `BOUNDED`
- When to use: Run agentic-kit pr closeout-check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_file` | `TyperArgument` | json_file | `True` |  |  |

### `agentic-kit pr merge-if-green`

- Safety: `DESTRUCTIVE`
- When to use: Merge only when PR checks are green, refs match, and merge state is clean.
- Dry-run available: `True`

Merge only when PR checks are green, refs match, and merge state is clean.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to merge only after green checks. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | GitHub merge method: squash, merge, or rebase. |
| `delete_branch` | `TyperOption` | --delete-branch, --no-delete-branch | `False` | `True` | Delete the branch after a successful merge. |
| `dry_run` | `TyperOption` | --dry-run | `False` | `False` | Evaluate without merging. |
| `no_verify_main` | `TyperOption` | --no-verify-main | `False` | `False` | Do not verify main CI after merge. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Expected base branch and post-merge verification branch. |
| `expected_base_branch` | `TyperOption` | --expected-base-branch | `False` | `` | Expected PR base branch. Defaults to --main-branch. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` | `` | Expected PR head SHA. Refuses merge if the head moved. |
| `main_ci_timeout_seconds` | `TyperOption` | --main-ci-timeout-seconds | `False` | `300` | Post-merge main CI wait timeout. |
| `main_ci_poll_seconds` | `TyperOption` | --main-ci-poll-seconds | `False` | `10` | Post-merge main CI polling interval. |
| `merge_state_timeout_seconds` | `TyperOption` | --merge-state-timeout-seconds | `False` | `60` | Pre-merge GitHub merge-state wait timeout. |
| `merge_state_poll_seconds` | `TyperOption` | --merge-state-poll-seconds | `False` | `5` | Pre-merge GitHub merge-state polling interval. |

### `agentic-kit pr status`

- Safety: `READ_ONLY`
- When to use: Print deterministic PR/CI status and fetch failed logs for red CI.
- Dry-run available: `False`

Print deterministic PR/CI status and fetch failed logs for red CI.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to inspect. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of the text report. |
| `no_failed_log_fetch` | `TyperOption` | --no-failed-log-fetch | `False` | `False` | Do not fetch failed GitHub Actions logs for red checks. |
| `failed_log_lines` | `TyperOption` | --failed-log-lines | `False` | `120` | Maximum failed-log excerpt lines. |

### `agentic-kit pr wait-ci`

- Safety: `BOUNDED`
- When to use: Wait for pull-request CI; guard merge preparation with --expected-head-sha.
- Dry-run available: `False`

Wait for pull-request CI; guard merge preparation with --expected-head-sha.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to inspect. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` |  | Expected PR head SHA for --expected-head-sha. The command fails closed if the head moves. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `2700` | Maximum wait time. |
| `interval_seconds` | `TyperOption` | --interval-seconds | `False` | `20` | Polling interval. |
| `expected_check` | `TyperOption` | --expected-check | `False` | `[]` | Check name that must be present before readiness can pass. Repeatable. |

### `agentic-kit pr-closeout`

- Safety: `BOUNDED`
- When to use: Run agentic-kit pr-closeout.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_file` | `TyperArgument` | json_file | `True` |  |  |

### `agentic-kit pr-hygiene`

- Safety: `BOUNDED`
- When to use: Run agentic-kit pr-hygiene.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit profile-explain`

- Safety: `BOUNDED`
- When to use: List available project profiles and policy packs.
- Dry-run available: `False`

List available project profiles and policy packs.

_No parameters._

### `agentic-kit project-direction`

- Safety: `BOUNDED`
- When to use: Render project direction sections from the YAML source.
- Dry-run available: `False`

Render project direction sections from the YAML source.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |
| `section` | `TyperOption` | --section | `False` | `all` | all, strategy, roadmap, plans, ideas, done, or discarded. |
| `output_format` | `TyperOption` | --format | `False` | `text` | text, markdown, or json. |

### `agentic-kit release prepare`

- Safety: `BOUNDED`
- When to use: Generate release summary evidence and run release-prep safely.
- Dry-run available: `True`

Generate release summary evidence and run release-prep safely.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `version` | `TyperOption` | --version | `True` |  | Target release version. |
| `from_tag` | `TyperOption` | --from-tag | `False` | `` | Previous release tag. Defaults to latest local v* git tag. |
| `to_ref` | `TyperOption` | --to-ref | `False` | `main` | Target ref. |
| `date` | `TyperOption` | --date | `False` | `` | Release date. Defaults to today. |
| `dry_run` | `TyperOption` | --dry-run, --write | `False` | `True` | Dry-run by default. Use --write to update release metadata. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit release ready`

- Safety: `BOUNDED`
- When to use: Run release readiness through the standard-error scan wrapper.
- Dry-run available: `False`
- Replaces raw: `git tag`, `gh release create`

Run release readiness through the standard-error scan wrapper.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `version` | `TyperOption` | --version | `True` |  | Target release version. |
| `from_tag` | `TyperOption` | --from-tag | `False` | `` | Previous release tag. Defaults to latest local v* git tag. |
| `to_ref` | `TyperOption` | --to-ref | `False` | `main` | Target ref. |
| `date` | `TyperOption` | --date | `False` | `` | Release date. Defaults to today. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit release-check`

- Safety: `BOUNDED`
- When to use: Validate release state for a target version.
- Dry-run available: `False`

Validate release state for a target version.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` |  | Release version without leading v. |

### `agentic-kit release-metadata-authority-gate`

- Safety: `BOUNDED`
- When to use: Block manual release metadata anchor edits without release-prep evidence.
- Dry-run available: `False`

Block manual release metadata anchor edits without release-prep evidence.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `base_ref` | `TyperOption` | --base-ref | `False` | `origin/main` | Git ref used as the diff base. |
| `version` | `TyperOption` | --version | `False` |  | Expected release version without leading v. |
| `evidence` | `TyperOption` | --evidence | `False` |  | Authoritative release-prep evidence file. May be passed more than once. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print a machine-readable result. |

### `agentic-kit release-notes-generate`

- Safety: `BOUNDED`
- When to use: Generate deterministic evidence-backed release notes from a local git tag diff.
- Dry-run available: `False`

Generate deterministic evidence-backed release notes from a local git tag diff.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `True` |  | Target release version without leading v. |
| `from_tag` | `TyperOption` | --from-tag | `True` |  | Previous release tag used as the lower diff bound. |
| `to_ref` | `TyperOption` | --to-ref | `False` | `HEAD` | Upper git ref used for release-note evidence. |
| `json_out` | `TyperOption` | --json-out | `False` |  | Write generated JSON release notes here. |
| `out` | `TyperOption` | --out | `False` |  | Write generated Markdown release notes here. |
| `summary_lines_json` | `TyperOption` | --summary-lines-json | `False` |  | Write a compact JSON artifact containing explicit release-prep summary lines. |
| `write` | `TyperOption` | --write | `False` | `False` | Write --json-out and --out files. |
| `check` | `TyperOption` | --check | `False` | `False` | Check existing --json-out and --out files for generated-output drift. |
| `include_github_metadata` | `TyperOption` | --include-github-metadata | `False` | `False` | Augment PR evidence with optional gh pr view metadata. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print a machine-readable result. |

### `agentic-kit release-plan`

- Safety: `BOUNDED`
- When to use: Print a release preparation checklist for the current project.
- Dry-run available: `False`

Print a release preparation checklist for the current project.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` |  | Release version without leading v. |

### `agentic-kit release-preflight`

- Safety: `BOUNDED`
- When to use: Validate before-metadata release readiness for a target version.
- Dry-run available: `False`

Validate before-metadata release readiness for a target version.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `version` | `TyperOption` | --version | `True` |  | Target release version without leading v. |

### `agentic-kit release-prep`

- Safety: `BOUNDED`
- When to use: Prepare release metadata through the supported agentic-kit route.
- Dry-run available: `True`

Prepare release metadata through the supported agentic-kit route.

This edits only local release metadata files. It does not tag, publish,
push, create GitHub releases, or write Zenodo DOI metadata.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `True` |  | Target release version without leading v. |
| `release_date` | `TyperOption` | --date | `False` |  | Release metadata date in YYYY-MM-DD format. Defaults to today. |
| `summary_lines` | `TyperOption` | --summary-line | `False` |  | Release changelog summary line. Repeat for multiple lines; required to avoid stale template reuse. |
| `summary_lines_from` | `TyperOption` | --summary-lines-from | `False` |  | Read explicit release changelog summary lines from a JSON artifact generated from release notes. |
| `dry_run` | `TyperOption` | --dry-run | `False` | `False` | Report changed paths without writing files. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print a machine-readable result. |

### `agentic-kit release-publish`

- Safety: `DESTRUCTIVE`
- When to use: Plan release publishing without live tag/release side effects.
- Dry-run available: `True`

Plan release publishing without live tag/release side effects.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `version` | `TyperOption` | --version | `False` | `0.4.12` |  |
| `dry_run` | `TyperOption` | --dry-run, --no-dry-run | `False` | `True` |  |
| `execute` | `TyperOption` | --execute | `False` | `False` |  |
| `allow_execute` | `TyperOption` | --allow-execute | `False` | `False` |  |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit release-status`

- Safety: `BOUNDED`
- When to use: Render the local release lifecycle state without mutating release files.
- Dry-run available: `False`

Render the local release lifecycle state without mutating release files.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` |  | Release version without leading v. |
| `include_remote` | `TyperOption` | --include-remote | `False` | `False` | Include remote tag, GitHub Release, and DOI/Zenodo checks. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print a machine-readable result. |

### `agentic-kit remote-branch-hygiene`

- Safety: `BOUNDED`
- When to use: Dry-run remote branch hygiene classification for K3.
- Dry-run available: `False`

Dry-run remote branch hygiene classification for K3.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit remote-branch-hygiene-apply`

- Safety: `BOUNDED`
- When to use: Safely apply exactly one remote branch deletion candidate.
- Dry-run available: `True`

Safely apply exactly one remote branch deletion candidate.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `only` | `TyperOption` | --only | `True` |  |  |
| `execute` | `TyperOption` | --execute | `False` | `False` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit remote-branch-hygiene-report`

- Safety: `BOUNDED`
- When to use: Write a K3 remote branch hygiene evidence report only with --execute.
- Dry-run available: `True`

Write a K3 remote branch hygiene evidence report only with --execute.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `output_path` | `TyperOption` | --output | `True` |  |  |
| `execute` | `TyperOption` | --execute | `False` | `False` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit remote-next`

- Safety: `BOUNDED`
- When to use: Run agentic-kit remote-next.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON result. |

### `agentic-kit rn`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rn.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON result. |

### `agentic-kit rnc`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rnc.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `no_push` | `TyperOption` | --no-push | `False` | `False` | Commit locally without pushing. |

### `agentic-kit rule-registry check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit rule-registry check.
- Dry-run available: `False`

_No parameters._

### `agentic-kit rule-registry register`

- Safety: `BOUNDED`
- When to use: Add one reviewed rule mechanism with direct evidence coverage.
- Dry-run available: `False`

Add one reviewed rule mechanism with direct evidence coverage.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `mechanism_id` | `TyperOption` | --id | `True` |  | Unique rule mechanism id. |
| `rule_class` | `TyperOption` | --class | `True` |  | Rule mechanism class/category. |
| `owner` | `TyperOption` | --owner | `True` |  | Responsible owner. |
| `priority` | `TyperOption` | --priority | `True` |  | Positive enforcement priority. |
| `enforcement_phase` | `TyperOption` | --enforcement-phase | `True` |  | Allowed enforcement phase. |
| `conflict_domains` | `TyperOption` | --conflict-domain | `True` |  | Conflict domain; repeat for multiple domains. |
| `surfaces` | `TyperOption` | --surface | `True` |  | Covered rule surface; repeat for multiple surfaces. |
| `source_path` | `TyperOption` | --source | `True` |  | Repository-relative source path. |
| `required_terms` | `TyperOption` | --required-term | `True` |  | Required source anchor term; repeat for multiple terms. |
| `test_paths` | `TyperOption` | --test | `True` |  | Direct regression test path; repeat for multiple tests. |
| `protected_rule_intent` | `TyperOption` | --protected-rule-intent | `True` |  | Protected intent preserved by this rule. |
| `assertion_statement` | `TyperOption` | --assertion-statement | `True` |  | Direct coverage assertion statement. |
| `assertion_kind` | `TyperOption` | --assertion-kind | `False` | `guard` | Coverage assertion kind. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit rule-registry report`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit rule-registry report.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |
| `fail_on_followups` | `TyperOption` | --fail-on-followups | `False` | `False` | Exit non-zero when follow-up items remain, even if validation passes. |

### `agentic-kit rules acknowledge`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules acknowledge.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `output_path` | `TyperOption` | --output | `False` | `PosixPath('.agentic/rule_ack/current.json')` |  |
| `next_allowed_action` | `TyperOption` | --next-allowed-action | `False` | `run_next_command` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules acknowledge-communication-refresh`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules acknowledge-communication-refresh.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `ack_file` | `TyperOption` | --ack-file | `True` |  | Path to RULE_REFRESH_ACK JSON/text. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules communication-refresh`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules communication-refresh.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `publish` | `TyperOption` | --publish | `False` | `False` | Write d2 pending state and emit carrier metadata. |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules handoff-refresh`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules handoff-refresh.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules require-current-communication-context`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules require-current-communication-context.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules snapshot`

- Safety: `BOUNDED`
- When to use: Run agentic-kit rules snapshot.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit rules validate-sources`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit rules validate-sources.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit scaffold planning-doc`

- Safety: `BOUNDED`
- When to use: Run agentic-kit scaffold planning-doc.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `title` | `TyperArgument` | title | `True` |  | Planning document title |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `status` | `TyperOption` | --status | `False` | `active` |  |
| `decision_status` | `TyperOption` | --decision-status | `False` | `proposed` |  |
| `scope` | `TyperOption` | --scope | `False` | `planning` |  |
| `review_policy` | `TyperOption` | --review-policy | `False` | `review before implementation and after each milestone` |  |
| `output` | `TyperOption` | --output | `False` |  |  |
| `overwrite` | `TyperOption` | --overwrite | `False` | `False` |  |

### `agentic-kit slice gate`

- Safety: `BOUNDED`
- When to use: Run agentic-kit slice gate.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `kind` | `TyperOption` | --kind | `False` | `planning-doc` | Slice gate kind to run. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Repository root. |

### `agentic-kit standard-gates-audit-suite`

- Safety: `READ_ONLY`
- When to use: Run the audit suite required by standard project gates.
- Dry-run available: `False`

Run the audit suite required by standard project gates.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` |  |
| `version` | `TyperOption` | --version | `False` | `0.4.12` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` |  |

### `agentic-kit state freshness-check`

- Safety: `BOUNDED`
- When to use: Run agentic-kit state freshness-check.
- Dry-run available: `False`

_No parameters._

### `agentic-kit state mode-check`

- Safety: `BOUNDED`
- When to use: Run agentic-kit state mode-check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `target` | `TyperArgument` | target | `True` |  | Execution target: local or remote. |
| `expected_branch` | `TyperOption` | --expected-branch | `False` |  |  |
| `allow_dirty` | `TyperOption` | --allow-dirty | `False` | `False` | Allow a dirty worktree. |

### `agentic-kit state mode-write`

- Safety: `BOUNDED`
- When to use: Run agentic-kit state mode-write.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `target` | `TyperArgument` | target | `True` |  | Execution target: local or remote. |
| `expected_branch` | `TyperOption` | --expected-branch | `False` |  |  |
| `reason` | `TyperOption` | --reason | `False` | `manual_mode_transition` |  |
| `allow_dirty` | `TyperOption` | --allow-dirty | `False` | `False` | Allow a dirty worktree. |

### `agentic-kit todo complete`

- Safety: `BOUNDED`
- When to use: Mark a TODO item as done and store evidence.
- Dry-run available: `False`

Mark a TODO item as done and store evidence.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `item_id` | `TyperArgument` | item_id | `True` |  |  |
| `evidence` | `TyperOption` | --evidence | `True` |  | Evidence for completing the item. |
| `render` | `TyperOption` | --render, --no-render | `False` | `True` | Regenerate docs/TODO.md. |

### `agentic-kit todo list`

- Safety: `READ_ONLY`
- When to use: List project TODO items from .agentic/todo.yaml.
- Dry-run available: `False`

List project TODO items from .agentic/todo.yaml.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `all_items` | `TyperOption` | --all | `False` | `False` | Show completed items too. |

### `agentic-kit todo render`

- Safety: `BOUNDED`
- When to use: Regenerate docs/TODO.md from .agentic/todo.yaml.
- Dry-run available: `False`

Regenerate docs/TODO.md from .agentic/todo.yaml.

_No parameters._

### `agentic-kit transfer admin-refresh-pr`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer admin-refresh-pr.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `after_pr` | `TyperOption` | --after-pr | `True` |  | Merged PR number that requires the administrative handoff refresh. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Main branch to refresh from. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer apply`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer apply.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `PosixPath('.agentic/transfer/inbox/current.yaml')` | Transfer order path. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer branch-create`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer branch-create.
- Dry-run available: `False`
- Replaces raw: `git switch -c`, `git checkout -b`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `True` |  | Branch name to create. |
| `start_point` | `TyperOption` | --start-point | `False` | `main` | Start point for the new branch. |
| `push` | `TyperOption` | --push | `False` | `False` | Push the new branch and set upstream. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer branch-delete`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit transfer branch-delete.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `True` |  | Branch name to delete. |
| `remote` | `TyperOption` | --remote | `False` | `False` | Delete branch on origin instead of locally. |
| `force` | `TyperOption` | --force | `False` | `False` | Force local branch deletion with -D. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer branch-switch`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer branch-switch.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `True` |  | Branch name to switch to. |
| `pull` | `TyperOption` | --pull | `False` | `False` | Fast-forward pull from origin after switching. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer chat-switch-complete`

- Safety: `BOUNDED`
- When to use: Create a deterministic successor handoff package and prompt projections.
- Dry-run available: `False`

Create a deterministic successor handoff package and prompt projections.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |
| `render_prompt` | `TyperOption` | --render-prompt | `False` | `False` | Print the generated copy-and-paste successor chat prompt. |
| `output_dir` | `TyperOption` | --output-dir | `False` | `docs/reports/handoff-packages/latest` | Directory for the generated successor handoff package. |
| `update_canonical_prompts` | `TyperOption` | --update-canonical-prompts, --no-update-canonical-prompts | `False` | `True` | Update NEXT_CHAT_BOOTSTRAP, START_NEW_CHAT_PROMPT, and CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT. |

### `agentic-kit transfer closeout`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer closeout.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `no_remove_transfer_dir` | `TyperOption` | --no-remove-transfer-dir | `False` | `False` | Do not remove .agentic/transfer during closeout. |
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer command-composition-check`

- Safety: `BOUNDED`
- When to use: Block common copied-command mistakes before running patch, transfer, or release gates.
- Dry-run available: `False`

Block common copied-command mistakes before running patch, transfer, or release gates.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `test_paths` | `TyperOption` | --test-path | `False` |  | Repository-relative test path that must exist before composing a pytest command. Repeatable. |
| `commands` | `TyperOption` | --command | `False` |  | agentic-kit command prefix that must exist in docs/reference/agentic-kit-commands.json. Repeatable. |
| `sequence_commands` | `TyperOption` | --sequence-command | `False` |  | Command sequence entry to check for avoidable low-level workflow chains. Repeatable. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer command-reference-check`

- Safety: `READ_ONLY`
- When to use: Check whether the committed agentic-kit command reference is current.
- Dry-run available: `False`

Check whether the committed agentic-kit command reference is current.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer command-reference-refresh`

- Safety: `BOUNDED`
- When to use: Regenerate the agentic-kit command reference without committing changes.
- Dry-run available: `False`

Regenerate the agentic-kit command reference without committing changes.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer command-stack-begin`

- Safety: `BOUNDED`
- When to use: Begin a repo-local command-stack state for deterministic local preflight cleanup.
- Dry-run available: `False`

Begin a repo-local command-stack state for deterministic local preflight cleanup.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer command-stack-end`

- Safety: `BOUNDED`
- When to use: End the repo-local command-stack state after a local command stack completed.
- Dry-run available: `False`

End the repo-local command-stack state after a local command stack completed.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer commit`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer commit.
- Dry-run available: `False`
- Replaces raw: `git commit`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `message` | `TyperOption` | --message, -m | `True` |  | Commit message. |
| `path` | `TyperOption` | --path | `False` | `[]` | Path to add before commit. Repeatable. |
| `branch` | `TyperOption` | --branch | `False` | `` | Expected branch for the commit. If set, the transfer monitor switches to it or blocks safely. |
| `allow_main` | `TyperOption` | --allow-main | `False` | `False` | Allow committing directly on main. Use only for explicit emergency/admin flows. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer conflict-resolve-file`

- Safety: `BOUNDED`
- When to use: Resolve one conflicted file by replacing it from an explicit source and staging it.
- Dry-run available: `False`

Resolve one conflicted file by replacing it from an explicit source and staging it.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `True` |  | Repository-relative conflicted file to resolve. |
| `source` | `TyperOption` | --source | `True` |  | File whose content should replace the conflicted target. |
| `expected_branch` | `TyperOption` | --branch | `False` | `` | Expected current branch. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer conflict-status`

- Safety: `BOUNDED`
- When to use: Report merge/rebase conflict state without resolving anything.
- Dry-run available: `False`

Report merge/rebase conflict state without resolving anything.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer continue`

- Safety: `BOUNDED`
- When to use: Continue chat/local transfer communication through the safest available wrapper path.
- Dry-run available: `False`

Continue chat/local transfer communication through the safest available wrapper path.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `False` |  | Optional target branch. If omitted, infer a single active transfer order. |
| `json_output` | `TyperOption` | --json, --no-json | `False` | `False` | Print machine-readable JSON. |
| `skip_llm_context_gate` | `TyperOption` | --skip-llm-context-gate | `False` | `False` | Recovery-only: continue without requiring fresh generated LLM context. |

### `agentic-kit transfer delete-merged-work-branch`

- Safety: `DESTRUCTIVE`
- When to use: Delete a merged non-main work branch after PR merge-state verification.
- Dry-run available: `False`
- Replaces raw: `git push --delete`, `git branch -D`

Delete a merged non-main work branch after PR merge-state verification.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `True` |  | Merged feature/docs/fix/chore/evidence branch to delete. |
| `remote` | `TyperOption` | --remote, --no-remote | `False` | `True` | Delete the branch on origin. |
| `local` | `TyperOption` | --local, --no-local | `False` | `True` | Delete the local branch. |
| `force_local` | `TyperOption` | --force-local | `False` | `False` | Force local deletion with git branch -D. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer diagnose-removed-ns-commands`

- Safety: `BOUNDED`
- When to use: Diagnose ns command definitions/usages removed or reduced between release refs.
- Dry-run available: `False`

Diagnose ns command definitions/usages removed or reduced between release refs.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `old` | `TyperOption` | --old | `False` | `0.4.6` | Old release tag/ref. |
| `new` | `TyperOption` | --new | `False` | `0.4.8` | New release tag/ref. |
| `json_out` | `TyperOption` | --json-out | `False` |  | Write machine-readable report. |
| `md_out` | `TyperOption` | --md-out | `False` |  | Write Markdown report. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print full JSON report to stdout. |

### `agentic-kit transfer divergence-status`

- Safety: `READ_ONLY`
- When to use: Report local/upstream divergence without mutating repository state.
- Dry-run available: `False`

Report local/upstream divergence without mutating repository state.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer evidence-finalize-current-transfer`

- Safety: `BOUNDED`
- When to use: Finalize the current transfer evidence log through the stricter evidence CLI.
- Dry-run available: `False`

Finalize the current transfer evidence log through the stricter evidence CLI.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `slice_name` | `TyperOption` | --slice | `True` |  | Evidence slice label. |
| `run_log` | `TyperOption` | --run-log | `False` | `PosixPath('docs/reports/transfer_runs/latest-transfer-report.log')` | Local run log to finalize. |
| `remote_log` | `TyperOption` | --remote-log | `False` |  | Repository-relative remote evidence log path under docs/reports/terminal/. |
| `scope` | `TyperOption` | --scope | `False` | `transfer` | Evidence scope summary. |
| `mode_check` | `TyperOption` | --mode-check | `False` | `standard` | Evidence mode check summary. |
| `pr` | `TyperOption` | --pr | `False` | `NONE` | Associated PR number or NONE. |
| `ci` | `TyperOption` | --ci | `False` | `not-required` | CI state summary. |
| `merge` | `TyperOption` | --merge | `False` | `not-required` | Merge state summary. |
| `command_report` | `TyperOption` | --command-report | `False` | `transfer lifecycle completed` | Command report summary. |
| `interpretation` | `TyperOption` | --interpretation | `False` | `Evidence finalized through transfer wrapper.` | Evidence interpretation summary. |
| `safe_step` | `TyperOption` | --safe-step | `False` | `Continue with the next planned slice.` | Next safe step. |
| `push` | `TyperOption` | --push | `False` | `False` | Push evidence commit if finalize-log creates one. |
| `branch` | `TyperOption` | --branch | `False` | `` | Expected branch for evidence finalize-log commits. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer evidence-inspect-latest`

- Safety: `BOUNDED`
- When to use: Inspect the latest evidence log with the required-summary contract.
- Dry-run available: `False`

Inspect the latest evidence log with the required-summary contract.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer evidence-pr-complete`

- Safety: `BOUNDED`
- When to use: Finalize transfer evidence on an evidence branch and complete it through a PR.
- Dry-run available: `False`

Finalize transfer evidence on an evidence branch and complete it through a PR.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `slice_name` | `TyperOption` | --slice | `True` |  | Evidence slice label. |
| `evidence_branch` | `TyperOption` | --evidence-branch | `True` |  | Evidence branch to use as PR head. |
| `title` | `TyperOption` | --title | `True` |  | Evidence PR title. |
| `body` | `TyperOption` | --body | `False` | `` | Evidence PR body. |
| `base` | `TyperOption` | --base | `False` | `main` | Base branch for the evidence PR. |
| `run_log` | `TyperOption` | --run-log | `False` | `PosixPath('docs/reports/transfer_runs/latest-transfer-report.log')` | Local run log to finalize. |
| `remote_log` | `TyperOption` | --remote-log | `False` |  | Repository-relative remote evidence log path under docs/reports/terminal/. |
| `scope` | `TyperOption` | --scope | `False` | `transfer` | Evidence scope summary. |
| `mode_check` | `TyperOption` | --mode-check | `False` | `standard` | Evidence mode check summary. |
| `source_pr` | `TyperOption` | --source-pr | `False` | `NONE` | Associated source PR number or NONE. |
| `ci` | `TyperOption` | --ci | `False` | `not-required` | CI state summary. |
| `merge` | `TyperOption` | --merge | `False` | `not-required` | Merge state summary. |
| `command_report` | `TyperOption` | --command-report | `False` | `transfer lifecycle completed` | Command report summary. |
| `interpretation` | `TyperOption` | --interpretation | `False` | `Evidence finalized through transfer evidence-pr-complete wrapper.` | Evidence interpretation summary. |
| `safe_step` | `TyperOption` | --safe-step | `False` | `Continue with the next planned slice.` | Next safe step. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | GitHub merge method. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `300` | Maximum CI wait time. |
| `poll_seconds` | `TyperOption` | --interval-seconds, --poll-seconds | `False` | `10` | CI polling interval. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer fetch-origin`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer fetch-origin.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperOption` | --branch | `False` | `main` | Remote branch to fetch from origin. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer head-sha`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer head-sha.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `full` | `TyperOption` | --full | `False` | `False` | Print the full HEAD SHA instead of the short SHA. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer inspect`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer inspect.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `PosixPath('.agentic/transfer/inbox/current.yaml')` | Transfer order path. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer list-refs`

- Safety: `BOUNDED`
- When to use: List local release tags and branches for safe work-start selection.
- Dry-run available: `False`

List local release tags and branches for safe work-start selection.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer log-header`

- Safety: `BOUNDED`
- When to use: Render the dynamic local-to-LLM copy/paste log header from rule files.
- Dry-run available: `False`

Render the dynamic local-to-LLM copy/paste log header from rule files.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `log_path` | `TyperOption` | --log-path | `False` | `` | Optional log path to include in the dynamic local-to-LLM header. |

### `agentic-kit transfer log-upload-hint`

- Safety: `BOUNDED`
- When to use: Render the terminal hint for copy/paste communication with the LLM.
- Dry-run available: `False`

Render the terminal hint for copy/paste communication with the LLM.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `log_path` | `TyperOption` | --log-path | `True` |  | Log file path to mention in the terminal upload hint. |
| `return_code` | `TyperOption` | --rc | `False` |  | Optional return code to explain in the upload hint. |

### `agentic-kit transfer normalize-files`

- Safety: `BOUNDED`
- When to use: Normalize active transfer files by adding missing command IDs and archiving stale active files.
- Dry-run available: `True`

Normalize active transfer files by adding missing command IDs and archiving stale active files.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `dry_run` | `TyperOption` | --dry-run | `False` | `False` | Report transfer file lifecycle repairs without applying them. |
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer normalize-session`

- Safety: `BOUNDED`
- When to use: Normalize and summarize the local transfer session state.
- Dry-run available: `False`

Normalize and summarize the local transfer session state.

The MVP is diagnostic and evidence-producing only. It does not switch branches,
pull, delete files, commit, push, or mutate the worktree except for writing the
canonical transfer outbox file.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |
| `repair_known_volatile` | `TyperOption` | --repair-known-volatile | `False` | `False` | Restore known volatile transfer output files before checking the session. |
| `write_outbox` | `TyperOption` | --write-outbox, --no-write-outbox | `False` | `False` | Write the normalized session result to the canonical transfer outbox. |

### `agentic-kit transfer patch-cycle-status`

- Safety: `BOUNDED`
- When to use: Render the current four-slice patch/handoff workflow state.
- Dry-run available: `False`

Render the current four-slice patch/handoff workflow state.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperOption` | --pr | `False` |  | Optional pull request number to include in the patch-cycle state. |
| `include_ci` | `TyperOption` | --include-ci | `False` | `False` | Include PR statusCheckRollup summary when --pr is provided. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer post-merge-check`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit transfer post-merge-check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Expected current branch after merge. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer post-merge-complete`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit transfer post-merge-complete.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `after_pr` | `TyperOption` | --after-pr | `True` |  | Merged PR number to complete. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Main branch to verify. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | Merge method for admin refresh PR. |
| `refresh_expected_head_sha` | `TyperOption` | --refresh-expected-head-sha | `False` | `` | Expected admin refresh PR head SHA. Existing commands resolve empty values. |
| `ci_timeout_seconds` | `TyperOption` | --ci-timeout-seconds | `False` | `300` | CI wait timeout. |
| `ci_poll_seconds` | `TyperOption` | --ci-poll-seconds | `False` | `10` | CI polling interval. |
| `merge_state_timeout_seconds` | `TyperOption` | --merge-state-timeout-seconds | `False` | `60` |  |
| `merge_state_poll_seconds` | `TyperOption` | --merge-state-poll-seconds | `False` | `5` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer pr-closeout-complete`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-closeout-complete.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `after_pr` | `TyperOption` | --after-pr | `True` |  | Substantive PR number to merge if needed and close out with post-merge handoff refresh. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Main branch to synchronize and verify. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | Merge method for the substantive PR and any administrative refresh PR. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `300` | CI wait timeout for the substantive PR and refresh PR. |
| `poll_seconds` | `TyperOption` | --poll-seconds | `False` | `10` | CI polling interval for the substantive PR and refresh PR. |
| `merge_state_timeout_seconds` | `TyperOption` | --merge-state-timeout-seconds | `False` | `60` |  |
| `merge_state_poll_seconds` | `TyperOption` | --merge-state-poll-seconds | `False` | `5` |  |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer pr-complete`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-complete.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to complete. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` | `` | Expected PR head SHA, or current to use git rev-parse HEAD before the merge. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Main branch to sync after the merge. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | GitHub merge method. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `300` | Maximum CI wait time. |
| `poll_seconds` | `TyperOption` | --interval-seconds, --poll-seconds | `False` | `10` | CI polling interval. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |
| `skip_llm_context_gate` | `TyperOption` | --skip-llm-context-gate | `False` | `False` | Recovery-only: run PR completion without requiring fresh generated LLM context. |
| `post_merge_complete` | `TyperOption` | --post-merge-complete | `False` | `False` | Invalid for pr-complete. Use pr-create-complete --post-merge-complete for new PRs, or run post-merge-complete separately after an existing PR is merged. |

### `agentic-kit transfer pr-create`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-create.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `base` | `TyperOption` | --base | `False` | `main` | Base branch. |
| `head` | `TyperOption` | --head | `True` |  | Head branch. |
| `title` | `TyperOption` | --title | `True` |  | Pull request title. |
| `body` | `TyperOption` | --body | `False` | `` | Pull request body. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |
| `skip_llm_context_gate` | `TyperOption` | --skip-llm-context-gate | `False` | `False` | Recovery-only: create PR without requiring fresh generated LLM context. |

### `agentic-kit transfer pr-create-complete`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-create-complete.
- Dry-run available: `False`
- Replaces raw: `gh pr create`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `title` | `TyperOption` | --title | `True` |  | Pull request title. |
| `body` | `TyperOption` | --body | `False` | `` | Pull request body. |
| `base` | `TyperOption` | --base | `False` | `main` | Base branch. |
| `head` | `TyperOption` | --head | `False` | `current` | Head branch. Use current to resolve git branch --show-current. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | GitHub merge method. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `300` | Maximum CI wait time. |
| `poll_seconds` | `TyperOption` | --interval-seconds, --poll-seconds | `False` | `10` | CI polling interval. |
| `post_merge_complete` | `TyperOption` | --post-merge-complete | `False` | `False` | After pr-complete, run visible post-merge closeout using the concrete PR number. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |
| `skip_llm_context_gate` | `TyperOption` | --skip-llm-context-gate | `False` | `False` | Recovery-only: run PR create/complete without requiring fresh generated LLM context. |

### `agentic-kit transfer pr-existing-for-branch`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-existing-for-branch.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `head` | `TyperOption` | --head | `False` | `current` | Head branch to look up. Use current to resolve git branch --show-current. |
| `base` | `TyperOption` | --base | `False` | `main` | Base branch to match. |
| `state` | `TyperOption` | --state | `False` | `all` | GitHub PR state filter. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text report. |

### `agentic-kit transfer pr-merge-safe`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit transfer pr-merge-safe.
- Dry-run available: `False`
- Replaces raw: `gh pr merge`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to merge safely. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` | `` | Expected PR head SHA. If omitted, the PR head SHA is resolved automatically. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Expected base branch. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | GitHub merge method. |
| `no_verify_main` | `TyperOption` | --no-verify-main | `False` | `False` | Skip post-merge main verification. |
| `merge_state_timeout_seconds` | `TyperOption` | --merge-state-timeout-seconds | `False` | `60` | Pre-merge GitHub merge-state wait timeout. |
| `merge_state_poll_seconds` | `TyperOption` | --merge-state-poll-seconds | `False` | `5` | Pre-merge GitHub merge-state polling interval. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |
| `skip_llm_context_gate` | `TyperOption` | --skip-llm-context-gate | `False` | `False` | Recovery-only: run PR merge without requiring fresh generated LLM context. |

### `agentic-kit transfer pr-status`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to inspect through the transfer wrapper. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text report. |
| `no_failed_log_fetch` | `TyperOption` | --no-failed-log-fetch | `False` | `False` | Do not fetch failed GitHub Actions logs for red checks. |
| `failed_log_lines` | `TyperOption` | --failed-log-lines | `False` | `120` | Maximum failed-log excerpt lines. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` | `` | Expected full PR head SHA. |

### `agentic-kit transfer pr-wait-ci`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pr-wait-ci.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `pr_number` | `TyperArgument` | pr_number | `True` |  | Pull request number to wait for. |
| `expected_head_sha` | `TyperOption` | --expected-head-sha | `False` | `` | Expected PR head SHA, or current to use git rev-parse HEAD. |
| `timeout_seconds` | `TyperOption` | --timeout-seconds | `False` | `300` | Maximum wait time. |
| `poll_seconds` | `TyperOption` | --interval-seconds, --poll-seconds | `False` | `10` | Polling interval. |
| `quiet_report` | `TyperOption` | --quiet-report | `False` | `False` | Write the detailed wait output to a transfer report and print only go lines. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer prepare-successor-handoff`

- Safety: `BOUNDED`
- When to use: Deprecated compatibility alias for transfer chat-switch-complete.
- Dry-run available: `False`

Deprecated compatibility alias for transfer chat-switch-complete.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |
| `repair_known_volatile` | `TyperOption` | --repair-known-volatile | `False` | `False` | Deprecated compatibility option; volatile repair belongs in normalize-session. |
| `render_prompt` | `TyperOption` | --render-prompt | `False` | `False` | Print the generated copy-and-paste successor chat prompt. |
| `write_outbox` | `TyperOption` | --write-outbox, --no-write-outbox | `False` | `False` | Deprecated compatibility option. The deterministic package is written to docs/reports/handoff-packages/latest. |

### `agentic-kit transfer protected-diff-plan`

- Safety: `READ_ONLY`
- When to use: Write the current diff to /tmp and run the Python protected change planner on it.
- Dry-run available: `False`

Write the current diff to /tmp and run the Python protected change planner on it.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `label` | `TyperOption` | --label | `False` | `protected-change-plan` | Stable label for the temporary diff file. |
| `cached` | `TyperOption` | --cached | `False` | `False` | Use staged diff. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer publish-last-report`

- Safety: `DESTRUCTIVE`
- When to use: Run agentic-kit transfer publish-last-report.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `label` | `TyperOption` | --label | `False` | `transfer-handoff` | Label for the published tracked handoff report. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of concise handoff lines. |

### `agentic-kit transfer pull-current`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer pull-current.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer push-current`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer push-current.
- Dry-run available: `False`
- Replaces raw: `git push`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperOption` | --branch | `False` | `` | Expected branch to push. If set, the transfer monitor switches to it or blocks safely. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer read-user-task`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer read-user-task.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer rebase-on-upstream`

- Safety: `BOUNDED`
- When to use: Rebase the current branch on its upstream with bounded conflict reporting.
- Dry-run available: `False`

Rebase the current branch on its upstream with bounded conflict reporting.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `upstream` | `TyperOption` | --upstream | `False` | `` | Upstream ref. Defaults to origin/<current-branch>. |
| `expected_branch` | `TyperOption` | --branch | `False` | `` | Expected current branch before rebasing. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer refresh-llm-context-carriers`

- Safety: `BOUNDED`
- When to use: Refresh outbox and latest handoff report with fresh generated LLM context.
- Dry-run available: `False`

Refresh outbox and latest handoff report with fresh generated LLM context.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer remote-next`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer remote-next.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `False` |  | Optional remote transfer branch. If omitted, read branch from the transfer order. |
| `json_output` | `TyperOption` | --json, --no-json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer remote-work-start`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer remote-work-start.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperArgument` | branch | `True` |  | Feature branch to prepare, for example feature/name. |
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Base branch for new work branches. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer repo-diff`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer repo-diff.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `cached` | `TyperOption` | --cached | `False` | `False` | Show staged diff. |
| `name_only` | `TyperOption` | --name-only | `False` | `False` | Show only changed path names. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer repo-log`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer repo-log.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `limit` | `TyperOption` | --limit, -n | `False` | `5` | Number of commits to show. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer repo-status`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer repo-status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `short` | `TyperOption` | --short, --full | `False` | `True` | Use short git status by default. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer require-fresh-llm-context`

- Safety: `READ_ONLY`
- When to use: Require fresh generated LLM context before transfer planning.
- Dry-run available: `False`

Require fresh generated LLM context before transfer planning.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `max_age_minutes` | `TyperOption` | --max-age-minutes | `False` | `60` | Maximum acceptable age of generated LLM context. |
| `allow_clean_post_merge_carrier_staleness` | `TyperOption` | --allow-clean-post-merge-carrier-staleness | `False` | `False` | Downgrade stale volatile LLM-context carrier state to WARN when post-merge-check is NOOP and the worktree is clean. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer restore-known-volatile`

- Safety: `BOUNDED`
- When to use: Restore the canonical known volatile transfer files.
- Dry-run available: `False`

Restore the canonical known volatile transfer files.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer run-and-log`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer run-and-log.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `label` | `TyperOption` | --label | `False` | `transfer-run` | Label for the transfer uplink report. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer run-local`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer run-local.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `PosixPath('.agentic/transfer/inbox/current.yaml')` | Transfer order path. |
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer run-sequence-and-log`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer run-sequence-and-log.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `step` | `TyperOption` | --step | `True` |  | One command step; quote it as one shell argument. |
| `label` | `TyperOption` | --label | `False` | `transfer-sequence` | Label for the transfer sequence report. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer show-last-report`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer show-last-report.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print the full latest transfer report JSON. |

### `agentic-kit transfer standard-error-scan`

- Safety: `BOUNDED`
- When to use: Run a bounded scan for known workflow standard errors before patch/transfer/release work.
- Dry-run available: `False`

Run a bounded scan for known workflow standard errors before patch/transfer/release work.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `before_release` | `TyperOption` | --before-release | `False` | `False` | Run the release-oriented standard-error scan bundle. |
| `version` | `TyperOption` | --version | `False` | `` | Release version for before-release checks. Required with --before-release. |
| `from_tag` | `TyperOption` | --from-tag | `False` | `` | Previous release tag for release notes checks. Defaults to the latest local v* git tag. |
| `to_ref` | `TyperOption` | --to-ref | `False` | `main` | Target ref for release notes checks. |
| `date` | `TyperOption` | --date | `False` | `` | Release date for release-prep dry-run. Defaults to today. |
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer state`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer state.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json, --no-json | `False` | `True` | Print machine-readable JSON. |

### `agentic-kit transfer status`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `PosixPath('.agentic/transfer/inbox/current.yaml')` | Transfer order path. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer submit-user-task`

- Safety: `BOUNDED`
- When to use: Run agentic-kit transfer submit-user-task.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `title` | `TyperOption` | --title | `False` | `GUI file-transfer task` | Task title. |
| `body_file` | `TyperOption` | --body-file | `True` |  | UTF-8 text file containing the task body. |
| `communication_mode` | `TyperOption` | --communication-mode | `False` | `file_transfer` | GUI communication mode: remote, file_transfer, or copy_paste. |
| `publish` | `TyperOption` | --publish | `False` | `False` | Publish the canonical GUI task carrier to the gui-transfer-tasks remote branch. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit transfer sync-main`

- Safety: `BOUNDED`
- When to use: Synchronize main, acknowledge rules, and normalize the session.
- Dry-run available: `False`

Synchronize main, acknowledge rules, and normalize the session.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `main_branch` | `TyperOption` | --main-branch | `False` | `main` | Main branch to synchronize. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer verify-llm-context-refresh`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit transfer verify-llm-context-refresh.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print JSON instead of text. |

### `agentic-kit transfer work-order-patch`

- Safety: `BOUNDED`
- When to use: Apply a guarded JSON/YAML text-replacement patch work order.
- Dry-run available: `True`

Apply a guarded JSON/YAML text-replacement patch work order.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperOption` | --path | `False` | `PosixPath('.agentic/transfer/inbox/patch.yaml')` | JSON/YAML patch work-order path. |
| `dry_run` | `TyperOption` | --dry-run | `False` | `False` | Validate without writing files. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON only. |

### `agentic-kit transfer workflow-next`

- Safety: `BOUNDED`
- When to use: Read repo and transfer state and print the next safe wrapper command without mutating state.
- Dry-run available: `False`

Read repo and transfer state and print the next safe wrapper command without mutating state.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json, --no-json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit validate-contract`

- Safety: `READ_ONLY`
- When to use: Validate the machine-readable project contract.
- Dry-run available: `False`

Validate the machine-readable project contract.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/project.yaml. |

### `agentic-kit validate-output-contract`

- Safety: `READ_ONLY`
- When to use: Validate an output file against a machine-readable output contract.
- Dry-run available: `False`

Validate an output file against a machine-readable output contract.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `output_path` | `TyperArgument` | output_path | `True` |  | Output text file to validate. |
| `contract_path` | `TyperOption` | --contract, -c | `True` |  | Output contract YAML file. |
| `report_path` | `TyperOption` | --report | `False` |  | Write a JSON validation report. |
| `report_schema_path` | `TyperOption` | --report-schema | `False` |  | Validate the JSON report against a generated validation-report.schema.json file. |
| `repair_output_path` | `TyperOption` | --repair-output | `False` |  | Write a deterministically repaired output file when supported. |
| `repair_report_path` | `TyperOption` | --repair-report | `False` |  | Write a JSON repair report. Requires --repair-output. |

### `agentic-kit validate-sections`

- Safety: `READ_ONLY`
- When to use: Validate that a text file contains required literal section markers.
- Dry-run available: `False`

Validate that a text file contains required literal section markers.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `path` | `TyperArgument` | path | `True` |  | Text file to validate. |
| `required_section` | `TyperOption` | --required-section, -s | `True` |  | Required literal section marker. Repeat the option for multiple sections. |

### `agentic-kit work check`

- Safety: `READ_ONLY`
- When to use: Run common human workflow gates without committing or pushing.
- Dry-run available: `False`

Run common human workflow gates without committing or pushing.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `profile` | `TyperOption` | --profile | `False` | `code` | Check profile: minimal, code, docs, or release. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit work discard-changes`

- Safety: `BOUNDED`
- When to use: Preview or execute the explicit destructive discard-all workflow.
- Dry-run available: `True`

Preview or execute the explicit destructive discard-all workflow.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `execute` | `TyperOption` | --execute | `False` | `False` | Discard all feature-branch changes. Dry-run is the default. |
| `expected_signature` | `TyperOption` | --expected-signature | `False` | `` | Optional dry-run signature that must match before execute. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit work finish`

- Safety: `BOUNDED`
- When to use: Finish a human work slice by planning or executing commit, push, PR, merge, and post-merge checks.
- Dry-run available: `True`

Finish a human work slice by planning or executing commit, push, PR, merge, and post-merge checks.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperOption` | --branch | `True` |  | Feature branch to finish. |
| `title` | `TyperOption` | --title | `True` |  | Pull request title. |
| `message` | `TyperOption` | --message | `True` |  | Commit message. |
| `paths` | `TyperOption` | --path | `False` |  | Path to include in the commit. Repeatable. |
| `merge_method` | `TyperOption` | --merge-method | `False` | `squash` | PR merge method. |
| `dry_run` | `TyperOption` | --dry-run, --execute | `False` | `True` | Plan by default. Use --execute to commit, push, and merge. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit work recover`

- Safety: `BOUNDED`
- When to use: Run safe recovery/status commands after interrupted work.
- Dry-run available: `False`

Run safe recovery/status commands after interrupted work.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit work start`

- Safety: `BOUNDED`
- When to use: Start a human patch/slice workflow with the safe standard startup sequence.
- Dry-run available: `False`

Start a human patch/slice workflow with the safe standard startup sequence.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `branch` | `TyperOption` | --branch | `True` |  | Feature branch to create or switch to. |
| `kind` | `TyperOption` | --kind | `False` | `patch` | Human label for the work kind. |
| `from_ref` | `TyperOption` | --from-ref | `False` | `main` | Start new work from this tag or branch ref. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON. |

### `agentic-kit work-order check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit work-order check.
- Dry-run available: `False`

_No parameters._

### `agentic-kit work-order list`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit work-order list.
- Dry-run available: `False`

_No parameters._

### `agentic-kit work-order prepare`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order prepare.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `template_id` | `TyperArgument` | template_id | `True` |  |  |
| `work_order_id` | `TyperArgument` | work_order_id | `True` |  |  |
| `expected_branch` | `TyperArgument` | expected_branch | `True` |  |  |

### `agentic-kit work-order run`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order run.
- Dry-run available: `True`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `work_order_id` | `TyperArgument` | work_order_id | `True` |  |  |
| `execute` | `TyperOption` | --execute | `False` | `False` | Actually run the work order. Omit for dry-run. |

### `agentic-kit work-order show`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit work-order show.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `work_order_id` | `TyperArgument` | work_order_id | `True` |  |  |

### `agentic-kit work-order templates`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order templates.
- Dry-run available: `False`

_No parameters._

### `agentic-kit work-order typed-next`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order typed-next.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON result. |

### `agentic-kit work-order typed-queue-status`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order typed-queue-status.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `inbox_path` | `TyperOption` | --inbox | `False` | `PosixPath('.agentic/typed_work_orders/inbox')` | Typed work order inbox directory. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON queue status. |

### `agentic-kit work-order typed-run`

- Safety: `BOUNDED`
- When to use: Run agentic-kit work-order typed-run.
- Dry-run available: `True`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `work_order_path` | `TyperArgument` | work_order_path | `True` |  |  |
| `execute` | `TyperOption` | --execute | `False` | `False` | Actually run the typed work order. Omit for dry-run. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Print machine-readable JSON result. |

### `agentic-kit workflow cleanup`

- Safety: `BOUNDED`
- When to use: Cleanup completed or stale temporary workflow evidence branches.
- Dry-run available: `False`

Cleanup completed or stale temporary workflow evidence branches.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing tools/next-step.py. |

### `agentic-kit workflow fail-report`

- Safety: `BOUNDED`
- When to use: Upload preserved FAILED workflow evidence without cleanup or retry.
- Dry-run available: `False`

Upload preserved FAILED workflow evidence without cleanup or retry.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing tools/next-step.py. |

### `agentic-kit workflow go`

- Safety: `BOUNDED`
- When to use: Request the configured workflow and run one bounded step.
- Dry-run available: `False`

Request the configured workflow and run one bounded step.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/current_work.yaml and tools/next-step.py. |

### `agentic-kit workflow list`

- Safety: `READ_ONLY`
- When to use: List stored local workflow items.
- Dry-run available: `False`

List stored local workflow items.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/work_items. |

### `agentic-kit workflow request`

- Safety: `BOUNDED`
- When to use: Request the configured declarative workflow without running it.
- Dry-run available: `False`

Request the configured declarative workflow without running it.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/current_work.yaml. |

### `agentic-kit workflow run`

- Safety: `BOUNDED`
- When to use: Run the current workflow, or set a stored workflow item and run it.
- Dry-run available: `False`

Run the current workflow, or set a stored workflow item and run it.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `name` | `TyperArgument` | name | `False` |  | Optional stored workflow item name to set before running. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing tools/next-step.py. |

### `agentic-kit workflow show`

- Safety: `READ_ONLY`
- When to use: Show the current workflow request or one stored workflow item.
- Dry-run available: `False`

Show the current workflow request or one stored workflow item.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `name` | `TyperArgument` | name | `False` |  | Optional stored workflow item name. |
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/current_work.yaml. |

### `agentic-kit workflow state`

- Safety: `READ_ONLY`
- When to use: Show guided workflow state; shortcut for workflow status --explain.
- Dry-run available: `False`

Show guided workflow state; shortcut for workflow status --explain.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/workflow_state. |

### `agentic-kit workflow status`

- Safety: `READ_ONLY`
- When to use: Print the current workflow state and bounded evidence pointers.
- Dry-run available: `False`

Print the current workflow state and bounded evidence pointers.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing .agentic/workflow_state. |
| `explain` | `TyperOption` | --explain | `False` | `False` | Explain the current state and recommend a safe next step. |

### `agentic-kit workflow upload`

- Safety: `BOUNDED`
- When to use: Alias for upload-output.
- Dry-run available: `False`

Alias for upload-output.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing tools/next-step.py. |

### `agentic-kit workflow upload-output`

- Safety: `BOUNDED`
- When to use: Alias for upload-output.
- Dry-run available: `False`

Alias for upload-output.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `project_root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Project root containing tools/next-step.py. |

### `agentic-kit workflow-guard check`

- Safety: `READ_ONLY`
- When to use: Run agentic-kit workflow-guard check.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `paths` | `TyperArgument` | paths | `False` |  |  |

### `agentic-kit workflow-guard diagnose`

- Safety: `BOUNDED`
- When to use: Run agentic-kit workflow-guard diagnose.
- Dry-run available: `False`

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `paths` | `TyperArgument` | paths | `False` |  |  |

### `agentic-kit workspace adopt`

- Safety: `BOUNDED`
- When to use: Analyze an existing repository without writing workspace files.
- Dry-run available: `False`

Analyze an existing repository without writing workspace files.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Target repository root. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit workspace init`

- Safety: `BOUNDED`
- When to use: Plan or create a bounded operating-layer workspace.
- Dry-run available: `True`

Plan or create a bounded operating-layer workspace.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Target repository root. |
| `name` | `TyperOption` | --name | `False` |  | Project name override. |
| `project_type` | `TyperOption` | --type | `False` |  | Project type override: python, node, or generic. |
| `profile` | `TyperOption` | --profile | `False` |  | Workspace profile override. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Write the planned workspace files. |
| `inject_ci` | `TyperOption` | --inject-ci | `False` | `False` | Opt in to GitHub Actions workflow injection. |
| `inject_pre_commit` | `TyperOption` | --inject-pre-commit | `False` | `False` | Opt in to pre-commit snippet injection. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |

### `agentic-kit workspace upgrade`

- Safety: `BOUNDED`
- When to use: Plan or run deterministic workspace manifest schema upgrades.
- Dry-run available: `True`

Plan or run deterministic workspace manifest schema upgrades.

| Parameter | Type | Options | Required | Default | Help |
|---|---:|---|---:|---|---|
| `root` | `TyperOption` | --root | `False` | `PosixPath('.')` | Target repository root. |
| `execute` | `TyperOption` | --execute | `False` | `False` | Write the upgraded manifest and backups. |
| `json_output` | `TyperOption` | --json | `False` | `False` | Emit machine-readable JSON. |
