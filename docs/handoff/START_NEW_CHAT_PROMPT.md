---
schema_version: 2
artifact_type: chat_switch_prompt
role: start_new_chat
current_handoff_marker: 6533a98a
current_branch_at_generation: docs/post-pr2166-handoff-refresh
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
successor_context: docs/reports/handoff-packages/latest/successor_context.yaml
paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - successor_context.yaml
  - source_manifest.json
  - validation_report.json
  - agentic-kit transfer chat-switch-complete
  - AGENTS.md
  - README.md
  - SECURITY.md
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Start New Chat Prompt

Current handoff marker: `6533a98a`.

Copy `docs/reports/handoff-packages/latest/successor_prompt.md` into the successor chat.

The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.

If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.

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

Command manifest entrypoint:
- MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json (manifest_sha: 7f061e6ff4ea). Every reply containing commands MUST start with: COMMAND_MANIFEST_ACK 7f061e6ff4ea. Consult `agentic-kit command-for` before proposing commands and choose the most specific available Kit workflow command.
- Before proposing ANY command run/consult `agentic-kit command-for` and choose the most specific available Kit workflow command.
- raw git/gh commands with a mapped wrapper are rejected by instruction lint.

Command reference contract:
- Read `docs/reference/agentic-kit-commands.json` before composing agentic-kit commands.
- Read `docs/reference/AGENTIC_KIT_COMMANDS.md` before composing agentic-kit commands.
- `must_not_reconstruct_commands_from_memory: true`.
- Treat `source_hashes` as freshness evidence.
source_hashes:
- docs/reference/AGENTIC_KIT_COMMANDS.md: 70def8f6264c2d0dfbd12c9e78a7b59007716029b5e2737a2a803e498863ddfe
- docs/reference/agentic-kit-commands.json: 81730dad5c5c3db1d8099cfa5e1fc247bbe8147e04164919dd43a6ed6c7aba41
## Operational documentation refresh state after PR #2228

Current administrative handoff refresh state is `8922573c` (`Refresh chat-switch handoff package (#2228)`). Continue next only after this post-PR2228 refresh is committed and merged; the next substantive slice must be created from fresh main.
