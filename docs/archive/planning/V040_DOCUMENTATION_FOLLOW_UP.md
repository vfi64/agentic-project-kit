<!--
Status: superseded
Authority: docs/planning/PROJECT_DIRECTION.yaml
Reason: Strategy, roadmap, and idea direction now live in the machine-readable project direction source.
Retention: Keep as historical context until a later protected reference check archives or removes it explicitly.
-->

# Documentation Follow-up Plan After v0.4.0

Status-date: 2026-05-23
Status: planned follow-up, not part of the DOI metadata closeout

## Purpose

This plan records documentation and review follow-up work that must not be mixed into the v0.4.0 DOI metadata closeout PR.

## Claude review follow-up

1. Inspect `inspect_selected()` for dead code and remove it if confirmed by tests.
2. Replace hard-coded local paths in `AGENTS.md` with project-relative placeholders.
3. Enrich CHANGELOG entries for v0.3.36, v0.3.37, and v0.4.0 with meaningful release content.
4. Add a guard against local absolute paths in `AGENTS.md`.
5. Add tests for pure GUI cockpit functions without opening a Tkinter window.
6. Check `CockpitActionResult.result_status` against a constant instead of a raw string where appropriate.
7. Inspect `cockpit_actions()` caching before changing it; do not optimize prematurely.
8. Consider splitting `AGENTS.md` into `docs/agent_rules/` only if the split reduces drift and preserves startup clarity.
9. Add formal CHANGELOG quality checks where deterministic, but avoid naive minimum bullet-count rules.

## Document and Artifact Governance OS

The former broader professionalization track is superseded; current strategy, roadmap, and ideas are governed by `docs/planning/PROJECT_DIRECTION.yaml`.

That plan treats documentation, generated handoffs, terminal evidence, temporary artifacts, security filters, source-of-truth relationships, update triggers, garbage-collector integration, and LLM/Codex/Claude-Code collaboration artifacts as one modular governance subsystem.

The implementation must stay modular. Registry, validators, security filters, source-of-truth graph, update triggers, artifact lifecycle, garbage collection, and advisory semantic review must remain separate modules that compose through documented CLI profiles.

## Active documentation language cleanup

All active documentation should be in English. German sections in active documentation should be translated into English. Terminal logs, historical evidence, and intentionally localized artifacts must be classified before editing and must not be rewritten blindly.
