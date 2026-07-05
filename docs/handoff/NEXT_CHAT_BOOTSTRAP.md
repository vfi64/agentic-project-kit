# NEXT CHAT BOOTSTRAP

This file is a deterministic projection of `docs/reports/handoff-packages/latest/successor_context.yaml`.
Do not start from chat memory. Read the Successor Handoff Package first.

## Current verified repository state

- Repo: `vfi64/agentic-project-kit`
- HEAD: `57c5e7572ec9a8456fdd8606ba91e67d590afd3d` (`57c5e757`)
- Handoff freshness marker: `57c5e757`
- Branch at generation: `docs/post-pr1721-handoff-refresh`
- Worktree clean at generation: `False`

## Successor handoff package

- `docs/reports/handoff-packages/latest/successor_context.yaml`
- `docs/reports/handoff-packages/latest/source_manifest.json`
- `docs/reports/handoff-packages/latest/validation_report.json`
- `docs/reports/handoff-packages/latest/successor_prompt.md`

## Canonical chat-switch prompt files

- Start a successor chat with `docs/handoff/START_NEW_CHAT_PROMPT.md`.
- Before leaving a chat, run the closeout routine in `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`.

## Bootstrap-Akzeptanzbremse

Zusätzliche Startbremse nach dem Bootstrap:

Nach Ausführung des Bootstrap-Blocks darfst du nicht sofort mit neuer Arbeit beginnen. Werte zuerst ausschließlich das Bootstrap-Log aus.

Prüfe:
- `RC=0`
- `RESULT=NEW_CHAT_BOOTSTRAP_DONE`
- `main == origin/main`
- Worktree clean
- `post-merge-check PASS` mit `refresh_required=False`, `result=NOOP`, `next_safe_action=none`
- Wenn `validation_report.generated_head` vom aktuellen HEAD abweicht, akzeptiere nur die
  durch `post-merge-check` geloggte Evidence `successor_package_head_status=refresh_only_descendant`;
  sonst `BLOCK`.
- `repo-status PASS`
- `docs-audit PASS`
- `validation_report.json PASS`
- `execution_contract.json` wurde gelesen

Gib danach genau eine kurze Statusentscheidung aus:

- `Übergabe akzeptiert, keine Admin-Arbeit nötig.`

oder:

- `BLOCK: ...` mit konkretem Grund aus dem Log.

Beginne erst nach dieser Statusentscheidung mit neuer Arbeit.

Wenn der Bootstrap grün ist:
- PR #1304 nicht erneut validieren.
- Übergabedateien nicht neu erzeugen.
- `prepare-successor-handoff --render-prompt` nicht erneut ausführen.
- Keine Admin-Refresh-Arbeit starten.
- Neue Produktarbeit nur aus frischem, sauberem `main` beginnen.

## Required first action in a successor chat

1. Read the Successor Handoff Package files completely.
2. Run or request the Pflichtstart commands from the package.
3. Verify current main HEAD, local status, open PRs, CI, STATUS, CURRENT_HANDOFF, rule registry, command reference, and final-summary contracts before mutation.
4. If the package, prompts, HEAD, or validation report are stale: stop and repair handoff drift first.

## Open high-priority work

Source: `docs/planning/project_direction.yaml`.

- `transfer-test-plan` (planned): Specify transfer tests for remote, transfer-file, and copy-paste modes for v0.4.12
- `audit-status-current-state` (planned): Add current-state drift audit with STATUS.md consistency checks for v0.4.12
- `send-read-ref-consistency` (planned): Test that g/go reads the gui-transfer-tasks carrier ref for v0.4.12
- `tooltip-idempotence` (planned): Make GUI tooltip attachment idempotent for v0.4.12
- `gui-modularization-smoke-tests` (planned): Add GUI smoke tests before modularizing large GUI files for v0.4.12
- `guided-work-cycle-bar` (planned): Add guided work-cycle bar over existing work wrappers for v0.4.12
- `communication-mode-examples` (planned): Add communication-mode explanations with examples for v0.4.12
- `wrapper-live-status` (planned): Add bounded live status for pr-create-complete for v0.4.12
- `artifact-gc-extension` (planned): Extend artifact-gc instead of adding duplicate log-GC commands for v0.4.12
- `documentation-auto-registration` (planned): Plan documentation auto-registration for post-v0.4.12
- `rule-auto-registration-inventory` (planned): Inventory rule auto-registration prerequisites for post-v0.4.12

### RESULT: PASS ###
