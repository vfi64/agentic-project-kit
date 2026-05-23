# Documentation Registry Contract

Status-date: 2026-05-23
Status: experimental governance schema baseline
Scope: documentation and artifact classification for agentic-project-kit

## Purpose

The documentation registry introduces a small, additive governance layer for classifying project documents and artifacts before any broad documentation migration.

The first registry slice is deliberately narrow. It defines document classes, class-level rule fields, a small initial document list, and a deterministic guard. It does not replace `docs/DOCUMENTATION_COVERAGE.yaml`, `agentic-kit check-docs`, `agentic-kit docs-audit`, `agentic-kit doc-mesh-audit`, lifecycle audit, handoff checks, release checks, or artifact GC.

## Document classes

The first schema supports these classes:

- governance/system
- planning
- architecture
- release
- operational/automation
- user-facing description
- evidence/log
- generated artifact
- temporary artifact
- historical archive

These classes are registry vocabulary, not a migration command. A later migration may classify more files only in small reversible slices.

## Required class rule fields

Every class rule must define:

- ownership
- freshness
- language policy
- redundancy boundary
- machine readability
- retention / GC behavior
- update triggers
- portability/local-path scanning
- gate coverage

The exact machine-readable field names are stored in `docs/DOCUMENTATION_REGISTRY.yaml` and validated by the registry guard.

## First-slice guard

The first guard validates only deterministic structure:

- the registry file exists;
- the registry version is `1`;
- all required classes have class rules;
- class rules contain all required fields;
- registered document entries have a path, class, and owner;
- registered paths are unique;
- registered paths exist in the repository;
- registered classes are known.

The guard intentionally does not claim semantic documentation quality. It cannot prove that a document is well-written, complete, or architecturally optimal.

## Integration points

The first guard is wired into `agentic-kit check-docs`. Since `agentic-kit docs-audit` uses `check-docs` for its correctness and completeness dimensions, the registry schema also participates in the umbrella documentation-system audit without a separate migration.

Future slices may integrate the registry with doc-mesh, lifecycle audit, handoff checks, release checks, and artifact GC. Those integrations must remain additive, modular, reversible, and test-backed.

## Migration boundary

No broad migration is allowed in this first slice. The registry starts with a small set of canonical documents and evidence logs so that the schema and guard can be reviewed before the repository is classified broadly.

A later migration must preserve existing documentation quality, current-state boundaries, release history, evidence logs, and compatibility anchors. It must not delete or move documents merely to satisfy a taxonomy.

## Rule hardening

The registry is hardened through:

- `docs/DOCUMENTATION_REGISTRY.yaml` as the machine-readable source;
- `src/agentic_project_kit/documentation_registry.py` as the validation core;
- `agentic-kit check-docs` integration;
- targeted tests for allowed classes, required fields, duplicate path detection, missing path detection, and docs-audit participation;
- documentation coverage anchors for the registry contract.
