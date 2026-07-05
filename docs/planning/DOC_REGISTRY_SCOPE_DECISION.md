# Documentation Registry Scope Decision Template

Status: active
Decision status: undecided
Review policy: required

Generated from the current repository filesystem and `docs/DOCUMENTATION_REGISTRY.yaml`.
Counts exclude generated report prefixes that are already outside the registry candidate scan.
No scope recommendation is encoded here; maintainers fill the proposed column after review.

| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |
|---|---:|---:|---:|---|
| docs/ | 4 | 3 | 1 |  |
| docs/agent_rules/ | 2 | 2 | 0 |  |
| docs/architecture/ | 9 | 9 | 0 |  |
| docs/archive/ | 3 | 3 | 0 |  |
| docs/examples/ | 1 | 0 | 1 |  |
| docs/governance/ | 15 | 15 | 0 |  |
| docs/gui/ | 1 | 1 | 0 |  |
| docs/handoff/ | 6 | 6 | 0 |  |
| docs/ideas/ | 5 | 0 | 5 |  |
| docs/patterns/ | 2 | 2 | 0 |  |
| docs/planning/ | 28 | 28 | 0 |  |
| docs/reference/ | 2 | 2 | 0 |  |
| docs/releases/ | 1 | 1 | 0 |  |
| docs/reports/ | 64 | 0 | 64 |  |
| docs/testing/ | 1 | 1 | 0 |  |
| docs/workflow/ | 19 | 19 | 0 |  |

Notes:
- `required_files` means each declared file must have a registry entry.
- `required_paths` means every Markdown file in that declared path must be registered.
- `exempt_paths` means a declared path is intentionally registration-free and must carry a reason.
- This template is evidence for a maintainer decision; it does not modify scope by itself.
