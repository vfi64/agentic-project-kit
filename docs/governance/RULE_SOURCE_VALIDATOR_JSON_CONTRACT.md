# Rule Source Validator JSON Contract

Document class: governance/system
Status-date: 2026-07-08
Moved-from: docs/planning/RULE_SOURCE_VALIDATOR_JSON_CONTRACT.md

Status: active
Decision status: accepted
Review policy: Review before derived rule snapshots, LLM acknowledgement gates, or GUI rule-state buttons consume this JSON.
Project: agentic-project-kit

## Purpose

This document defines the stable JSON contract for the read-only canonical rule source validator.

The validator checks existing repository-backed rule sources. It must not write files, generate snapshots, or introduce a second manually maintained rule system.

If a mandatory source is missing or invalid, the validator must fail closed and return a blocking result.

## Command

Indented command form:

    agentic-kit rules validate-sources --json

Project-local equivalent:

    ./.venv/bin/python -m agentic_project_kit.cli rules validate-sources --json

## Exit Semantics

- Exit code `0`: all canonical rule sources are present and valid.
- Exit code `1`: validation fails closed because at least one blocking rule-source problem exists.

The GUI and transfer workflow must treat exit code `1` as a hard WAIT/BLOCK state, not as a recoverable warning.

## Stable JSON Fields

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Contract version for this JSON shape. Current value: `1`. |
| `sources_total` | integer | yes | Number of de-duplicated canonical source paths checked. |
| `is_valid` | boolean | yes | True only when no blocking reasons exist. |
| `fail_closed` | boolean | yes | True when validation must block downstream rule-refresh, acknowledgement, or GUI state. |
| `source_paths` | list of strings | yes | Ordered canonical source paths checked by the validator. |
| `missing_required_paths` | list of strings | yes | Required source files that are missing. |
| `yaml_parse_error_paths` | list of strings | yes | YAML source files that cannot be parsed. |
| `handoff_state_errors` | list of strings | yes | Structural validation errors from `.agentic/handoff_state.yaml`. |
| `blocking_reasons` | list of strings | yes | Human-readable blocking reasons. Empty only when `is_valid` is true. |

## Invariants

- `schema_version` must remain present.
- `is_valid` must equal `not blocking_reasons`.
- `fail_closed` must equal `bool(blocking_reasons)`.
- Missing required paths must create blocking reasons.
- YAML parse errors must create blocking reasons.
- Handoff-state validation errors must create blocking reasons.
- The validator is read-only and must not mutate repository files.
- The validator consumes existing canonical rule source lists instead of maintaining a separate rule list.

## Downstream Use

This JSON is the first machine-readable gate for the hardened rule-refresh handshake.

Allowed downstream consumers:

- derived rule snapshot generation,
- LLM acknowledgement gates,
- transfer-state gates,
- GUI rule-state display and button enablement.

Downstream consumers must not infer rule freshness from Markdown text alone. They must use this validation result before trusting generated projections or acknowledgement state.

## GUI Mapping

| JSON State | GUI State | Meaning |
| --- | --- | --- |
| `is_valid=true`, `fail_closed=false` | READY | Rule sources are structurally valid. |
| `missing_required_paths` non-empty | BLOCKED | Canonical rule source is missing. |
| `yaml_parse_error_paths` non-empty | FAILED | Canonical YAML source is malformed. |
| `handoff_state_errors` non-empty | FAILED | Handoff state is structurally invalid. |
| `blocking_reasons` non-empty | WAIT/BLOCKED | Downstream rule-refresh handshake must not proceed. |

The GUI must show the blocking reason and must not expose write actions that depend on fresh rules while `fail_closed` is true.

## Relationship To Canonical Rule Source Contract

This contract supports the single-source model from `docs/governance/RULE_REFRESH_HANDSHAKE_CONTRACT.md`.

The validator checks canonical sources. It does not create canonical state. Snapshots and Markdown projections remain derived artifacts.
