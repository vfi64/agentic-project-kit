# Layered CLI Usability

Status: idea-note
Decision status: not implemented as a binding CLI policy
Review policy: keep while CLI usability and command growth are active architecture concerns
Next review: before v0.4.0 or when public workflow, release, doctor, repair, or audit commands change
Removal rule: delete, archive, or convert into binding documentation if the model is superseded or fully implemented elsewhere
Roadmap relation: future hardening of user-facing CLI complexity, guided workflows, and capability boundaries

## Purpose

`agentic-project-kit` should support high functionality, high automation, and professional project governance without making daily operation difficult.

The central principle is:

```text
Internal complexity is allowed. Default user experience must stay simple.
```

This note preserves a layered usability model for future CLI design. It is not yet a binding command taxonomy and does not require immediate implementation changes.

## Problem

As the kit grows, it accumulates commands for validation, documentation gates, workflow state, release checks, repair, audit, evidence handling, and agent-facing diagnostics.

That power is useful, but it creates risks:

- users must remember too many commands;
- debug or maintainer workflows leak into daily usage;
- public CLI semantics become harder to explain;
- new features add surface area without a clear audience;
- automation becomes professional internally but intimidating externally.

The goal is not to remove functionality. The goal is to keep the everyday path small while allowing advanced capabilities to exist behind clear boundaries.

## Usability layers

### Daily layer

Audience: normal daily users and chat-assisted workflows.

Goal: keep common operation obvious, safe, and low-friction.

Typical commands:

```text
ns
agentic-kit doctor
agentic-kit check-docs
agentic-kit workflow status
```

Characteristics:

- low cognitive load;
- safe to run repeatedly;
- clear pass/fail or no-op behavior;
- minimal flags;
- suitable for the default workflow path.

### Guided layer

Audience: users who want the kit to lead them through a bounded workflow.

Goal: provide explicit next steps without exposing raw implementation details.

Typical commands:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow cleanup
```

Possible future commands:

```text
agentic-kit assist
agentic-kit next
agentic-kit explain
agentic-kit diagnose
```

Characteristics:

- explains current state and recommended action;
- writes bounded evidence when useful;
- preserves no-op and stop-state behavior;
- avoids requiring users to inspect raw state files unless diagnosis needs it.

### Maintainer layer

Audience: repository maintainers and power users.

Goal: support release, governance, audit, and project health decisions.

Typical commands:

```text
agentic-kit release-plan
agentic-kit release-check
agentic-kit post-release-check
agentic-kit doc-mesh-audit
```

Characteristics:

- may require more context;
- may influence release readiness or architecture hygiene;
- should be documented clearly;
- should not become part of the daily happy path unless the output is simple and stable.

### Debug layer

Audience: developers, maintainers diagnosing failures, or coding agents.

Goal: expose internal evidence and raw diagnostics without making them the normal interface.

Typical entry points:

```text
tools/*
--json
--verbose
raw reports
state files
```

Characteristics:

- high detail;
- may expose implementation concepts;
- useful for failure diagnosis and development;
- must not be required for ordinary operation.

## Golden Path rule

The Golden Path should remain close to the Daily layer.

A user should be able to understand ordinary repository health and workflow state with a small number of stable commands. Advanced functionality should support the Golden Path, not replace it with a larger checklist.

A rough target is:

```text
Daily: know what is healthy and what the current state is.
Guided: ask the kit to run or explain the next bounded workflow step.
Maintainer: prepare releases, audits, and durable project decisions.
Debug: diagnose why something failed.
```

## Feature placement rule

Every new user-facing feature should be placed in one of the usability layers before it is treated as part of the public experience.

Review questions:

1. Is this command or option needed for daily use?
2. Can it be hidden behind a guided command or summarized by `doctor`?
3. Is it maintainer-only because it affects release, audit, governance, or persistent state?
4. Is it a debug tool that should stay under `tools/`, `--json`, `--verbose`, or raw reports?
5. Does it make the Golden Path harder to explain?

Features that only make sense in the Debug layer must not become default behavior.

## Relationship to capability matrices

This idea overlaps with the `Capability Matrix` pattern in `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md`.

A capability matrix may become useful if command availability depends on role, workflow state, profile, release phase, or maintainer-only authority.

Layered CLI usability is a broader UX concept. A future capability matrix could implement part of it, but this note should not force that abstraction before the command surface actually needs it.

## Relationship to DCO

Layered CLI usability and Deterministic Cell Orchestration solve different problems.

DCO structures complex generated outputs for validation, selective repair, and deterministic rendering.

Layered CLI usability structures the user-facing command surface so that complex internals do not make ordinary operation harder.

Both patterns share the same design principle: add structure only when it reduces overall complexity.

## ADR guidance

No ADR is required while this remains an idea note.

Recommend an ADR when the project makes a durable choice such as:

- all public commands must be assigned a usability layer;
- `agentic-kit assist` or a similar command becomes the official guided entry point;
- command visibility or behavior becomes role-, state-, or capability-dependent;
- the Golden Path is formally defined as part of the architecture contract.

## Current recommendation

Use this note as a review lens for future command growth.

Before adding new public CLI surface area, ask whether it keeps simple workflows simple and whether the feature belongs in Daily, Guided, Maintainer, or Debug.
