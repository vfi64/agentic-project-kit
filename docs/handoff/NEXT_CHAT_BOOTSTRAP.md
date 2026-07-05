# NEXT CHAT BOOTSTRAP

This file is a deterministic projection of `docs/reports/handoff-packages/latest/successor_context.yaml`.
Do not start from chat memory. Read the Successor Handoff Package first.

## Current verified repository state

- Repo: `vfi64/agentic-project-kit`
- HEAD: `ae0664953a315506b2b2106ae8da628d91288731` (`ae066495`)
- Handoff freshness marker: `ae066495`
- Branch at generation: `codex/remove-obsolete-planning-docs`
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
- `pre-gui-hardening-line` (next): Finish wrapper, evidence, rule-refresh, and closeout hardening before GUI expansion for v0.4.12
- `workflow-kernel-and-transfer-hardening` (planned): Harden next-turn, transfer, branch, PR, evidence, and remote state-machine workflows for pre-GUI
- `release-and-doi-governance` (planned): Keep release metadata, publish, and DOI closeout behind authoritative commands for pre-GUI
- `gui-gatekeeper-workbench` (planned): Build the local gatekeeper/workbench GUI over deterministic actions for GUI
- `documentation-artifact-governance-os` (planned): Convert document, artifact, evidence, and policy control into lifecycle-aware governance for governance
- `direction-schema-command-migration` (active): Introduce direction schema, command, migration, cleanup, scope, and gate slices for v0.4.12
- `pre-gui-hardening-plan` (active): Execute the pre-GUI hardening backlog in small wrapper-first slices for v0.4.12
- `next-turn-workflow-kernel` (active): Move recurring next-step execution from chat discipline into a deterministic local workflow kernel for v0.4.12
- `release-command-authority` (active): Keep release preparation, publishing, and DOI closeout under explicit command authority for v0.4.12
- `rule-registry-hardening` (active): Preserve active rule identity, source validation, and refresh handshakes for v0.4.12
- `portability-and-ns-closeout` (planned): Finish replacing legacy ns adapter dependencies with Python-backed agentic-kit commands for v0.4.12
- `gui-workbench-plan` (planned): Implement the GUI gatekeeper/workbench as a view over governed action specs for v0.4.x

### RESULT: PASS ###
