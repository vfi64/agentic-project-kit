# Governed Rule Registry Architecture

Status: planned
Priority: 1
Language: English

## Decision

The project will introduce a governed rule registry before continuing the documentation-management rebuild.

The registry will be the canonical source of truth for active project rules. Status files, handoff files, compiled agent context, and successor prompts must become generated or validated projections. They must not be treated as independent rule stores.

## Problem

The v0.4.1 closeout exposed a governance failure mode: active rules can be lost when prose-heavy control files are shortened, reorganized, or refreshed manually. Compatibility anchors and Markdown-only requirements are not enough. They can detect some loss after the fact, but they do not model rule identity, status, priority, dependencies, conflicts, or enforcement coverage.

## Target Design

Rules are stored as small modular YAML files under `.agentic/rules/`.

Proposed modules:

- `000-core.yaml`
- `100-communication.yaml`
- `200-evidence.yaml`
- `300-terminal.yaml`
- `400-remote-git.yaml`
- `500-release.yaml`
- `600-gui.yaml`
- `700-documentation.yaml`

Each rule has a stable id, English normative text, status, category, priority, scope, enforcement references, projection targets, dependencies, conflicts, and migration metadata.

## Required Properties

- Small files: rule modules stay reviewable and connector-friendly.
- Machine-readable: active rules are YAML objects, not Markdown-only prose.
- English-only: persistent active project rules are written in English.
- Testable: critical and required rules need deterministic tests, guards, or generator checks.
- Complete: active rules must be represented in the registry before they are rendered into projections.
- Non-lossy: rule ids are stable and never recycled; obsolete or migrated rules keep explicit metadata.
- Compatible: dependencies and conflicts are validated across the full registry.
- Projection-based: `STATUS.md`, `CURRENT_HANDOFF.md`, and generated successor prompts are concise outputs, not canonical rule stores.

## Planned CLI

- `agentic-kit rules check`
- `agentic-kit rules render --check`
- `agentic-kit rules diff`
- `agentic-kit rules audit`

## Initial Migration Boundary

The first implementation slice must migrate the active rules currently protected by `.agentic/rule_preservation.yaml` into the modular registry. It must not perform a broad documentation migration and must not modify release, tag, or DOI state.

## Acceptance Criteria

- Duplicate ids fail.
- Non-English active persistent rules fail.
- Critical active rules without enforcement fail.
- Unknown dependencies fail.
- Active conflicts fail.
- Obsolete rules rendered into active projections fail.
- Projection drift fails.
- Workflow guard includes the registry check.
- Existing PR716 rule-preservation checks remain green during migration.
