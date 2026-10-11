# PAA v0.3 — preserved review input

Status: archived
Authority: docs/planning/PROJECT_DIRECTION.yaml
Superseded-by: docs/planning/PROJECT_DIRECTION.yaml
Source-version: 0.3
Source-date: 2026-10-11
Source-SHA256: 29a4a8aeeb47726d3822ee9394c05774815a7c3d37bb3387a5ec79903a3a924c

This is the complete user-supplied German discussion draft, preserved as
historical review input. Its embedded reviewer and execution instructions
are quoted proposals, not operational authorization. Current phase status,
decisions and acceptance live only in the canonical Direction YAML under
`proof-assurance-assessment`. Claims about earlier independent reviews
are source claims; the underlying reviews were not supplied or verified.
The integration does not execute P0, authorize P1-P6, select a tool or
establish current DPA conformance. No active architecture contract is changed.

## Original discussion draft (unaltered)

PAA v0.3 – Vollständiger Entwicklungs- und Untersuchungsplan

Die neue Fassung integriert die bisherigen Überlegungen, beide Gutachten von Grok und die fünf zuletzt vereinbarten Ergänzungen. Sie ist als eigenständiges, versioniertes Diskussionsdokument angelegt, das du anderen KI-Modellen zur unabhängigen Begutachtung geben kannst.

Die wesentlichen Entscheidungen sind jetzt eindeutig: Das Kit bleibt die alleinige Prozessautorität, der Mensch verantwortet die fachliche Akzeptanz der zu beweisenden Eigenschaften, und formale Modellnachweise dürfen nicht als Beweise für die tatsächliche Python-Implementierung ausgegeben werden.

Freigegeben wird im Plan zunächst ausschließlich P0: eine lesende, revisionsgebundene Bestandsaufnahme. Alle weiteren Phasen stehen unter gesonderten Entscheidungsvorbehalten.

PAA – Proof Assurance Assessment

Bestandsanalyse, Machbarkeitsstudie, Architekturkonzept, Aufwandsabschätzung und Entwicklungsplan

Projekt: Agentic Project Kit (AGP Kit)
Dokumentversion: 0.3 – konsolidierter Diskussions- und Entscheidungsentwurf
Stand: 11. Oktober 2026
Status: REVIEW_REQUIRED
Gesamtbewertung: PROCEED_WITH_CHANGES
Freigabestatus: Ausschließlich Phase P0 zur lesenden Untersuchung vorgeschlagen
Grundlagen: PAA v0.1, PAA v0.2, zwei unabhängige Gutachten von Grok und anschließende fachliche Bewertung

⸻

1. Zusammenfassung

Das Agentic Project Kit soll um eine optionale, profilgebundene Domäne für formale und systematische Softwareverifikation erweitert werden.

Diese Erweiterung trägt die vorläufige Bezeichnung Proof Assurance Assessment (PAA).

PAA soll die Fähigkeit bereitstellen, ausgewählte Eigenschaften eines Softwareprojekts systematisch zu untersuchen, formale Beweisverpflichtungen zu verwalten, geeignete Prüfverfahren einzusetzen und deren Ergebnisse innerhalb der vorhandenen Kit-Governance nachvollziehbar zu bewerten.

Der Ansatz orientiert sich methodisch an der DPA: Bestandsaufnahme, Klassifikation, Bewertung, kontrollierte Ausführung, Evidenzgewinnung und Entscheidung.

Die tatsächliche technische Wiederverwendbarkeit der DPA-Implementierung ist jedoch noch nachzuweisen.

1.1 Zentrale Leitidee

PAA soll nicht möglichst viele positive Beweislabels erzeugen, sondern unberechtigte Korrektheitsbehauptungen verhindern und belastbare, klar begrenzte Nachweise ermöglichen.

Es soll ausdrücklich unterscheiden zwischen:

* erfolgreich ausgeführten Tests;
* begrenzten systematischen Prüfungen;
* formal bewiesenen Modelleigenschaften;
* formal bewiesenen Implementierungseigenschaften;
* empirisch getesteter Modell-Code-Konformität;
* formal nachgewiesener Modell-Code-Konformität;
* unvollständigen, ungültigen oder veralteten Nachweisen.

1.2 Strategische Zielsetzung

Das Kit soll langfristig nicht nur belegen, dass vorgeschriebene Entwicklungsprozesse eingehalten wurden.

Es soll zusätzlich ausgewählte Korrektheitseigenschaften des entwickelten Produkts mit nachvollziehbarer, gegebenenfalls formaler Evidenz absichern können.

Prozesskorrektheit und Produktkorrektheit bleiben dabei strikt getrennt.

1.3 Grundentscheidungen

1. Das Kit bleibt alleinige Autorität für Repository-Governance und Entwicklungsprozesse.
2. PAA ist eine Fachdomäne innerhalb des Kits, keine zweite Steuerungsinstanz.
3. Das Cockpit darf PAA-Berichte darstellen und transportieren, aber nicht deren formale Gültigkeit autorisieren.
4. Menschen verantworten die fachliche Akzeptanz der zu beweisenden Eigenschaften.
5. LLMs dürfen Spezifikationen, Modelle, Tests und Beweise vorschlagen, jedoch keine formale Gültigkeit selbst bestätigen.
6. Verifikationswerkzeuge liefern prüfbare technische Ergebnisse, keine unbegrenzten Qualitätsgarantien.
7. Die Nachweisgültigkeit muss an Eigenschaften, Voraussetzungen, Artefakte und überprüfbare Revisionen gebunden werden.
8. Der erste PoC muss klein und implementierungsnah sein.
9. Bestehende Kit-Funktionen sind vor jeder Neuentwicklung auf Wiederverwendbarkeit zu untersuchen.
10. Die Umsetzung erfolgt ausschließlich nach phasenweisen Entscheidungen.

⸻

2. Ausgangslage und Problemstellung

2.1 Bestehendes System

Das Agentic Project Kit stellt eine sprach- und werkzeugoffene Governance-Infrastruktur für KI-gestützte Softwareentwicklung bereit.

Die dokumentierte Architektur umfasst unter anderem:

* Projektverträge;
* Profile und Policy-Pakete;
* deterministische Prüfungen;
* Entwicklungs- und Release-Gates;
* Evidenzverwaltung;
* Repository-Zustandskontrolle;
* DPA-Assessment;
* Handoff-Verfahren;
* CI-Integration;
* kontrollierte GitHub-Lifecycle-Abläufe.

Das AGP Cockpit ergänzt diese Infrastruktur um die Bedienung, Kommunikation und kontrollierte lokale Ausführung KI-gestützter Arbeitsaufträge.

Die vorläufige Bestandsanalyse stützt sich auf die öffentlich zugänglichen Architektur- und Governance-Dokumente. Eine vollständige Code-Inventur liegt noch nicht vor.

2.2 Bestehende Sicherheitsgrenze

Das Kit kann kontrollieren, ob definierte Verfahren, Zustände, Berechtigungen und Prüfungen eingehalten werden.

Daraus folgt jedoch nicht automatisch, dass die entwickelte Software fachlich korrekt ist.

Beispiel:

Ein PR kann sämtliche vorgeschriebenen Tests bestehen und ordnungsgemäß gemergt werden, obwohl die implementierte Funktion einen fachlichen Fehler enthält.

2.3 Aufgabe der Erweiterung

PAA soll die bestehende Prozess-Governance um überprüfbare Aussagen über ausgewählte Produkteigenschaften ergänzen.

Die Erweiterung soll keine absolute Fehlerfreiheit versprechen.

Ihr Nutzen muss anhand konkret vermiedener oder erkennbarer Fehlerklassen nachgewiesen werden.

⸻

3. Ziele, Anforderungen und Nichtziele

3.1 Funktionale Ziele

FR-01: Verifikationseignung eines Projekts untersuchen.

FR-02: Kandidaten für formale oder systematische Nachweise identifizieren.

FR-03: Eigenschaften und Beweisverpflichtungen eindeutig erfassen.

FR-04: Nachweisarten und ihre Aussagekraft unterscheiden.

FR-05: Geeignete Prüfwerkzeuge profilgebunden auswählen.

FR-06: Externe Verifikationswerkzeuge kontrolliert ausführen oder deren Evidenz prüfen.

FR-07: Beweise, Gegenbeispiele, Annahmen und Prüfgrenzen erfassen.

FR-08: Nachweise an konkrete Modelle, Implementierungen und Revisionen binden.

FR-09: Ungültig gewordene Nachweise erkennen.

FR-10: Ergebnisse in bestehende Kit-Gates und Evidenzverfahren integrieren.

FR-11: Menschliche Entscheidungen und LLM-Empfehlungen getrennt dokumentieren.

FR-12: Modell-, Implementierungs- und Konformitätsnachweise unterscheiden.

FR-13: Reproduzierbare positive und negative Verifikationsfälle unterstützen.

FR-14: Greenfield- und Brownfield-Projekte perspektivisch unterstützen.

FR-15: Nachweisstatus über Handoffs hinweg erhalten, ohne seine Gültigkeit ungeprüft zu übernehmen.

3.2 Nichtfunktionale Anforderungen

* Deterministische Evidenzbewertung
* Reproduzierbarkeit
* Nachvollziehbare Vertrauensgrenzen
* Begrenzte Ressourcenverwendung
* Konservative Fehlerbehandlung
* Kontrollierte Werkzeugausführung
* Sprach- und Werkzeugoffenheit der Infrastruktur
* Keine zweite Prozessautorität
* Keine stillschweigende Erweiterung von Berechtigungen
* Keine unberechtigten positiven Korrektheitsbehauptungen
* Möglichst geringe Verdopplung vorhandener Kit-Funktionen
* Rückwärtskompatibilität entsprechend bestehender Verträge

3.3 Nichtziele

PAA soll nicht:

* beliebige Software vollständig automatisch verifizieren;
* absolute Fehlerfreiheit garantieren;
* fachliche Anforderungen ohne menschliche Verantwortung festlegen;
* Tests ersetzen;
* LLM-Aussagen als formale Beweise akzeptieren;
* abstrakte Modellkorrektheit als vollständige Implementierungskorrektheit ausgeben;
* eine allgemeine Softwarezertifizierungsstelle bilden;
* neue autonome Entwicklungscontroller einführen.

⸻

4. Bestandsanalyse

4.1 Dokumentierter Ausgangsbestand

Bereich	Dokumentierter Zustand	PAA-Relevanz
Kit-Architektur	Sprach- und werkzeugoffen	Sehr hoch
Governance	Deterministische Regeln und Gates	Sehr hoch
DPA	Assessment und Repository-Adoption	Hoch
Evidenz	Strukturierte Prüf- und Ausführungsnachweise	Sehr hoch
Revisionen	Git-basierte Zustandskontrolle	Sehr hoch
Profile	Projektabhängige Konfiguration	Hoch
Handoffs	Validierte Übergabepakete	Hoch
CI	Bestehende Prüf- und Freigabeabläufe	Hoch
Cockpit	Deterministische Ausführung und Transport	Mittel bis hoch

Die Tabelle belegt noch keine unmittelbare technische Wiederverwendbarkeit.

4.2 Verpflichtende Implementierungsinventur

Phase P0 muss mindestens untersuchen:

1. DPA-CLI-Routen und Orchestratoren.
2. DPA-Datenmodelle und Klassifikationslogik.
3. Bestehende Evidenzschemas und Speichermechanismen.
4. Revisions-, Hash- und Manifestbezüge.
5. Gate-Enums, Ergebnisnormalisierung und Entscheidungsregeln.
6. Bestehende externe Tool-Adapter und Ausführungsmechanismen.
7. Profil- und Policy-Erweiterungspunkte.
8. Invalidierungs- und Drift-Mechanismen.
9. Handoff-Integration.
10. Tests für die möglichen PoC-Protokolle.
11. Sicherheitsgrenzen externer Prozesse.
12. Bereits vorhandene Mechanismen zur Erkennung widersprüchlicher Evidenz.

4.3 Evidenzpflicht

Jeder technische Befund muss enthalten:

* Repository;
* exakte untersuchte Revision;
* Dateipfad;
* Funktion, Klasse oder Konfiguration;
* relevanten Test;
* beobachtetes beziehungsweise dokumentiertes Verhalten;
* Wiederverwendungseinschätzung;
* verbleibende Unsicherheit.

Nicht verifizierte Vermutungen sind ausdrücklich als solche zu kennzeichnen.

4.4 Wiederverwendungsmatrix

Klassifikation	Bedeutung
REUSE	Unmittelbar wiederverwendbar
EXTEND	Gezielt erweiterbar
NEW	Nachgewiesene funktionale Lücke
UNDECIDED	Noch nicht ausreichend untersucht
NOT_APPLICABLE	Für PAA nicht relevant

Die Kategorien beschreiben den Untersuchungsbefund, keine Implementierungsfreigabe.

⸻

5. Fachliches Nachweismodell

5.1 Ebene A – Formale Modelleigenschaften

Ein abstraktes Modell wird gegen eine formal definierte Eigenschaft geprüft.

Beispiele:

* Ein Merge ist ohne gültige Freigabe nicht erreichbar.
* Ein blockierter Prozess kann nicht unautorisiert fortgesetzt werden.
* Ein unbekanntes Ausführungsergebnis wird nicht blind erneut ausgeführt.

Geeignete Verfahren können Model Checking oder deduktive Modellbeweise sein.

Zulässige Aussage: Die Eigenschaft gilt für das untersuchte Modell unter den dokumentierten Voraussetzungen und Prüfbedingungen.

Nicht zulässig: Daraus unmittelbar auf vollständige Korrektheit der Python-Implementierung zu schließen.

5.2 Ebene B – Implementierungseigenschaften

Eigenschaften der tatsächlichen Implementierung werden untersucht oder bewiesen.

Beispiele:

* Vor- und Nachbedingungen;
* Datenstrukturinvarianten;
* definierte Zustandsübergänge;
* bestimmte algorithmische Eigenschaften.

Mögliche Verfahren:

* deduktive Programmverifikation;
* symbolische Ausführung;
* geeignete statische Analysen;
* formale Programmverträge.

Nicht jede statische Analyse liefert einen vollständigen formalen Beweis.

5.3 Ebene C – Modell-Code-Konformität

Die Beziehung zwischen abstraktem Modell und Implementierung wird untersucht.

Mögliche Verfahren:

* modellbasierte Tests;
* Zustandsübergangsvergleiche;
* Trace-Konformität;
* systematische Konformitätsprüfung;
* Refinement-Beweise.

Zentrale Regel: Eine endliche Menge erfolgreicher Konformitätstests belegt nicht automatisch vollständige Konformität.

Die Evidenz muss unterscheiden, ob die Beziehung lediglich getestet, begrenzt geprüft oder formal bewiesen wurde.

5.4 Verhältnis der Ebenen

Die Ebenen A, B und C sind logisch verschieden.

Sie müssen nicht zwingend in dieser Reihenfolge entwickelt werden.

Für den ersten PoC wird A mit einer bewusst kleinen empirischen C-Brücke bevorzugt, sofern P0 diese Wahl bestätigt.

Ein vollständiger B-Nachweis ist keine MVP-Voraussetzung.

⸻

6. Verantwortung für die Spezifikation

6.1 Problem

Ein mathematisch korrekter Beweis kann eine fachlich falsch formulierte Eigenschaft betreffen.

Beispiel:

Ein Modell beweist, dass eine Aktion nur bei gesetztem Freigabeflag ausgeführt wird.

Wenn das fachliche Sicherheitsziel zusätzlich verlangt, dass die Freigabe zur aktuellen Revision und konkreten Aktion gehört, ist der Beweis möglicherweise unzureichend.

6.2 Human-owned Property Acceptance

Die fachliche Akzeptanz einer Beweisverpflichtung liegt beim Menschen.

LLMs dürfen:

* Anforderungen analysieren;
* Eigenschaften vorschlagen;
* Mehrdeutigkeiten aufzeigen;
* formale Spezifikationen entwerfen;
* Gegenbeispiele suchen;
* Reviews durchführen.

Sie dürfen die fachliche Akzeptanz nicht eigenmächtig ersetzen.

6.3 Drei getrennte Entscheidungen

Entscheidung 1 – Fachliche Akzeptanz

Der Mensch bestätigt, dass die Eigenschaft das beabsichtigte Sicherheits- oder Korrektheitsziel angemessen beschreibt.

Entscheidung 2 – Technischer Nachweis

Ein geeignetes Werkzeug untersucht die formal definierte Eigenschaft.

Entscheidung 3 – Evidenzakzeptanz

Das Kit prüft, ob der technische Nachweis zum richtigen Bezugsstand gehört, vollständig und konsistent ist und die behauptete Aussage trägt.

Eine menschliche Risikoakzeptanz kann fehlende Beweise nicht in vorhandene Beweise verwandeln.

⸻

7. Proof Obligations und Evidenzschema

7.1 Mindestdaten einer Beweisverpflichtung

Jede Proof Obligation benötigt:

* stabile Kennung;
* fachliche Beschreibung;
* formale Eigenschaft;
* Nachweisebene;
* Bezugsobjekt;
* relevante Artefakte;
* explizite Annahmen;
* fachliche Akzeptanzentscheidung;
* Prüfverfahren;
* erwarteten Nachweisumfang;
* Akzeptanzbedingungen;
* Invalidierungsregeln.

7.2 Mindestdaten eines Nachweises

Ein Nachweis benötigt:

* Proof-Obligation-ID;
* Modell- oder Programmidentität;
* relevante Inhalts-Hashes;
* Repository-Revision;
* Werkzeugidentität und Version;
* Werkzeugkonfiguration;
* ausgeführten Prüfauftrag;
* Ergebnis;
* Prüfgrenzen;
* Annahmen;
* Gegenbeispiel, falls vorhanden;
* Ausführungsstatus;
* Evidenzherkunft;
* Zeitpunkt und Umgebung;
* Gültigkeitsstatus.

Die genaue technische Schemaform wird erst nach P0 festgelegt.

7.3 Autoritätskennzeichnung

Mindestens zu unterscheiden sind:

* formal_tool
* human
* llm_advisory

Ein LLM-Kommentar darf ein technisches Prüfergebnis weder ersetzen noch in einen stärkeren Nachweisstatus umwandeln.

7.4 Ergebnissemantik

Zustand	Aussage
PROVEN	Definierte Eigenschaft formal bewiesen, mit explizitem Scope
BOUNDED_VERIFIED	Definierte begrenzte Untersuchung erfolgreich
TESTED	Definierte empirische Tests erfolgreich
COUNTEREXAMPLE	Verletzung innerhalb des geprüften Modells oder Gegenstands festgestellt
UNKNOWN	Keine belastbare Entscheidung
NOT_APPLICABLE	Nachweis nicht anwendbar
STALE	Evidenz für den aktuellen Bezugsstand nicht mehr gültig

Wichtig: Ein von TLC erfolgreich vollständig untersuchter endlicher Modellzustandsraum kann eine Invariante innerhalb dieses konkreten Modells nachweisen. Ob daraus PROVEN oder BOUNDED_VERIFIED folgt, hängt vom definierten Bezugsobjekt, den Grenzen der Modellierung und der Semantik des Nachweisvertrags ab.

Ein Werkzeugname oder Exitcode entscheidet diese Einstufung nicht allein.

7.5 Mehrdimensionale Ergebnisbewertung

Für die Implementierung ist zu prüfen, ob folgende Informationen getrennt gespeichert werden müssen:

* technisches Werkzeugergebnis;
* Nachweisstärke;
* Evidenzgültigkeit;
* fachliche Akzeptanz;
* Kit-Gate-Entscheidung.

Dadurch wird vermieden, dass beispielsweise STALE mit COUNTEREXAMPLE verwechselt wird.

Ein früher gültiger Nachweis kann veraltet sein, ohne dass dadurch die geprüfte Eigenschaft widerlegt wurde.

⸻

8. Trust Boundary und Vertrauensanker

8.1 Grundsatz

PAA muss nicht nur einen Nachweis speichern, sondern dessen Herkunft und Aussagegrenzen überprüfbar machen.

8.2 Vertrauensbestandteile

Zu untersuchen sind:

1. Korrektheit der formalen Spezifikation bezüglich des fachlichen Ziels.
2. Semantik des verwendeten Verifikationsverfahrens.
3. Vertrauenswürdigkeit des Werkzeugs.
4. Korrektheit der Werkzeugkonfiguration.
5. Vollständigkeit beziehungsweise Begrenzung der Untersuchung.
6. Integrität der Eingabeartefakte.
7. Integrität der Ergebnisevidenz.
8. Zuordnung zur untersuchten Revision.
9. Zuverlässigkeit der Modell-Code-Verknüpfung.
10. Korrektheit der Ergebnisinterpretation.

8.3 LLM-Grenze

LLMs dürfen keine PROVEN-Aussage allein durch textuelle Bewertung erzeugen.

Auch mehrere übereinstimmende LLM-Gutachten bilden keinen mathematischen Beweis.

LLM-Reviews sind zusätzliche fachliche Prüfungen und können Fehler aufdecken, aber keine fehlende formale Evidenz ersetzen.

8.4 Unabhängige Beweisprüfung

Langfristig können unabhängig prüfbare Beweiszertifikate oder kleine vertrauenswürdige Prüferkerne interessant sein.

Für den MVP ist diese Fähigkeit nicht verpflichtend.

Die dadurch verbleibende Vertrauensannahme muss dokumentiert werden.

⸻

9. Invalidierung und STALE-Regeln

9.1 Grundsatz

Ein Nachweis darf nicht stillschweigend für einen geänderten Bezugsstand weiterverwendet werden.

9.2 Verbindlicher Mindestkatalog für P1

Mindestens folgende Änderungen müssen eine erneute Gültigkeitsprüfung auslösen:

Änderung	Mindestreaktion
Formale Eigenschaft geändert	STALE
Modellinhalt geändert	STALE
Relevanter Implementierungscode geändert	STALE für davon abhängige Nachweise
Verifikationskonfiguration geändert	STALE oder erneute Bewertung
Relevante Werkzeugversion geändert	Erneute Vertrauens- und Gültigkeitsbewertung
Explizite Annahme geändert	STALE
Relevante Abhängigkeit geändert	STALE oder nachgewiesene Unabhängigkeit
Proof-Obligation-Vertrag geändert	Erneute Bewertung
Evidenzhash stimmt nicht	Evidenz zurückweisen
Manifest oder Referenzidentität widersprüchlich	Evidenz zurückweisen

9.3 Pfad- und Manifestabhängigkeiten

P1 muss definieren, welche konkreten Dateien, Pfadmuster und Manifestfelder für jede Beweisverpflichtung relevant sind.

Dabei gilt:

* Ein Dateiname allein ist kein ausreichender Integritätsnachweis.
* Eine unveränderte Git-Revision ist nicht automatisch ausreichend, wenn externe Artefakte einfließen.
* Eine geänderte Revision bedeutet nicht zwingend, dass jeder Nachweis fachlich ungültig ist.
* Solange die Unabhängigkeit nicht nachgewiesen ist, wird konservativ invalidiert.

9.4 MVP-Regel

Der MVP darf zu häufig STALE melden.

Er darf aber nicht aufgrund einer unbelegten Unabhängigkeitsannahme einen tatsächlich ungültigen Nachweis als gültig behandeln.

Spätere Optimierungen können die Invalidierung präzisieren.

⸻

10. Architektur und Governance

10.1 Einordnung

PAA wird als optionale Fachdomäne innerhalb des Kits konzipiert.

Die logische Architektur lautet:

Mensch/LLM → Kit-Autorität → PAA-Verifikationsverfahren → Evidenzbewertung → Kit-Governance

Das Cockpit bleibt eine separate Kommunikations-, Bedien- und Ausführungsschicht.

10.2 Logische Verantwortlichkeiten

Assessment: Ermittlung geeigneter Eigenschaften und Verfahren.

Obligation Management: Verwaltung der Beweisverpflichtungen.

Verification Adapter: Kontrollierte Anbindung externer Werkzeuge.

Evidence Evaluation: Prüfung von Herkunft, Vollständigkeit und Konsistenz.

Validity Management: Gültigkeit, Abhängigkeiten und Invalidierung.

Governance Integration: Einbindung in bestehende Kit-Gates.

Review Support: Aufbereitung für menschliche und KI-gestützte Begutachtung.

Diese Bezeichnungen sind keine verbindliche Vorgabe neuer Python-Module.

P0 entscheidet, welche Funktionen bereits existieren.

10.3 Gate-Politik

Für den MVP gilt:

* PAA-Berichte haben zunächst beratende Wirkung auf bestehende Merge- und Release-Entscheidungen.
* Die interne Validierung einer Beweisaussage muss dagegen strikt sein.
* Fehlende, widersprüchliche oder veraltete Evidenz darf keinen positiven Beweisstatus erhalten.
* Ein Timeout darf nicht als PROVEN interpretiert werden.
* PAA darf bestehende Kit-Blockaden nicht umgehen.
* Neue verpflichtende Proof-Gates benötigen eine gesonderte menschliche Freigabe.

10.4 Cockpit-Abgrenzung

Das Cockpit darf:

* PAA-Aufträge über die vorhandene Kit-Autorität anstoßen;
* Fortschritt und Ergebnisse anzeigen;
* Evidenz transportieren;
* menschliche Entscheidungen anfordern.

Das Cockpit darf nicht:

* formale Ergebnisse eigenmächtig umklassifizieren;
* fehlende Evidenz ersetzen;
* Beweise unabhängig vom Kit autorisieren;
* eine zweite Proof- oder Task-Governance etablieren.

⸻

11. Auswahl des ersten PoC-Gegenstands

11.1 Kandidaten

Kandidat A – Safe-Merge-Voraussetzungen

Eine Merge-Aktion darf nur erfolgen, wenn die relevanten Sicherheits- und Kontextbedingungen erfüllt sind.

Kandidat B – Publication Policy

Eine Veröffentlichungsaktion darf festgelegte Freigabe- und Zustandsbedingungen nicht umgehen.

Kandidat C – Gate-Zustandsautomat

Ein nicht akzeptierter Prüfzustand darf nicht durch einen unzulässigen Übergang als erfolgreich behandelt werden.

11.2 Auswahlkriterien

Jeder Kandidat wird anhand folgender Kriterien bewertet:

Kriterium	Gewichtungsvorschlag
Sicherheitsrelevanz	20 %
Präzision der vorhandenen Anforderungen	20 %
Nähe zur realen Implementierung	20 %
Beherrschbarkeit des Modells	15 %
Verfügbarkeit bestehender Tests	10 %
Möglichkeit gezielter Gegenbeispiele	10 %
Wartungsaufwand	5 %

Die Gewichtungen sind Diskussionswerte und werden vor der Bewertung festgelegt.

Jedes Kriterium erhält eine dokumentierte Bewertung mit Begründung und Codebelegen.

11.3 Entscheidung

P0 muss alle drei Kandidaten untersuchen und eine Rangfolge mit Begründung liefern.

Ein Kandidat darf trotz hoher Gesamtpunktzahl ausgeschlossen werden, wenn ein zwingendes Sicherheits- oder Machbarkeitskriterium nicht erfüllt ist.

Die endgültige Auswahl erfolgt erst nach menschlicher Entscheidung.

⸻

12. Werkzeugauswahl

12.1 Grundsatz

Die Werkzeugwahl folgt dem konkreten Nachweisproblem.

Sie darf nicht allein aufgrund von Bekanntheit, Popularität oder LLM-Präferenz erfolgen.

12.2 Zu untersuchende Verfahren

* TLA+/TLC
* Apalache, sofern sachlich passend
* modellbasierte Tests
* Property-Based Testing
* symbolische Ausführung
* deduktive Programmverifikation

Dafny, CBMC und Lean 4 bleiben mögliche spätere beziehungsweise profilspezifische Werkzeuge.

12.3 Entscheidungsraster

Kriterium	Gewichtungsvorschlag
Aussagekraft für die gewählte Eigenschaft	30 %
Nähe zur tatsächlichen Implementierung	25 %
Modellierungs- und Integrationsaufwand	20 %
Reproduzierbarkeit und Gegenbeispiele	15 %
Laufzeit- und Wartungskosten	10 %

Bewertet werden mindestens:

* formale Aussagekraft;
* unterstützte Eigenschaften;
* Grenzen;
* Ausführbarkeit in der vorgesehenen Umgebung;
* Integrationskosten;
* Nachvollziehbarkeit;
* Wiederholbarkeit;
* erforderliche Vertrauensannahmen.

12.4 Vorläufige Präferenz

TLA+/TLC bleibt ein plausibler Kandidat für ein kleines Zustandsprotokoll.

Die Entscheidung ist ausdrücklich nicht vorweggenommen.

P0 kann zu dem Ergebnis kommen, dass ein anderes Verfahren für den ersten Erkenntnisgewinn geeigneter ist.

⸻

13. Begrenzung der Modell-Code-Brücke

13.1 Ziel

P3 soll zeigen, ob ein formaler Modellnachweis mit überschaubarem Aufwand einen belastbaren Bezug zur realen Kit-Implementierung erhalten kann.

Es soll noch keine vollständige Python-Programmverifikation entstehen.

13.2 Harte Umfangsgrenzen

Für den ersten P3-Versuch werden folgende vorläufige Obergrenzen vorgeschlagen:

* höchstens 2 Sicherheitsinvarianten;
* höchstens 3 unmittelbar untersuchte Python-Entscheidungsfunktionen;
* höchstens 8 modellierte Übergangsklassen;
* genau ein ausgewähltes Kit-Protokoll;
* keine Ausweitung auf den gesamten GitHub-Lifecycle;
* keine Browser- oder Cockpit-End-to-End-Verifikation;
* kein zusätzlicher formaler Hauptprüfer ohne neue Freigabe.

Die endgültigen Grenzen werden nach P0 festgelegt.

Eine Überschreitung benötigt eine explizite neue Entscheidung.

13.3 Erwarteter Nachweis

P3 soll mindestens liefern:

1. Eine dokumentierte Abbildung zwischen Modellzuständen und Implementierungszuständen.
2. Eine dokumentierte Abbildung zwischen Modellaktionen und konkreten Python-Funktionen.
3. Automatisierte Vergleiche ausgewählter Übergänge.
4. Mindestens einen negativen Implementierungstest.
5. Einen Bericht über nicht abgedeckte Zustände, Effekte und Annahmen.

13.4 Aussagegrenze

Erfolgreiche P3-Tests dürfen zunächst nur als TESTED beziehungsweise bei nachgewiesen begrenzter systematischer Untersuchung als BOUNDED_VERIFIED ausgewiesen werden.

Ein PROVEN-Status für die Python-Implementierung ist ohne entsprechenden formalen Implementierungs- oder Konformitätsnachweis unzulässig.

13.5 Stop-Regel

Wenn P3 innerhalb des vereinbarten Umfangs keinen relevanten Implementierungsbezug herstellen kann, ist die Phase zu stoppen und fachlich neu zu bewerten.

Eine schrittweise unkontrollierte Erweiterung ist nicht zulässig.

⸻

14. Machbarkeitsanalyse

14.1 Vorläufige Einschätzung

Ziel	Machbarkeit	Vorbehalt
Integration in Kit-Governance	Hoch	Implementierung prüfen
Proof-Obligation-Verwaltung	Hoch	Schemaentscheidung erforderlich
Reproduzierbare Werkzeugausführung	Hoch	Ausführungsumgebung prüfen
Formale Prüfung eines kleinen Modells	Hoch	Modellgröße und Semantik
Reproduzierbares Gegenbeispiel	Hoch	Geeigneter Kandidat erforderlich
Revisionsgebundene Evidenz	Hoch bis mittel	Bestehende Mechanismen prüfen
Automatische Invalidierung	Mittel bis hoch	Abhängigkeitsmodell offen
Kleine Modell-Code-Brücke	Mittel	Fachlich anspruchsvoll
Vollständige Implementierungsverifikation	Stark fallabhängig	Hoher Zusatzaufwand möglich
Universelle Produktkorrektheitsgarantie	Nicht allgemein realistisch	Grundsätzliche Grenzen

14.2 Hauptrisiken

R1: Falsche oder unvollständige fachliche Spezifikation.

R2: Fehlerhafte Abstraktion.

R3: Unzureichende Modell-Code-Konformität.

R4: Zustandsraumexplosion.

R5: Fehlerhafte oder falsch konfigurierte Prüfwerkzeuge.

R6: Veraltete Evidenz.

R7: Überhöhte Beweisaussagen.

R8: Verdopplung vorhandener Kit-Funktionen.

R9: Unvertretbarer Ressourcenbedarf.

R10: Neue Governance-Konflikte.

R11: Unzulässige LLM-Selbstzertifizierung.

R12: Unzureichend dokumentierte Vertrauensannahmen.

R13: Hohe Folgekosten durch Modellpflege.

R14: Unklare Abhängigkeiten bei der Evidenzinvalidierung.

14.3 Risikobewertung

Für jedes Risiko müssen erfasst werden:

* Ursache;
* Eintrittswahrscheinlichkeit;
* Auswirkung;
* Erkennungsverfahren;
* Gegenmaßnahme;
* Restrisiko;
* verantwortliche Entscheidung;
* Status.

Die Risikomatrix wird in P0 begonnen und in jeder Phase aktualisiert.

⸻

15. Vollständiger Entwicklungsplan

P0 – Lesende, revisionsgebundene Bestandsaufnahme

Status: Als einziger nächster Schritt zur Freigabe vorgeschlagen.

Ziel: Tatsächlichen Implementierungsbestand und Wiederverwendungspotenzial ermitteln.

Arbeiten:

1. Repository-Revision und Untersuchungsumfang erfassen.
2. DPA-Code und Tests analysieren.
3. Evidenz- und Gate-Mechanismen analysieren.
4. Profil-, Policy- und Adaptermechanismen untersuchen.
5. Revisions- und Invalidierungslogik prüfen.
6. Kandidaten A/B/C mit Codebelegen vergleichen.
7. Werkzeugentscheidungsraster anwenden.
8. Wiederverwendungsmatrix erstellen.
9. Risiken und Aufwand aktualisieren.
10. Konkrete Empfehlung für P1 und den PoC erstellen.

Lieferobjekte:

* P0-Bestandsbericht;
* revisionsgebundenes Datei- und Testinventar;
* Wiederverwendungsmatrix;
* PoC-Kandidatenvergleich;
* Werkzeugvergleich;
* aktualisierte Aufwandsschätzung;
* Risikoregister;
* offene Fragen;
* Entscheidungsvorlage.

Abnahmekriterien:

* keine Repository-Mutation;
* keine neue Architektur implementiert;
* keine unbelegten Aussagen über fehlende Funktionen;
* wesentliche Befunde mit konkreten Codebelegen;
* Unsicherheiten dokumentiert;
* PoC-Empfehlung nachvollziehbar.

Gate P0: ACCEPT / ACCEPT_WITH_CHANGES / REWORK / STOP.

⸻

P1 – Fachlicher Nachweisvertrag

Status: Nicht freigegeben.

Ziel: Die Semantik aller Nachweisaussagen definieren.

Arbeiten:

1. Proof-Obligation-Vertrag entwerfen.
2. A/B/C-Nachweise unterscheiden.
3. Human-owned Property Acceptance festlegen.
4. Formal-/Human-/LLM-Autoritäten trennen.
5. Ergebnisstatus definieren.
6. Mindestkatalog der STALE-Trigger festlegen.
7. Vertrauensanker dokumentieren.
8. Gate-Politik beschließen.
9. Negativ- und Missbrauchsfälle definieren.
10. Unabhängigen Review durchführen.

Lieferobjekte:

* fachlicher Nachweisvertrag;
* vorläufiges maschinenlesbares Schema;
* Status- und Autoritätsmodell;
* Invalidierungskatalog;
* Governance-Entscheidung;
* Review-Bericht.

Gate P1: Keine widersprüchliche oder überhöhte Nachweissemantik.

⸻

P2 – Isolierter formaler PoC

Status: Nicht freigegeben.

Ziel: Eine oder zwei konkrete Sicherheitsinvarianten formal prüfen.

Arbeiten:

1. Freigegebenes Kit-Protokoll verwenden.
2. Modell erstellen.
3. Annahmen dokumentieren.
4. Invarianten formulieren.
5. Verifikationslauf durchführen.
6. Vollständigkeit und Grenzen der Untersuchung feststellen.
7. Absichtlich fehlerhafte Modellvariante erstellen.
8. Gegenbeispiel reproduzieren.
9. Ergebnisse dokumentieren.
10. Unabhängig prüfen lassen.

Lieferobjekte:

* Modell;
* Spezifikation;
* Werkzeugkonfiguration;
* positiver Prüfbericht;
* Gegenbeispiel;
* dokumentierte Grenzen.

Gate P2: Reproduzierbare Modellprüfung und reproduzierbares Gegenbeispiel.

⸻

P3 – Begrenzte Modell-Code-Brücke

Status: Nicht freigegeben.

Ziel: Relevanz des Modells für die tatsächliche Implementierung untersuchen.

Arbeiten:

1. Zustandsabbildung definieren.
2. Aktionsabbildung definieren.
3. Relevante Python-Funktionen auswählen.
4. Modellbasierte Vergleichstests erstellen.
5. Negative Implementierungsfälle untersuchen.
6. Abdeckung und nicht modellierte Effekte dokumentieren.
7. Nachweisstärke korrekt klassifizieren.
8. Aufwand und Erkenntnisgewinn bewerten.

Lieferobjekte:

* Modell-Code-Mapping;
* automatisierte Konformitätstests;
* Negativtests;
* Abdeckungsbericht;
* Aussagegrenzen;
* Wirtschaftlichkeitsbewertung.

Gate P3: Nachweisrelevanz vorhanden und korrekt begrenzt; andernfalls REWORK oder STOP.

⸻

P4 – Kit-Integration

Status: Nicht freigegeben.

Ziel: PAA in vorhandene Kit-Mechanismen einbinden.

Arbeiten:

1. Nachgewiesene Wiederverwendung realisieren.
2. Minimalen Tool-Adapter integrieren.
3. Proof Obligations verwalten.
4. Evidenz erfassen und normalisieren.
5. Revisionsbindung umsetzen.
6. STALE-Regeln implementieren.
7. Interne Nachweisvalidierung integrieren.
8. Beratende Gate-Ausgabe bereitstellen.
9. Tests und Dokumentation ergänzen.
10. Regression bestehender Kit-Funktionen prüfen.

Lieferobjekte:

* integrierter PAA-MVP;
* Evidenzschema;
* Adapter;
* Tests;
* Dokumentation;
* Integrationsbericht.

Gate P4: Keine Governance-Umgehung und keine unberechtigten Beweislabels.

⸻

P5 – Unabhängige Validierung

Status: Nicht freigegeben.

Ziel: Robustheit und Aussagekraft des MVP prüfen.

Arbeiten:

1. Unabhängige KI-Reviews.
2. Fachliche Formal-Methods-Begutachtung, soweit verfügbar.
3. Manipulierte Evidenz prüfen.
4. STALE-Fälle prüfen.
5. Timeouts und Ressourcenlimits prüfen.
6. Widersprüchliche Ergebnisse prüfen.
7. Gegenbeispiele erneut reproduzieren.
8. LLM-Autoritätsgrenzen prüfen.
9. Kit-Regression durchführen.
10. Risiken und Folgekosten bewerten.

Lieferobjekte:

* Validierungsbericht;
* Findings;
* Regressionsevidenz;
* Risikoregister;
* Entscheidungsvorlage.

Gate P5: ACCEPT / ACCEPT_WITH_CHANGES / REWORK / STOP.

⸻

P6 – Optionale Generalisierung

Status: Nicht freigegeben.

Voraussetzung: Erfolgreiche P5-Abnahme.

Mögliche Arbeiten:

* zusätzliche Verifikationsprofile;
* weitere Werkzeugadapter;
* Greenfield-/Brownfield-Unterstützung;
* stärkere Implementierungsnachweise;
* Refinement-Verfahren;
* verpflichtende Proof-Gates für ausdrücklich ausgewählte Projektprofile;
* externe Referenzprojekte;
* Langzeitpflege und Wiederholbarkeit.

Gate P6: Nachweis der Wiederverwendbarkeit an mindestens einem unabhängigen Repository.

⸻

16. Aufwandsabschätzung

16.1 Voraussetzungen

Die folgenden Werte sind Planungsgrößen für effektive Entwicklungsarbeit mit KI-Unterstützung.

Sie sind keine gemessenen Projektdaten.

Die Schätzung setzt voraus, dass zentrale Kit-Funktionen tatsächlich wiederverwendet werden können.

16.2 Aufwand nach Phasen

Phase	Geschätzter Aufwand
P0 – Bestandsaufnahme	16–30 h
P1 – Nachweisvertrag	12–24 h
P2 – Formaler PoC	30–60 h
P3 – Modell-Code-Brücke	40–80 h
P4 – Kit-Integration	35–75 h
P5 – Validierung	37–70 h
Gesamt P0–P5	170–339 h

P6 ist nicht enthalten.

16.3 Wirtschaftlichkeitsprüfung

Nach P0, P3 und P5 muss überprüft werden:

* Welche zusätzliche Sicherheit wurde tatsächlich gewonnen?
* Welche Fehlerklassen können nachweislich erkannt oder ausgeschlossen werden?
* Welche Risiken bleiben bestehen?
* Wie hoch sind die laufenden Pflegekosten?
* Wie oft müssen Nachweise wiederholt werden?
* Wie teuer sind Änderungen an Modellen und Spezifikationen?
* Ist der Nutzen größer als der Aufwand alternativer Testverfahren?

Ein Abbruch oder eine Reduzierung des Vorhabens ist ein zulässiges und gegebenenfalls richtiges Ergebnis.

⸻

17. Abnahme- und Qualitätskriterien

Der integrierte MVP ist nur akzeptabel, wenn:

1. jede Beweisverpflichtung eindeutig identifiziert ist;
2. die fachliche Eigenschaft menschlich akzeptiert wurde;
3. die formale Spezifikation versioniert ist;
4. Annahmen ausdrücklich dokumentiert sind;
5. die Nachweisebene angegeben ist;
6. der Verifikationslauf reproduzierbar ist;
7. ein gezielt fehlerhaftes Modell ein Gegenbeispiel liefert;
8. ein negativer Implementierungstest die erwartete Abweichung erkennt;
9. die Modell-Code-Beziehung dokumentiert ist;
10. die Aussagekraft der Konformitätstests nicht überhöht wird;
11. LLM-Kommentare keine formalen Ergebnisse ersetzen;
12. ein Timeout nicht zu PROVEN führt;
13. widersprüchliche Evidenz zurückgewiesen wird;
14. relevante Änderungen eine Gültigkeitsprüfung auslösen;
15. relevante STALE-Fälle zuverlässig erkannt werden;
16. Werkzeug und Konfiguration identifizierbar sind;
17. das Vertrauensmodell dokumentiert ist;
18. keine zweite Prozessautorität entsteht;
19. bestehende Kit-Gates nicht umgangen werden;
20. keine unnötige Verdopplung vorhandener Funktionen erfolgt;
21. der MVP innerhalb des genehmigten Umfangs bleibt;
22. externe Werkzeugausführung kontrolliert erfolgt;
23. ein unabhängiger Review die Nachweisgrenzen bestätigt;
24. keine unqualifizierte Aussage „Software formal verifiziert“ erzeugt wird;
25. die Folgekosten als vertretbar bewertet werden.

⸻

18. Stop-, Eskalations- und Änderungsregeln

18.1 Sofortiger Stopp

Eine Phase ist zu stoppen, wenn:

* die bestehende Kit-Autorität umgangen werden müsste;
* eine unberechtigte positive Beweisaussage entsteht;
* die erforderliche Evidenz nicht reproduzierbar ist;
* der genehmigte Umfang überschritten werden müsste;
* die fachliche Eigenschaft nicht hinreichend präzisiert werden kann;
* ein sicherheitsrelevanter Befund ohne geeignete Behandlung verbleibt.

18.2 Eskalation

Eine neue menschliche Entscheidung ist erforderlich bei:

* Wechsel des PoC-Gegenstands;
* Wechsel des Hauptverifikationsverfahrens nach Freigabe;
* Überschreitung der P3-Umfangsgrenzen;
* Einführung zusätzlicher verpflichtender Gates;
* neuer externer Ausführungsberechtigung;
* wesentlicher Architekturänderung;
* erheblich gestiegenem Aufwand.

18.3 Änderungsdisziplin

Änderungen am PAA-Plan sind versioniert und mit Begründung zu dokumentieren.

Frühere Review-Findings dürfen nicht allein durch Umformulierung als erledigt gelten.

Jeder geschlossene Finding benötigt eine nachvollziehbare Entscheidung oder Evidenz.

⸻

19. Offene Fragen für die weitere Diskussion

Architektur

F01: Welche DPA-Komponenten sind tatsächlich wiederverwendbar?

F02: Welche generischen Kit-Schnittstellen eignen sich für PAA?

F03: Wie wird PAA integriert, ohne neue Autoritätskonflikte zu erzeugen?

Formale Methoden

F04: Welcher der drei PoC-Kandidaten ist am besten spezifizierbar?

F05: Ist TLA+/TLC oder ein anderes Verfahren für den ersten PoC geeigneter?

F06: Wie lässt sich die Modell-Code-Brücke mit geringstem Aufwand sinnvoll gestalten?

F07: Wann ist ein Nachweis formal, begrenzt oder nur empirisch?

Fachliche Korrektheit

F08: Wie wird sichergestellt, dass die formale Eigenschaft die tatsächliche Anforderung beschreibt?

F09: Welche Mindestanforderungen gelten für die menschliche Eigenschaftsakzeptanz?

Evidenz und Vertrauen

F10: Welche Vertrauensannahmen sind für die eingesetzten Werkzeuge akzeptabel?

F11: Welche STALE-Trigger sind zwingend?

F12: Wie wird Evidenzintegrität über Änderungen und Handoffs hinweg erhalten?

Wirtschaftlichkeit

F13: Welche Fehlerklassen rechtfertigen den zusätzlichen Aufwand?

F14: Wie hoch ist der langfristige Pflegeaufwand?

F15: Wann ist ein alternatives Testverfahren wirtschaftlicher?

⸻

20. Auftrag an unabhängige KI-Gutachter

Bitte prüfe diesen vollständigen PAA-v0.3-Plan unabhängig, kritisch und evidenzorientiert.

Gesucht werden nicht Zustimmung oder stilistische Verbesserungen, sondern fachliche Schwächen, falsche Annahmen, fehlende Risiken, bessere Alternativen und realistische Aufwandseinschätzungen.

20.1 Prüfaufträge

A – Architekturprüfung

Untersuche, ob PAA zur bestehenden Kit-Architektur passt und ob Funktionen unnötig dupliziert würden.

B – Nachweissemantik

Prüfe die Unterscheidung zwischen Modelleigenschaften, Implementierungseigenschaften und Modell-Code-Konformität.

C – Spezifikationsverantwortung

Bewerte, ob Human-owned Property Acceptance ausreichend ist und wie Spezifikationsfehler zusätzlich erkannt werden können.

D – Trust Boundary

Untersuche, ob LLMs, Menschen oder externe Werkzeuge unzulässig positive Beweisaussagen erzeugen könnten.

E – PoC-Auswahl

Vergleiche Safe-Merge, Publication Policy und Gate-Zustandsautomat hinsichtlich Spezifikationsnähe, Implementierungsnähe und Aufwand.

F – P3-Begrenzung

Prüfe, ob die vorgeschlagenen Grenzen sinnvoll sind und welchen minimalen Konformitätsnachweis sie ermöglichen.

G – Invalidierung

Bewerte den STALE-Mindestkatalog auf Vollständigkeit und praktische Umsetzbarkeit.

H – Aufwand und Wirtschaftlichkeit

Überprüfe die Schätzungen, insbesondere die Modell-Code-Brücke und die Folgekosten.

I – Alternativen

Untersuche, ob ein anderer Ansatz mit geringerem Aufwand vergleichbare oder bessere Sicherheit liefern könnte.

20.2 Verbindliche Review-Regeln

1. Keine unbegründete Zustimmung.
2. Dokumentierte Architektur und nachgewiesene Implementierung unterscheiden.
3. Aussagen über Kit-Funktionen möglichst mit Code- und Testbelegen versehen.
4. Keine fehlenden Funktionen behaupten, ohne sie untersucht zu haben.
5. Keine zusätzlichen autonomen Prozessautoritäten vorschlagen.
6. Keine LLM-Bewertung als mathematischen Beweis behandeln.
7. Keine begrenzte Modellprüfung als umfassende Softwareverifikation ausgeben.
8. Annahmen und Unsicherheiten offen ausweisen.
9. Vorschläge nach Sicherheitsnutzen, Aufwand und Risiko priorisieren.
10. Gegenargumente ausdrücklich behandeln.

20.3 Erwartete Antwortstruktur

1. Gesamturteil.
2. Bestätigte Stärken.
3. Kritische Befunde mit Schweregrad.
4. Unbelegte Annahmen.
5. Übersehene Risiken.
6. Bewertung der drei PoC-Kandidaten.
7. Bewertung der P3-Umfangsgrenzen.
8. Bewertung der STALE-Regeln.
9. Alternative Architektur- oder Verifikationsansätze.
10. Überarbeitete Aufwandsschätzung.
11. Konkrete Änderungsvorschläge.
12. Abschließende Empfehlung.

Zulässige Gesamturteile:

* PROCEED
* PROCEED_WITH_CHANGES
* RECONSIDER
* STOP

⸻

21. Verbindlicher P0-Untersuchungsauftrag

21.1 Auftragstitel

PAA-P0 – Read-only Implementation Inventory and Feasibility Assessment

21.2 Zielrepository

vfi64/agentic-project-kit

Die Untersuchung ist auf die tatsächlich vorliegende Revision zu beziehen.

21.3 Autoritätsregeln

* Ausschließlich lesende Untersuchung.
* Keine Repository-Mutation.
* Keine neuen Branches, Commits oder PRs.
* Keine Installation neuer Verifikationswerkzeuge.
* Keine Änderung bestehender Gates.
* Keine Änderung der Kit-Konfiguration.
* Keine Implementierung von PAA.
* Keine Netzwerk- oder sonstigen Effekte ohne gesonderte Freigabe.
* Vorhandene Kit-Kommandos nur entsprechend ihrem dokumentierten Wirkungsumfang verwenden.
* Keine erfundenen Kit-Kommandos.

Falls der bestehende Arbeitsablauf für die Untersuchung selbst lokale Artefakte erzeugen muss, sind ausschließlich die bereits autorisierten temporären oder externen Evidenzpfade zu verwenden. Eine solche Ausnahme darf nicht stillschweigend den Repository-Inhalt verändern.

21.4 Konkrete Untersuchungsaufgaben

1. Repository-Identität und Revision feststellen.
2. DPA-Implementierung vollständig hinsichtlich möglicher PAA-Wiederverwendung untersuchen.
3. Evidenzmechanismen und Schemas erfassen.
4. Gate- und Statuslogik erfassen.
5. Revisions- und Driftmechanismen erfassen.
6. Externe Tool-Ausführung und Sicherheitsgrenzen untersuchen.
7. Profil- und Policy-System untersuchen.
8. Handoff-Relevanz untersuchen.
9. Safe-Merge-Protokoll analysieren.
10. Publication-Policy-Protokoll analysieren.
11. Gate-Zustandsautomat analysieren.
12. Kandidatenvergleich erstellen.
13. Werkzeugvergleich erstellen.
14. Wiederverwendungsmatrix erstellen.
15. Risiken und Aufwand aktualisieren.
16. Konkrete P1-Empfehlung formulieren.

21.5 Erwartete Ergebnisartefakte

* paa_p0_inventory.md
* paa_p0_reuse_matrix.json
* paa_p0_protocol_candidates.md
* paa_p0_tool_selection.md
* paa_p0_risk_register.md
* paa_p0_effort_estimate.md
* paa_p0_decision_report.md

Die Dateinamen sind Vorschläge für das Berichtspaket, keine Anweisung zur Ablage im Repository.

21.6 P0-Erfolgskriterien

P0 ist erfolgreich, wenn:

* die Untersuchung revisionsgebunden ist;
* alle wesentlichen technischen Aussagen belegt sind;
* Wiederverwendung und Neuentwicklung klar unterschieden werden;
* die drei PoC-Kandidaten nachvollziehbar bewertet sind;
* ein geeigneter erster Verifikationsgegenstand empfohlen wird;
* die Werkzeugentscheidung nachvollziehbar vorbereitet ist;
* die Aufwandsabschätzung aktualisiert wurde;
* offene Fragen ausdrücklich benannt sind;
* keine unautorisierte Mutation stattgefunden hat.

21.7 Abschlussentscheidung

Nach P0 wird ausdrücklich entschieden:

* P1 freigeben;
* P0 gezielt ergänzen;
* Architekturansatz verändern;
* Vorhaben zurückstellen;
* Vorhaben beenden.

Ohne diese Entscheidung beginnt keine weitere Phase.

⸻

22. Schlussbewertung und Empfehlung

Die geplante PAA-Erweiterung ist eine plausible Weiterentwicklung des Agentic Project Kit.

Sie ergänzt dessen bisherige Stärke – kontrollierte, evidenzbasierte Entwicklungsprozesse – um die Möglichkeit, ausgewählte Korrektheitseigenschaften von Software systematisch und gegebenenfalls formal nachzuweisen.

Ihr entscheidender Nutzen entsteht jedoch nicht durch den Einsatz eines bestimmten Beweiswerkzeugs.

Er entsteht durch die Verbindung von:

1. fachlich akzeptierten Eigenschaften;
2. geeigneten formalen Prüfverfahren;
3. klar dokumentierten Annahmen;
4. überprüfbarer Evidenz;
5. kontrollierter Gültigkeit;
6. einer belastbaren Beziehung zur tatsächlichen Implementierung.

Die Modell-Code-Brücke bleibt der entscheidende fachliche Prüfstein.

PAA darf keine falsche Sicherheit erzeugen.

Deshalb gelten drei übergeordnete Grundsätze:

Keine Beweisaussage ohne klaren Geltungsbereich.

Keine Gleichsetzung von Modell und Implementierung ohne nachgewiesene Beziehung.

Keine neue Prozessautorität neben dem Kit.

Abschließende Empfehlung

PROCEED_WITH_CHANGES

Die Architekturidee ist hinreichend plausibel, um eine systematische Bestandsaufnahme zu rechtfertigen.

Eine vollständige Implementierungsfreigabe wäre derzeit verfrüht.

Nächster Schritt: ausschließlich P0 – revisionsgebundene, lesende Code-Bestandsaufnahme.

Nach P0 werden PoC-Gegenstand, Werkzeug, Umfang, Aufwand und weitere Freigabe auf Basis tatsächlicher Implementierungsevidenz entschieden.

Ende des Diskussionsentwurfs PAA v0.3.

Die Fassung v0.3 ist damit vollständig und kann unverändert an weitere KI-Gutachter übergeben werden. Gegenüber v0.2 sind insbesondere die menschliche Spezifikationsverantwortung, der STALE-Mindestkatalog, das gewichtete Werkzeug- und Protokollraster, die harte Begrenzung von P3 und der ausführbare Untersuchungsauftrag für P0 hinzugekommen.

Ich würde jetzt die unabhängige Begutachtung abschließen und anschließend P0 im Kit-Repository durchführen lassen – noch ohne eine einzige PAA-Funktion zu implementieren.