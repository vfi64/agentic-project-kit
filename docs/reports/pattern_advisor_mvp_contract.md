# Pattern Advisor MVP contract

## Goal

Define a small, non-binding Pattern Advisor MVP contract before any implementation work. The MVP should clarify scope, boundaries, command surface, evidence requirements, and non-goals.

## Proposed MVP shape

- Start with read-only pattern catalog support.
- Keep Pattern Advisor advisory-only.
- Do not connect Pattern Advisor output to workflow state, gates, doctor, cleanup, release, or repair behavior.
- Keep wrapper-project lessons as evidence sources, not wrapper-specific behavior.
- Prefer stable IDs, small metadata files, and human-readable Markdown explanations.

## Candidate command-level contract

- agentic-kit patterns list: list known patterns and anti-patterns from a local catalog.
- agentic-kit patterns show <id>: show one catalog entry by stable ID.

## Deferred commands

- agentic-kit patterns suggest
- agentic-kit patterns capture-candidate
- agentic-kit advise

## Non-goals for the MVP

- No automatic architecture advice.
- No automatic candidate promotion.
- No binding pattern lifecycle.
- No deterministic gate based on pattern classification.
- No remote dependencies.
- No broad catalog.

## Likely future files if implementation is approved

- .agentic/patterns/catalog.yaml
- docs/patterns/<pattern-id>.md
- src/agentic_project_kit/patterns.py
- src/agentic_project_kit/cli_commands/patterns.py
- tests/test_patterns.py

## Required evidence for a later implementation slice

- catalog loader tests
- schema or structure validation tests
- CLI list/show tests
- documentation coverage update if public CLI is added
- check-docs, doctor, doc-mesh-audit, pytest, and ruff

## ADR assessment

An ADR is not needed for this contract-only slice. An ADR should be reconsidered if a public patterns CLI, binding catalog format, lifecycle rules, or workflow-impacting advisory behavior is implemented.
