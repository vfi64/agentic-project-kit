## Machine-readable execution contract

The markdown successor prompt is a compact projection. The machine-readable files take precedence.

Read first: `execution_contract.json`, `successor_context.yaml`, `validation_report.json`, and `source_manifest.json`.

## Durable agentic-kit operating model

- scope: `durable-agentic-kit-operating-model`
- agentic-kit wrappers are the authoritative control plane.
- Use the rule system, command reference, documentation registry, project direction authority, the `agentic-kit project-direction` command, the `agentic-kit docs-reconciliation` command, gates, evidence logs, report-retention GC, and successor handoff package as active subsystems.
- GC is technical retention, not semantic documentation migration.
- Historical `ns` migration documents are not active rule locations.

Source authorities:
- `.agentic/compiled_agent_context.yaml`
- `.agentic/transfer_safety_rules.yaml`
- `.agentic/transfer/one_command_transfer_protocol.yaml`
- `docs/planning/PROJECT_DIRECTION.yaml`
- `docs/DOCUMENTATION_REGISTRY.yaml`
- `docs/reference/agentic-kit-commands.json`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`

Critical rule IDs:
- `local-copy-paste-protocol` (critical)
- `strict-start-decision` (critical)
- `bootstrap_acceptance_gate` (critical)
- `wrapper-first-complete-development-cycle` (critical)
- `successor-package-not-prompt-only` (critical)
- `documentation-authority-model` (critical)
- `repo-backed-rules-and-gates` (critical)
- `gc-retention-not-document-migration` (critical)
- `ns-legacy-not-active-control-plane` (critical)
- `generated-handoff-projection-update-policy` (critical)
- `patch-cycle-diagnostic-gate` (critical)
- `copy-paste-output-discipline` (critical)
- `protected-file-preservation` (critical)

## Current continuation state

- branch: `docs/post-pr1736-handoff-refresh`
- head_matches_origin_main: `True`
- worktree_clean: `False`
- open_tasks_source: `docs/planning/PROJECT_DIRECTION.yaml`
- document_registry_source: `docs/DOCUMENTATION_REGISTRY.yaml`
- Current state is volatile continuation data, not a durable rule source.

## Wrapper-first complete development cycle

Normal feature lifecycle: feature branch -> tests/audits -> `transfer protected-diff-plan` -> `transfer commit` -> `rules acknowledge` -> fresh successor/LLM context -> `transfer pr-create-complete ... --post-merge-complete` -> sync main -> `transfer post-merge-check` on main -> `transfer repo-status` -> docs/program/standard gates -> final successor handoff package.

`transfer post-merge-check` is a main/post-merge lifecycle check, not a feature-branch pre-PR gate. Use `transfer repo-status` for feature-branch cleanliness.

## Handoff package precedence

- prompt_is_projection_only: `True`
- machine_readable_files_take_precedence: `True`
- source_of_truth: `generator_and_machine_readable_successor_package`
- generator_command: `agentic-kit transfer prepare-successor-handoff --render-prompt`
- Markdown handoff files and latest package files are generated projections; update generator/contract/rule sources first, then regenerate projections.
- Forbidden update path: manual direct edits to generated handoff projections as the primary source of new rules.
- Do not use stale copied prompt text or `NEW_CHAT_HANDOFF_PROMPT.md` as sole authority.

## Patch-cycle diagnostic gate

After one failed patch, exactly one direct correction is allowed. After a second failure in the same patch family, stop mutations, run bounded diagnosis, classify product bug versus test-model bug, and record `next_mutation_allowed`.

## Local copy-and-paste protocol

Use exactly one complete Bash block per local action. The block must start by changing into the repository root, write verbose output to `~/Downloads/*.log`, and end by printing `LOG=...` and `RC=...`.

Chat output after local blocks should be only `LOG=...` and `RC=...`; large diagnostics belong in compact JSON summaries or log files.

Forbidden local-command patterns: loose command fragments, manual editor instructions, naked `python`, naked `pytest`, `git add .`, `{ ... } > "$OUT" 2>&1` as the recommended logging pattern, `cat` of whole diagnostic files, and unbounded grep over reports/outbox/generated logs.

# Successor Chat Prompt

Du bist ein neuer LLM-/Coding-Chat für das Repo `vfi64/agentic-project-kit`.

Arbeite nicht aus Chat-Erinnerung. Quelle der Wahrheit ist der aktuelle Remote-Stand von `main`, der lokale Repo-Zustand, repo-/log-backed Evidenz und das maschinenlesbare Successor-Paket.

## Pflichtstart

```bash
cd /path/to/agentic-project-kit
./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile
./.venv/bin/agentic-kit rules acknowledge
./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile
git branch --show-current
git status -sb
git status --short
./.venv/bin/agentic-kit transfer post-merge-check
./.venv/bin/agentic-kit transfer repo-status
```

## Zuerst lesen

- `docs/reports/handoff-packages/latest/successor_context.yaml`
- `docs/reports/handoff-packages/latest/source_manifest.json`
- `docs/reports/handoff-packages/latest/validation_report.json`
- `docs/reports/handoff-packages/latest/execution_contract.json`
- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`

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

## Aktueller Paketstand

```json
{
  "open_tasks": [
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "p1-planning-consolidation",
      "status": "next",
      "summary": "Consolidate scattered planning into project direction for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "p2-workspace-manifest-followup",
      "status": "planned",
      "summary": "Continue workspace manifest and schema-gated operating model work for P2"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "pre-gui-hardening-line",
      "status": "next",
      "summary": "Finish wrapper, evidence, rule-refresh, and closeout hardening before GUI expansion for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "workflow-kernel-and-transfer-hardening",
      "status": "planned",
      "summary": "Harden next-turn, transfer, branch, PR, evidence, and remote state-machine workflows for pre-GUI"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "release-and-doi-governance",
      "status": "planned",
      "summary": "Keep release metadata, publish, and DOI closeout behind authoritative commands for pre-GUI"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "gui-gatekeeper-workbench",
      "status": "planned",
      "summary": "Build the local gatekeeper/workbench GUI over deterministic actions for GUI"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "documentation-artifact-governance-os",
      "status": "planned",
      "summary": "Convert document, artifact, evidence, and policy control into lifecycle-aware governance for governance"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "direction-schema-command-migration",
      "status": "active",
      "summary": "Introduce direction schema, command, migration, cleanup, scope, and gate slices for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "pre-gui-hardening-plan",
      "status": "active",
      "summary": "Execute the pre-GUI hardening backlog in small wrapper-first slices for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "next-turn-workflow-kernel",
      "status": "active",
      "summary": "Move recurring next-step execution from chat discipline into a deterministic local workflow kernel for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "release-command-authority",
      "status": "active",
      "summary": "Keep release preparation, publishing, and DOI closeout under explicit command authority for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "rule-registry-hardening",
      "status": "active",
      "summary": "Preserve active rule identity, source validation, and refresh handshakes for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "portability-and-ns-closeout",
      "status": "planned",
      "summary": "Finish replacing legacy ns adapter dependencies with Python-backed agentic-kit commands for v0.4.12"
    },
    {
      "files": [
        "docs/planning/PROJECT_DIRECTION.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "gui-workbench-plan",
      "status": "planned",
      "summary": "Implement the GUI gatekeeper/workbench as a view over governed action specs for v0.4.x"
    }
  ],
  "recent_lessons": [
    "The old prepare-successor-handoff mechanism is not sufficient as a standalone chat-switch source.",
    "Successor handoff must combine repo-backed long-term context with explicit short-term local work state.",
    "Generated prompt files must be deterministic projections, not accumulative append targets.",
    "Stale prompt markers, literal backslash-n artifacts, and old current-state PR anchors must block handoff trust.",
    "The copy prompt must be usable by other LLMs, not only ChatGPT.",
    "After v0.4.9, release metadata preparation must have one supported agentic-kit route before manual-metadata gates are tightened.",
    "release_publish_core must not remain able to execute removed ./ns release routes after the ns entrypoint removal."
  ],
  "repo": {
    "branch": "docs/post-pr1736-handoff-refresh",
    "full_name": "vfi64/agentic-project-kit",
    "head": "f00e6c86840d41716ca1afdaa6e82b36ecc6a513",
    "head_matches_origin_main": true,
    "head_short": "f00e6c86",
    "local_path": "cd /path/to/agentic-project-kit",
    "origin_main": "f00e6c86840d41716ca1afdaa6e82b36ecc6a513",
    "origin_main_short": "f00e6c86",
    "worktree_clean": false
  }
}
```

## Arbeitsregeln

- Deutsch, knapp, direkt.
- Keine langen Terminalausgaben in den Chat ziehen.
- Große Ausgaben nach `~/Downloads/*.log` umleiten und nur `LOG=...` posten.
- Vor Commit: tatsächlichen Diff inspizieren, Tests laufen lassen, protected-diff-plan ausführen.
- Bei `BLOCK` oder `FAIL`: sofort stoppen, Diagnose statt Weiterarbeiten.
- Aktive Aufgaben stammen aus `docs/planning/PROJECT_DIRECTION.yaml`; alte Planungsdokumente sind keine Startautorität.
- Allgemeingültige Regeln stehen in `execution_contract.json.general_contract`; aktueller Fortsetzungspunkt steht in `execution_contract.json.current_state_contract` und `successor_context.yaml`.
- `successor_prompt.md` ist nur Projektion. Maschinenlesbare Dateien haben Vorrang.
- Komplexe `agentic-kit`-Wrapper haben Vorrang vor selbstgebauten Git-/GitHub-/Handoff-/GC-/Release-Blöcken.
- Garbage Collector nur für technische Retention verwenden, nicht für semantische Dokumentenmigration.

## Nächste sichere Entscheidung

1. Wenn `validation_report.json` nicht PASS ist: Handoff-Projektion reparieren.
2. Wenn der Arbeitsbaum dirty ist: nur explizite WIP-Dateien prüfen und abschließen oder sauber dokumentieren.
3. Danach die nächste aktive Aufgabe aus `docs/planning/PROJECT_DIRECTION.yaml` bearbeiten.
