## Machine-readable execution contract

The markdown successor prompt is a projection of the machine-readable execution contract.

- branch: `docs/post-pr1500-handoff-refresh`
- head_matches_origin_main: `True`
- worktree_clean: `False`

Critical rule IDs:
- `local-copy-paste-protocol` (critical)
- `strict-start-decision` (critical)
- `bootstrap_acceptance_gate` (critical)
- `protected-file-preservation` (critical)

## Local copy-and-paste protocol

Use exactly one complete Bash block per local action. The block must start by changing into the repository root, write verbose output to `~/Downloads/*.log`, and end by printing `LOG=...` and `RC=...`.

Forbidden local-command patterns: loose command fragments, manual editor instructions, naked `python`, naked `pytest`, `git add .`, and `{ ... } > "$OUT" 2>&1` as the recommended logging pattern.

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
        "docs/planning/project_direction.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "project-direction",
      "status": "active",
      "summary": "Unify strategy, roadmap, and ideas into a machine-readable source for v0.4.10"
    },
    {
      "files": [
        "docs/planning/project_direction.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "docs-reconciliation",
      "status": "active",
      "summary": "Reconcile docs/planning, docs/plans, docs/roadmap, docs/strategy, and docs/workflow for v0.4.10"
    },
    {
      "files": [
        "docs/planning/project_direction.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "release-v0.4.10",
      "status": "planned",
      "summary": "Prepare and publish v0.4.10 for v0.4.10"
    },
    {
      "files": [
        "docs/planning/project_direction.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml"
      ],
      "id": "gui-gatekeeper",
      "status": "planned",
      "summary": "Start deterministic GUI gatekeeper for v0.5.0"
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
    "branch": "docs/post-pr1500-handoff-refresh",
    "full_name": "vfi64/agentic-project-kit",
    "head": "24fb9714703d07bba919132e3083c6a60cecfa1e",
    "head_matches_origin_main": true,
    "head_short": "24fb9714",
    "local_path": "cd /path/to/agentic-project-kit",
    "origin_main": "24fb9714703d07bba919132e3083c6a60cecfa1e",
    "origin_main_short": "24fb9714",
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
- Aktive Aufgaben stammen aus `docs/planning/project_direction.yaml`; alte Planungsdokumente sind keine Startautorität.

## Nächste sichere Entscheidung

1. Wenn `validation_report.json` nicht PASS ist: Handoff-Projektion reparieren.
2. Wenn der Arbeitsbaum dirty ist: nur explizite WIP-Dateien prüfen und abschließen oder sauber dokumentieren.
3. Danach die nächste aktive Aufgabe aus `docs/planning/project_direction.yaml` bearbeiten.
