# Release Notes Generator MVP Analysis

- schema_version: 1
- kind: release_notes_generator_mvp_analysis
- command: `agentic-kit release-notes-generate`

## Summary

The MVP generates deterministic, evidence-backed release notes from local Git tag-diff data. JSON is the canonical generated artifact. Markdown is a projection rendered from the JSON/core model and must not become the manual source of truth.

## State Model Fit

The command is read-only unless `--write` is passed with explicit `--json-out` and `--out` paths. It does not tag, publish, close out DOI metadata, or create GitHub releases. It fits after release planning/preparation and before final publication notes are committed.

## Validation

The generator blocks missing refs, unparseable git records, unclassified product PRs, and product items without PR evidence. Administrative handoff refresh commits are separated from product release-note items.

## Determinism

`generated_at_utc` is derived from the `to_ref` committer date normalized to UTC, not from wall-clock time. The same inputs should produce the same JSON and Markdown.

## Follow-Up

- Optional GitHub PR metadata enrichment can be added later without making GitHub required.
- Release-prep can consume or validate release-note outputs once the MVP is stable.
- A drift gate can be added if generated release-note files become committed release artifacts.
