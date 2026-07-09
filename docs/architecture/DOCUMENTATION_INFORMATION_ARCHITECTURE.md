# Documentation Information Architecture

Status: architecture contract
Review policy: update when documentation directories, planning workflow, roadmap handling, strategy handling, idea lifecycle, or documentation automation changes

## Purpose

This document defines where durable project information belongs. Its purpose is to prevent documentation drift, duplicated planning truth, stale idea notes, and inconsistent roadmap or strategy statements.

The repository must preserve information, but it must not preserve ambiguity. Each durable information type should have one canonical home. Other documents may summarize or reference that information, but they should not become competing sources of truth.

## K2d documentation taxonomy baseline

K2d uses four operational documentation classes for triage decisions:

1. Architecture and governance: durable rules, contracts, invariants, safety boundaries, and authority limits. Canonical homes are docs/architecture/ and docs/governance/.
2. Reference and user-facing documentation: command references, research inputs, stable examples, user-facing descriptions, and reusable explanatory material. Canonical homes include docs/reference/, docs/examples/, and selected top-level anchors such as README.md.
3. Workflow, release, and operational automation: active process documentation, release records, workflow guards, automation contracts, and code-backed operational documents. Canonical homes include docs/workflow/, docs/releases/, and explicitly justified root exceptions.
4. Evidence, reports, planning, and archive: generated reports, handoff projections, run evidence, project direction, completed or discarded plans, and superseded historical material. Canonical homes include docs/reports/, docs/handoff/, docs/planning/, and docs/archive/.

The taxonomy is intentionally operational rather than literary. A document is classified by the role it plays in repository governance and automation, not by its prose style.

## Root exceptions

The docs/ root should stay small. Root-level documentation is allowed only when a file is a stable public anchor, code-backed control file, or historically entrenched compatibility anchor.

Current justified root exceptions include:

- docs/DOCUMENTATION_REGISTRY.yaml: machine-readable documentation registry.
- docs/DOC_REGISTRY_SCOPE.yaml: machine-readable required/exempt scope declaration.
- docs/DOCUMENTATION_COVERAGE.yaml: code-backed documentation coverage contract and explicit exception to the no-root-sprawl rule.
- docs/TEST_GATES.md: public gate overview.
- docs/STATUS.md: current human status projection.
- docs/WORKFLOW_OUTPUT_CYCLE.md: code-/audit-backed workflow output-cycle contract retained at its legacy path.

New root files require an explicit reason in the registry or coverage contract. Convenience is not enough.

## Status header convention

Active Markdown documents in registry-governed scope should use this compact header before the title when practical:

    Status: active
    Status-date: YYYY-MM-DD
    Superseded-by: n/a

Superseded or archived documents should use Status: superseded or Status: archived and a concrete Superseded-by: target when one exists.

Generated reports, evidence bundles, examples, and legacy compatibility anchors may have specialized metadata, but they must not contradict the registry. A missing or conflicting lifecycle header is a documentation hygiene finding, not a license to infer semantic truth.

## Handoff model

The current handoff model is package-first.

docs/reports/handoff-packages/latest/ contains the authoritative machine-readable handoff package:

- successor_context.yaml
- source_manifest.json
- validation_report.json
- execution_contract.json
- successor_prompt.md

docs/handoff/*.md files are human prompt/bootstrap projections and safety belts. They are useful entry points for a maintainer or successor chat, but they are not more authoritative than the validated package data. If a docs/handoff/*.md projection disagrees with the latest validated package, the package wins and the projection must be regenerated through the supported closeout/chat-switch workflow.

Feature-branch handoff packages must not be treated as final main-state evidence when a gate requires validation against origin/main. Final handoff/status refresh belongs after merge or in a workflow that explicitly supports branch handoff state.

## Directory responsibilities

### docs/architecture

Canonical home for durable architecture contracts, invariants, boundaries, non-goals, system design rules, advisory boundaries, state-machine rules, and automation authority limits.

This directory may contain research inputs only when they are explicitly labelled as research input and linked to a governing architecture contract.

It must not contain short-term release planning or unresolved feature wishlists.

### docs/strategy

Canonical home for long-term direction, milestone intent, strategic risks, and product-level priorities.

Strategy documents are not release contracts. They explain why a direction matters and what risks should be avoided.

### docs/roadmap

Canonical home for versioned development sequence, milestone order, and planned release progression.

Roadmap documents should answer what comes in which order. They should not duplicate deep architecture rationale from docs/architecture or broad strategy rationale from docs/strategy.

### docs/planning

Canonical home for active or near-term slice planning, scoped implementation options, and concrete work preparation.

Planning documents must not remain indefinitely active. When a slice is implemented, rejected, superseded, or archived, the document should be updated or moved according to the lifecycle rules below.

### docs/ideas

Canonical home for non-binding ideas that are not yet accepted architecture, roadmap, or implementation work.

Idea notes must remain advisory unless explicitly promoted through a reviewable change. They must not silently define CLI behavior, workflow-state behavior, gates, or architecture decisions.

### docs/reports

Canonical home for generated or manually captured evidence, audits, workflow reports, and diagnostic summaries.

Reports may support decisions, but they are not themselves the canonical home for new project policy.

### docs/handoff

Canonical home for current continuation context, last safe state, and next safe step.

Handoff documents must stay concise. They should link to strategy, roadmap, planning, architecture, and reports instead of duplicating them.

## Lifecycle states

Documents that represent ideas, plans, or candidates should use an explicit status. Allowed status values are:

- idea-note
- proposed
- active
- accepted
- implemented
- rejected
- superseded
- archived

A document without a clear status should be treated as a documentation hygiene finding.

## Promotion rules

Ideas may inform later work, but they do not become binding merely by existing.

Promotion paths:

- idea to planning: when a concrete slice is being considered
- planning to roadmap: when a slice becomes part of the intended version sequence
- planning or idea to architecture: when a durable rule, boundary, invariant, or authority limit is accepted
- roadmap or strategy to handoff: only as a short current-context reference

Promotion must be explicit, reviewable, and traceable through a normal repository change.

## Advisory alignment

Strategy, roadmap, status, handoff, ideas, and planning documents should be periodically compared for drift.

Such comparison is advisory by default. A tool or LLM may identify inconsistencies, stale documents, missing references, or conflicting next steps, but it must not make hidden architecture decisions or silently mutate workflow state.

Allowed advisory findings include:

- stale planning documents
- idea notes that appear implemented but are not marked implemented
- roadmap items missing from strategy or handoff references
- strategy claims not reflected in roadmap
- duplicated next-step claims across multiple files
- unclear authority level of a document

## Automation boundaries

Documentation automation should be introduced in stages.

Stage 1: read-only inventory and audit.
Stage 2: advisory findings and migration recommendations.
Stage 3: guided migration plans with dry-run output.
Stage 4: garbage-collection candidates with dry-run output.

Destructive documentation automation must require explicit human approval. Garbage collection must default to dry-run and must prefer archiving over deletion until references and audit value are checked.

## Current classification baseline

- docs/architecture/ARCHITECTURE_CONTRACT.md: governing architecture contract
- docs/reference/AGENTIC_CODING_RESEARCH_INPUTS.md: labelled research and planning input linked to architecture
- Idea notes: represented in `docs/planning/PROJECT_DIRECTION.yaml` unless promoted into a dedicated governed document type
- docs/planning/PROJECT_DIRECTION.yaml: canonical project strategy, roadmap, plan, idea, done, and discarded direction source
- superseded historical output-repair roadmap candidate; current direction is `docs/planning/PROJECT_DIRECTION.yaml`
- superseded historical professional single-user strategy candidate; current strategy is `docs/planning/PROJECT_DIRECTION.yaml`

## Invariants

- One durable information type should have one canonical home.
- Strategy is not a release contract.
- Roadmap is not deep architecture rationale.
- Ideas are not binding decisions.
- Reports are evidence, not policy.
- Handoff is current continuation context, not full history.
- Advisory review must not become hidden automation authority.
- Garbage collection must not delete information before classification.
