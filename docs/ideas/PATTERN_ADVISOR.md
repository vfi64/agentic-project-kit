# Pattern Advisor

Status: idea-note / architecture research track
Decision status: not implemented
Review policy: keep while advisory pattern guidance is an active architecture option
Next review: before v0.4.0 or before adding a public `agentic-kit patterns` / `agentic-kit advise` CLI
Removal rule: delete, archive, or convert into implemented documentation if superseded, rejected, or fully implemented
Source: uploaded concept note, curated for repository use

## Purpose

This note preserves the Pattern Advisor concept as a governed architecture option for `agentic-project-kit`.

The goal is not to add another mandatory subsystem now. The goal is to keep the idea discoverable, reviewable, and bounded so future work can decide whether a small pattern catalog or advisory CLI is worth implementing.

The central project-level constraint remains:

```text
agentic-project-kit is a metatool for agentic and LLM-assisted project development in general.
Wrapper-project experiences are important evidence and pattern sources, but the kit must not become wrapper-specific.
```

## Cause

Agent-assisted projects often fail in recurring ways:

- the same patch pattern is repeated instead of naming the underlying problem class;
- branch, handoff, workflow, or release drift reappears across sessions;
- local evidence is lost in chat context instead of becoming repository state;
- semantic review expectations drift into deterministic gates without a clear boundary;
- new commands increase capability but make the daily user path harder;
- project-specific lessons remain trapped in a single repo instead of becoming reusable governed knowledge.

The current kit already mitigates some of these problems with state docs, gates, workflow requests, evidence branches, release checks, and idea notes. What is still missing is a disciplined way to capture recurring problem patterns and suggest reusable solution patterns without pretending to automate architecture decisions.

## Idea

The Pattern Advisor would be an advisory layer that maps evidence from project state to known patterns, anti-patterns, and candidate patterns.

It would answer questions like:

```text
What recurring problem class does this resemble?
Which established kit pattern should be considered?
Which anti-pattern should be avoided?
What evidence is still missing before a safe decision?
Should this repeated lesson become a candidate pattern?
```

The Pattern Advisor is not an oracle and not an autonomous architect. It should never silently change project state or override deterministic gates.

## Discussion

### Advisory versus deterministic gates

The Pattern Advisor must stay clearly separated from deterministic gates.

```text
doctor / check-docs / release-check / doc-mesh-audit
= deterministic or bounded checks

pattern-advisor / advise / patterns suggest
= advisory review support
```

A pattern suggestion can be useful even when it is not provable. That is acceptable only if the output is labelled as advice and does not become a pass/fail gate by accident.

### Relation to existing ideas

The Pattern Advisor relates to existing idea notes:

- `GOVERNED_WORKFLOW_PATTERNS.md` preserves workflow, ADR, capability, and state-model design patterns.
- `DETERMINISTIC_CELL_ORCHESTRATION.md` preserves a decision pattern for complex rule-bound AI outputs.
- `LAYERED_CLI_USABILITY.md` preserves a usability model for keeping daily operation simple.

The Pattern Advisor would be the meta-layer that can point maintainers toward such patterns when evidence suggests that a recurring problem class has appeared.

### Relation to didactic simplification

This idea must not fight the usability direction. A Pattern Advisor can easily become a complexity amplifier if it exposes too many pattern names, lifecycle states, and subcommands too early.

Therefore the Golden Path must stay small. Pattern advice should be optional, explainable, and likely Guided or Maintainer level rather than Daily level.

### Non-goals

The Pattern Advisor must not become:

- an autopilot;
- a hidden decision engine;
- a replacement for human architecture judgment;
- a new hard gate without explicit policy;
- a wrapper-project special case;
- a semantic proof system;
- a reason to blur the semantic quality boundary;
- a reason to overload `doctor`;
- a large CLI surface before the Golden Path is simplified.

## Conclusions

1. The Pattern Advisor is strategically useful but too large for immediate full implementation.
2. It should first be preserved as an idea note.
3. A later implementation should start with a very small MVP, not a full advisory engine.
4. The first possible MVP should probably be a pattern catalog, not automatic suggestion.
5. Any public CLI that recommends patterns may require an ADR because it affects public command semantics and long-term agent-facing behavior.
6. Pattern suggestions must be labelled as advisory.
7. Wrapper-project lessons may supply evidence, but the resulting patterns must be project-neutral.
8. The idea should remain compatible with Layered CLI Usability: high internal capability, simple daily operation.

## Possible later MVP

A restrained later MVP could include only:

```text
.agentic/patterns/
docs/patterns/
agentic-kit patterns list
agentic-kit patterns show <id>
schema / loader tests
3 to 5 starter patterns
```

This MVP would not include automatic `suggest`, candidate capture, promotion/deprecation workflow, or a broad pattern library.

Possible starter pattern families:

- repository-state-as-source-of-truth;
- explicit workflow request before execution;
- bounded deterministic repair;
- evidence branch for local-output transfer;
- layered CLI usability.

## Candidate lifecycle

A later implementation could use a simple lifecycle:

```text
candidate -> accepted -> deprecated -> archived
```

Candidate promotion should require evidence, tests where applicable, and maintainer review. There should be no automatic promotion from repeated occurrence alone.

## ADR guidance

No ADR is needed for this idea note.

Consider an ADR if any of the following become true:

- a public `agentic-kit patterns` or `agentic-kit advise` CLI is introduced;
- pattern classification becomes part of a documented project contract;
- advisory output influences workflow state or gate behavior;
- pattern lifecycle rules become binding;
- the project commits to a long-term pattern catalog format.

## Plan

Near-term:

1. Keep this file as a non-binding idea note.
2. Do not implement Pattern Advisor during the didactic simplification slice.
3. Use the idea as a reference when evaluating recurring problems.
4. Revisit before v0.4.0 or before adding public advisory CLI.

Later, if implemented:

1. Start with read-only catalog support.
2. Keep output clearly advisory.
3. Add schema and loader tests.
4. Keep pattern count small.
5. Only then consider suggestion or candidate-capture commands.

## Implementation notes for future work

A future implementation should prefer:

- plain YAML or JSON for pattern metadata;
- deterministic validation of metadata structure;
- Markdown documentation for human-readable explanations;
- stable IDs for patterns and anti-patterns;
- test fixtures with no remote dependencies;
- no direct coupling to a single project such as the wrapper project.

Possible shape:

```text
.agentic/patterns/catalog.yaml
docs/patterns/<pattern-id>.md
src/agentic_project_kit/patterns.py
tests/test_patterns.py
```

Initial command surface, if approved:

```text
agentic-kit patterns list
agentic-kit patterns show <id>
```

Defer:

```text
agentic-kit patterns suggest
agentic-kit patterns capture-candidate
agentic-kit advise
```

## Review trigger

Review this idea note when:

- the same architecture or workflow problem recurs across multiple repos;
- the Guided CLI Usability work needs pattern-level explanation;
- `doc-mesh-audit` produces recurring finding classes;
- a release planning cycle needs a project-neutral pattern catalog;
- before v0.4.0.

## Removal or archive trigger

Delete or archive this note if:

- the idea is superseded by a simpler mechanism;
- it proves too complex for the kit's usability goals;
- pattern advice is intentionally rejected;
- the idea is fully absorbed into implemented docs, tests, and ADRs.
