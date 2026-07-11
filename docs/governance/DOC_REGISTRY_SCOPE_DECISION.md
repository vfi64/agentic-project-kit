# Documentation Registry Scope Decision Template

Status: decided
Decision status: decided 2026-07-08
Review policy: required
Document class: governance/system
Status-date: 2026-07-08
Moved-from: docs/planning/DOC_REGISTRY_SCOPE_DECISION.md
Decision source: docs/DOC_REGISTRY_SCOPE.yaml

Generated from the current repository filesystem and `docs/DOCUMENTATION_REGISTRY.yaml`.
Counts exclude generated report prefixes that are already outside the registry candidate scan.
Decision outcome: active registry scope is declared in `docs/DOC_REGISTRY_SCOPE.yaml`; this document is retained as governance decision evidence. Historical template note retained for coverage compatibility: No scope recommendation is encoded here; maintainers filled the active scope in `docs/DOC_REGISTRY_SCOPE.yaml` after review.

| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |
|---|---:|---:|---:|---|
| docs/ | 3 | 3 | 0 |  |
| docs/architecture/ | 9 | 9 | 0 |  |
| docs/archive/ | 17 | 17 | 0 |  |
| docs/examples/ | 1 | 0 | 1 |  |
| docs/governance/ | 27 | 27 | 0 |  |
| docs/handoff/ | 4 | 4 | 0 |  |
| docs/planning/ | 2 | 2 | 0 |  |
| docs/reference/ | 7 | 7 | 0 |  |
| docs/releases/ | 1 | 1 | 0 |  |
| docs/reports/ | 65 | 0 | 65 |  |
| docs/workflow/ | 11 | 11 | 0 |  |

Notes:
- `required_files` means each declared file must have a registry entry.
- `required_paths` means every Markdown file in that declared path must be registered.
- `exempt_paths` means a declared path is intentionally registration-free and must carry a reason.
- This template is evidence for a maintainer decision; it does not modify scope by itself.
