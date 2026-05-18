# Persistent Handoff State and Rule Lifecycle Plan

Status: proposed
Decision status: Planned

## Purpose

The project needs a persistent handoff state so future chats, agents, and the local cockpit no longer reconstruct project state from conversation memory. The repository must contain the current handoff truth in a structured file.

## MVP scope

The first implementation slice should be read-only.

Planned files:

- `.agentic/handoff_state.yaml`
- `src/agentic_project_kit/handoff_state.py`
- `src/agentic_project_kit/handoff_prompt.py`
- `tests/test_handoff_state.py`
- `tests/test_handoff_prompt.py`
- `docs/workflow/HANDOFF_STATE.md`

Planned commands:

- `./ns handoff-show`
- `./ns handoff-check`
- `./ns handoff-prompt`

Out of scope for the MVP:

- automatic Git state mutation
- automatic release mutation
- GUI mutation controls
- release-cycle automation

## Rule lifecycle hygiene

Chat-end lessons must be curated, not accumulated blindly.

The handoff state should support rule statuses:

- `active`: currently binding.
- `superseded`: replaced by a newer mechanism or workflow.
- `historical`: kept only as background evidence.

The generated handoff prompt should include active rules by default. Superseded or historical rules should not appear as binding instructions.

When the system changes, obsolete rules must be removed from active instructions or marked as superseded/historical. The project must avoid duplicate rules, contradictory rules, and stale workaround instructions.

## Initial YAML shape

The first `.agentic/handoff_state.yaml` should include at least:

- `schema_version`
- `updated`
- `repo`
- `safe_state`
- `release`
- `open_items`
- `completed_since_previous_handoff`
- `current_capabilities`
- `rules` with stable ids and lifecycle statuses
- `recent_failure_patterns` with prevention notes
- `next_allowed_tasks`
- `blocked_until_closeout`
- `first_instruction`
- `handoff_maintenance`

## Required checks

`handoff-check` should verify:

- required top-level fields exist
- no empty critical fields
- each rule has `id`, `status`, and text
- active rule ids are unique
- superseded rules include `superseded_by` or a reason
- generated prompts contain no duplicate active rule ids
- `first_instruction` does not contradict blocked work

## Strategic rule

Do not continue GUI/Cockpit mutation controls before persistent handoff state and parameterized action objects exist. Otherwise the GUI would become a nicer surface over the same fragile terminal procedures.
