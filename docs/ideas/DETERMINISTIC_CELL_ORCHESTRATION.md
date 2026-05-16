# Deterministic Cell Orchestration

Status: idea-note
Decision status: deferred; not implemented as a binding architecture
Review policy: keep while DCO is an active architecture option
Next review: before v0.4.0 or when workflow, repair, validation, rendering, or audit architecture changes
Removal rule: delete or archive if DCO is no longer useful, superseded, or fully absorbed into implemented docs
Source: uploaded concept note, curated for repository use
Rule location: `AGENTS.md` (`Deterministic Cell Orchestration Decision Rule`)

## Purpose

This note preserves the Deterministic Cell Orchestration (DCO) concept without turning it into an immediate implementation requirement.

DCO is meant for complex, rule-bound AI-generated outputs where free-form text generation is too fragile. Its goal is to reduce instruction drift, improve validation and repair, and separate model-generated content from deterministic rendering.

Use this idea only when it reduces overall workflow complexity. Do not introduce schemas, validators, repair plans, or renderers merely for architectural symmetry.

## Core idea

DCO splits a complex output into explicit, typed cells. Each cell has a bounded responsibility, stable identity, required fields, and validation rules.

A model may generate or repair cell content, but deterministic project code validates the resulting structure and renders the final user-facing artifact.

The important shift is from one large, fragile generated document to a set of smaller, reviewable units:

```text
model output -> typed cells -> validation -> selective repair -> deterministic rendering
```

## Problems DCO may address

### Instruction drift

Large prompts with many formatting and governance rules can cause the model to preserve narrative flow while losing formal requirements. Cell-level contracts can make required parts explicit and independently checkable.

### Fragile free-form structure

Markdown sections, repeated structures, required labels, and nested output contracts are difficult to validate reliably when they exist only as prose. Typed cells can provide a more stable intermediate representation.

### All-or-nothing failure

A single malformed section near the end of a long output can make the whole artifact unusable. With DCO, failed cells can be localized and repaired without regenerating valid cells.

### Renderer instability

If the model is responsible for final formatting, output quality depends on prompt adherence. With DCO, a deterministic renderer can turn validated cells into Markdown, HTML, reports, or other artifacts.

## Candidate architecture

A minimal DCO implementation would usually include:

1. Cell schema
   - stable cell IDs;
   - explicit cell types;
   - required fields;
   - allowed values;
   - dependency or ordering rules where needed.

2. Cell validation
   - syntax and schema checks;
   - required-section checks;
   - known guardrail checks;
   - bounded semantic checks only where the semantic property is deterministic.

3. Selective repair
   - repair only failed cells;
   - keep repair prompts narrow;
   - preserve valid cells;
   - stop after a bounded number of attempts;
   - record the repair reason and evidence.

4. Deterministic rendering
   - render only validated cells;
   - keep display formatting out of model responsibility where practical;
   - test renderer expectations.

## Candidate use cases

DCO may be useful for:

- complex output contracts with required sections or repeated structures;
- structured audit or handoff reports;
- validation and repair reports;
- release or review artifacts that need machine-readable intermediate state;
- AI-generated content where only a subset should be repaired;
- workflows where deterministic rendering is safer than prompt-based formatting.

DCO is not a good default for:

- simple Markdown documents;
- small CLI additions;
- ordinary documentation edits;
- one-off reports without repair or renderer needs;
- features where a typed intermediate layer would be harder to understand than the direct implementation.

## Relationship to agentic-project-kit

For `agentic-project-kit`, DCO should remain an architecture option rather than a default requirement.

The current review-only rule in `AGENTS.md` is intentionally narrower than a binding implementation policy. It asks reviewers to check whether DCO would help for complex, rule-bound AI-generated outputs, but it also says not to use DCO when a simpler document, command, gate, or Markdown update is clearer.

If DCO becomes concrete implementation work, the relevant parts should move from this idea note into one or more of:

- tests;
- schemas;
- validators;
- repair plans;
- renderer contracts;
- `doctor` or `check-docs` checks;
- architecture documentation;
- an ADR if the decision has durable consequences.

## Relationship to Comm-SCI-Control

The uploaded concept note came from the Comm-SCI-Control context, where complex rule sets and generated responses can suffer from instruction drift, formatting instability, and all-or-nothing repair failures.

That context is useful background, but this repository should not import Comm-SCI-Control-specific assumptions blindly. DCO should be adapted only when a concrete `agentic-project-kit` feature has similar validation, repair, rendering, or auditability needs.

## ADR guidance

No ADR is required while DCO remains an idea note.

Create or recommend an ADR when the project makes a durable choice such as:

- DCO becomes the official architecture for a concrete feature;
- DCO is rejected for a major workflow or repair design after considering alternatives;
- public CLI behavior or persistent state depends on DCO;
- tests, schemas, or renderer contracts make DCO part of the maintained architecture.

## Current recommendation

Keep DCO as a curated idea until a concrete feature needs it. Prefer the smallest architecture that solves the actual drift, validation, repair, rendering, or auditability problem.
