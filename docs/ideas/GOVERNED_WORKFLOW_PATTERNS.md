# Governed Workflow Patterns

Status: idea note / architecture research track
Decision status: not implemented as a single feature
Rule location: `AGENTS.md` (`Governed Workflow Design Principles`)
Roadmap relation: future hardening of workflow, release, repair, validation, and agent-facing features

## Purpose

This note preserves governed workflow patterns that may be useful for future agentic-project-kit development without making them immediate implementation requirements.

The goal is to avoid repeating failure modes seen in complex AI-assisted projects: implicit state, unclear command semantics, unbounded repair, hidden side effects, fragile parsing of free text, and loss of diagnostic evidence after failures.

Use these patterns only when they reduce drift, improve restartability, preserve evidence, or make behavior easier to test. Do not add machinery merely for architectural symmetry.

## Event-Sourcing Light

Event-Sourcing Light means recording a small, bounded sequence of important workflow events in addition to the current state.

Example events:

```yaml
events:
  - requested
  - started
  - gates_passed
  - evidence_uploaded
  - cleaned_up
```

Potential benefits:

- clearer diagnosis after interrupted workflows;
- less reliance on chat memory;
- better audit trail for workflow transitions;
- easier reconstruction of what happened before a failure.

Risks:

- log noise;
- stale or privacy-sensitive evidence;
- confusing users if event history becomes another state source of truth;
- excessive permanent history in the repository.

Guidance:

- keep event history bounded;
- prefer current slice reports or local JSONL evidence over permanent repo history unless the event has long-term audit value;
- keep the current state authoritative;
- never let event logs become a substitute for explicit state-machine rules.

## Capability Matrix

A capability matrix makes command availability and authority explicit instead of scattering conditionals across code.

Example:

```yaml
capabilities:
  workflow.request:
    changes_state: true
    allowed_in_failed: false
    requires_clean_worktree: false
  release.tag:
    maintainer_only: true
    requires_clean_worktree: true
```

Potential benefits:

- clearer command permissions;
- fewer hidden special cases;
- easier tests for state-dependent command behavior;
- better preparation for future profile, role, or multi-agent scenarios.

Risks:

- premature abstraction;
- a matrix that duplicates simple code;
- divergence between matrix, documentation, and actual command behavior.

Guidance:

- introduce a capability matrix only when command availability depends on state, role, profile, workflow phase, or maintainer-only authority;
- keep it machine-readable if it governs runtime behavior;
- test the matrix-to-runtime mapping;
- avoid using a matrix as documentation-only decoration when direct code is simpler.

## ADR Policy

ADR means Architecture Decision Record. An ADR is a short document that records an important architecture decision, the alternatives considered, the chosen option, and the consequences.

An ADR policy defines when ADRs are required, where they live, how they are named, and what minimum fields they contain.

Potential ADR path:

```text
docs/adr/0001-explicit-workflow-request.md
docs/adr/0002-deterministic-cell-orchestration.md
```

Suggested minimum ADR fields:

```markdown
# ADR 0001: Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD
Context:
Decision:
Alternatives considered:
Consequences:
Follow-up:
```

Use ADRs for:

- durable architecture decisions with real alternatives;
- public CLI semantics that are hard to change later;
- state-machine design choices;
- release, repair, validation, or evidence conventions with long-term consequences;
- decisions that future agents are likely to rediscover incorrectly without context.

Do not use ADRs for:

- routine implementation details;
- small refactors with no long-term alternative;
- simple documentation edits;
- decisions already captured sufficiently in code, tests, and existing docs.

Guidance:

- ADRs should explain why, not merely what;
- ADRs should not replace tests or documentation coverage;
- superseded ADRs should remain in place and point to the successor;
- avoid creating an ADR backlog that nobody reads.

## State-Model Templates

State-model templates provide a consistent way to define workflows before implementation.

Suggested template:

```markdown
# State Model: Name

Purpose:
State file or storage:
Authoritative state source:

## States

- READY: ...
- REQUESTED: ...
- RUNNING: ...
- UPLOADED: ...
- FAILED: ...

## Allowed transitions

- READY -> REQUESTED: explicit request
- REQUESTED -> RUNNING: workflow starts
- RUNNING -> UPLOADED: evidence uploaded
- RUNNING -> FAILED: failure preserved
- UPLOADED -> READY: cleanup complete

## No-op behavior

- READY + run command: no-op

## Stop states

- FAILED: diagnose before cleanup or continuation

## Evidence

- local evidence files:
- remote evidence branch:
- report path:

## Tests

- transition tests:
- idempotency tests:
- failure preservation tests:
- cleanup tests:
```

Potential benefits:

- fewer hidden workflow transitions;
- better test planning;
- clearer recovery behavior after failures;
- easier handoff between chat sessions or coding agents.

Risks:

- over-modeling simple commands;
- adding states that do not change behavior;
- documentation drift when implementation changes.

Guidance:

- require explicit state models only for persistent, resumable, multi-step, side-effecting, or failure-prone processes;
- name no-op and stop-state behavior explicitly;
- keep states behaviorally meaningful;
- update tests when transitions change.

## Relationship to DCO

Deterministic Cell Orchestration is a related but narrower pattern. DCO structures AI-generated outputs into typed cells for validation, repair, and deterministic rendering.

These governed workflow patterns focus on runtime and process reliability: state transitions, command authority, event evidence, and architecture-decision memory.

Both patterns share the same principle: make implicit model- or chat-dependent behavior explicit, reviewable, and testable when the added structure reduces overall workflow complexity.

## Current recommendation

Keep this file as an idea note until one of the patterns becomes concrete implementation work. When a pattern moves from idea to implementation, convert the relevant part into one or more of:

- tests;
- schema checks;
- `doctor` or `check-docs` checks;
- documentation coverage entries;
- CLI contract documentation;
- ADRs for durable architecture choices.
