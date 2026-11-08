# KIT-GF-104: Generator-Typen im Workspace-Recovery-Pfad

Status: Umsetzung und lokale Abnahme ausstehend; Ergebnisse aus Auftrag 212 beachten.

## Reproduktion und Ursache

Ein durch `agentic-kit init --type python-cli` (ebenso python-lib,
governance-wrapper) erzeugtes Projekt bewahrt den Generator-Typ in
`.agentic/project.yaml`. Die unvollständige Betriebsschicht enthält noch
keine `.agentic/config.yaml`. Normales `workspace init` bleibt
`FOREIGN_AGENTIC`; `--recover-partial` scheiterte bisher an der engeren
Workspace-Typmenge.

## Korrektur und Sicherheitsvertrag

Nur der Recovery-Weg verwendet eine explizite Generator-zu-Workspace-Abbildung:
python-cli, python-lib und governance-wrapper werden python; generic bleibt
generic. Unbekannte Typen sind gesperrt. `ALLOWED_PROJECT_TYPES` und die
Generator-Typen bleiben unverändert. Der Projektvertrag wird nicht überschrieben.
Der signierte `approval_subject` enthält Generator- und Workspace-Typ.
Passende Workspace-Typ-Overrides sind erlaubt, widersprechende gesperrt.

## Evidenz

Basis: `78a38d95ba31235ccfaf06cf4f4e8110479fbd99`; Branch: `fix/gf-104-generator-type-recovery`.
Gezielte Regressionstests: `tests/test_workspace_recovery.py`.
Lokales Prüfergebnis, CI, PR-Nummer und Head-SHA sind erst nach Ausführung
und Prüfung der Work-Orders einzutragen. Kein Merge ohne Owner-Freigabe.
