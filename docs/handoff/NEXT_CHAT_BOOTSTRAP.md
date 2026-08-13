# NEXT CHAT BOOTSTRAP

This file is a deterministic projection of `docs/reports/handoff-packages/latest/successor_context.yaml`.
Do not start from chat memory. Read the Successor Handoff Package first.

## Current verified repository state

- Repo: `vfi64/agentic-project-kit`
- HEAD: `173d89e6e810852a4eb83288bbb24acdbd39d02e` (`173d89e6`)
- Handoff freshness marker: `173d89e6`
- Branch at generation: `docs/post-pr2086-handoff-refresh`
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

Source: `docs/planning/PROJECT_DIRECTION.yaml` or external workspace state.

- `p5c-physical-migration` (blocked): Plan physical migration after legacy profile deprecation for P5
- `v1-0-milestone` (next): Reach the 1.0 operating-layer stability milestone for unphased
- `v2-0-legacy-profile-removal` (planned): Remove the implicit legacy profile in 2.0.0 for unphased
- `pre-gui-hardening-line` (next): Finish wrapper, evidence, rule-refresh, and closeout hardening before GUI expansion for pre-GUI
- `workflow-kernel-and-transfer-hardening` (planned): Harden next-turn, transfer, branch, PR, evidence, and remote state-machine workflows for pre-GUI
- `release-and-doi-governance` (planned): Keep release metadata, publish, and DOI closeout behind authoritative commands for pre-GUI
- `gui-gatekeeper-workbench` (planned): Build the local gatekeeper/workbench GUI over deterministic actions for GUI
- `documentation-artifact-governance-os` (planned): Convert document, artifact, evidence, and policy control into lifecycle-aware governance for governance
- `master-implementation-q` (active): Master Implementation Q2 rest sequence
- `lifecycle-backlog-clearance` (active): Clear current documentation lifecycle backlog before suite-level strict mode
- `governance-doc-backfill` (active): Backfill reviewed governance document registry entries
- `planning-ideas-residual-cleanup` (planned): Resolve remaining planning and idea residual documents
- `pre-gui-hardening-plan` (active): Execute the pre-GUI hardening backlog in small wrapper-first slices
- `next-turn-workflow-kernel` (active): Move recurring next-step execution from chat discipline into a deterministic local workflow kernel
- `release-command-authority` (active): Keep release preparation, publishing, and DOI closeout under explicit command authority
- `rule-registry-hardening` (active): Preserve active rule identity, source validation, and refresh handshakes
- `portability-and-ns-closeout` (planned): Finish replacing legacy ns adapter dependencies with Python-backed agentic-kit commands
- `gui-workbench-plan` (planned): Implement the GUI gatekeeper/workbench as a view over governed action specs
- `docs-centralize-and-remove-command` (planned): Build governed docs centralize-and-remove command before K3
- `standard-error-hardening-backlog` (active): Standard-error hardening backlog and legacy ns command coverage map
- `post-merge-lifecycle-state-model` (active): Post-merge lifecycle state model and command authority
- `mechanize-doc-registry-scope-reconcile` (planned): Mechanize documentation registry scope reconciliation
- `mechanize-failure-mode-review-automation` (planned): Mechanize failure-mode review automation
- `mechanize-pre-gui-hardening-readiness` (planned): Mechanize pre-GUI hardening readiness
- `mechanize-operating-layer-public-onboarding-evidence` (planned): Mechanize operating-layer public onboarding and evidence
- `reports-retention-policy` (planned): Mechanize report and evidence retention policy
- `agf-dpa-adoption-tracker` (blocked): Track AGF/DPA Package-G adoption evaluation without implementation claims

### RESULT: PASS ###

Command manifest entrypoint:
- MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json (manifest_sha: 4a6368de864c). Every reply containing commands MUST start with: COMMAND_MANIFEST_ACK 4a6368de864c. Consult `agentic-kit command-for` before proposing commands and choose the most specific available Kit workflow command.
- Before proposing ANY command run/consult `agentic-kit command-for` and choose the most specific available Kit workflow command.
- raw git/gh commands with a mapped wrapper are rejected by instruction lint.

Command reference contract:
- Read `docs/reference/agentic-kit-commands.json` before composing agentic-kit commands.
- Read `docs/reference/AGENTIC_KIT_COMMANDS.md` before composing agentic-kit commands.
- `must_not_reconstruct_commands_from_memory: true`.
- Treat `source_hashes` as freshness evidence.
source_hashes:
- docs/reference/AGENTIC_KIT_COMMANDS.md: 0200ba8c7dc99792004a14dd522129f50eba4abcac4f411b38ad856db905a23c
- docs/reference/agentic-kit-commands.json: f1af5c2d038a7bf6ad6c55ede61bec1b7a8347173ffa46f3f599ac96127aada7
