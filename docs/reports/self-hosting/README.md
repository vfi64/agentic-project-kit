# Self-Hosting-Archiv: Historie, Drift und Qualität (Oktober 2026)

Status: historische Evidence, vorläufig; archiviert über Issue #2505  
Stand der Quellen: 14.–16.10.2026; Kit-Basis `ef78a255` (v1.0.25), Messungen am 16.10. gegen `main` `3f5ab2c`

Dieses Verzeichnis archiviert die Untersuchungen zum Self-Hosting des Agentic Project Kit und seiner Consumer. Die Berichte sind **Evidence**. Sie sind keine Governance-Regel, keine Direction-Entscheidung und kein Produktivitätsbenchmark. Die Markdown- und strukturierten Dateien sind die alleinige Text- und Datenautorität. Die ursprünglichen PDF-/DOCX-Fassungen sind nicht eingecheckt; ihre Hashes stehen in `SOURCE_MANIFEST.json`.

## Dateien

| Datei | Inhalt |
|---|---|
| `HISTORICAL_DEVELOPMENT_20261015.md` | Historie, Architektur, Self-Hosting-/Bootstrapping-These und kritische Einordnung; redigierte Textfassung der 28-seitigen Ergänzungsrevision |
| `figures/` | acht Abbildungen der Historie (zwei durch Tabellen bzw. Verweise ersetzt, siehe R1) |
| `DRIFT_QUALITY_AUDIT_20261015.md` | Drift- und Qualitätsaudit mit den Nachmessungen P1–P3 vom 16.10. |
| `DRIFT_EVENTS_20261015.csv` | selektiertes, belegtes Ereignisregister (E01–E16, HD-01–HD-08); kein Gesamtzähler |
| `DRIFT_METRICS_20261015.json` | Definitionen, Nenner, Zählregeln, Zeitstände, Ergebnisse und ausdrücklich nicht messbare Größen |
| `FINDING_ID_JOIN_20261015.csv` | ID-genauer Kit-/Consumer-Abgleich mit getrennten Statushoheiten (nur IDs, Status, Daten) |
| `reproduce_drift_audit.py` | Reproduktion von Join, PR-Klassifikation, Refresh-Ketten und Hashes |
| `SOURCE_MANIFEST.json` | Revisionen, Blobs, Hashes der eingebrachten Artefakte und der Archivdateien |

## Aussageklassen

| Klasse | Bedeutung | Beispiel |
|---|---|---|
| Historischer Fakt | aus Git, CI, Releases oder kanonischen JSON-Dateien belegt | 83 von 166 Oktober-PRs ändern nur generierte Handoff-Träger |
| Autorenaussage | Einschätzung des Autors, nicht experimentell geprüft | AU03: Die Solo-Entwicklungsgeschwindigkeit war nur durch konsequentes Self-Hosting erreichbar |
| Rekonstruktion | plausible Verknüpfung belegter Punkte | Comm-SCI-Problemlage als Auslöser späterer Kit-Mechanismen |
| Bewertung | Urteil auf Basis der Evidenzstärke | „Evidenced process controls / incomplete effect estimate“ |

## Wichtigste Ergebnisse

- Mechanismen gegen bestimmte Handoff-, Merge- und Zustandsdrift sind belegt; mehrere frühere Fehlübergänge sind repariert.
- Der Anteil zusätzlicher Refresh-Runden nach Produktänderungen sank von 7–8 % (Juli/August) auf 0–1,2 % (September/Oktober). Das ist deskriptiv, nicht kausal.
- Im Oktober sind 50 % der PRs reine Handoff-Refreshs. Sie verbrauchen 22 % der CI-Laufzeit auf PR-Heads.
- Kit und Consumer widersprechen sich bei 16 von 68 Kit-`CLOSED`-Familien; bei einer davon ist der Fall als critical eingestuft.
- Eine Projektionsdrift wurde bestätigt: Die Terminal-Handoff-Projektionen nennen weiterhin Version 0.4.13.
- Nicht messbar sind: die persistierende Gesamtdriftrate, die Recovery-Kosten, der Netto-Produktivitäts- und der Codequalitätseffekt.

## Redaktionen gegenüber den Arbeitsfassungen

Die Arbeitsfassungen stützen sich auch auf private Repositories (AGP Cockpit, Comm-SCI-Control-private). Für die öffentliche Archivierung gilt:

- **R1** Zwei Abbildungen sind ersetzt, weil ihr eingebetteter Text redigierte Inhalte enthielt: das Schichtenmodell durch eine Tabelle, die Phasenübersicht durch einen Verweis auf die Phasentabelle.
- **R2** Private Consumer-Quellen (P01, P02) werden ohne URL zitiert, mit Commit-SHA als Provenance. Aussagen über frühere Sichtbarkeit sind entfernt.
- **R3** Links in das private Comm-SCI-Repository sind durch Datei- bzw. Commit-Angaben ersetzt.
- **R4** Eine Formulierung zu internen Integrationspfaden einer privaten Quelle ist verallgemeinert.
- **R5** Persönliche Kontextangaben sind auf die Verfügbarkeitsaussage reduziert (Nutzungslimits, begrenzte Freizeit).
- **Join-CSV:** Sie enthält keine Titel, Beobachtungs-, Workaround- oder Verifikationstexte aus dem privaten Ledger.
- **Nicht übernommen:** die DOCX/PDF-Binärdateien, darunter 18 nicht referenzierte ältere Bilder im DOCX, und die vollständigen Beobachtungsdaten des Consumer-Ledgers.

## Verhältnis zu anderen Berichten

- `docs/reports/COMMAND_USAGE_AUDIT_20261015.md` misst die Kommandonutzung (statisch, dynamisch, historisch) und ersetzt die vorläufige Kennzahl K43 der Historie.
- Die Statushoheit über Consumer-Findings bleibt beim Consumer; dieses Archiv ändert keinen Ledger.

## Reproduktion

```bash
python3 docs/reports/self-hosting/reproduce_drift_audit.py chains --clone <Kit-Klon mit Historie> --out chains.json
python3 docs/reports/self-hosting/reproduce_drift_audit.py prs --from 2026-10-01 --to 2026-10-15 --cutoff 2026-10-15T19:00:41Z --out prs.json
python3 docs/reports/self-hosting/reproduce_drift_audit.py join --kit external-findings-status.json --consumer AGENTIC_KIT_GREENFIELD_FINDINGS.json --out join.csv
python3 docs/reports/self-hosting/reproduce_drift_audit.py hashes docs/reports/self-hosting/*.md docs/reports/self-hosting/*.csv
```

`prs` benötigt die GitHub-CLI mit Lesezugriff. `join` benötigt eine lokale Kopie des privaten Consumer-Ledgers.
