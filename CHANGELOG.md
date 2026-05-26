## v0.4.3 - 2026-05-26

- Release: publish a safety baseline after PR #812 so the merged PR811 closeout, evidence logs, protected-diff hardening, and Tk window-smoke guard are included in the rollback point.
- Governance: refresh status and handoff state after PR811/PR812, preserve the canonical PR811 finalize evidence at `docs/reports/terminal/pr811-merge-finalize.log`, and keep the failed GUI-smoke precursor log visible as repair evidence.
- Safety: require explicit `AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1` before a real Tk window-smoke opens, preventing local gates from aborting the Python process in non-window-safe sessions.
- Testing: keep the successor-handoff YAML/YML freshness regression, protected YAML anchor matching regression, handoff-state preservation tests, and GUI window guard regression in the release line.

Zenodo verification pending until GitHub Release publication and archive processing.
Zenodo Concept DOI: 10.5281/zenodo.20101359

## v0.4.2 - 2026-05-25

- Release: prepare a safety release after the governed rule-registry completion baseline and before successor-chat/documentation-management continuation.
- Governance: preserve the completed rule-registry baseline, including mechanism inventory, migration map, coverage map, direct-test plan, validator, CLI check/report, workflow-guard integration, and patch-preflight integration.
- Planning: carry forward the accepted rule-registry improvement backlog without blocking the next documentation-registry/projection slices.
- Evidence: release-check, documentation gates, registry checks, tests, linting, and package build are expected before tag publication.

Zenodo verification pending until GitHub Release publication and archive processing.
Zenodo Concept DOI: 10.5281/zenodo.20101359

## v0.4.1 - 2026-05-23

- Release: freeze the current functioning documentation-governance baseline before the Document and Artifact Governance OS rebuild.
- Governance: carry forward the release-before-rebuild rule, additive migration strategy, guard-preservation requirement, and parity-proof policy for future registry work.
- Documentation: preserve the hardened CHANGELOG quality guard, active-document language cleanup, local-path protection, terminal-safety rules, and PR CI readiness checks as the stable pre-rebuild baseline.
- Evidence: release metadata, GitHub Release publication, and post-release Zenodo verification are complete for v0.4.1 with version DOI `10.5281/zenodo.20357657`.

Zenodo v0.4.1 DOI: 10.5281/zenodo.20357657
Zenodo Concept DOI: 10.5281/zenodo.20101359

## v0.4.0 - 2026-05-20

Zenodo v0.4.0 DOI: 10.5281/zenodo.20348382
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Released and post-release verified the first bounded GUI MVP line.
- Closed the GUI MVP baseline with three bounded read-only actions visually verified on `main`: `cockpit-readiness`, `doctor`, and `check-docs`.
- Kept `agent-run`, remote mutation, destructive actions, tag creation, release publication, and cleanup actions disabled in the GUI MVP.
- Added and hardened communication, portable execution, bootstrap/drift, terminal safety, and final-summary governance contracts so successor chats must read canonical repo sources before mutation.
- Hardened terminal safety after recurring workflow errors: Ruff is scoped to Python sources, shell files use shell checks, heredocs and risky multiline `python -c` snippets are forbidden in generated terminal blocks, and quote-safety is covered by tests.
- Preserved v0.4.0 release and DOI evidence through `agentic-kit post-release-check --version 0.4.0`, the verified Zenodo version DOI, and committed release metadata.
- Recorded the post-release successor-handoff state so future chats start from repository evidence rather than chat memory.

## v0.3.37 - 2026-05-20

Zenodo v0.3.37 DOI: 10.5281/zenodo.20329450
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Prepared the final GUI-preparation closeout line before the v0.4.0 bounded GUI MVP.
- Preserved documentation-order and status-boundary hardening by keeping `CHANGELOG.md` as the long-term project protocol and `docs/STATUS.md` as the concise live dashboard.
- Preserved release, GUI, no-copy, remote evidence, evidence guard, typed work order, Zenodo, and handoff-prompt history in long-term release/history files instead of expanding current-state docs.
- Kept v0.3.36 current-state cleanup historically visible because it exposed the status-boundary failure mode.
- Closed the pre-v0.4.0 documentation-state line without changing GUI behavior, release automation, or action execution semantics.

## v0.3.36 - 2026-05-21

Zenodo v0.3.36 DOI: 10.5281/zenodo.20329180
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Cleaned up README and CHANGELOG current-state wording before the first bounded Tkinter cockpit MVP slice.
- Re-established the documentation boundary between concise live state and long-term history: `docs/STATUS.md` remains the current dashboard, while `CHANGELOG.md` carries durable release narrative.
- Kept the release line documentation-only and avoided GUI behavior changes, action execution changes, tag creation, and release publication outside the explicit release workflow.
- Preserved the current-state cleanup as a historical regression anchor because it exposed how status-boundary drift can hide release and GUI-readiness history.
- Verified and recorded the v0.3.36 Zenodo version DOI after release closeout.

## v0.3.35 - 2026-05-20

- Released the pre-GUI core and CLI consolidation line with verified Zenodo version DOI `10.5281/zenodo.20316280`.
- Expanded regression coverage for finalize-guard, local-feature-gate, and release-DOI safety behavior.
- Wired finalize-guard shell classification to the tested Python decision core.
- Treated already-merged PR closeout as an idempotent completion state instead of a false failure.
- Extracted release-gate behavior into the tested Python `release_gate_core`, leaving `tools/ns_release_gate.sh` as a thin adapter.

## v0.3.34 - 2026-05-20

- Hardened the pre-GUI portable Python core by adding typed work-order unit-test coverage, explicit `./ns dev-local-feature-gate` routing, and a shared local feature gate core.
- Added a tested finalize-guard decision core with module CLI/render contract and reachable superseded-branch handling.
- Recorded remote terminal evidence for the v0.3.34 hardening slices before the Tkinter cockpit work starts.

## v0.3.33 - 2026-05-20

- Prepare release metadata for v0.3.33.
- Extract verified release DOI archive from README into docs/releases/VERIFIED_RELEASES.md.
- Keep README within documentation gate limits while preserving DOI history.
- Keep Tkinter explicitly deferred until after this release is verified.

## v0.3.32 - 2026-05-20

Zenodo v0.3.32 DOI: 10.5281/zenodo.20314341

- Prepare release metadata for v0.3.32.
- Add release-preflight for before-metadata release phase validation.
- Add evidence clean-check to prevent self-dirty terminal log false failures.
- Keep Tkinter explicitly deferred until after this release is verified.

## v0.3.31 - 2026-05-20

Zenodo v0.3.31 DOI: 10.5281/zenodo.20313834

- Prepare release metadata for v0.3.31.
- Close out pre-GUI execution hardening with terminal evidence guard support.
- Add typed Work Order evidence contract and runtime validation.
- Keep Tkinter explicitly deferred until after this release is verified.

## v0.3.30 - 2026-05-20

Zenodo v0.3.30 DOI: 10.5281/zenodo.20308526
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Prepare release metadata for v0.3.30.
- GUI readiness hardening closeout: ActionResult core contract, `cockpit run --json`, registry-only action contract, Queue-State contract, and Evidence-State contract.
- Tkinter implementation remains explicitly deferred until after this contract baseline is released and post-release verified.
- Zenodo verification pending until the GitHub Release exists and the version-specific DOI is recorded.

## v0.3.29 - 2026-05-20

- Post-release verification complete: GitHub Release exists, Zenodo concept DOI `10.5281/zenodo.20101359`, verified v0.3.29 DOI `10.5281/zenodo.20303218`.

Zenodo v0.3.29 DOI: 10.5281/zenodo.20303218
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Hardened communication artifact GC before GUI readiness: symlink rejection, protected evidence coverage, TTL-based local tmp-log cleanup, and GC closeout documentation.
- Added a safe file replacement helper to prevent malformed generated Python replacements from corrupting source files.
- Recorded quote-guard hardening for nested shell/Python quote-layer failures.

## v0.3.28

- Prepare release metadata for v0.3.28.
- Post-release verification complete: GitHub Release exists, Zenodo concept DOI `10.5281/zenodo.20101359`, verified v0.3.28 DOI `10.5281/zenodo.20286394`.

Zenodo v0.3.28 DOI: 10.5281/zenodo.20286394
Zenodo Concept DOI: 10.5281/zenodo.20101359

## v0.3.27

- Prepare release metadata for v0.3.27.

## v0.3.26

- Prepare release metadata for v0.3.26.

## v0.3.25
- Post-release verification complete: GitHub Release exists, Zenodo concept DOI `10.5281/zenodo.20101359`, verified v0.3.25 DOI `10.5281/zenodo.20273989`.

- Prepare release metadata for v0.3.25.

## v0.3.24
- Post-release verification complete: GitHub Release exists, Zenodo concept DOI `10.5281/zenodo.20101359`, verified v0.3.24 DOI `10.5281/zenodo.20270197`.

- Prepare release metadata for v0.3.24.

## v0.3.23
Zenodo v0.3.23 DOI: 10.5281/zenodo.20261956
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Prepare release metadata for v0.3.23.

# Changelog

## v0.3.22

- Continue hardening deterministic no-copy release and finalization workflows.
- Add safeguards for recurring non-semantic release-cycle failure modes.

## v0.3.21 DOI: 10.5281/zenodo.20258057

- Add no-copy release shortcut commands for release preparation, release gating, and confirmation-gated release publishing.
- Harden `./ns up` PR completion for safer no-copy workflows.

## v0.3.20 - 2026-05-17

Zenodo v0.3.20 DOI: 10.5281/zenodo.20256637

Release focus: experimental local Tkinter GUI cockpit.

- Add the experimental `agentic-kit-gui` entry point.
- Reuse the existing cockpit action registry instead of creating a second GUI command system.
- Show registered cockpit actions with action details, safety status, and command metadata.
- Add a persistent GUI output widget for command output and blocked-action messages.
- Keep the GUI read-only by default: bounded and destructive actions remain blocked by the shared cockpit action layer.
- Document Tk setup requirements for macOS/Homebrew, including `python-tk@3.13`.
- Add GUI/Tk smoke expectations to the test gates.

## v0.3.19 - 2026-05-16

Zenodo v0.3.19 DOI: 10.5281/zenodo.20246121
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `agentic-kit cockpit select` as an inspect-only numbered action-selection view backed by the cockpit action registry.
- Added repo-local `./ns select` as a thin adapter to `agentic-kit cockpit select`.
- Added a numbered `./ns select` entry to `./ns-menu` without adding new shell execution logic.
- Kept bounded and destructive execution semantics unchanged: `select` lists actions only, while `cockpit run` remains the only execution path.
- Added regression coverage for the selection renderer, CLI command, and `ns` / `ns-menu` adapters.

## v0.3.18 - 2026-05-16

Zenodo v0.3.18 DOI: 10.5281/zenodo.20245754
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Updated `./ns-menu` so it no longer clears the terminal by default; screen clearing is now opt-in via `NS_MENU_CLEAR=1`.
- Added a numbered `./ns actions --json` entry so the menu can consume the schema-versioned cockpit action inventory.
- Added regression coverage for non-clearing menu behavior and the cockpit JSON menu entry, raising the suite to 217 tests.

## v0.3.17 - 2026-05-16

Zenodo v0.3.17 DOI: 10.5281/zenodo.20245113
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `agentic-kit cockpit actions --json` for schema-versioned machine-readable cockpit action inventory output.
- Kept human `agentic-kit cockpit actions` output unchanged.
- Used raw Typer output for JSON so consumers can parse it without Rich rendering artifacts.
- Added regression coverage for JSON schema stability, CLI parseability, and non-execution of inventory listing.

## v0.3.16 - 2026-05-16

Zenodo v0.3.16 DOI: 10.5281/zenodo.20244944
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `./ns cockpit-run <action-id>` as a conservative repo-local shortcut to the existing cockpit action layer.
- Added a read-only `./ns cockpit-run git.status` entry to `./ns-menu`.
- Kept bounded and destructive cockpit actions out of the menu path; safety decisions remain centralized in `run_cockpit_action(...)`.
- Added regression coverage for shortcut routing, menu visibility, and shell-safety constraints.

## v0.3.15 - 2026-05-16

Zenodo v0.3.15 DOI: 10.5281/zenodo.20244397
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added `agentic-kit cockpit run <action-id>` for registered read-only cockpit actions.
- Added a structured cockpit action result and execution layer with argument-vector command execution.
- Kept bounded cockpit actions blocked without explicit allow and destructive cockpit actions blocked.
- Updated cockpit safety documentation and gate expectations for the action execution layer.

## v0.3.14 - 2026-05-16

Zenodo v0.3.14 DOI: 10.5281/zenodo.20242582
Zenodo Concept DOI: 10.5281/zenodo.20101359

- Added the Local Cockpit Foundation with read-only `agentic-kit cockpit status` and `agentic-kit cockpit actions` commands.
- Added a structured cockpit action inventory with explicit safety classification for read-only and bounded actions.
- Added repo-local `./ns cockpit` and `./ns actions` shortcuts plus matching `./ns-menu` entries.
- Documented the future shared action-layer direction for CLI, shell/menu adapters, and a later Tkinter cockpit without shell-quoting based command synthesis.
- Refreshed README, documentation coverage, TEST_GATES, STATUS, and CURRENT_HANDOFF after the Local Cockpit Foundation merge.

## v0.3.13 - 2026-05-16

Zenodo v0.3.13 DOI: 10.5281/zenodo.20241908

- Integrated document lifecycle auditing into `agentic-kit doctor`.
- Updated state and handoff documentation after the doctor lifecycle integration.
- Kept `doc-lifecycle-audit` available as a direct read-only smoke check while making lifecycle findings part of the standard doctor gate.

## v0.3.12 - 2026-05-15

Zenodo v0.3.12 DOI: 10.5281/zenodo.20218213

- Added the read-only Pattern Advisor catalog with stable local pattern IDs.
- Added advisory-only `agentic-kit patterns list` and `agentic-kit patterns show <id>` commands.
- Documented Pattern Advisor MVP boundaries: no gates, no automatic architecture decisions, no workflow-state mutation, and no candidate capture or promotion.

## v0.3.11 - 2026-05-15

- Added repo-local workflow-item shortcuts for listing, showing, running, uploading, and status checks through `./ns` aliases.
- Added stored workflow-item support for the Pattern Advisor read-only catalog MVP preparation path.
- Fixed named workflow-item runs so temporary item selection does not permanently replace `.agentic/current_work.yaml`.
- Refreshed state and handoff documentation after the workflow-item shortcut and current-work isolation slices.

Zenodo v0.3.11 DOI: 10.5281/zenodo.20215460

## v0.3.10 - 2026-05-15

Release candidate for the workflow shortcut and Pattern Advisor contract line.
