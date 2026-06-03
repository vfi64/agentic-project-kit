Wir arbeiten im Repo `vfi64/agentic-project-kit`.

Arbeite nicht aus Chat-Erinnerung. Lies zuerst Bootloader und Repo-Pflichtquellen.

Lokaler Pfad:

`/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`

Starte mit:

```zsh
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
./.venv/bin/agentic-kit boot prompt
./.venv/bin/agentic-kit rules acknowledge --next-allowed-action run_next_command
git branch --show-current
git status --short
git diff --stat
cat docs/reports/terminal/release-publish-agentic-cli-wip-handoff.md
```

Aktive Aufgabe:

Fortsetzen des dirty WIP auf Branch:

`feature/harden-release-publish-head-guards`

Ziel:

Ein sauberes offizielles `agentic-kit release-publish` Kommando implementieren.

Pflicht:

1. `release_publish_core.py` sauber dynamisch bauen/reparieren.
2. `agentic-kit release-publish` registrieren.
3. Tests auf agentic-kit CLI und Guard-Semantik aktualisieren.
4. Keine `./ns`-Aufrufe innerhalb von `release_publish_core.py`.
5. Version nicht hart auf `v0.4.4` fixieren.
6. Confirmation Token: `publish-v<version>`.
7. Optionaler `--expected-head-sha` mit voller SHA-Prüfung.
8. Guards: main branch, clean tree, local tag absence, remote tag absence, GitHub release absence, created-tag-target guard.
9. Inconclusive remote state blockiert vor Tag-Erzeugung.
10. Kein Push, wenn der erzeugte Tag nicht auf erwarteten/current HEAD zeigt.
11. Falls nötig kleine getestete agentic-kit/core Wrapper für guarded tag create/push ergänzen.

Aktueller Zustand ist dirty WIP, kein PASS.

Erwartete dirty Dateien:

- `src/agentic_project_kit/release_publish_core.py`
- `tests/test_release_publish_core.py`

Bei zusätzlichen dirty Dateien zuerst Drift prüfen.

Verwende file-backed Python patch scripts. Kein fragiles inline `python -c`.

Nach Implementierung mindestens:

```zsh
./.venv/bin/python -m pytest tests/test_release_publish_core.py tests/test_release.py tests/test_release_prep_core.py tests/test_release_preflight_phase.py tests/test_release_doi_safety.py tests/test_v036_release_route_help_safety.py tests/test_repo_ns_entrypoint.py
./.venv/bin/python -m ruff check src/agentic_project_kit/release_publish_core.py src/agentic_project_kit/cli_commands/release.py tests/test_release_publish_core.py
./.venv/bin/python -m ruff check .
./.venv/bin/python -m pytest
```

Nur bei grünen Gates: Diff prüfen, protected-change/governance checks, commit, push, PR, CI abwarten, nur grün mergen, main syncen, handoff refreshen, evidence finalize-log.
