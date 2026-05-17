# Changelog

## v0.3.20 - 2026-05-17

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