# Didactic Guidance

Review policy: keep while didactic guidance is an active architecture option
Next review: before adding public advisory review commands or before v0.4.0

## Purpose

This note documents didactic guidance as a non-binding orientation layer for `agentic-project-kit`.

The kit is not only a command collection. It is also a method for making agentic project work understandable, restartable, teachable, and auditable.

Didactic guidance explains how project state, handoffs, gates, workflow requests, and idea notes help humans and agents understand what is happening, why it is happening, and what a safe next step looks like.

## Contract

Didactic guidance is advisory, human-facing, and documentation-first.

This foundation slice must not add runtime code, public CLI commands, deterministic gates, workflow states, Pattern Advisor implementation, or pattern catalog behavior.

## Guidance questions

Didactic guidance should help a maintainer or agent answer five questions:

1. What is the current state?
2. What is the intended next step?
3. Which rules are binding and which are advisory?
4. What must not be mixed into this slice?
5. What evidence is needed to trust the result?

## Relation to deterministic gates

`doctor`, `check-docs`, and `doc-mesh-audit` are hard checks for known structural and consistency problems.

They cannot prove didactic optimality, audience fit, architectural wisdom, or future handoff sufficiency.

Any future didactic review command must remain advisory unless it is converted into a deterministic rule with a clear, testable failure condition.

## Relation to Pattern Advisor

Pattern Advisor work remains separate.

Didactic guidance can make Pattern Advisor safer later by clarifying how advice should be framed, limited, and explained.

This note does not approve a Pattern Advisor MVP, a pattern catalog, automatic suggestions, candidate capture, promotion or deprecation workflow, or public `patterns` / `advise` CLI behavior.

## Current decision

For now, didactic guidance is documented as an idea-level orientation layer.

It is advisory, human-facing, documentation-first, and separate from deterministic gates and runtime behavior.
