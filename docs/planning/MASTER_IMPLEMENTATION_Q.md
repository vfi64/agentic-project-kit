# Master Implementation Q2 — Restumsetzung

Status: active
Status-date: 2026-07-11
Decision status: accepted
Review policy: review_after:release:>=0.4.13
Supersedes: previous Master Implementation Q ordering after PR #1806
Repository: vfi64/agentic-project-kit

This document is the central planning anchor for Master Implementation Q2.
The Q2 update adopts the maintainer-supplied `CODEX_AUFTRAG_Q2_VERBESSERT.md`
input as the current rest-implementation order after verifying the repository state.
Historical appendices in this file remain useful baseline detail. Where they
conflict with the Q2 update below, the Q2 update and current repository state
take precedence.

## Evidence anchor

K3 closeout documentation was merged by PR #1776.
Merge commit: 7ef6ba8cf3b782c5b521e8ee1ad45b473c6a2bb8
P4b resolver sweep was merged by PR #1803.
P5a self-hosting manifest was merged by PR #1805.
Post-PR1805 handoff refresh was merged by PR #1806.
Q2 rest-plan adoption is tracked by PR #1807.

## Binding sequence

One slice equals one branch and one PR.

1. Stufe A, Schutzschirm: CM3 → CM4.
2. Stufe B, Lock-Vertrag, Repo-Identität, Hygiene: LC1 → LC2 → ID1 → ID2 → K3.
3. Stufe C, Self-hosting-Abschluss und Operating Layer: P5b → P5d → P5c-PLAN → P6a → P6b.
4. Stufe D, Lock-Nachrüstung und Negativpfade: LC3 → TH1.
5. Stufe E, Doc Lifecycle: L0 → L1 → L2 → L3 → L4 → L5.

CM1, CM2, P4a, P4b, and P5a are not active Q2 rest-work slices. Their state
is still verified by Turn 0 probes before depending on them.

## Q2 Pflichtstart

Before each new Q2 work session, read the generated handoff package and current
state documents named by the Q2 Auftrag, then run these gates before mutation:

- `agentic-kit transfer fetch-origin`
- branch, HEAD, `origin/main`, ahead/behind, and worktree checks
- `agentic-kit transfer repo-status`
- `agentic-kit transfer post-merge-check`
- `agentic-kit docs-audit`
- `agentic-kit direction validate`
- `agentic-kit direction audit-drift`
- `agentic-kit doc-registry check-unregistered --strict-scope`
- `agentic-kit standard-gates-audit-suite`

If any required startup result is not PASS or an explicit PASS/NOOP, stop with
diagnosis before product work.

## Turn 0 Entry Rule

Turn 0 is read-only except for the Q2-allowed mini-slice that may mark
`command-for-selector` done when the command is already functionally merged and
only the Direction item remains active.

The next Q2 slice is the first item in the binding sequence whose Direction item
is not `done`, whose code or evidence probe is negative, or whose acceptance is
not demonstrably satisfied. Items created by their own slice are treated as
absent until that slice runs: LC items by LC1, `repo-identity-sweep` by ID2,
`negative-path-hardening` by TH1, and L items by L0.

An item marked done while its probe is negative, or code that exists while its
Direction status is absent or stale, is an inconsistent state and a hard stop.

## Updated P5 Consequence

P4b and P5a are complete. The remaining P5 work is no longer a generic resolver
alias sweep. Q2 narrows it to:

1. P5b: enforce active path and identity literal classes, while non-active
   references and message literals remain visible but non-blocking.
2. P5d: deprecate the implicit legacy profile and warn only in manifest-less
   legacy workspaces.
3. P5c-PLAN: produce the physical migration plan only, then mark execution as
   maintainer-gated.

## Maintainer-gated stops

- LC2 Turn 1 reentrancy decision.
- P5c physical migration execution.
- strict lifecycle switch in the kit repository.
- --strict-unknown.
- propose-delete execution.
- first Comm-SCI adoption.
- the 2.0 line.

## Historical Full Text

The following Masterauftrag Q text and appendices remain historical baseline
material. The Q2 update above supersedes them when the order or acceptance
differs from the verified repository state.

MASTERAUFTRAG Q — Gesamtumsetzung: CM → LC/ID → P4–P6 → LC3/TH1 → L
Repo: vfi64/agentic-project-kit

ANHÄNGE (der Maintainer liefert sie mit diesem Auftrag; ohne sie STOPP)
  ANHANG A = Auftrag "CM — Command-Manifest-Contract" (Slices CM1–CM4)
  ANHANG B = Auftrag "LC/ID — Lock-Contract-Audit, Reentranz, Repo-Identität"
             (Slices LC1, LC2, ID1)
  ANHANG C = Auftrag "K1–K3 + P4–P6" (K3, P4a, P4b, P5a, P5b, P5d,
             P5c-PLAN, P6a, P6b)
  ANHANG D = Auftrag "L — Doc-Lifecycle" (L0–L5)
KONFLIKTREGEL: Die Anhänge gelten wörtlich; die DELTAS in diesem
Masterauftrag gehen ihnen vor. Bei Widerspruch Master↔Anhang↔
Architekturdokument: STOPP und Diagnose.

EXECUTOR-MODUS (funktioniert für Codex UND Chat-LLM)
- Codex: Führe jeden VERIFY-Block selbst aus; Tests-zuerst ROT→GRÜN
  eigenständig; Standardsequenz je Slice (work start auf frischem main →
  ruff → fokussierte pytest → docs-audit → audit-doc-currency →
  standard-gates-audit-suite → transfer protected-diff-plan
  --label <label> → commit → rules acknowledge → pr-create-complete
  --post-merge-complete).
- Chat-LLM: Der Maintainer ist die Testmaschine. Jeder VERIFY-Block wird
  formuliert als "Bitte ausführen und Ausgabe vollständig posten: …".
  NIE ein Ergebnis behaupten, das nicht gemeldet wurde. Lieferform:
  neue Dateien vollständig als "# FILE: <pfad>"; Änderungen als
  Anker-Ersetzungen (≥5 Zeilen Originalkontext davor/danach); je Schritt
  Tests → ROT gemeldet → Implementation → GRÜN gemeldet.
- GEMEINSAM: Jede Datei frisch lesen (nie Gedächtnis). Namens-Gegencheck
  vor jedem Bauen (main + offene Branches). PR-Nummern-Verfahren:
  completed_by_pr / meta.updated_after_pr erst als zweiter Commit nach
  Bekanntwerden der PR-Nummer; nie Platzhalter. Direction-Pflege ist
  Pflicht am Ende jedes Slices.

MASTER-SEQUENZ (verbindlich; ein Slice = ein Branch = ein PR)
  Stufe 1: CM1 → CM2 → CM3 → CM4                     [Anhang A]
  Stufe 2: LC1 → LC2 → ID1                           [Anhang B]
  Stufe 3: K3 → P4a → P4b → P5a → P5b → P5d →
           P5c-PLAN → P6a → P6b                      [Anhang C]
  Stufe 4: LC3 → TH1                                 [inline unten]
  Stufe 5: L0 → L1 → L2 → L3 → L4 → L5               [Anhang D]
Nach grünem Closeout automatisch zum nächsten Slice. Je Stufenabschluss
eine kompakte Statusmeldung (erledigte Slices, PR-Nummern, Besonderes).

GEPLANTE ZWISCHENSTOPPS (die einzigen; alles andere läuft durch)
  S1  LC1 Turn 3: Maintainer bestätigt die Gap-Tabelle.
  S2  LC2 Turn 1: Maintainer entscheidet Reentranz-Option A oder B.
  S3  P5c: Der Slice erzeugt NUR den Migrationsplan; Exec ist harter
      Stopp (Maintainer-Freigabe), die Sequenz läuft mit P6a weiter.
  S4  CM3/K2c-Erbe: falls ein Anhang-Turn explizit Maintainer-OK zu einer
      Tabelle verlangt, gilt das unverändert.
HARTE STOPPGRÜNDE (jederzeit): Gates FAIL nach Reparaturversuch,
protected-diff BLOCK, Architektur-Widerspruch, Anhang fehlt/unlesbar,
VERIFY zeigt inkonsistenten Zustand (teilweise vorhandene Slices),
Nutzerentscheidung nötig. MAINTAINER-GATED bleiben dauerhaft: P5c-Exec,
strict-lifecycle-Umschaltung im Kit-Repo, --strict-unknown (CM),
propose-delete-Ausführung, Comm-SCI-Erstadoption, 2.0-Linie.

════════════════════════════════════════════════════════════════
TURN 0 — ANHANGSCHECK + ZUSTANDSERMITTLUNG (Pflicht bei JEDEM Start,
auch bei Wiederaufnahme in neuer Session)
════════════════════════════════════════════════════════════════
1. Bestätige die vier Anhänge durch Auflisten ihrer Slice-IDs (A: CM1–CM4;
   B: LC1,LC2,ID1; C: K1,K2,K3,P4a,P4b,P5a,P5b,P5d,P5c,P6a,P6b;
   D: L0–L5). Fehlt einer → STOPP "attachment missing".
2. VERIFY-Zustandsampel (Codex: ausführen / Chat: ausführen lassen,
   Ausgabe roh posten):
     python3 - <<'EOF'
     import yaml
     d=yaml.safe_load(open('docs/planning/PROJECT_DIRECTION.yaml'))
     ids={e['id']:e.get('status') for k in ('roadmap','plans')
          for e in (d.get(k) or [])}
     probes=['command-manifest-hardening','command-for-selector',
       'instruction-lint-gate','chat-entrypoint-contract',
       'lock-contract-audit','lock-reentrancy-decision',
       'lock-coverage-remediation','repo-identity-literals',
       'p4-namespace-completion','p5a-self-hosting-manifest',
       'p5b-resolver-aliases','p5d-legacy-path-deprecation',
       'p5c-physical-migration','p6-gui-project-selection-and-ci-recipe',
       'doc-lifecycle-metadata','doc-lifecycle-signals',
       'doc-lifecycle-sweep','doc-lifecycle-strict-adoption',
       'hygiene-manifest-adopt-baseline','negative-path-hardening']
     print('updated_after_pr:',(d.get('meta') or {}).get('updated_after_pr'))
     [print(f"  {p}: {ids.get(p,'ABSENT')}") for p in probes]
     EOF
     grep -c "manifest_sha" docs/reference/agentic-kit-commands.json
     grep -rn "vfi64/agentic-project-kit" src/agentic_project_kit/successor_handoff_package.py | wc -l
     grep -c "NAMESPACE_DEFAULTS" src/agentic_project_kit/workspace.py
     ls .agentic/config.yaml 2>/dev/null; ls docs/architecture/evidence/ | grep -cE "mutation|branch-hygiene"
     grep -c "lifecycle" src/agentic_project_kit/cli.py
3. EINSTIEGSREGEL (deterministisch): Der nächste auszuführende Slice ist
   der ERSTE in der Master-Sequenz, dessen Direction-Item nicht done ist
   bzw. (falls Item erst vom Slice selbst angelegt wird: CM-Items durch
   CM1, LC-Items durch LC1, L-Items durch L0, negative-path-hardening
   durch TH1) dessen Code-Probe negativ ist. Interpretationstabelle:
     CM1 fertig ⇔ manifest_sha-grep ≥ 1 UND Item done
     ID1 fertig ⇔ vfi64-Zählung == 0 im successor-Modul
     P4a fertig ⇔ NAMESPACE_DEFAULTS ≥ 1
     P5a fertig ⇔ .agentic/config.yaml existiert
     K3  fertig ⇔ branch-hygiene-Evidence ≥ 1
     L   begonnen ⇔ lifecycle-Zählung ≥ 1 oder L-Items präsent
   Zeigt die Ampel einen TEILZUSTAND innerhalb eines Slices (z.B. Item
   done, aber Code-Probe negativ): STOPP "inconsistent state" mit Befund.
4. Melde: "Einstieg bei <Slice> (Stufe <n>); erledigt: <Liste>". Dann
   beginne dort. KEINE erledigten Slices wiederholen.

════════════════════════════════════════════════════════════════
DELTAS ZU DEN ANHÄNGEN (gehen dem Anhangstext vor)
════════════════════════════════════════════════════════════════
Δ-C1  K1 und K2 aus Anhang C werden ÜBERSPRUNGEN — anderweitig erledigt.
      Beleg-VERIFY vor Stufe 3 (muss beides positiv sein, sonst STOPP):
        grep -c "strict-scope" src/agentic_project_kit/standard_gates_audit_suite.py   (≥1)
        ls docs/agent_rules 2>/dev/null || echo TAXONOMY-OK                            (TAXONOMY-OK)
      K3 wird ausgeführt wie spezifiziert.
Δ-C2  P4b zusätzlich: Der Abschluss-Evidence-Report erhält eine zweite
      Sektion "repo identity literals" (Muster: vfi64/, github.com/…) —
      Input ist die ID1-Restliste aus Stufe 2; Findings dort werden NICHT
      in P4b migriert, nur ausgewiesen (Folgearbeit sichtbar machen).
Δ-C3  P6a: Der GUI-Button "Lint clipboard" existiert nach CM3 bereits —
      nicht doppeln; beim Header-/Panel-Umbau erhalten bleiben (Smoke-Test
      deckt ihn mit ab).
Δ-C4  Anhang-C-Kopfzeile "Beruht auf Tarball-Verifikation …" ist
      historisch; maßgeblich ist die Turn-0-Ampel dieses Masterauftrags.
Δ-D1  L0 legt NUR die fünf L-Items an (die CM-/LC-Items existieren nach
      Stufe 1/2 bereits — Anhang-D-Wortlaut entsprechend reduzieren).
Δ-D2  Vor L3: Abgleich mit dem Direction-Item
      docs-centralize-and-remove-command [Maintainer-Parallellinie].
      VERIFY: dessen Status + grep nach bereits existierender
      Sweep-/Centralize-Funktionalität. Teilüberdeckung → ERWEITERN statt
      doppeln; Befund und Abgrenzung im L3-PR dokumentieren.
Δ-D3  L4 Release-Haken: release ready kann durch die aktive
      release-command-authority-Linie verändert sein — Implementierung
      FRISCH lesen (steht im Anhang, hier verschärft: bei Abweichung vom
      Anhangs-Wortlaut Anpassung im PR begründen, nicht stoppen).
Δ-A1  CM1-Direction-Paket: zusätzlich prüfen, ob die Parallellinie
      bereits Items mit überlappender Bedeutung trägt (grep 'command' in
      der Direction) — Kollision → melden statt anlegen.

════════════════════════════════════════════════════════════════
STUFE 4 — INLINE-SPEZIFIKATIONEN (in keinem Anhang enthalten)
════════════════════════════════════════════════════════════════
LC3 — Lock-Coverage-Remediation
Branch: codex/lc3-lock-coverage-remediation · Label: lc3-lock-coverage-remediation
VORBEDINGUNG (VERIFY): LC1-Evidence existiert (mutation-lock-coverage-*);
KIT_AS_OS_ARCHITECTURE.md §5.5 trägt den LC2-Entscheid (Option A oder B —
Wortlaut zitieren). P4b ist done (Item-Check) — LC3 arbeitet auf
resolver-finalem Code.
ZUERST LESEN: workspace_lock.py; die LC1-Gap-Tabelle (Evidence-Datei);
jede Gap-Funktion samt Aufrufern.
AUFGABE
1. Reentranz gemäß Entscheid implementieren:
   OPTION A: acquire_workspace_lock erkennt eigene lebende PID im Lock
   und kehrt als dokumentierter No-op-Kontext zurück (Zähler für
   verschachtelte Nutzung; Release nur auf äußerster Ebene). Tests:
   nested-acquire-no-deadlock, fremde-PID-bleibt-busy, release-Tiefe.
   OPTION B: Primitive der Gap-Liste erhalten Docstring-Vertrag
   "must be called under workspace lock (LC2/Option B)" + assert-freien
   Laufzeit-Hinweis NUR im Debug-Log; alle TOP-LEVEL-Einstiege
   (CLI-Kommandos, GUI-Brücke) der Kategorien A–C nehmen das Lock. Tests:
   je Top-Level-Einstieg lock-taken/released.
2. Nachrüstung: JEDE Funktion der LC1-Gap-Liste (Kategorien A–C) wird
   gemäß Entscheid versorgt (direkt gelockt bzw. vertraglich dem
   Top-Level zugeordnet — Zuordnung je Funktion in einer Tabelle im
   PR-Text, keine stillen Auslassungen). branch_create ist der
   Referenzfall und MUSS versorgt sein.
3. Kommandoisierung: neues READ_ONLY-Audit audit-mutation-lock-coverage —
   die LC1-Methodik als Code (Introspektion der Kommandos + statische
   Erkennung von git/gh/Schreib-Operationen, konservativ; bekannte
   Grenzen im Report-Kopf deklariert). Findings: Kategorie-A–C-Funktion
   ohne Lock UND ohne Option-B-Vertragsmarker → BLOCK-Finding.
   Suite-Aufnahme ERST, wenn der Lauf auf main clean ist (Reihenfolge im
   Slice: erst nachrüsten, dann Gate scharf; main nie rot).
4. Frische Evidence (post-lc3) committen + registrieren; §5.5-Verweis
   "remediation completed (PR <n>)" ergänzen.
AKZEPTANZ: Gap-Liste = 0 im neuen Audit; Audit in Suite grün;
Reentranz-Verhalten testfest; direction: lock-coverage-remediation → done.

TH1 — Negative-Path-Hardening
Branch: codex/th1-negative-path-hardening · Label: th1-negative-path-hardening
AUFGABE: Fehlpfad-Tests (tmp_path) für vier Module — Verhalten heute erst
ERHEBEN (Test dokumentiert Ist), dann NUR dort härten, wo ein unbehandelter
Traceback oder eine irreführende Meldung vorliegt (Golden-Änderungen je
einzeln begründet):
  successor_handoff_package: fehlende Handoff-Quelle · kaputtes YAML in
    einer Quelle · leere Registry
  workspace_init: teilbeschriebenes .agentic/ (Verzeichnis da, kein
    Manifest = foreign-Pfad) · Zieldatei-Kollision bei --inject-ci
  workspace_upgrade: korruptes/leeres Manifest · unbekannter Feldtyp
  instruction lint (aus CM3): leerer Input · Binär-/Nicht-UTF8-Input ·
    nur-Prosa-Input
Direction: neues plans-Item negative-path-hardening [active] zu Beginn,
→ done am Ende (completed_by_pr).
AKZEPTANZ: definierte, getestete Fehlermeldungen statt Tracebacks in
allen gelisteten Fällen; keine Verhaltensänderung auf Happy Paths.

════════════════════════════════════════════════════════════════
ABSCHLUSS NACH STUFE 5
════════════════════════════════════════════════════════════════
1. Turn-0-Ampel erneut laufen lassen: ALLE Probes done/positiv —
   Abweichung melden.
2. Gesamtabschluss-Evidence: frisches audit-command-manifest,
   audit-mutation-lock-coverage, audit-path-literals, Lifecycle-Audit —
   als ein Sammel-Evidence-Dokument committen + registrieren.
3. Statusmeldung an den Maintainer: erledigte Slices mit PR-Nummern,
   offene Maintainer-Gates (P5c-Exec-Plan liegt vor; strict-Schalter;
   Comm-SCI-Adoption als nächster menschlicher Schritt Richtung 1.0-
   Kriterium b). DANN STOPP. Nichts Weiteres eigenmächtig.


Anhänge:

# Anhänge A–D zum Masterauftrag Q (agentic-project-kit)

Zweck: Dieses Dokument bündelt die vier Detailaufträge, auf die der
Masterauftrag Q verweist. Es wird IMMER ZUSAMMEN mit dem Masterauftrag Q an
den Executor (Codex oder Chat-LLM) übergeben.

Nutzungsregeln:
- Die Anhänge gelten wörtlich; die DELTAS im Masterauftrag Q gehen ihnen vor
  (u.a. Δ-C1: K1 und K2 aus Anhang C werden übersprungen).
- Turn 0 des Masterauftrags prüft die Vollständigkeit anhand der Slice-IDs:
    ANHANG A: CM1, CM2, CM3, CM4
    ANHANG B: LC1, LC2, ID1
    ANHANG C: K1, K2, K3, P4a, P4b, P5a, P5b, P5d, P5c, P6a, P6b
    ANHANG D: L0, L1, L2, L3, L4, L5

════════════════════════════════════════════════════════════════════════════
ANHANG A — AUFTRAG CM (Command-Manifest-Contract: CM1–CM4)
════════════════════════════════════════════════════════════════════════════

AUFTRAG CM — Command-Manifest-Contract: Hash-Ack, Selektor, Instruction-Lint,
Einstiegspunkte
Repo: vfi64/agentic-project-kit
Vier Slices, je eigener Branch + PR, Reihenfolge strikt:
  CM1  codex/cm1-command-manifest-hardening · Label cm1-command-manifest-hardening
  CM2  codex/cm2-command-for-selector       · Label cm2-command-for-selector
  CM3  codex/cm3-instruction-lint-gate      · Label cm3-instruction-lint-gate
  CM4  codex/cm4-chat-entrypoint-contract   · Label cm4-chat-entrypoint-contract

EXECUTOR-MODUS (dieser Auftrag funktioniert für Codex UND Chat-LLM)
- WENN du selbst ausführen kannst (Codex): Führe jeden VERIFY-Block selbst
  aus, arbeite Tests-zuerst ROT→GRÜN eigenständig, nutze die
  Standardsequenz (work start auf frischem main → ruff → fokussierte
  pytest → docs-audit → audit-doc-currency → standard-gates-audit-suite →
  transfer protected-diff-plan --label <label> → commit →
  rules acknowledge → pr-create-complete --post-merge-complete).
- WENN du NICHT ausführen kannst (Chat-LLM): Der Maintainer ist die
  Testmaschine. Jeder VERIFY-Block wird als "Bitte ausführen und Ausgabe
  vollständig posten: …" formuliert. Behaupte NIE ein Ergebnis, das nicht
  gemeldet wurde. Lieferform: neue Dateien VOLLSTÄNDIG als "# FILE: <pfad>";
  Änderungen als Anker-Ersetzungen (≥5 Zeilen Originalkontext davor/danach).
  Rhythmus je Schritt: Tests liefern → ROT gemeldet → Implementation →
  GRÜN gemeldet.
- GEMEINSAM: Jede Datei frisch lesen (nie Gedächtnis). Namens-Gegencheck
  vor jedem Bauen: prüfe insbesondere, ob bereits existieren:
  ein JSON/MD-Generator für die Kommandoreferenz (Suche: command-taxonomy,
  commands.*export|render|generate, reference.*generate), Clipboard-Helfer
  in der GUI, ein Ack-Mechanismus jenseits rules acknowledge. Fund →
  ERWEITERN statt doppeln, Entscheidung im PR begründen.
- PR-Nummern-Verfahren: completed_by_pr / meta.updated_after_pr erst als
  zweiter Commit im PR-Branch nach Bekanntwerden der Nummer; nie
  Platzhalter-Strings.
- Direction-Pflege je Slice: zugehöriges plans-Item auf done; direction
  validate PASS.
- Maßgeblich: docs/architecture/KIT_AS_OS_ARCHITECTURE.md (§4 Safety-
  Regeln, §12 Evidence) und docs/governance/ (Command-Safety-Normen).
  Widerspruch → STOPP/melden, nicht raten.

DESIGN-KONSTANTEN (gelten überall)
- BLOCK-Philosophie: Eindeutiges blockt hart (Exit 2); nur ungemappte
  Raw-Muster sind WARN (Exit 1) mit Schalter --strict-unknown (dann auch
  Exit 2). Exit 0 = clean.
- Hash: manifest_sha = sha256(kanonisches JSON der commands-Liste OHNE
  meta-Block; json.dumps(..., sort_keys=True, separators=(",",":")))[:12].
- Determinismus: kein Gate hängt an Systemzeit oder Netz.
- ACK-Zeile (exakter Wortlaut): "COMMAND_MANIFEST_ACK <manifest_sha>".

════════════════════════════════════════════════════════════════
CM1 — Manifest härten: Selektionsfelder, Hash, MD-Generator, Sync-Gate
════════════════════════════════════════════════════════════════
ZUERST LESEN
docs/reference/agentic-kit-commands.json (VOLLSTÄNDIG: heutiges Schema,
Eintragsfelder, wie viele Kommandos), docs/reference/AGENTIC_KIT_COMMANDS.md
(Kopf: generiert oder Hand?), cli.py (Typer-Struktur für Introspektion),
das Kommando-Inventar-Testmuster (tests/test_transfer_command_inventory.py),
docs/governance/COMMAND_SAFETY_*-Norm (Safety-Vokabular).

AUFGABE
1. Direction-Items anlegen (ein YAML-Paket, Feldstil wie Bestand):
   command-manifest-hardening [active], command-for-selector [planned,
   depends_on: command-manifest-hardening], instruction-lint-gate
   [planned, depends_on: command-for-selector], chat-entrypoint-contract
   [planned, depends_on: instruction-lint-gate].
2. JSON-Schema erweitern (abwärtskompatibel, bestehende Felder unberührt):
   je Kommando NEU: safety (READ_ONLY|BOUNDED|DESTRUCTIVE — PFLICHT),
   task_tags [str] (optional), when_to_use str (optional),
   replaces_raw [str] (default []), dry_run_available bool (default false).
   Top-Level meta: {schema_version: 1, manifest_sha: <hash>,
   generated_md: "docs/reference/AGENTIC_KIT_COMMANDS.md"}.
3. Erstbefüllung, konservativ: safety für JEDES Kommando aus Governance-
   Norm/Code ableiten (Unklares → BOUNDED + im PR gelistet).
   replaces_raw-Startkuratierung — RAW-Seite fest, Wrapper-Seite aus der
   JSON verifizieren (exakte CLI-Namen, nicht raten):
     git push            → der push-current-Wrapper
     git commit          → der commit-paths-Wrapper
     git switch -c / git checkout -b → der branch-create-Wrapper
     gh pr create        → pr-create-complete-Flow
     gh pr merge         → der merge-Flow-Wrapper
     git push --delete / branch -D remote → delete-merged-work-branch
     git tag / release publish roh → release ready/prepare (+ Hinweis:
       Tag/Publish ist Maintainer-Akt)
   Nur belegbare Mappings eintragen; dry_run_available=true überall dort,
   wo das Kommando einen dry-run/plan-Modus hat (aus JSON/CLI-Hilfe belegen).
4. Neues Kommando `agentic-kit commands render-md` (READ_ONLY, schreibt
   nur mit --execute die MD): generiert AGENTIC_KIT_COMMANDS.md
   deterministisch aus der JSON (Kopfzeile "GENERATED FROM
   agentic-kit-commands.json — do not edit; manifest_sha: <sha>";
   Gruppierung wie heute, plus safety-Spalte und when_to_use).
   MD einmal regenerieren und committen.
5. Neues Gate `agentic-kit audit-command-manifest` (deterministisch):
   BLOCK-Findings: CLI-Kommando ohne JSON-Eintrag (via Typer-Introspektion
   — Muster des Inventar-Tests verallgemeinern) · JSON-Eintrag ohne
   CLI-Kommando · safety fehlt/ungültig · manifest_sha stimmt nicht mit
   Neuberechnung überein · MD weicht vom Generator-Output ab ·
   replaces_raw-Ziel existiert nicht im Manifest.
   In die standard-gates-audit-suite aufnehmen — ERST nachdem alles obige
   konsistent ist (main darf nicht rot werden; Reihenfolge im Slice:
   erst Daten fixen, dann Gate scharf).

VERIFY (Codex: ausführen / Chat: ausführen lassen und posten)
  agentic-kit audit-command-manifest            → PASS
  agentic-kit commands render-md --execute && git diff --stat → leer
  python -m pytest <neue Testdatei> -q          → grün
TESTS: Introspektion-vs-JSON beidseitig (Fixture-App), Hash-Stabilität
(Feldreihenfolge egal), Hash-Änderung bei Eintragsänderung, MD-Drift
erkannt, replaces_raw-Ziel-Validierung, safety-Pflicht.
AKZEPTANZ: Gate in Suite grün auf main; MD generiert; Startmappings
belegt; direction: command-manifest-hardening → done.

════════════════════════════════════════════════════════════════
CM2 — Deterministischer Selektor: agentic-kit command-for
════════════════════════════════════════════════════════════════
ZUERST LESEN: CM1-Manifestcode (Lade-/Hash-Helfer wiederverwenden),
ein READ_ONLY-Kommando als CLI-Muster.
AUFGABE
`agentic-kit command-for (--raw "<cmdline>" | --task <tag>) [--json]`
(READ_ONLY):
- --raw: Normalisierung (führende $/#/> strippen, Whitespace kollabieren),
  Match = längster replaces_raw-Präfix der Zeile (z.B. "git push origin
  HEAD" matcht "git push"). Treffer → Ausgabe: verbotener Raw-Befehl,
  Wrapper-Kommando(s), safety, when_to_use, dry-run-Hinweis falls
  verfügbar. Kein Treffer → "no mapping; if this mutates the repo,
  check the manifest before running raw" (Exit 0 — der Selektor blockt
  nicht, das tut der Lint).
- --task: alle Kommandos mit dem Tag, sortiert READ_ONLY→BOUNDED→
  DESTRUCTIVE, je Zeile name·safety·when_to_use. Unbekannter Tag →
  Liste existierender Tags.
VERIFY: drei --raw-Beispiele (git push origin main / gh pr create -f /
git status) + ein --task-Beispiel; Ausgaben prüfen.
TESTS: Präfix-Längstmatch-Matrix, Normalisierung, kein-Mapping-Pfad,
Task-Sortierung, --json-Shape.
AKZEPTANZ: deterministisch, sekundenschnell, keine Manifest-Mutation;
direction: command-for-selector → done.

════════════════════════════════════════════════════════════════
CM3 — instruction lint: der harte Empfänger-Gate (Kern-Slice)
════════════════════════════════════════════════════════════════
ZUERST LESEN
CM1/CM2-Module; transfer apply/inspect-Implementierung (WO wird
Order-Text gelesen — exakte Einhängestelle); gui_task_editor SEND
(Carrier-Header-Erzeugung); GUI-Brücke + ein READ_ONLY-Button als Muster;
tkinter-Clipboard-Zugriff im Bestand (Gegencheck).

AUFGABE
1. Kommando `agentic-kit instruction lint (--file <pfad> | --stdin)
   [--require-ack/--no-require-ack (Default: AN)] [--strict-unknown]
   [--json]` (READ_ONLY):
   EXTRAKTION (konservativ, deterministisch): bewertet werden nur
   (a) Zeilen innerhalb fenced code blocks und (b) Zeilen, die nach Strip
   von führenden $/#/>-Prompts mit einem der Präfixe beginnen:
   git | gh | agentic-kit | python -m agentic_project_kit. Alles andere
   ist Prosa und wird ignoriert.
   REGELN:
   R1 RAW_REPLACED (BLOCK): Zeile matcht (Längstpräfix) ein
      replaces_raw-Mapping → Meldung "REJECTED: use `<wrapper>` instead
      of `<raw>` (safety: <s>)".
   R2 UNKNOWN_SUBCOMMAND (BLOCK): `agentic-kit <sub...>` existiert nicht
      im Manifest (Halluzinationsschutz; Vergleich gegen Introspektions-/
      Manifestliste).
   R3 ACK (BLOCK, wenn --require-ack): erste nicht-leere Zeile des
      Eingabetextes ist nicht exakt "COMMAND_MANIFEST_ACK <aktueller sha>"
      → "REJECTED: missing/stale COMMAND_MANIFEST_ACK — read
      docs/reference/agentic-kit-commands.json (sha <sha>) first".
   R4 DESTRUCTIVE_NO_DRYRUN (BLOCK): Manifest-Kommando mit
      safety=DESTRUCTIVE und dry_run_available=true erscheint OHNE dass
      im selben Text davor dieselbe Kommandobasis mit --dry-run|plan
      vorkommt.
   W1 UNKNOWN_RAW (WARN; mit --strict-unknown BLOCK): git/gh-Zeile ohne
      Mapping.
   AUSGABE: je Finding Zeile+Regel+Meldung; am Ende ein copy-paste-
   fertiger REJECTION-Block (für die Rückgabe in den Chat) bei Exit 2.
   Exit: 0 clean · 1 nur WARN · 2 BLOCK.
2. Integration transfer apply (und inspect als Anzeige): VOR jeder
   Anwendung läuft der Lint über den Order-Text; Exit 2 → Refusal mit dem
   REJECTION-Block, keine Anwendung; Exit 1 → Anwendung mit geloggtem
   WARN. Bestehende apply-Contract-Tests bleiben grün (Fixtures bekommen
   ACK-Zeile + saubere Kommandos — Anpassung je Fixture begründen).
3. SEND-Carrier-Header: zwei Zeilen ergänzen
   "manifest: docs/reference/agentic-kit-commands.json" und
   "manifest_sha: <sha>" (Wiederholung im Kanal; Golden-Tests des
   Carriers entsprechend nachführen, begründet).
4. GUI-Button "Lint clipboard" (READ_ONLY-Gruppe): liest Clipboard via
   tkinter (Bestandsmuster nutzen, sonst self.clipboard_get() mit
   Fehlerpfad "clipboard empty/unavailable"), pipe't an
   `instruction lint --stdin` über die zentrale Brücke, zeigt Ausgabe im
   Ausgabefenster. GUI bleibt dünn; kein Auto-Execute von irgendetwas.

VERIFY: Lint gegen drei Fixture-Texte (sauber mit ACK / git push +
fehlender ACK / halluziniertes Subkommando) — erwartete Exits 0/2/2;
transfer apply-Refusal im Fixture; GUI-Smoke headless.
TESTS (Matrix, tmp_path): jede Regel Positiv+Negativ; Extraktion
(Prosa mit "git push" im Fließtext wird NICHT bewertet; fenced block
wird bewertet); Längstpräfix; ACK exakt/stale/fehlend; strict-unknown;
Exit-Codes; apply-Integration beidseitig; Carrier-Header-Golden.
AKZEPTANZ: Kein non-konformer Order-Text erreicht die Anwendung;
REJECTION-Block ist chat-tauglich formuliert; Suite grün; direction:
instruction-lint-gate → done.

════════════════════════════════════════════════════════════════
CM4 — Einstiegspunkte: session-start, refresher, AGENTS.md, Drift-Gate
════════════════════════════════════════════════════════════════
ZUERST LESEN
AGENTS.md (Kopfstruktur); ALLE Initial-Prompt-Quellen per Suche
(grep -rn "INITIAL_LLM_PROMPT\|initial.prompt" src/ docs/ — inkl.
workspace_init-Template und GUI-Quelle); chat-bootstrap-drift-rules-
Mechanismus (Erweiterungsort oder Verweis).

AUFGABE
1. `agentic-kit chat refresher [--mode copy-paste|remote|file-transfer]`
   (READ_ONLY): erzeugt den 6-Zeilen-Block —
     COMMAND_MANIFEST_ACK-Pflicht (mit aktuellem sha eingesetzt),
     Manifest-Pfad, "before proposing ANY command run/consult
     `agentic-kit command-for`", "raw git/gh commands with a mapped
     wrapper are rejected by instruction lint", Modus-Zusatzzeile
     (copy-paste: "your reply will be linted before execution";
     remote: "read the manifest file first, it is the single source";
     file-transfer: "the carrier header pins the manifest sha").
2. `agentic-kit chat session-start --mode copy-paste` (READ_ONLY):
   Refresher + generierte Kompaktliste ALLER Kommandos aus der JSON
   (eine Zeile je Kommando: name · safety · when_to_use) — bewusst
   vollständig inline (Token-Preis ist gewollt).
3. AGENTS.md-Kopf (Anker-Ersetzung, oberster Abschnitt):
   "MANDATORY FIRST READ: docs/reference/agentic-kit-commands.json
   (manifest_sha: <sha>). Every reply containing commands MUST start
   with: COMMAND_MANIFEST_ACK <sha>. Consult `agentic-kit command-for`
   before proposing commands."
4. Alle gefundenen Initial-Prompt-Quellen: denselben Kopfblock einfügen
   (Template-seitig; erzeugte Fremd-Repo-Prompts tragen ihn dadurch
   automatisch).
5. audit-command-manifest erweitern: zusätzliche BLOCK-Findings, wenn
   AGENTS.md oder eine Initial-Prompt-Quelle einen sha trägt, der nicht
   dem Manifest entspricht (Einstiegspunkte können nie veralten).
   HINWEIS UMSETZUNG: sha-Nennungen in diesen Dateien werden vom
   render/refresher-Codepfad geschrieben — ein kleines
   `agentic-kit commands sync-entrypoints --execute` aktualisiert alle
   Nennungen deterministisch; das Gate prüft nur.

VERIFY: refresher/session-start-Ausgaben zeigen; sync-entrypoints
Roundtrip (sha in JSON künstlich ändern im Fixture → Gate BLOCK →
sync → PASS); Suite grün.
TESTS: Block-Golden je Modus, session-start enthält alle Kommandos
(Zählung = Manifest), AGENTS.md/Template-sha-Konsistenz Positiv+Negativ,
sync-entrypoints idempotent.
AKZEPTANZ: Jeder Einstiegspunkt (AGENTS.md, Initial-Prompts, Refresher,
Carrier-Header aus CM3) trägt denselben, gate-geprüften sha; direction:
chat-entrypoint-contract → done.

════════════════════════════════════════════════════════════════
NACH CM4 — STOPP
════════════════════════════════════════════════════════════════
Frisches audit-command-manifest-Ergebnis als Evidence unter
docs/architecture/evidence/ ablegen + registrieren. Maintainer-gated
bleiben: --strict-unknown-Scharfstellung (nach Mapping-Reife),
replaces_raw-Erweiterungen (kuratiert), LC3/L-Serie/P4–P6 unberührt.
Nichts eigenmächtig. Abschluss melden.

════════════════════════════════════════════════════════════════════════════
ANHANG B — AUFTRAG LC/ID (Lock-Contract-Audit, Reentranz, Repo-Identität:
LC1, LC2, ID1)
════════════════════════════════════════════════════════════════════════════

AUFTRAG LC/ID — Lock-Contract-Audit, Reentranz-Entscheid, Repo-Identität
Repo: vfi64/agentic-project-kit
Drei Slices, je eigener Branch + PR, Reihenfolge strikt:
  LC1  codex/lc1-mutation-lock-audit        · Label lc1-mutation-lock-audit
  LC2  codex/lc2-lock-reentrancy-decision   · Label lc2-lock-reentrancy-decision
  ID1  codex/id1-repo-identity-derivation   · Label id1-repo-identity-derivation

ARBEITSMODUS (gilt für alle drei Slices)
- Du (ChatGPT) hast KEINE Ausführungsumgebung. Alles Ausführen (git, grep,
  ruff, pytest, agentic-kit-Kommandos, PR) macht der Maintainer lokal und
  meldet dir die Ausgabe. Behaupte NIE ein Ergebnis (Test grün, Gate PASS,
  grep-Befund), das nicht gemeldet wurde — formuliere stattdessen "Bitte
  ausführen und Ausgabe posten: …".
- Lies jede Datei frisch über den GitHub-Connector (main), nie aus
  Gedächtnis. Nicht sicher lesbar → als Paste anfordern.
- Lieferform: neue Dateien VOLLSTÄNDIG als Codeblock mit Kopfzeile
  "# FILE: <pfad>". Änderungen an Bestandsdateien als Ersetzungsblöcke mit
  eindeutigen Ankern (≥5 Zeilen Originalkontext davor und danach), keine
  Zeilennummern. Tests IMMER vor Implementation (Maintainer meldet ROT,
  dann Code, dann GRÜN).
- PR-Nummern-Verfahren (verhindert Platzhalter-Strings): completed_by_pr
  und meta.updated_after_pr werden erst NACH Bekanntwerden der PR-Nummer
  als zweiter Commit im selben PR-Branch gesetzt; niemals raten, niemals
  Platzhalter.
- Lokale Standardsequenz je Slice (Maintainer): git switch main && git pull
  --ff-only → agentic-kit work start --branch <branch> --from-ref main →
  Pakete einspielen → ruff (geänderte Dateien) → fokussierte pytest →
  agentic-kit docs-audit → audit-doc-currency → standard-gates-audit-suite
  → transfer protected-diff-plan --label <label> → commit →
  rules acknowledge → pr-create-complete --post-merge-complete.
- Maßgeblich: docs/architecture/KIT_AS_OS_ARCHITECTURE.md (§4 Regel 7,
  §5.5, §12). Widerspruch Auftrag↔Dokument → melden, nicht raten.

HARTE VERBOTE
- Kein Umbau von workspace_lock.py und keine Lock-Nachrüstung in anderen
  Modulen — das ist LC3 (Codex, nach LC2-Entscheid). LC1 ist reine
  Analyse+Evidence, LC2 reine Architektur-Doku, ID1 der einzige Code-Slice.
- Die Standard-Suite darf durch nichts hier rot werden; LC1 wird NICHT in
  die Suite eingehängt (der bekannte branch_create-Gap würde sonst main
  blocken — Kommandoisierung+Enforcement sind LC3).
- Keine Löschungen außer den zwei in ID1 benannten Konstanten.

VERIFIZIERTER KONTEXT (Anker für deine Arbeit; am Code gegenchecken)
- Lock-Nehmer heute: transfer_repo_actions.py (commit_paths ~Z.675,
  push_current ~Z.770), workspace_init.py (Z.141: "workspace_init"),
  workspace_upgrade.py. workspace_lock.py: O_CREAT|O_EXCL, JSON
  {pid, command, acquired_at}, busy-fail-fast, stale-takeover,
  finally-Release.
- Bewiesener Gap: transfer_repo_actions.py Z.561 branch_create()
  (git switch -c, optional push) läuft OHNE Lock.
- ID1-Ziel: successor_handoff_package.py Z.14
  REPO_FULL_NAME = "vfi64/agentic-project-kit", Z.15 DEFAULT_LOCAL_PATH =
  "cd /path/to/agentic-project-kit", Nutzung Z.249-250, Fallback-Literal
  Z.640 repo.get("full_name", "vfi64/agentic-project-kit").

════════════════════════════════════════════════════════════════
LC1 — Mutation/Lock-Coverage-Audit (Analyse + Evidence, kein Code)
════════════════════════════════════════════════════════════════
TURN 1 — LESEN + DIRECTION-ITEMS
Lies: workspace_lock.py komplett; KIT_AS_OS_ARCHITECTURE.md §4 Regel 7 +
§5.5; die drei Lock-Callsites; transfer_repo_actions.py um Z.561. Liefere
dann EIN YAML-Paket (Anker-Ersetzungen PROJECT_DIRECTION.yaml, Feldstil
exakt wie Bestand) mit vier plans-Items:
  lock-contract-audit [active]
  lock-reentrancy-decision [planned, depends_on: lock-contract-audit]
  lock-coverage-remediation [planned, depends_on: lock-reentrancy-decision]
  repo-identity-literals [active]
rationale je 1 Satz; source_files: [docs/architecture/KIT_AS_OS_ARCHITECTURE.md].
Maintainer: direction validate melden.

TURN 2 — GREP-BATTERIE (Maintainer führt aus, postet ALLE Ausgaben roh)
  grep -rn "acquire_workspace_lock" src/agentic_project_kit/
  grep -rn "subprocess" src/agentic_project_kit/ | grep -n "\"git\"\|'git'"
  grep -rnE "\"(push|switch|checkout|commit|add|mv|restore|clean|stash|tag|merge|rebase)\"" src/agentic_project_kit/ | grep -v tests
  grep -rn "\"gh\"\|'gh'" src/agentic_project_kit/
  grep -rnE "write_text|open\(.*[\"']w|safe_dump|shutil\.|os\.replace|os\.rename" src/agentic_project_kit/ | grep -v tests | head -80
  grep -rn "def " src/agentic_project_kit/transfer_repo_actions.py
Falls eine Ausgabe >80 Zeilen: in Teilen anfordern, nichts überspringen.

TURN 3 — INVENTAR + GAP-LISTE
Baue aus den Ausgaben EINE Tabelle: Funktion · Modul:Zeile · Kategorie ·
Lock-Status · Beleg. Kategorien (exakt diese):
  A workspace-state-mutierend  (schreibt .agentic/, Registry-, Direction-,
    Status-, Handoff-Dateien)
  B git-worktree-mutierend     (add/commit/switch/mv/restore/clean/stash …)
  C remote-mutierend           (push, gh pr create/merge, release publish)
  D read-only                  (nimmt per Vertrag NIE das Lock)
Lock-Status ∈ {direkt, geerbt-vom-Orchestrator (Beleg: Aufrufer), FEHLT,
unklar}. "Geerbt" nur mit belegter Aufrufkette (bei Bedarf gezielte
Zusatz-greps anfordern). Gegencheck: branch_create MUSS als FEHLT
erscheinen — sonst Methodik prüfen. Ergebnis: Gap-Liste (Kategorie A–C
ohne Lock) + Zählung je Kategorie. Tabelle dem Maintainer zur Bestätigung
vorlegen; STOPP bis OK.

TURN 4 — EVIDENCE + PR
# FILE: docs/architecture/evidence/mutation-lock-coverage-<JJJJ-MM-TT>.md
Inhalt: Methodik (die exakten grep-Kommandos), die Inventar-Tabelle, die
Gap-Liste, Limitierungen (statische Sicht; dynamische Aufrufe evtl.
unerfasst — §12-konform: die geposteten grep-Ausgaben sind die Logs,
als Anhangsabschnitt einbetten). Dazu der register-Aufruf (class/owner
nach Vorbild eines bestehenden evidence-Eintrags — zuerst zitieren).
Direction: lock-contract-audit → done (PR-Verfahren). Standardsequenz;
alle Gate-Ausgaben melden lassen.
AKZEPTANZ: Report committed+registriert; Gap-Liste maintainer-bestätigt;
branch_create enthalten; Suite unverändert grün.

════════════════════════════════════════════════════════════════
LC2 — Reentranz-Entscheid + §5.5-Präzisierung (reine Doku)
════════════════════════════════════════════════════════════════
TURN 1 — ENTSCHEIDUNGSVORLAGE (nichts ändern)
Auf Basis der LC1-Tabelle: Für beide Optionen Konsequenzen beziffern
(wie viele Gap-Funktionen wären je Option nachzurüsten; wo drohte
Selbst-Deadlock, wenn ein gelockter Orchestrator eine dann ebenfalls
gelockte Primitive riefe — konkrete Kandidaten aus der Tabelle nennen):
  OPTION A — same-PID-reentrant: acquire bei eigener lebender PID kehrt
    als No-op zurück (Design-Beschreibung; Umsetzung LC3). Pro: Primitive
    dürfen überall locken. Contra: verdeckte Doppel-Orchestrierung wird
    nicht mehr erkannt.
  OPTION B — top-level-only: Nur oberste Orchestrierungsebene lockt;
    Primitive bleiben lockfrei und dokumentieren "must be called under
    workspace lock". Pro: einfach, erkennbar. Contra: CLI-Direktaufrufe
    von Primitiven bleiben ungeschützt (aus LC1 belegen, welche das
    betrifft).
  Plus in beiden: Kohärenzregel zum Live-Status — "the lock holder is the
  sole writer of the wrapper live status for the locked section"
  (ergänzt safe_to_interrupt, ersetzt es nicht).
Begründete Empfehlung abgeben. STOPP: Maintainer entscheidet A oder B.

TURN 2 — UMSETZUNG DES ENTSCHEIDS
Anker-Ersetzungen in docs/architecture/KIT_AS_OS_ARCHITECTURE.md §5.5:
den gewählten Reentranz-Modus als normativen Absatz, die
Live-Status-Kohärenzregel, und einen Verweis "coverage remediation
tracked as lock-coverage-remediation (LC3)". Falls §4 Regel 7 einen
Halbsatz braucht (Kategorien A–C aus LC1 als Geltungsbereich), dort
minimal ergänzen. KEINE Codeänderung. Direction:
lock-reentrancy-decision → done; im Item lock-coverage-remediation die
gewählte Option als rationale-Zusatz vermerken. Standardsequenz + Gates
melden lassen (docs-audit/doc-currency beachten die geänderte Datei).
AKZEPTANZ: §5.5 trägt den Entscheid + Kohärenzregel; direction gepflegt;
Gates grün.

════════════════════════════════════════════════════════════════
ID1 — Repo-Identität ableiten statt hartkodieren (einziger Code-Slice)
════════════════════════════════════════════════════════════════
ZWECK: Ein adoptiertes Fremd-Repo darf in Handoff-Artefakten nie
"vfi64/agentic-project-kit" behaupten. Identität kommt künftig aus dem
git-Remote des Workspace; das Kit-Repo verhält sich (mit seinem origin)
byte-identisch.

TURN 1 — LESEN + RESTLISTE
Lies successor_handoff_package.py (Z.1–60, 240–260, 630–650 und jede
weitere Nutzung der zwei Konstanten) und ALLE Tests, die
REPO_FULL_NAME / full_name / "vfi64" / local_path prüfen:
  grep -rn "REPO_FULL_NAME\|full_name\|/path/to/agentic\|vfi64" tests/ | head -40
Maintainer zusätzlich ausführen lassen:
  grep -rn "vfi64\|/path/to/agentic" src/agentic_project_kit/ | grep -v test
Nur successor_handoff_package.py wird in ID1 umgebaut; alle weiteren
Fundstellen als Restliste-Tabelle in den PR-Text (Folge-Slice-Material,
nicht anfassen). Melde, welche bestehenden Assertions/Snapshots die
Identität einfrieren.

TURN 2 — TESTS ZUERST (ROT melden lassen)
Neue Tests (Datei gemäß Bestandskonvention; tmp_path-Fixtures mit
git init):
  test_repo_identity_parses_https_url         (https://github.com/o/r.git
                                               und ohne .git → "o/r")
  test_repo_identity_parses_ssh_url           (git@github.com:o/r.git → "o/r")
  test_repo_identity_no_origin_falls_back     (kein remote →
                                               "<dirname> (no git remote 'origin')")
  test_local_path_hint_uses_workspace_dirname (…"cd /path/to/<dirname>")
  test_kit_identity_preserved_with_origin     (Fixture mit
    git remote add origin https://github.com/vfi64/agentic-project-kit.git
    → full_name exakt "vfi64/agentic-project-kit")
Bestehende Snapshot-/Golden-Tests: NUR falls sie die alte Konstante
einfrieren, minimal anpassen (Fixture bekommt definierten origin) — jede
Anpassung einzeln begründen; keine Lockerung von Struktur-Assertions.

TURN 3 — IMPLEMENTATION (Anker-Ersetzungen)
1) Private Helfer im Modul (kein neues Modul, kein workspace.py-Umbau —
   workspace.py bleibt reine Pfad-Quelle):
     _detect_repo_full_name(root: Path) -> str
       via subprocess ["git","-C",str(root),"remote","get-url","origin"];
       Parser für https://github.com/o/r(.git), ssh://git@github.com/o/r,
       git@github.com:o/r(.git); Fehler/kein origin → Fallback-String aus
       Turn-2-Test; deterministisch, keine Netzwerkzugriffe.
     _default_local_path_hint(root: Path) -> str  ("cd /path/to/"+root.name)
2) Konstanten REPO_FULL_NAME und DEFAULT_LOCAL_PATH ersatzlos entfernen;
   Z.249/250 auf die Helfer umstellen; Z.640-Fallback:
   repo.get("full_name", _detect_repo_full_name(root)).
3) ruff; fokussierte Tests GRÜN melden lassen; volle Suite; Restliste in
   den PR-Text; Direction: repo-identity-literals → done (PR-Verfahren);
   Standardsequenz.
AKZEPTANZ: Fremd-Fixture liefert eigene Identität, no-origin-Fallback
benennt sich ehrlich, Kit-Fixture mit origin byte-identisch zur alten
Ausgabe; keine vfi64-Literale mehr in diesem Modul; Restliste
dokumentiert; Gates grün — alles per gemeldeter Ausgabe.

════════════════════════════════════════════════════════════════
NACH ID1 — STOPP
════════════════════════════════════════════════════════════════
LC3 (Lock-Nachrüstung gemäß Entscheid + Kommandoisierung des Audits als
Suite-Check) und TH1 (Negativtest-Härtung) sind Codex-Slices ab
Limit-Rückkehr; die Restliste aus ID1 ist deren Input. Nichts davon
eigenmächtig beginnen. Abschluss melden.

════════════════════════════════════════════════════════════════════════════
ANHANG C — AUFTRAG K1–K3 + P4–P6
(Hinweis Masterauftrag Δ-C1: K1 und K2 sind anderweitig erledigt und werden
ÜBERSPRUNGEN; K3 wird ausgeführt.)
════════════════════════════════════════════════════════════════════════════

Repo: vfi64/agentic-project-kit

HINWEIS: Beruht auf Remote-Verifikation (main @ updated_after_pr 1744 +
Branch-Liste via ls-remote). Vor jedem Slice Namens-Gegencheck gegen main
UND offene Branches — auch unter abweichenden Namen.

MASSGEBLICHES DOKUMENT
docs/architecture/KIT_AS_OS_ARCHITECTURE.md — hier verbindlich: §4 (Regeln
1–7), §5.2 (Ziel-Layout), §8 (Resolver/Legacy-Profil), §9 (1.0/2.0),
§10 (P4–P6), §12 (Evidence). Widerspruch Prompt↔Dokument → STOPP.

ELF SLICES, REIHENFOLGE STRIKT:
K1  strict-scope in die Standard-Suite
K2  Planning-/Ideas-Restbereinigung (D-Nacharbeit)
K3  Remote-Branch-Hygiene (Report + Abbau via Bestandskommando)
P4a Namespace-Defaults für manifest-tragende Workspaces + init-Vervollständigung
P4b Literal-Restmigration (Report-getrieben, src → resolver-only)
P5a Kit-Self-Hosting: Manifest only (neutrale Legacy-paths)
P5b Resolver-Alias-Evidence (Abschlussnachweis P4/P5-Basis)
P5d Legacy-Profil-Deprecation dokumentieren (2.0-Ankündigung)
P5c Physische Migration: NUR PLAN erzeugen — Exec ist maintainer-gated
P6a GUI-Projektwahl (--root, Open project…, cwd-Durchreichung)
P6b Operating-Layer-Quickstart-Doku + CI-Template-Test

Jeder Slice eigener Branch, eigener PR. Nach grünem Closeout automatisch
weiter. STOPP nur bei: Gates FAIL nach Reparaturversuch, protected-diff
BLOCK, Architektur-Widerspruch, Referenz nicht sicher ersetzbar,
Remote-Mutation außerhalb der freigegebenen Kommandos, P5c-Exec (explizit
gated), Nutzerentscheidung nötig.

GLOBALE ARBEITSWEISE
- Zuerst je Slice die genannten Dateien lesen. stdlib + vorhandene deps.
  Englisch in Code/Doku/Ausgaben. Tests in tmp_path-Fixtures.
- Direction-Pflege ist PFLICHT je Slice: Nach Merge das zugehörige
  roadmap/plans-Item auf done (completed_by_pr) und meta.updated_after_pr
  aktualisieren (im selben PR als letzter Commit oder Kleinst-Folge-PR);
  direction validate PASS.
- Vor Commit: ruff, fokussierte Tests, docs-audit, audit-doc-currency,
  standard-gates-audit-suite, transfer protected-diff-plan --label <label>.
- Nach Commit: rules acknowledge. PR via pr-create-complete
  --post-merge-complete.

════════════════════════════════════════════════════════════════
K1 — strict-scope in die Standard-Suite
════════════════════════════════════════════════════════════════
Branch: codex/strict-scope-suite-adoption
Label: strict-scope-suite-adoption
KONTEXT: governance-Backfill ist komplett (15/15 registriert); das
direction-plans-Item strict-scope-suite-adoption ist fällig.
ZUERST LESEN: cli_commands/doc_registry.py (--strict-scope-Pfad),
docs/DOC_REGISTRY_SCOPE.yaml, standard_gates_audit_suite.py.
AUFGABE: (1) Lokal doc-registry check-unregistered --strict-scope
ausführen. Violations in required-Bereichen? Dann diese Dateien ZUERST
registrieren (einzeln, additiv — vermutlich 0 nach Backfill) oder, falls
eine Datei bewusst nicht registriert werden soll, als exempt_files-Eintrag
mit reason (nur mit klarer Begründung im PR). (2) Den strict-scope-Aufruf
als Suite-Step aufnehmen (analog direction validate). (3) Ein Test:
Suite-Step vorhanden; strict-scope FAIL bricht die Suite (Fixture).
AKZEPTANZ: Suite enthält strict-scope; auf main 0 Violations; direction:
strict-scope-suite-adoption → done. Gates PASS.

════════════════════════════════════════════════════════════════
K2 — Planning-/Ideas-Restbereinigung
════════════════════════════════════════════════════════════════
Branch: codex/planning-ideas-residual-cleanup
Label: planning-ideas-residual-cleanup
KONTEXT: docs/ideas/ enthält noch 5 Dateien, docs/planning/ noch ~28
Alt-Markdown neben den kanonischen Direction-Dateien. Zielzustand des
Konsolidierungsplans gilt unverändert: ideas/ leer→löschen; planning/
reduziert auf PROJECT_DIRECTION.yaml, die View-/README-Dateien und wenige
bewusste Bleiber. DOC_REGISTRY_SCOPE_DECISION.md ist Audit-Artefakt und
BLEIBT. Autorität für Löschbarkeit ist das Kommando direction audit-drift.
AUFGABE: Für JEDE Restdatei genau eine Auflösung, audit-drift-getrieben:
(a) reference-clean löschbar → löschen; source_files im YAML auf
deleted_source-Markierung umstellen, Registry-Eintrag entfernen falls
vorhanden; (b) noch aktiv referenziert → Referenz auf Direction/Archiv
umbiegen, DANN löschen; (c) bewusster Bleiber → registrieren (falls in
required-Pfad) ODER exempt_files-Eintrag mit reason; im PR begründen.
ideas/-Verzeichnis am Ende entfernen, wenn leer. KEINE Löschung außerhalb
der fünf Planungsflächen; Governance/Handoff/Evidence tabu.
AKZEPTANZ: audit-drift PASS oder nur begründete Mini-Restliste im PR;
keine toten Registry-Einträge; strict-scope (K1) bleibt grün; direction:
planning-ideas-residual-cleanup → done. Gates PASS.

════════════════════════════════════════════════════════════════
K3 — Remote-Branch-Hygiene
════════════════════════════════════════════════════════════════
Branch: codex/remote-branch-hygiene
Label: remote-branch-hygiene
KONTEXT: ~20 stale Remote-Branches (u.a. codex/release-0.4.10*,
chore/a1-state-refresh, dependabot/…). Bestandskommando existiert:
transfer delete-merged-work-branch (transfer_repo_pre_pr.py:518) — gated,
einzeln. KEINE neue Löschmechanik bauen.
ZUERST LESEN: delete-merged-work-branch (exakte Guards: welche Präfixe
erlaubt? merged-Prüfung?), remote_execution_policy-Regeln.
AUFGABE: (1) READ_ONLY-Report erzeugen: je Remote-Branch (ohne main,
gui-transfer-tasks, HEAD) → merged-in-main? (git merge-base
--is-ancestor), letzter Commit-Zeitpunkt, zugehöriger PR falls
ermittelbar. Als Evidence-Datei docs/architecture/evidence/
remote-branch-hygiene-<datum>.md committen + registrieren. (2) Für jeden
Branch, der NACHWEISLICH merged UND vom Kommando-Guard erlaubt ist:
delete-merged-work-branch <branch> ausführen (einzeln, protokolliert im
PR-Text). Nicht-erlaubte/unklare Branches (z.B. dependabot/*, fremde
Präfixe) NUR im Report als "maintainer decision" listen — nicht löschen.
(3) Die Löschungen selbst sind Remote-Mutationen über das freigegebene
Bestandskommando — jede andere Remote-Löschung ist verboten.
AKZEPTANZ: Report committed+registriert; alle guard-konformen merged
Branches entfernt; Restliste klar deklariert; keine Löschung außerhalb
des Bestandskommandos. Gates PASS.

════════════════════════════════════════════════════════════════
P4a — Namespace-Defaults + init-Vervollständigung
════════════════════════════════════════════════════════════════
Branch: codex/p4a-namespace-defaults
Label: p4a-namespace-defaults
ZUERST LESEN: Architekturdokument §5.2 (Ziel-Layout) und §8;
workspace.py (KitConfig-Felder, load_workspace, P2-paths-Overrides);
workspace_init.py (was init heute anlegt); test_workspace_foundation.py
(Legacy-Golden).
AUFGABE:
1. Zweites Default-Set NAMESPACE_DEFAULTS in workspace.py: je
   KitConfig-Pfadfeld der §5.2-Zielwert, u.a.
     doc_registry_path → .agentic/registries/documentation.yaml
     rule_registry_*   → .agentic/registries/rules.yaml bzw. rules/
     status_path       → .agentic/state/status.md
     handoff_*         → .agentic/state/handoff/…
     tmp               → .agentic/tmp
     transfer_*        → .agentic/transfer/… (wie bisher)
   docs_root des ZIELPROJEKTS bleibt dessen docs/ (Projekt-Doku ist nicht
   Kit-Governance). Vollständige Mapping-Tabelle Legacy↔Namespace als
   Kommentarblock/Doku im Modul.
2. load_workspace: Manifest vorhanden → Basis = NAMESPACE_DEFAULTS;
   explizite paths-Overrides schlagen weiterhin alles (P2-Mechanik
   unverändert). Kein Manifest → Legacy-Profil exakt wie bisher
   (bestehender Golden bleibt wörtlich grün).
3. workspace init vervollständigen auf §5.2: state/status.md-Seed
   (minimaler Live-Block), state/handoff/-Struktur; erzeugtes Workspace
   MUSS mit load_workspace + NAMESPACE_DEFAULTS konsistent sein (Test:
   init --execute im Fixture, dann liefern ALLE Resolver-Methoden
   existierende .agentic/-Pfade).
TESTS: manifest_defaults_resolve_into_namespace (jede Methode),
explicit_override_beats_namespace_default, legacy_golden_unchanged,
init_workspace_roundtrip_with_namespace_resolvers.
AKZEPTANZ: Manifest-Workspaces lösen vollständig nach .agentic/ auf;
manifest-lose byte-identisch; init erzeugt §5.2 komplett; direction:
p4-namespace-completion bleibt bis P4b offen. Gates PASS.

════════════════════════════════════════════════════════════════
P4b — Literal-Restmigration (Report-getrieben)
════════════════════════════════════════════════════════════════
Branch: codex/p4b-resolver-sweep
Label: p4b-resolver-sweep
ZUERST LESEN: aktuellster audit-path-literals-Report (Autorität für
Modul-Reihenfolge, absteigend); workspace.py-API; die drei P1-Migrationen
als Muster (Sicherungstest → mechanische Ersetzung → Literale=0).
AUFGABE: Alle verbleibenden src-Module mit docs/- oder tmp/-Literalen auf
Workspace-Resolver umstellen — Ziel: audit-path-literals meldet in src/
AUSSCHLIESSLICH workspace.py (deklarierte Single-Source). Vorgehen in
thematischen Commits nach Report-Reihenfolge; je Modul mit
Artefakt-/Ausgabe-relevanz zuerst ein Snapshot-/Golden-Test (P1b-Muster);
fehlende Resolver-Methoden zentral ergänzen (nie Literal im Zielmodul).
Kritische Einzelfälle ausdrücklich enthalten: wrapper_live_status
(WRAPPER_STATUS_RELATIVE_PATH), gui_panel_state, gui_activity_log-Export,
doc_registry-/rule_registry-Kernmodule, standard_gates-Beteiligte.
Templates/Generator-Ausgaben (init/scaffold-INHALTE) sind DATEN, keine
Kit-Pfade → von der Migration ausgenommen und im Audit ggf. als
deklarierte Ausnahmeliste geführt (Report-Feld, im PR begründet).
NICHT-ZIELE: keine Verhaltensänderung; keine GUI-Umbauten; kein Anfassen
der Generator-Template-Texte.
AKZEPTANZ: frischer Report als Evidence committed+registriert: src-Literale
nur noch workspace.py (+ deklarierte Template-Ausnahmen); voller
Testbestand grün; direction: p4-namespace-completion → done. Gates PASS.

════════════════════════════════════════════════════════════════
P5a — Kit-Self-Hosting: Manifest only
════════════════════════════════════════════════════════════════
Branch: codex/p5a-selfhost-manifest
Label: p5a-selfhost-manifest
ZUERST LESEN: §10-P5a; workspace.py (P2-Overrides, P4a-Defaults);
Legacy-Golden-Test.
AUFGABE: Das Kit-Repo erhält .agentic/config.yaml — schema 1,
project{name: agentic-project-kit, type: python}, profile: python-default,
und paths: mit EXPLIZITEN Legacy-Werten für JEDES Feld, dessen
Namespace-Default vom heutigen Kit-Pfad abweicht (status_path: docs/
STATUS.md, doc_registry_path: docs/DOCUMENTATION_REGISTRY.yaml, handoff…,
tmp: tmp, …). Ergebnis: load_workspace liefert im Kit-Repo trotz Manifest
EXAKT die bisherigen Pfade.
TESTS: kit_repo_manifest_yields_legacy_paths (Golden-Vergleich Methode für
Methode gegen die bisherige Legacy-Erwartung); Suite komplett grün;
erzeugte Artefakte (mindestens die bestehenden Snapshot-Tests) unverändert.
AKZEPTANZ: Manifest committed; Verhalten byte-identisch belegt; das
Manifest selbst via doc-registry register erfasst (falls Schema das
vorsieht; sonst im PR begründen); direction: p5a → done. Gates PASS.

════════════════════════════════════════════════════════════════
P5b — Enforce-Check auf aktive Klassen
════════════════════════════════════════════════════════════════
Branch: codex/p5b-resolver-evidence
Label: p5b-resolver-evidence
ZUERST LESEN: Audit-Implementierung, P4b-Evidence, ID2-Identity-
Klassifikation, standard_gates_audit_suite.
AUFGABE: Den Enforce-Modus auf aktive Klassen begrenzen. FAIL entsteht,
wenn aktive Pfad-Literale außerhalb workspace.py und deklarierter
Ausnahmen > 0 sind oder aktive Identity-Literale außerhalb deklarierter
Ausnahmen > 0 sind. Nicht auf Gesamtliterale prüfen. False Positives und
reference_or_message-Fälle bleiben sichtbar, blockieren aber nicht.
HEURISTIK-STICHPROBE: Mindestens drei reference_or_message-Fälle manuell
prüfen und dokumentieren: wirklich nur Meldungstext, kein aktiver
Pfadzugriff, keine Verhaltenssteuerung.
SUITE-AUFNAHME: Erst wenn der Enforce-Lauf auf aktuellem main sauber ist;
main darf nie absichtlich rot werden.
EVIDENCE: Frische P5b-Evidence für path, identity und
Klassifikationsstichprobe erzeugen und registrieren.
TESTS: aktives Pfadliteral → FAIL; Referenzliteral → PASS; aktives
Identity-Literal → FAIL; deklarierte Identity-Ausnahme → PASS; sauberer
Baum → PASS.
AKZEPTANZ: Enforce in Suite aktiv und grün; Evidence registriert;
Stichprobe dokumentiert; direction: p5b-resolver-aliases → done. Gates PASS.

════════════════════════════════════════════════════════════════
P5d — Legacy-Profil-Deprecation dokumentieren
════════════════════════════════════════════════════════════════
Branch: codex/p5d-legacy-deprecation-note
Label: p5d-legacy-deprecation-note
AUFGABE (reine Doku + eine Warnzeile): (1) Im Architekturdokument §8/§9
den Status präzisieren: implicit legacy profile ist ab jetzt DEPRECATED,
Entfernung in 2.0.0 (bereits so vorgesehen — jetzt als geltende
Ankündigung markieren, Datum/PR). (2) CHANGELOG-Eintrag unter Unreleased.
(3) load_workspace gibt im Legacy-Fall (kein Manifest) EINMAL pro Lauf
einen dezenten Hinweis auf stderr/Log: "implicit legacy profile is
deprecated; run `agentic-kit workspace init` (removal in 2.0.0)" —
unterdrückbar via --quiet/ENV, damit Skripte nicht brechen; Kit-Repo
selbst ist nach P5a manifest-tragend und sieht ihn nicht. Test für
Hinweis + Unterdrückung. (4) direction: p5d → done; v2-0-Item verlinkt.
AKZEPTANZ: Doku+Changelog+Warnpfad getestet; keine Suite-Störung. Gates PASS.

════════════════════════════════════════════════════════════════
P5c — Physische Migration: NUR PLAN (Exec maintainer-gated)
════════════════════════════════════════════════════════════════
Branch: codex/p5c-physical-migration-plan
Label: p5c-physical-migration-plan
GRUND FÜR DAS GATE: P5c bewegt öffentliche Doku-Fläche (docs/STATUS.md,
Handoff-Baum) — irreversibel für externe Links. Das Dokument sagt: move
last, if at all; Projektion statt Zwang.
AUFGABE: Einen ENTSCHEIDUNGSREIFEN Plan als Dokument
docs/architecture/P5C_PHYSICAL_MIGRATION_PLAN.md erzeugen (+registrieren):
je Kandidat (registries, rules, state/status, handoff, tmp-Reste) —
Ist-Pfad, Zielpfad, alle Referenzen (Referenzscan-Ergebnis), Vorschlag
move / projection / stay, Risiko, Rückweg. Für docs/STATUS.md konkret das
Projektionskonzept ausarbeiten (Quelle .agentic/state/status.md →
generierte docs/STATUS.md, Generator-Kommando-Skizze, Drift-Gate-Idee).
KEINE Datei wird in diesem Slice bewegt.
DANACH: Exec ist HARTER STOPPGRUND — nicht beginnen. Serie fährt mit P6
fort; P5c-Exec nur nach ausdrücklicher Maintainer-Freigabe des Plans.
AKZEPTANZ: Plan vollständig, referenzscan-belegt, registriert;
direction: p5c-physical-migration → status blocked mit Verweis
"awaiting maintainer decision (plan: <pfad>)". Gates PASS.

════════════════════════════════════════════════════════════════
P6a — GUI-Projektwahl
════════════════════════════════════════════════════════════════
Branch: codex/p6a-gui-project-selection
Label: p6a-gui-project-selection
ZUERST LESEN: gui_cockpit.py (main()/CockpitGui-Init), die
Subprocess-Brücke (gui_cockpit_common/actions: WIE wird agentic-kit
aufgerufen — cwd?), gui_cockpit_header (Titel/Statuszeile),
gui_task_editor (Initial-Prompt-Quelle).
AUFGABE:
1. project_root-State in CockpitGui (Default: cwd). ALLE
   Subprocess-Aufrufe der Brücke laufen mit cwd=project_root (EIN
   zentraler Hebel in der Brücke — nicht 50 Einzelstellen; wenn die
   Brücke bereits zentral ist, dort; sonst zuerst zentralisieren als
   Mini-Refactor mit Smoke-Test).
2. CLI: agentic-kit-gui --root PATH (Argument an main()).
3. GUI: Button/Menüpunkt "Open project…" (filedialog.askdirectory) →
   Validierung: Verzeichnis existiert, ist git-Repo (sonst klare Meldung);
   Manifest-Status ermitteln (workspace adopt-Logik read-only nutzen:
   initialized / ready-for-init / foreign) und in der Statuszeile
   anzeigen; bei foreign: Hinweis, kein Auto-Init.
4. Titel/Status zeigen Projektname (Verzeichnis) + Branch des
   project_root. Nach Wechsel: View-Model-Refresh gegen neues Root.
5. Initial-Prompt-Button: nutzt .agentic/INITIAL_LLM_PROMPT.md des Ziels,
   falls vorhanden; sonst bisheriger Generator mit root-Parameter.
NICHT-ZIELE: kein Multi-Fenster, kein Projekt-Verlauf, keine
Auto-Init-Magie beim Öffnen.
TESTS: bridge_uses_project_root_cwd (Introspektion), open_project_
validates_git_and_updates_state, title_shows_project_and_branch,
initial_prompt_prefers_target_file; GUI-Smoke basic+advanced headless
mit gesetztem --root.
AKZEPTANZ: Cockpit steuerbar auf beliebiges Repo via --root und "Open
project…"; alle Aktionen wirken nachweislich im gewählten Root; direction:
p6-Teilitem entsprechend fortschreiben. Gates PASS.

════════════════════════════════════════════════════════════════
P6b — Operating-Layer-Quickstart + CI-Template-Test
════════════════════════════════════════════════════════════════
Branch: codex/p6b-operating-layer-docs-ci
Label: p6b-operating-layer-docs-ci
AUFGABE:
1. README: neuer Abschnitt "Govern an existing repository (operating
   layer)" — der Fremd-Repo-Quickstart: pip install → workspace adopt →
   workspace init --execute → (optional --inject-ci) → agentic-kit-gui
   --root … ; Privacy-Boundary-Hinweis; Abgrenzung zum Generator-Quickstart
   (agentic-kit init) in EINEM Satz gemäß §2.
2. CI-Template-Härtung: Test, der das erzeugte
   .agentic/ci/agentic-gate.yaml aus init parsed (yaml.safe_load) und
   prüft: referenziertes Kommando existiert im CLI-Inventar; Header/Struktur
   stabil (Golden). Analog pre-commit-Snippet.
3. docs-audit/doc-currency für die README-Änderung sauber.
AKZEPTANZ: Quickstart vorhanden und konsistent zu §2/§7; Template-Tests
grün; direction: p6-gui-project-selection-and-ci-recipe → done (sofern
P6a gemergt). Gates PASS.

════════════════════════════════════════════════════════════════
NACH P6b — ABSCHLUSS DER SERIE
════════════════════════════════════════════════════════════════
1. Frischen Evidence-Stand (path-literals, strict-scope, branch-hygiene)
   im PR-Text des letzten Slices zusammenfassen.
2. STOPP. Offen bleiben ausschließlich maintainer-gated: P5c-Exec (nach
   Plan-Freigabe), v1.0-Kriterium (b) — erste externe Adoption
   (Comm-SCI-Control-private, Maintainer-Akt mit workspace adopt/init),
   sowie 2.0-Linie. Nichts davon eigenmächtig beginnen. Abschluss melden.

════════════════════════════════════════════════════════════════════════════
ANHANG D — AUFTRAG L (Doc-Lifecycle: L0–L5)
════════════════════════════════════════════════════════════════════════════

Repo: vfi64/agentic-project-kit

HINWEIS: Beruht auf verifiziertem main-Stand nach K2c (docs-Taxonomie,
Status-Header-Konvention). Vor jedem Slice Namens-Gegencheck gegen main und
offene Branches — insbesondere: audit-doc-currency, documentation_currency*,
post_release_archive_check, communication_artifact_gc, audit-drift. Es gilt:
ERWEITERN STATT DOPPELN, wo Bestand die Aufgabe schon teilweise trägt.

MASSGEBLICHES DOKUMENT
docs/architecture/KIT_AS_OS_ARCHITECTURE.md (§4 Regeln, §5 Workspace, §12
Evidence) und docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md
(Vier-Klassen-Taxonomie + Status-Header-Konvention aus K2c). Widerspruch
Prompt↔Dokumente → STOPP und Diagnose.

SECHS SLICES, REIHENFOLGE STRIKT:
L0  Vorbedingungen + Direction-Items
L1  Lifecycle-Metadaten + Konsistenz-Gate (report-only)
L2  Obsoleszenz-Signale (review_after-Parser, Direction-Kopplung, Orphans)
L3  Geführter Sweep (archive | confirm-current | defer) + Bootstrap + GUI
L4  Gestufte Durchsetzung (Suite-WARN, strict, Release-Haken)
L5  Operating-Layer (Manifest-hygiene, init-Seed, adopt-Baseline)

Jeder Slice eigener Branch, eigener PR. Nach grünem Closeout automatisch
weiter. STOPP nur bei: Gates FAIL nach Reparaturversuch, protected-diff
BLOCK, Architektur-Widerspruch, Nutzerentscheidung nötig.

GLOBALE ARBEITSWEISE
- Zuerst je Slice die genannten Dateien lesen. stdlib + vorhandene deps.
  Englisch. Tests in tmp_path-Fixtures; das Kit-Repo wird von Tests nie
  mutiert.
- DETERMINISMUS-REGEL (gilt überall): Kein Suite-FAIL darf von der
  Systemzeit abhängen. Zeitbasierte Befunde sind maximal WARN. Für
  Testbarkeit nimmt jede zeitabhängige Funktion einen injizierbaren
  now-Parameter (Default: date.today()).
- Direction-Pflege je Slice: zugehöriges plans-Item auf done
  (completed_by_pr) + meta.updated_after_pr; direction validate PASS.
- Vor Commit: ruff, fokussierte Tests, docs-audit, audit-doc-currency,
  standard-gates-audit-suite, transfer protected-diff-plan --label <label>.
- Nach Commit: rules acknowledge. PR via pr-create-complete
  --post-merge-complete.

════════════════════════════════════════════════════════════════
L0 — Vorbedingungen + Direction-Items
════════════════════════════════════════════════════════════════
Branch: codex/l0-lifecycle-preconditions
Label: l0-lifecycle-preconditions
STOPP-CHECK: DOCUMENTATION_INFORMATION_ARCHITECTURE.md enthält die
Vier-Klassen-Taxonomie und die Status-Header-Konvention (K2c gemergt)?
Wenn NEIN: STOPP — "K2c must merge first".
AUFGABE: In PROJECT_DIRECTION.yaml fünf plans-Items anlegen (Feldstil wie
Bestand): doc-lifecycle-metadata [active], doc-lifecycle-signals [planned,
depends_on: doc-lifecycle-metadata], doc-lifecycle-sweep [planned,
depends_on: doc-lifecycle-signals], doc-lifecycle-strict-adoption
[planned, depends_on: doc-lifecycle-sweep],
hygiene-manifest-adopt-baseline [planned, depends_on:
doc-lifecycle-strict-adoption]. rationale je 1 Satz; source_files:
[docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md].
AKZEPTANZ: direction validate PASS; Gates PASS; PR wie üblich.

════════════════════════════════════════════════════════════════
L1 — Lifecycle-Metadaten + Konsistenz-Gate (report-only)
════════════════════════════════════════════════════════════════
Branch: codex/l1-doc-lifecycle-metadata
Label: l1-doc-lifecycle-metadata

ZUERST LESEN (Pflicht, Ergebnis in PR dokumentieren)
- Das Modul hinter audit-doc-currency (per grep finden): WAS prüft es
  heute exakt (Findings, Felder, Exit-Verhalten)?
- docs/DOCUMENTATION_REGISTRY.yaml: exakte Eintragsfelder + etwaige
  Schema-/Versions-Kopfzeile; Registrierungs-/Validierungscode
  (doc_registry-Kern) für die Felderweiterung.
- DOCUMENTATION_INFORMATION_ARCHITECTURE.md: der genaue Wortlaut der
  Status-Header-Konvention (Status / Status-date / Superseded-by).
WEICHE: Deckt audit-doc-currency Teile von unten ab → ERWEITERN (gleiches
Kommando, neue Findings). Sonst neues Kommando audit-doc-lifecycle.
Entscheidung im PR begründen.

AUFGABE
1. Registry-Felderweiterung, strikt OPTIONAL und abwärtskompatibel:
   review_after (String, Grammatik siehe L2 — in L1 nur gespeichert und
   syntaktisch grob geprüft), deferred_until (ISO-Datum, optional).
   Bestehende Einträge bleiben unangetastet gültig.
2. Konsistenz-Prüfungen (Findings, report-only, Exit 0 in L1):
   a) HEADER_MISSING: Datei in registry-pflichtiger Klasse ohne
      Status-/Status-date-Header (archive/, reports/, examples/ exempt).
   b) HEADER_REGISTRY_MISMATCH: Header-Status widerspricht Registry-Status
      (z.B. Header superseded, Registry active).
   c) SUPERSEDED_TARGET_MISSING: Superseded-by verweist auf nicht
      existierenden Pfad.
   d) STALE_BY_BUDGET (WARN-KLASSE, per Determinismus-Regel nie FAIL-fähig):
      Status-date älter als Klassenbudget. Budgets als benannte Konstanten:
      governance=180, reference=365, workflow=270 Tage; archive/reports/
      examples exempt; planning exempt (läuft über direction-Mechanik).
3. --json; Ausgabe gruppiert nach Finding-Typ mit Datei, Klasse, Alter.

TESTS: je Finding-Typ Positiv+Negativ (Fixture-Baum mit Mini-Registry);
Budget-Grenzfall (genau am Budget = ok, +1 Tag = Finding) mit injiziertem
now; Registry ohne neue Felder bleibt voll gültig (Abwärtskompatibilität).
AKZEPTANZ: Kommando läuft auf dem echten Repo mit Exit 0 und plausibler
Findings-Liste (im PR als Auszug); keine Suite-Änderung in L1; direction:
doc-lifecycle-metadata → done. Gates PASS.

════════════════════════════════════════════════════════════════
L2 — Obsoleszenz-Signale
════════════════════════════════════════════════════════════════
Branch: codex/l2-doc-lifecycle-signals
Label: l2-doc-lifecycle-signals

ZUERST LESEN: Versionsvergleichslogik im Bestand (release_state_validation
o.ä. — wiederverwenden, nicht neu bauen); direction audit-drift
(Erweiterungsort für die Direction-Kopplung); K2b/K2c-Referenzscan-Muster.

AUFGABE
1. review_after-Parser, exakte Grammatik (alles andere = Parse-Finding):
     date:YYYY-MM-DD
     release:<op><version>   op ∈ {<,<=,==,>=,>} ; Vergleich gegen die
                             aktuelle Version aus pyproject.toml über die
                             BESTEHENDE Versionslogik
     direction:<item-id>     fällig, sobald das Item done|discarded ist
   Neue Findings im L1-Kommando: REVIEW_DUE_RELEASE und
   REVIEW_DUE_DIRECTION (beide ereignisbasiert → FAIL-fähig ab L4),
   REVIEW_DUE_DATE (zeitbasiert → dauerhaft WARN-Klasse),
   REVIEW_AFTER_INVALID (Syntaxfehler).
2. Direction-Kopplung als audit-drift-Erweiterung: Datei ist source_file
   eines done/discarded-Items UND trägt Header-Status active →
   SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE.
3. Orphan-Erkennung: neues report-only audit-doc-orphans (Exit 0):
   registrierte Datei ohne eingehenden Verweis repo-weit (md/py/yaml,
   Scan-Mechanik analog K2-Referenzscan). EXEMPT per Konstruktion:
   archive/, reports/, examples/, alle required_files, die vier
   Wurzel-Kanonischen, PROJECT_DIRECTION-Paar. Ausgabe = Kandidatenliste
   mit letztem Commit-Datum je Datei.
4. Einmal-Helfer --suggest-review-after (report-only): scannt Freitext auf
   Versions-Zielmuster ("Target v…", "for v0.…") und druckt VORSCHLÄGE für
   review_after-Einträge. Kein Dauer-Signal, keine Registry-Mutation.

TESTS: Parser-Matrix (gültig/ungültig/Grenzen), release-Fälligkeit mit
gemockter current version, direction-Kopplung im Fixture, Orphan-Positiv/
-Negativ inkl. jeder Exempt-Kategorie.
AKZEPTANZ: Signale laufen report-only auf dem echten Repo (Auszug im PR);
direction: doc-lifecycle-signals → done. Gates PASS.

════════════════════════════════════════════════════════════════
L3 — Geführter Sweep + Bootstrap + GUI-Badge
════════════════════════════════════════════════════════════════
Branch: codex/l3-doc-lifecycle-sweep
Label: l3-doc-lifecycle-sweep

ZUERST LESEN: workspace.py (Resolver — ALLE Pfade des Sweeps laufen
darüber, keine Literale!); die K2b-Move-Mechanik als Verhaltensvorbild;
GUI-Brücke (run_kit_command) + gui_panel_state für das Badge; die
Direction-YAML-Schreiblogik (falls vorhanden — sonst gezielte, getestete
YAML-Edits).

AUFGABE
1. Kommando docs lifecycle sweep [--dry-run (DEFAULT) | --execute
   --only <finding-id,…>] [--json], Safety-Klasse BOUNDED:
   Nimmt L1/L2-Findings und erzeugt je Kandidat einen Aktionsplan mit
   genau EINER vorgeschlagenen Aktion:
   - archive: git mv nach docs/archive/<name>.md + Header (Status:
     superseded, Superseded-by gemäß Finding-Kontext, Status-date=today) +
     Registry-Eintrag (path, class=archive-Klasse) + source_files-
     Nachführung in PROJECT_DIRECTION.yaml (alter→neuer Pfad).
   - confirm-current: Status-date=today im Header; optional neues
     review_after per Flag-Vorgabe.
   - defer --until YYYY-MM-DD: deferred_until im Registry-Eintrag;
     Findings dieser Datei werden bis dahin unterdrückt (sichtbar als
     DEFERRED-Zeile, nie still).
   Dry-run druckt den vollständigen Plan (Diff-artig, je Datei); execute
   führt NUR die per --only benannten Findings aus. KEIN Löschpfad.
2. docs lifecycle propose-delete (report-only, Exit 0): Dateien in
   archive/, älter als 365 Tage seit Archivierung (Status-date), ohne
   eingehende Verweise — reine Liste für einen manuellen Maintainer-Akt.
3. docs lifecycle bootstrap [--dry-run|--execute] (BOUNDED): stempelt
   Dateien ohne Header mit "Status: unreviewed" +
   "Status-date: <letztes git-Commit-Datum der Datei>" (git log -1
   --format=%cs -- <pfad>). Keine inhaltliche Behauptung; exempt-Klassen
   wie L1.
4. GUI: Hygiene-Badge in der Statuszeile ("lifecycle: N warn / M due"),
   gespeist aus dem --json des Audits über die bestehende Brücke
   (READ_ONLY); Button "Sweep (dry-run)" zeigt den Plan im bestehenden
   Ausgabefenster. Execute NUR über die vorhandene Confirm-Mechanik mit
   expliziter --only-Auswahl. GUI bleibt dünn.

TESTS: Sweep-Plan-Golden auf Fixture; execute-archive führt ALLE vier
Teilschritte atomar-konsistent aus (Datei, Header, Registry, Direction —
Fixture-Roundtrip); confirm/defer je Roundtrip; bootstrap dry vs. execute;
propose-delete-Exempts; GUI-Smoke mit Badge.
AKZEPTANZ: Ein kompletter Fixture-Zyklus Finding→Sweep→Grün ist
testbewiesen; auf dem echten Repo nur dry-run im PR dokumentiert;
direction: doc-lifecycle-sweep → done. Gates PASS.

════════════════════════════════════════════════════════════════
L4 — Gestufte Durchsetzung
════════════════════════════════════════════════════════════════
Branch: codex/l4-lifecycle-strict-adoption
Label: l4-lifecycle-strict-adoption

ZUERST LESEN: standard_gates_audit_suite (Step-Muster), das
strict-scope-Adoptionsmuster (K1), release-ready-Implementierung
(human_workflows) und post_release_archive_check (Verwandtschaft prüfen —
erweitern statt doppeln, Befund im PR).

AUFGABE
1. Suite-Aufnahme des Lifecycle-Audits als WARN-Step (Suite bleibt bei
   Findings grün, druckt Zusammenfassung).
2. --strict-Modus: FAIL bei HEADER_REGISTRY_MISMATCH,
   SUPERSEDED_TARGET_MISSING, REVIEW_DUE_RELEASE, REVIEW_DUE_DIRECTION,
   SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE. NIEMALS FAIL bei STALE_BY_BUDGET /
   REVIEW_DUE_DATE (Determinismus-Regel — als Test festgeschrieben:
   test_time_based_findings_never_fail_strict).
3. Release-Haken: release ready erhält einen Step, der REVIEW_DUE_RELEASE-
   Findings mit Zielversion <= der angefragten Release-Version als BLOCK
   meldet (deterministisch: hängt an der Version). Meldung nennt den
   Sweep als Ausweg.
4. Aktivierung strict im Kit-Repo NUR, wenn der aktuelle Bestand nach
   einem dokumentierten Sweep-Durchgang clean ist — sonst strict-Schalter
   bauen, Suite auf WARN belassen und die Restliste als direction-plans-
   Item "lifecycle-backlog-clearance" [active] hinterlegen (kein rotes
   main erzeugen!).

AKZEPTANZ: WARN-Step aktiv; strict-Semantik testfest inkl. Zeit-Ausschluss;
Release-Haken testfest; main bleibt grün; direction:
doc-lifecycle-strict-adoption → done. Gates PASS.

════════════════════════════════════════════════════════════════
L5 — Operating-Layer: Manifest, init-Seed, adopt-Baseline
════════════════════════════════════════════════════════════════
Branch: codex/l5-hygiene-operating-layer
Label: l5-hygiene-operating-layer

ZUERST LESEN: workspace.py Manifest-Parsing (P2: unknown-top-level-fail —
hier wird die Key-Whitelist erweitert), workspace_init.py,
workspace_adopt.py, .agentic/config.yaml des Kit-Repos (P5a).

AUFGABE
1. Manifest-Schema: neuer OPTIONALER Top-Level-Block
     hygiene: { doc_lifecycle: off|warn|strict (default warn),
                review_budgets: {governance:int, reference:int,
                workflow:int} }
   Kein kit_schema_version-Bump (additiv-optional); dokumentierter Effekt:
   ältere Kits lehnen Manifeste mit hygiene laut ab (fail loud, gewollt) —
   CHANGELOG-Hinweis "hygiene requires kit >= <version>". Audit/Sweep
   lesen Budgets/Modus aus dem Workspace (Kit-Repo: Defaults, solange
   sein Manifest keinen Block trägt).
2. workspace init: seedet die Status-Header-Konvention als Kurzdatei
   .agentic/DOC_LIFECYCLE.md (Konvention + Budgets des Profils) und legt
   docs/archive/ mit README-Stub an, falls fehlend. hygiene: warn im
   erzeugten Manifest.
3. workspace adopt: Report-Erweiterung "documentation age baseline" — je
   docs-Unterverzeichnis: Dateizahl, Anteil mit Status-Header, Median +
   Maximum des letzten Commit-Datums; Hinweis auf bootstrap als ersten
   Schritt. Read-only bleibt read-only.
4. Profile: python-default und generic erhalten identische
   hygiene-Defaults (warn + Standardbudgets); Abweichungen sind
   Manifest-Sache.

TESTS: Manifest mit/ohne hygiene (Parsing, Defaults, invalid-Werte laut);
init-Seed-Roundtrip; adopt-Baseline auf drei Fixtures (leer / mit Headern /
Altbestand ohne Header); Kit-Repo-Verhalten unverändert (P5a-Golden grün).
AKZEPTANZ: Fremd-Repo-Fixture durchläuft init → bootstrap → audit → sweep
im Test; adopt zeigt die Baseline; direction:
hygiene-manifest-adopt-baseline → done. Gates PASS.

════════════════════════════════════════════════════════════════
NACH L5 — ABSCHLUSS
════════════════════════════════════════════════════════════════
Frisches Lifecycle-Audit als Evidence unter docs/architecture/evidence/
(+ Registrierung). DANN STOPP. Maintainer-gated bleiben: strict-Umschaltung
im Kit-Repo (nach Backlog-Clearance), propose-delete-Ausführung, P5c-Exec,
Comm-SCI-Adoption. Nichts davon eigenmächtig. Abschluss melden.

════════════════════════════════════════════════════════════════════════════
ENDE DER ANHÄNGE A–D
════════════════════════════════════════════════════════════════════════════
