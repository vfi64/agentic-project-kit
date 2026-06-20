# Agentic-Kit Transfer GUI Concept

- schema_version: 1
- kind: agentic_kit_gui_transfer_concept
- external_reference: vfi64/Comm-SCI-Control-private @ `e65d6c8a8c02204420703829a171f9423a5a49bf`
- image_reference_missing: true
- scope: concept only; no GUI implementation in this slice

## Design Target

The GUI should be a control and evidence surface, not a second shell, not a chat clone, and not a release bypass. It should expose a small set of wrapper-backed actions and make the current state, last evidence, and next safe action obvious.

## Structure

Use a main workspace plus a mode-aware side panel. This follows the reference repo's strongest reusable pattern: separate central work surface and grouped panel controls, with state-dependent visibility and guarded actions.

The main workspace should show current branch, clean/dirty state, mode, last command, last log path, RC, next safe action, and a bounded evidence preview. Full logs open externally or in a dedicated bounded viewer.

## Transfer Modes

| Mode | Goal | Minimal Buttons |
| --- | --- | --- |
| Remote | GitHub/PR/CI/Handoff work without bypassing governance | Sync main, Repo status, Post merge check, PR status, Open latest log, Prepare successor handoff, Publish last report, Require fresh LLM context, Run standard gates |
| Transferdateien | Inbox command -> `transfer continue` -> Outbox result | Inbox prüfen, Continue starten, Outbox anzeigen/kopieren/öffnen, Require fresh context, Restore known volatile |
| Copy-and-Paste | Execute complete local block, return only LOG/RC | Copy block vorbereiten, Terminal öffnen, Logpfad anzeigen, Log öffnen, LOG/RC kopieren, Fehlerdiagnose vorbereiten |
| Release | Release-state guarded workflow | Release status, Prep dry-run, Publish dry-run, Post-release check, DOI closeout dry-run |
| Diagnostics | Bounded audit surface | Docs audit, Doc currency, Planning docs audit, NS legacy audit, Program redundancy, Standard gates |

## Terminal Strategy

Use an external-terminal-first architecture for MVP. Embedded cross-platform terminal/PTY support is a later enhancement because it is fragile across macOS, Windows, and Linux. The GUI should open/copy a wrapper-backed command, watch the expected log path, parse compact JSON/RC state, and surface only bounded summaries.

## State Model

Each mode has explicit states in the JSON concept. The important UI rule is one primary next action when possible, with red/yellow/green/gray status semantics:

- green: checked PASS/success/clean/fresh
- yellow: running, stale, warning or unknown
- red: FAIL/BLOCK/dirty when clean required/CI red
- gray: not checked or unavailable

## Boundaries

- No raw shell/Git/GitHub/release logic in GUI.
- No live release action without release-state guard.
- No direct manual edits to generated handoff projections.
- No broad cleanup/delete/reset buttons except explicit safe wrappers with visible warnings.
- No unbounded log dumping into the chat.

See `agentic_kit_transfer_gui_concept.json` for the machine-readable version.
