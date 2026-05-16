# Documentation Information Architecture

Status: architecture contract
Review policy: update when documentation directories, planning workflow, roadmap handling, strategy handling, idea lifecycle, or documentation automation changes

## Purpose

This document defines where durable project information belongs. Its purpose is to prevent documentation drift, duplicated planning truth, stale idea notes, and inconsistent roadmap or strategy statements.

The repository must preserve information, but it must not preserve ambiguity. Each durable information type should have one canonical home. Other documents may summarize or reference that information, but they should not become competing sources of truth.

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
- docs/architecture/AGENTIC_CODING_RESEARCH_INPUTS.md: labelled research and planning input linked to architecture
- docs/ideas/*.md: non-binding idea notes unless promoted
- docs/planning/V0.3.8_SCOPE.md: historical planning candidate requiring lifecycle review
- docs/roadmap/V0.3.0_OUTPUT_REPAIR_PLAN.md: historical roadmap or planning candidate requiring lifecycle review
- docs/strategy/V0.4_PROFESSIONAL_SINGLE_USER_STRATEGY.md: current strategy document for professional single-user direction

## Invariants

- One durable information type should have one canonical home.
- Strategy is not a release contract.
- Roadmap is not deep architecture rationale.
- Ideas are not binding decisions.
- Reports are evidence, not policy.
- Handoff is current continuation context, not full history.
- Advisory review must not become hidden automation authority.
- Garbage collection must not delete information before classification.
