Wir arbeiten im Repo `{repo_full_name}`.

Arbeite nicht aus Chat-Erinnerung. Quelle der Wahrheit ist der aktuelle Remote-Stand von `main`, die lokalen `agentic-kit`-Kommandos und repo-committete Evidenz.

Lokaler Pfad:
{local_path_command}

Pflichtstart:
./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile
./.venv/bin/agentic-kit rules acknowledge
./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile

Wenn normalize-session nicht PASS meldet: nicht weiterarbeiten, sondern zuerst den Blocker beheben.

Aktueller maschinenlesbarer Zustand:
{prompt_state_json}

Pflichtquellen:
{required_sources}

Transferregeln:
{transfer_rules}

Arbeitsregeln:
1. Keine Arbeit direkt auf main.
2. Für neue Slices bevorzugt: ./.venv/bin/agentic-kit transfer remote-work-start feature/<name>
3. Für PR-Kommandos darf --expected-head-sha current genutzt werden.
4. Komplexe agentic-kit transfer Wrapper sind rohen Git-/Shell-Einzelschritten vorzuziehen.
5. Kanonische Transferdateien bleiben .agentic/transfer/inbox/next_command.py.txt und .agentic/transfer/outbox/last_result.txt.
6. d, f, g, w sind Kommunikationssignale, aber keine Evidenz.
7. Dauerhafte Evidenz gehört ins Repo.
8. Geschützte Dateien nie breit ersetzen.

Nächster sicherer Schritt:
Lies die Pflichtquellen, prüfe den Repo-Zustand mit den Startbefehlen und setze dann den nächsten offenen Slice fort.
