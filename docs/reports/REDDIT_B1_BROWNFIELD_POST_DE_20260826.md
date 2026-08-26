# Reddit-Entwurf: Brownfield-B1-Ergebnis

Status: Entwurf, nicht veröffentlicht  
Datum: 2026-08-26  
Evidenzbasis: `docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.md`

## Mögliche Titel

- Ich habe mein Repository-Governance-Tool zurück in das Brownfield-Python-Projekt gebracht, aus dem es entstanden ist
- Fünf echte Brownfield-Zyklen nach dreieinhalb Monaten Self-Hosting
- Wie viel Autonomie darf ein Repository einem Coding Agent sicher geben?

## Entwurf

Vor ungefähr dreieinhalb Monaten war eines meiner Python-Projekte so komplex
geworden, dass ich seinen Architekturzustand nicht mehr zuverlässig von einer
LLM-Session in die nächste tragen konnte. Daraus entstand nach und nach ein
dateibasiertes Repository-Governance-System.

Nach mehreren Monaten, in denen ich dieses System vor allem an sich selbst
entwickelt und getestet hatte, habe ich es jetzt zurück in das Repository
gebracht, das den Bau ursprünglich ausgelöst hatte.

Die Frage war einfach: Kann das inzwischen generalisierte System sicher in dem
Brownfield-Repository arbeiten, dessen Komplexität es überhaupt erst notwendig
gemacht hatte?

Das Ergebnis ist gemischt - und gerade deshalb nützlich. Ich habe fünf echte
Wartungszyklen in dem Brownfield-Repo ausgeführt. Das waren keine Spielaufgaben:
Die Arbeit hat Legacy-Seams in einer bestehenden Anwendung entfernt und später
die CI-Konfiguration des Zielrepos so angepasst, dass Pull Requests gegen dessen
Integrationsbranch echte Checks bekommen.

Gemessenes Ergebnis:

- fünf echte Wartungszyklen;
- vier Zyklen mit Merge-Grenze;
- Legacy-Seams gingen von 72 auf 58 zurück;
- die Full-Suite blieb in den Zyklen grün, in denen sie lief, und wuchs mit
  zusätzlicher Regressionstest-Abdeckung von 1.483 auf 1.490 Tests;
- Zyklus 005 änderte CI-Konfiguration statt Anwendungscode, deshalb gibt es
  dafür keinen historischen Full-Suite-Eintrag und die Bewertung läuft über
  Remote-CI-Evidenz;
- der Prozess fand vier Kit-Defekte in externen Kernpfaden, die beim
  Self-Hosting nicht sichtbar geworden waren.

Diese Defekte waren nicht kosmetisch. Einer lag im Packaging: Das installierte
Paket enthielt die Command-Manifest-Ressource nicht, sodass manifestabhängige
Kommandos in externen Workspaces brüchig waren. Ein weiterer lag im
Merge-Preflight, der Self-Hosting-Annahmen in ein Fremdrepo trug. Der dritte
nahm für Post-Merge-Prüfungen `main` an, obwohl das Ziel ein Integrationsbranch
war. Der vierte betraf Rule-Acknowledgement: Externe Workspaces brauchen
zielrepo-eigene Regelquellen statt die Self-Hosting-Regeldateien des Kits.

Drei dieser Fixes sind im veröffentlichten Paket 1.0.5 und wurden aus einem
PyPI-Install heraus erneut geprüft. Der Rule-Ack-Fix ist auf Kit-main und aus
einem Checkout extern erneut geprüft, aber noch keine Released-Package-Evidenz.

Auch die Merge-Geschichte ist keine perfekte Erfolgserzählung. Nachdem das
Zielrepo echte Remote-CI hatte, konnte der Safe-Merge-Wrapper die PRs zwar
mergen, aber der lokale Wrapper kehrte nach erfolgreichem Remote-Merge nicht
sauber zurück. Genau solche Reibung sollte der Test sichtbar machen, nicht
verstecken.

Der Claim bleibt deshalb bewusst eng:

Fünf echte Brownfield-Wartungszyklen sind stärkere Evidenz als reines
Self-Hosting, aber ein vertrautes privates Repository reicht nicht aus, um
allgemeine Brownfield-Portabilität zu belegen.

Die öffentliche Website beginnt jetzt nicht mehr mit einer riesigen
Kommandoliste, sondern mit der Wahl des Arbeitsmodus: File Transfer, Copy and
Paste, Agent Direct und eine experimentelle GUI-Oberfläche. Sie zeigt außerdem
die Brownfield-Evidenzgrenze, statt "Brownfield-Support bewiesen" zu behaupten.

Das Kit selbst ruft keine LLM-API auf und setzt keine LLM-API voraus. Es ersetzt
auch nicht Git, GitHub, CI oder AGENTS.md-artige Instruktionen. Git speichert
Historie, GitHub koordiniert Reviews, CI validiert konfigurierte Checks, und
Instruktionen führen einen Executor. Die Rolle des Kits ist langlebiger
operativer Zustand: Governance, Evidence, Command-Metadaten und Handoffs im
Repository, damit Arbeit über Sessions, Modelle und Oberflächen hinweg
fortgesetzt werden kann.

Die Frage, die für mich bleibt:

Wie viel Autonomie darf ein Repository sicher gewähren, wenn man nur die aktuell
vorliegende Evidenz betrachtet?

Weitere Fragen, zu denen mich Einschätzungen interessieren würden:

- Wo zieht ihr die Grenze zwischen Coding-Agent-Autonomie und
  repository-verändernden Operationen?
- Wie bewahrt ihr operativen Kontext über Sessions, Modelle und Oberflächen
  hinweg, ohne eine einzelne Agent-Runtime zur Source of Truth zu machen?
- Falls das überengineert wirkt: Welchen Teil würdet ihr zuerst entfernen, ohne
  die zugrunde liegende Sicherheitseigenschaft zu verlieren?

## Bewusst vermiedene Claims

- Allgemeine Brownfield-Portabilität wird nicht behauptet.
- Die Command-Anzahl wird nicht als Qualitätsmetrik verwendet.
- Die PR-Anzahl der Projektgeschichte wird nicht als Qualitätsbeleg verwendet.
- Remote-CI-Erfolg wird nicht für Zyklen behauptet, in denen das Zielrepository
  keine Checks gemeldet hat.
- Fixes auf main und Fixes in einem veröffentlichten Paket bleiben getrennte
  Evidenzarten.
- Die GUI wird nicht als vollständige CLI-Parität dargestellt.
