# Drift- und Qualitätsaudit – Self-Hosting des Agentic Project Kit (Stand 15./16.10.2026)

Status: historische Evidence, deskriptiv; kein Produktivitätsbenchmark, keine Kausalaussage  
Untersuchungsfenster: 09.05.–15.10.2026; Comm-SCI März/April nur als Kontrast  
Bezug: Issue #2505; Grundlage sind das Audit-Paket vom 15.10. (SHA-256 `d4260409…`), die Zwischenberichte im Issue und die Nachmessungen vom 16.10.  
Daten: `DRIFT_METRICS_20261015.json`, `DRIFT_EVENTS_20261015.csv`, `FINDING_ID_JOIN_20261015.csv`  
Reproduktion: `reproduce_drift_audit.py`

## Kurzurteil

**EVIDENCED PROCESS CONTROLS / INCOMPLETE EFFECT ESTIMATE.** Das Kit besitzt nachweislich funktionierende Mechanismen, die bestimmte Zustands-, Handoff-, Dokumentations- und Prozessabweichungen erkennen und begrenzen. Mehrere zuvor reale Fehlübergänge sind belegt repariert. Eine quantitative Abnahme *aller* Driftfälle pro Arbeitszyklus, ein Netto-Produktivitätsgewinn und eine allgemeine Codequalitätssteigerung sind mit den vorhandenen Daten **nicht** messbar.

Die Nachmessung vom 16.10. liefert zwei neue, echte Kennzahlen mit Nenner:

1. Bei **zusätzlichen Refresh-Runden** nach einer Produktänderung (Refresh-Kette ≥ 2) liegt der Anteil im Juli/August bei 7–8 % und im September/Oktober bei 0–1,2 % (Abschnitt 4).
2. Der **administrative Overhead** im Oktober ist präzisiert: 83 von 166 PRs sind laut Diff reine Handoff-Refreshes und verbrauchen 22 % der CI-Laufzeit auf PR-Heads (Abschnitt 5).

## 1. Belegregeln

- **DRIFT_CONFIRMED:** ein belegter Vertragsverstoß. **ALLOWED_ADVANCE:** eine absichtliche, zulässige Fortschreibung. **INCONCLUSIVE:** die Belege reichen nicht aus. **REPAIR_TESTED:** eine Reparatur, geprüft nur im angegebenen Scope. **FIXTURE_EVIDENCE:** geprüft mit simulierten Transporten, nicht live.
- „Erkannt“ ist nicht „verhindert“. Ein grünes Gate zählt nicht als verhinderter Fehler, wenn keine fehlerhafte Aktion nachweisbar blockiert wurde.
- Kit-`CLOSED` und Consumer-`VERIFIED_FIXED` sind getrennte Statushoheiten und keine Synonyme.
- Hohe Commit-, PR- oder CI-Zahlen messen Aktivität, keine Drift.
- Unbeobachtbar ist nicht gleich null. Was nicht messbar ist, steht ausdrücklich in Abschnitt 8.

## 2. Ereignisregister

`DRIFT_EVENTS_20261015.csv` enthält 24 selektierte, belegte Ereignisse: E01–E16 aus dem Audit-Paket und HD-01–HD-08 aus Zwischenbericht 1 des Issues. Das Register ist **kein vollständiger Ereigniszähler** und darf nicht als Zeitreihe einer Driftinzidenz gelesen werden.

Neu am 16.10. geklärt wurde **HD-08**. Die pro PR erzeugten Dateien `docs/reports/terminal/post-prN-successor-chat-handoff.md` rendern ihren Release-Abschnitt aus dem `release`-Block von `.agentic/handoff_state.yaml`. Dort steht weiterhin `current_version: 0.4.13`; der Block wird seit 0.4.13 nicht mehr fortgeschrieben. Das kanonische Successor-Paket und `docs/handoff/CURRENT_HANDOFF.md` zeigen korrekt 1.0.25. Auch die am 16.10. erzeugte Datei `post-pr2506-…` enthält 0.4.13.

Einordnung: **DRIFT_CONFIRMED in einer sekundären, nicht-kanonischen Projektion.** Eine Reparatur gehört in einen eigenen Kit-Slice.

## 3. Finding-ID-Join Kit × Consumer

| Kit-Status | Consumer-Status | Familien |
|---|---|---:|
| CLOSED | VERIFIED_FIXED | 24 |
| CLOSED | FIXED | 28 |
| CLOSED | OPEN | 16 |
| nicht im Kit-Ledger | OPEN | 4 |

- **Quellen:** Kit `external-findings-status.json` bei `ef78a255` (Blob `e7f8d493…`) und der private Consumer-Ledger bei `926e1f70…` (Blob `c2528e9c…`). Der Ledger-Blob ist am Consumer-HEAD vom 16.10. unverändert, der Join ist also aktuell.
- **Bedeutung der 16 CLOSED→OPEN:** Sie sind ein direkt messbarer Widerspruch zweier Statushoheiten, aber keine 16 bewiesenen offenen Codefehler. Bei fünf davon meldet das Kit einen erfolgreichen externen Fixture-Test (KIT-GF-001, -003, -005, -013, -016); der Consumer bleibt unabhängig bei OPEN. Eine der 16 ist im Consumer als *critical* klassifiziert (KIT-GF-010).
- **Verifikationsabstand:** Für 22 der 24 VERIFIED_FIXED-Familien sind beide Daten vorhanden. Median 1 Kalendertag, Mittel 3,1, Maximum 31 (KIT-GF-011). Das sind selektierte Fälle mit Selection Bias; offene und FIXED-Familien sind rechtszensiert. Es ist weder Arbeitszeit noch eine Reparaturdauer aller Defekte.
- **Öffentliche Fassung:** Die Join-CSV enthält bewusst nur IDs, Status, Version, Schweregrad, Daten und Ereignisanker, keine Titel oder Beobachtungstexte aus dem privaten Ledger.

## 4. Refresh-Ketten nach Produktänderungen (P1, neu)

Definition: Für jeden Produkt-Commit auf `main` (first-parent, Stand `3f5ab2c`) wird gezählt, wie viele reine Refresh-Commits direkt folgen. Eine Kette von 1 ist der vorgesehene einzelne Handoff-Refresh. Eine Kette von 2 oder mehr bedeutet eine zusätzliche Refresh-Runde, etwa Successor-Paket plus Handoff-Refresh oder eine Wiederholung.

| Monat | Produkt-Commits | Kette 0 | Kette 1 | Kette 2 | Kette ≥ 3 | Anteil ≥ 2 |
|---|---:|---:|---:|---:|---:|---:|
| 2026-05 | 867 | 820 | 47 | 0 | 0 | 0,0 % |
| 2026-06 | 324 | 39 | 278 | 6 | 1 | 2,2 % |
| 2026-07 | 138 | 4 | 123 | 9 | 2 | 8,0 % |
| 2026-08 | 139 | 7 | 122 | 8 | 2 | 7,2 % |
| 2026-09 | 40 | 1 | 39 | 0 | 0 | 0,0 % |
| 2026-10 | 82 | 0 | 81 | 1 | 0 | 1,2 % |

**Lesart:**
- Im Mai gab es den automatischen Refresh-Mechanismus noch nicht; deshalb dominiert dort Kette 0.
- Seit Juni folgt fast jeder Produktänderung genau ein Refresh.
- Zusätzliche Refresh-Runden waren im Juli/August am häufigsten und sind seit September selten.

Diese Abnahme ist ein **deskriptiver Indikator** für die beherrschte Refresh-Schleife, kein Kausalbeweis. Arbeitsvolumen und Arbeitsart unterscheiden sich stark zwischen den Monaten. Der September ist klein (40 Commits) und enthält eine Pause.

## 5. Administrativer Overhead im Oktober (P2, neu)

Grundlage sind alle 166 PRs mit Erstellungsdatum 01.–15.10.2026 bis zum Zeitpunkt der Issue-Analyse (15.10., 19:00 UTC). Jeder PR wurde nach seinen tatsächlich geänderten Dateien klassifiziert, und die CI-Laufzeit auf seinem Head-SHA wurde gemessen.

| Klasse | PRs | gemergt | CI-Läufe | CI-Wallclock (min) | Median CI je PR (s) |
|---|---:|---:|---:|---:|---:|
| ADMIN_REFRESH_ONLY | 83 | 82 | 83 | 62,9 | 44 |
| PRODUCT_PLUS_HANDOFF | 65 | 63 | 67 | 168,5 | 152 |
| REPAIR_OF_REFRESH_DEFECT | 8 | 8 | 8 | 28,9 | 142,5 |
| OTHER | 10 | 10 | 10 | 22,4 | 139,5 |

- **Titelanalyse reproduziert:** Die 83 Titeltreffer des Issues sind exakt die 83 PRs, die laut Diff nur generierte Handoff-, Status- und Evidence-Träger ändern. Es gibt keinen Titeltreffer mit Produktänderung und keinen reinen Refresh ohne Titeltreffer.
- **CI-Kosten:** Reine Refreshs laufen auf dem leichten CI-Pfad (Median 44 s). Zusammen sind es 50 % der PRs, aber 22 % der CI-Wallclock-Zeit auf PR-Heads. CI-Läufe auf `main` nach dem Merge sind nicht enthalten.
- **Die Klasse REPAIR_OF_REFRESH_DEFECT ist eine Heuristik** (Code- oder Teständerung mit Refresh-/Handoff-Bezug im Titel). Sie enthält zum Beispiel #2372 (final head identity), #2397 (KIT-GF-046), #2409/#2411 (KIT-GF-050) und #2383.
- **Nicht gemessen:** Menschliche Zeit und KI-Kontingent pro Refresh sind nicht protokolliert. Ob ein einzelner Refresh „unnötig“ war, lässt sich ohne Ausführungsquittungen nicht entscheiden.

## 6. Konsistenz- und Qualitätsgegenproben (P3)

- **Statushoheiten:** Die Divergenz aus Abschnitt 3 bleibt offen. Eine Korrektur in einem Ledger würde sie nicht rückwirkend ungeschehen machen.
- **Grünes Gate ist nicht vollständig konsistent:** Am 11.10. bestanden Standardgates, während die strenge DPA-Prüfung 9 Blocker und 4 Warnungen meldete (E11). Am 15.10. meldete `agentic-kit doctor` lokal einen Fehler im Standard-Audit-Suite-Schritt (`release-prep`-Probelauf zum CHANGELOG-Abschnitt v1.0.25) bei grüner CI; am 16.10. lief derselbe Check auf `main` `3f5ab2c` mit PASS. Die Ursache des wechselnden Ergebnisses ist nicht geklärt.
- **Projektionsdrift:** HD-08 (Abschnitt 2).
- **Command Authority:** `tools/next-step.py` führt `git push`, `git push --delete` und `git branch -D` direkt aus (E16; ebenso `COMMAND_USAGE_AUDIT_20261015.md`, Befund F4). Das ist ein statisches Risiko; ein Schaden ist nicht belegt.
- **Reverts:** Auf `main` gibt es zwischen Mai und Oktober 0 Revert-Commits. Daraus folgt keine Defektrate.

## 7. Bewertung nach Evidenzstärke

| Hypothese | Befund | Urteil |
|---|---|---|
| Das Kit stellt wirksame Prozess-/Handoff-Gates bereit | Work-Order-Vertrag, HD-01–HD-07, E05, E06, E10 | direkt belegt für Einzelpfade |
| Zusätzliche Refresh-Runden haben abgenommen | Abschnitt 4: 7–8 % (Jul/Aug) → 0–1,2 % (Sep/Okt) | deskriptiv belegt, kausal offen |
| Das Kit senkt die persistierende Drift insgesamt | kein Zyklus-Nenner | nicht messbar |
| Die Reparatur bis zur Consumer-Verifikation geht schnell | Median 1 Kalendertag bei 22 selektierten Familien | deskriptiv, ohne Vergleichsgruppe |
| Das Kit verbessert die Codequalität netto | einzelne Reparaturen validiert, keine Vergleichsrate | plausibel, kausal offen |
| Doctor PASS bedeutet driftfrei | DPA-Blocker 11.10.; HD-08; wechselndes doctor-Ergebnis 15./16.10. | widerlegt |
| Die Command Authority ist lückenlos | `tools/next-step.py` | statische Lücke |

## 8. Nicht messbar mit den vorhandenen Daten

- Persistierende Driftrate pro abgeschlossenem Arbeitszyklus: Es gibt keinen vollständigen Zyklus-Nenner und kein Aufrufprotokoll.
- `stale_escaped`, `stale_blocked` und `unnecessary_refresh` pro Handoff-Versuch: Für den größten Teil der Historie fehlen Ausführungsquittungen. Von 1.387 historischen Evidence-Dateiversionen enthalten nur 144 Kit-Aufrufe (`COMMAND_USAGE_AUDIT_20261015.md`).
- Recovery-Kosten (Zeit, Token, menschliche Eingriffe) pro wiederhergestelltem Fall.
- Netto-Produktivität und Codequalität gegenüber einem Workflow ohne Kit: Der A/B/C-Versuch (ohne Kit / Minimal-Kern / volles Kit) wurde nicht durchgeführt.

## 9. Empfohlene Folgearbeiten (Vorschläge, keine Entscheidungen)

1. Die 16 CLOSED→OPEN-Familien reconciliieren, zuerst die als critical eingestufte KIT-GF-010. Das gehört in den Consumer-Ledger, dessen Statushoheit beim Consumer bleibt.
2. HD-08 beheben: den `release`-Block in `.agentic/handoff_state.yaml` aus der Release-Autorität ableiten oder ihn aus der Terminal-Projektion entfernen, mit Regressionstest.
3. Ein lokales Aufrufprotokoll einführen (Kommando, Elternkette, Returncode, Dauer, Korrelations-ID). Erst damit werden Zyklus-Nenner und die Kennzahlen aus Abschnitt 8 messbar.
4. Den A/B/C-Versuch mit injizierten Fehlern und identischen Budgets aufsetzen, Remote-Effekte nur simuliert.

## Quellen

Öffentliche Kit-Quellen (Repository `vfi64/agentic-project-kit`):
- Q01 `docs/reports/greenfield/external-findings-status.json` bei `ef78a255`
- Q05 `docs/reports/documentation-system-closeout-20260612.md`
- Q06 `docs/reports/POST_0_5_0_BROWNFIELD_COMM_SCI_READONLY_20260811.md`
- Q07 `docs/reports/POST_0_5_0_GREENFIELD_B2_20260811.md`
- Q08 `docs/reports/DECOMPLEXIFICATION_AUDIT_20260815.md`
- Q09 `docs/reports/V1_0_1_DOCKER_PYPI_FIRST_CONTACT_20260820.md`
- Q10 `docs/reports/greenfield/KIT-GF-011-successor-final-head-identity-2026-10-04.md`
- Q11 `docs/reports/PLANNING_RELEASE_RECONCILIATION_20261011.md`
- Q12 `docs/reports/greenfield/KIT-GF-063-custom-ci-runtime-plan-2026-10-13.md`
- Q13 `docs/reports/greenfield/KIT-GF-069-release-publish-verdict-2026-10-13.md`
- Q14 `docs/governance/WORK_ORDER_WORKFLOW_CONTRACT.md`
- Q15 `tools/next-step.py` bei `ef78a255`
- Q17 erster CI-Lauf, GitHub Actions Run 25600234780
- Pull Requests #877, #880 und #2504
- `docs/reports/COMMAND_USAGE_AUDIT_20261015.md`

Private Quellen (nicht öffentlich prüfbar; Provenance in `SOURCE_MANIFEST.json`):
- Q02 Consumer-Ledger (`926e1f70…`, Blob `c2528e9c…`)
- Q03/Q04 Comm-SCI-Übergabeprompt und `MODULARIZATION.md` (Commit `3cb5acdf…`)
- Q16 historischer Bericht, öffentlich als redigierte Fassung `HISTORICAL_DEVELOPMENT_20261015.md`
