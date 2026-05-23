# Übergabeprompt

## 1. Arbeitsumgebung

Repo: `vfi64/agentic-project-kit`
Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Sicherer Stand

Branch: `main`
Commit: `499f7a6b`
Subject: Surface documentation registry in release checks (#701)
Semantics: `current_main_head`
Working tree expected clean: `true`

Administrative evidence / handoff refresh after this commit is allowed only for status, handoff, summary, prompt, and evidence documents. Product work after `499f7a6b` must be treated as a new substantive slice.

## 3. Release- und Produktstand

Current version: `0.4.1`
Previous version: `0.4.0`
Tag: `v0.4.1`
GitHub release: exists
Zenodo concept DOI: `10.5281/zenodo.20101359`
Verified Zenodo version DOI: `10.5281/zenodo.20357657`
Post-release check: `PASS`

## 4. Pflichtquellen vor jeder Mutation

Nicht aus Chat-Erinnerung starten. Lies zuerst diese repo-basierten Quellen. Wenn eine Quelle fehlt, widersprüchlich ist oder nicht gelesen werden kann, melde Drift und mutiere nicht außer zur Drift-Reparatur.

- `.agentic/compiled_agent_context.yaml`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/TEST_GATES.md`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `.agentic/handoff_state.yaml`
- `AGENTS.md`
- `CHANGELOG.md`
- `README.md`
- `CITATION.cff`
- `docs/releases/VERIFIED_RELEASES.md`
- relevant source files and tests for the requested slice

## 5. Aktueller verifizierter Stand

- `main` steht nach PR #701 auf `499f7a6b Surface documentation registry in release checks (#701)`.
- Keine offenen PRs wurden vor dem Closeout-Slice gesehen.
- v0.4.1 ist getaggt und veröffentlicht.
- GitHub Release v0.4.1 existiert.
- Zenodo Concept DOI: `10.5281/zenodo.20101359`.
- Verifizierte Zenodo Version DOI für v0.4.1: `10.5281/zenodo.20357657`.
- PR #689 hat den v0.4.1 DOI-Metadaten-Closeout auf main gebracht.
- PR #690 hat die finale lokale Verifikation nach PR #689 als Evidence auf main gebracht.
- PR #691 hat Handoff-State und canonical successor handoff prompt nach v0.4.1 aktualisiert.
- PR #692 hat das erste Dokumentationsregistry-Schema und den Guard eingeführt.
- PR #694 hat `docs/STATUS.md` nach dem Registry-Baseline-Slice aktualisiert.
- PR #695 hat `agentic-kit docs-registry` und erste operational/artifact Klassifikationen eingeführt.
- PR #696 hat `agentic-kit docs-registry --report PATH` als JSON-Handoff eingeführt.
- PR #697 hat Registry-Kontext in `docs-audit` sichtbar gemacht.
- PR #698 hat Registry-Kontext in `doc-mesh-audit` sichtbar gemacht.
- PR #699 hat Registry-Kontext in `doc-lifecycle-audit` sichtbar gemacht.
- PR #700 hat Registry-Kontext in `handoff check` und `handoff show` sichtbar gemacht.
- PR #701 hat Registry-Kontext in `release-check` und `post-release-check` sichtbar gemacht.

## 6. Wichtige verifizierte Gates und Evidence

- v0.4.1 `post-release-check --version 0.4.1`: PASS.
- v0.4.1 `docs-audit`: PASS.
- v0.4.1 `handoff-check`: PASS.
- v0.4.1 `./ns dev`: PASS.
- v0.4.1 pytest: 887 passed.
- CI für PR #691 war grün.
- CI für PR #701 war nach einer Testfixture-Korrektur grün: Ruff PASS, Tests PASS, CLI smoke PASS.
- Finales Verify-Log: `docs/reports/terminal/v041-final-main-verify-after-pr689.log`.
- Handoff-Refresh-Log aus dem vorigen Handoff: `docs/reports/terminal/v041-handoff-after-pr690.log`.

## 7. Dokumentationsregistry-Stand

Das neue Dokumentenverwaltungssystem ist noch kein vollständiges DMS, aber die registry-basierte Basis ist stabil genug für kleine Folgeslices.

Vorhanden:

- Registry-Schema in `docs/DOCUMENTATION_REGISTRY.yaml`.
- Registry-Vertrag in `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- Dokumentklassen mindestens für governance/system, planning, architecture, release, operational/automation, user-facing description, evidence/log, generated artifact, temporary artifact und historical archive.
- Pro Klasse vorbereitete Regeln für ownership, freshness, language policy, redundancy boundary, machine readability, retention/GC behavior, update triggers, portability/local-path scanning und gate coverage.
- Struktureller Guard in `check-docs` / `docs-audit`.
- Read-only Registry-CLI und JSON-Report.
- Registry-Sichtbarkeit in docs-audit, doc-mesh-audit, lifecycle-audit, handoff checks, release-check und post-release-check.

Noch nicht vorhanden:

- Keine breite Migration.
- Kein semantischer Qualitätsbeweis durch den Registry-Guard.
- Keine vollständige Artifact-GC-Automation aus der Registry.
- Keine vollständige GUI-Integration der Registry.

## 8. Nächste Hauptaufgabe

Weiter am Dokumentenverwaltungs-Umbau arbeiten, aber nur als kleinen, reversiblen, testgedeckten Slice.

Empfohlener nächster Slice:

1. Artifact-GC-Registry-Planung oder ein weiterer kleiner read-only Registry-Consumer.
2. Keine breite Dokumentenmigration.
3. Keine neue Release- oder Tag-Arbeit.
4. Keine destruktiven GUI- oder Remote-GUI-Aktionen.
5. Bestehende Dokumentationsqualität erhalten, nicht zerstören.
6. Additiv, modular, reversibel, testbar.

## 9. Leitplanken

- Kein neuer Tag.
- Kein neuer Release.
- Keine große Dokumentenmigration.
- Keine destruktiven GUI- oder Remote-GUI-Aktionen.
- Bestehende funktionierende Dokumentenverwaltung darf nicht verschlechtert werden.
- Ruff nur auf Python-Dateien bzw. Python-Quellen, nicht auf Markdown/YAML/CFF.
- Shell-Skripte mit Shell-Checks prüfen, nicht mit Ruff.
- Keine heredocs.
- Keine riskanten mehrzeiligen `python -c`-Blöcke.
- Keine verschachtelten quote-anfälligen Patch-Generatoren.
- Python 3.13 für lokale Gates verwenden.
- Relevante PASS/FAIL-Terminalausgaben nach `docs/reports/terminal/` sichern.
- `d`, `f`, `w`, `p` sind Kommunikationssignale, keine Evidence.

## 10. Kommunikations- und Summary-Regeln

User-Kürzel:

- `d`/`D`: letzter Block scheint fertig; Evidence prüfen, nicht blind fortsetzen.
- `f`/`F`: Fehler gemeldet; zuerst Remote-/lokale Evidence prüfen oder sichern.
- `w`/`W`: weiter im aktuellen Regelrahmen.
- `p`: log-backed PASS akzeptiert.

Final summaries müssen dem Governance-Vertrag folgen und konkrete Werte enthalten:

- `WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED`
- `OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED`
- `NEXT_CHAT_REPLY: p|f|paste-output|continue|stop`

## 11. Erste Arbeitsanweisung für den neuen Chat

Prüfe `main` gegen diesen Handoff, insbesondere aktuellen Branch, HEAD, offene PRs, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, Registry-Dateien und die letzte CI-Evidence. Erst danach mit dem nächsten kleinen Registry-Slice beginnen. Bevorzugter Start: Artifact-GC-Registry-Planung als read-only/additiver Consumer, nicht Migration.
