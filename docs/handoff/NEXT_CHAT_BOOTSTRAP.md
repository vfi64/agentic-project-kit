# NEXT CHAT BOOTSTRAP

This file is a deterministic projection of `docs/reports/handoff-packages/latest/successor_context.yaml`.
Do not start from chat memory. Read the Successor Handoff Package first.

## Current verified repository state

- Repo: `vfi64/agentic-project-kit`
- HEAD: `c1215490936f3fa33944b5fac651f25cf327420c` (`c1215490`)
- Handoff freshness marker: `c1215490`
- Branch at generation: `codex/project-direction-schema`
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

Source: `docs/planning/PROJECT_DIRECTION.yaml`.

- `p1-planning-consolidation` (next): Consolidate scattered planning into project direction for v0.4.12
- `p2-workspace-manifest-followup` (planned): Continue workspace manifest and schema-gated operating model work for P2
- `direction-schema-command-migration` (active): Introduce direction schema, command, migration, cleanup, scope, and gate slices for v0.4.12

### RESULT: PASS ###
