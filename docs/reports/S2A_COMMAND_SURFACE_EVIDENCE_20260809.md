Status: analysis
Status-date: 2026-08-09
Scope: S2a command-surface and safety evidence only
Branch: codex/s2a-command-surface-evidence

# S2a Command Surface and Safety Evidence

This slice does not change the command manifest, command metadata, safety labels,
GUI surfaces, or compatibility contracts. It records evidence and candidate
classifications for maintainer adjudication before S2b.

## Model Boundary

- `surface` answers which role a command plays for humans, GUI, or agents.
- `safety` answers which mutation the command may perform.
- The two dimensions are independent. `READ_ONLY` is not automatically diagnostic,
  and `primitive` is not an instability claim.

## Evidence Sources

- `ci`: `.github/workflows`
- `gui_action`: `src/agentic_project_kit/action_specs.py`, `src/agentic_project_kit/gui_button_catalog.py`, `src/agentic_project_kit/gui_action_execution.py`, `src/agentic_project_kit/gui_action_views.py`, `src/agentic_project_kit/gui_cockpit_actions.py`, `src/agentic_project_kit/gui_cockpit_task.py`, `src/agentic_project_kit/gui_tkinter_shell.py`
- `handoff_transfer`: `docs/handoff`, `docs/reports/handoff-packages/latest`, `.agentic/transfer_safety_rules.yaml`, `src/agentic_project_kit/patch_cycle_workflow.py`, `src/agentic_project_kit/cli_commands/transfer_context_flow.py`, `src/agentic_project_kit/cli_commands/transfer_diagnostics.py`, `src/agentic_project_kit/cli_commands/transfer_handoff_flow.py`, `src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py`, `src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py`
- `current_docs`: `README.md`, `docs/WORKFLOW_OUTPUT_CYCLE.md`, `docs/TEST_GATES.md`, `docs/planning/PROJECT_DIRECTION.yaml`, `docs/planning/PROJECT_DIRECTION.md`, `docs/architecture/ARCHITECTURE_CONTRACT.md`, `docs/releases/VERIFIED_RELEASES.md`
- `historical_sample`: `docs/reports/command_runs`, `docs/reports/release`, `docs/reports/workflows`, `docs/reports/remote-branch-hygiene`
- `tests`: `tests`
- `command_reference`: `docs/reference/AGENTIC_KIT_COMMANDS.md` is the generated catalog authority and is intentionally not counted as observed usage.
- Current action registry CLI evidence: `agentic-kit actions list` returned five actions:
  - `pr-check-merge	remote_mutation	Check and optionally merge a pull request`
  - `release-verify	read_only	Verify an already published release`
  - `release-prepare	local_only	Prepare release metadata`
  - `doi-record	local_only	Record verified DOI metadata`
  - `finalize-release	local_only	Finalize repository state after release closeout`

## Summary

- Registered manifest commands: 250
- Candidate surface counts: diagnostic=121, orchestrator=27, primitive=102
- Current safety counts: BOUNDED=164, DESTRUCTIVE=11, READ_ONLY=75
- Commands with observed current/sample usage outside the generated command reference: 177
- Safety anomaly candidates: 9
- Boundary cases captured for S2b adjudication: 54

## Candidate Surface Examples

### orchestrator
- `agentic-kit dpa final-closeout-check`
- `agentic-kit evidence commit-paths`
- `agentic-kit evidence finalize-log`
- `agentic-kit github-create`
- `agentic-kit init`
- `agentic-kit post-release-doi-closeout`
- `agentic-kit release prepare`
- `agentic-kit release ready`

### diagnostic
- `agentic-kit actions list`
- `agentic-kit actions show`
- `agentic-kit audit-absolute-path-portability`
- `agentic-kit audit-command-authority`
- `agentic-kit audit-command-manifest`
- `agentic-kit audit-doc-currency`
- `agentic-kit audit-doc-orphans`
- `agentic-kit audit-mutation-lock-coverage`

### primitive
- `agentic-kit artifact-gc`
- `agentic-kit boot closeout`
- `agentic-kit boot prompt`
- `agentic-kit boot write`
- `agentic-kit cockpit run`
- `agentic-kit cockpit select`
- `agentic-kit commands sync-entrypoints`
- `agentic-kit dev local-feature-gate`

## Boundary Cases

- `agentic-kit artifact-gc` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit boot closeout` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit boot prompt` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit doc-mesh-repair` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit doc-registry reconcile` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit docs lifecycle apply` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit docs-registry` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit dpa current-handoff-refresh` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit dpa fixture-evidence` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit dpa readonly-probe-execution` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit dpa repo-adoption-assessment` -> `diagnostic` (medium): DPA gate/readiness command; may become orchestrator if it writes evidence
- `agentic-kit dpa stable-readiness-check` -> `diagnostic` (medium): DPA gate/readiness command; may become orchestrator if it writes evidence
- `agentic-kit evidence clean` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit evidence finalize-log` -> `orchestrator` (high): listed lifecycle/user-operation wrapper
- `agentic-kit gui initial-llm-prompt` -> `primitive` (low): technical building block or delegated workflow step
- `agentic-kit patch-preflight` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit patch-scope-preflight` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit pr-closeout` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit pr-hygiene` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit profile-explain` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit project-direction` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit release-metadata-authority-gate` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit release-notes-generate` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit release-preflight` -> `primitive` (low): default pending semantic adjudication
- `agentic-kit remote-branch-hygiene` -> `primitive` (low): default pending semantic adjudication

## Safety Anomaly Candidates

- `agentic-kit boot write` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.
- `agentic-kit docs removed-source-audit` [READ_ONLY]: name suggests mutation while current safety is READ_ONLY; Review for possible under-classification; name suggests mutation despite READ_ONLY safety.
- `agentic-kit evidence commit-paths` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.
- `agentic-kit handoff post-merge-refresh-status` [DESTRUCTIVE]: name/contract appears diagnostic but manifest safety is DESTRUCTIVE; Review whether fail-closed destructive safety is intentional for a status/check command.
- `agentic-kit state mode-write` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.
- `agentic-kit transfer commit` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.
- `agentic-kit transfer diagnose-removed-ns-commands` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.
- `agentic-kit transfer post-merge-check` [DESTRUCTIVE]: name/contract appears diagnostic but manifest safety is DESTRUCTIVE; Review whether fail-closed destructive safety is intentional for a status/check command.
- `agentic-kit transfer push-current` [BOUNDED]: bounded mutator-like command without manifest dry-run flag; Review dry-run or exact-scope guard evidence for bounded mutation.

## Maintainer Adjudication Request

S2b should adjudicate the three-value surface model first: `orchestrator`,
`diagnostic`, `primitive`. The JSON report provides per-command candidate
surface, observed usage, confidence and evidence. Do not request 250 separate
maintainer decisions unless a boundary-case command materially changes the model.

## Machine Report

Full per-command evidence: `docs/reports/S2A_COMMAND_SURFACE_EVIDENCE_20260809.json`.
