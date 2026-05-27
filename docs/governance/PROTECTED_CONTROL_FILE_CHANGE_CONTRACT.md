# Protected Control File Change Contract

Status: active
Review Policy: This contract must be reviewed before protected_control, governance contract, or migration-record tooling is changed.

## Purpose

This contract prevents silent information loss in protected control files while still allowing legitimate cleanup, replacement, and removal.

## File Classes

- protected_control: machine-governance YAML and JSONL files whose anchors drive agent behavior.
- governance_contract: Markdown contracts with required anchors.
- user_facing_docs: README and manuals; these may be edited normally unless registered anchors are removed.
- evidence_logs: historical evidence; deletion requires explicit cleanup policy.

## Rule

Protected files may be changed and may shrink, but risky semantic removal requires a migration record or a repo-recorded user decision.

## Required Migration Record Fields

- file
- removed_anchor
- decision: keep, migrate, obsolete, or abort
- rationale
- successor or explicit no_successor_required
- user decision evidence
- test evidence

## Dialog Requirement

When a protected anchor would be removed without a migration record, the workflow must stop and ask the user to choose keep, migrate, obsolete, or abort. Chat-only decisions are not sufficient; the decision must be written to the repo.


## Generated Artifacts

Generated artifacts must not be edited directly. If a generated file changes, the diff must also include the generator source or another registered generator input. For example, `docs/handoff/NEXT_CHAT_BOOTSTRAP.md` is generated from `src/agentic_project_kit/chat_bootloader.py`; direct edits to the generated Markdown must be blocked and the generator path must be used instead.
