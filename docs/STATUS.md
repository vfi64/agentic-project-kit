# Project Status

## Current safe state

- Current version: `0.3.24`.
- Safe branch: `main`.
- Safe commit after DOI metadata closeout: `17a2e8e Record v0.3.24 DOI metadata (#341)`.
- Release tag: `v0.3.24` at `39603bf Prepare v0.3.24 release metadata (#340)`.
- GitHub Release `v0.3.24` exists and contains wheel and source distribution assets.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Zenodo v0.3.24 DOI: `10.5281/zenodo.20270197`.
- Post-release verification: PASS.
- Local gates after DOI metadata merge: `319 passed`, ruff PASS, check-docs PASS, doctor PASS.

## Completed closeout

- PR #341 `Record v0.3.24 DOI metadata` has been merged into `main`.
- The release/DOI state for v0.3.24 is now complete.
- No new release, tag, or GUI work should be started from the old pre-closeout state.

## Next planned slices

1. `feature/persistent-handoff-state`
   - Add `.agentic/handoff_state.yaml` as the structured source for future handoffs.
   - Add read-only commands such as `./ns handoff-show`, `./ns handoff-check`, and `./ns handoff-prompt`.
   - Include rule lifecycle hygiene: active, superseded, historical.
   - Curate chat-end lessons into the YAML state and generated prompt without redundancy or inconsistency.
   - Remove obsolete rules when system improvements make them unnecessary, or mark them as superseded/historical.
2. `feature/parametrized-git-release-actions`
   - Add checked, parameterized actions for PR, release, DOI, and finalize workflows.
   - Start with PR check/merge because PR #341 exposed the need for machine-readable status checks.
3. GUI/Cockpit continuation
   - Continue GUI work only after persistent handoff state and parameterized actions exist.

## Current workflow lesson

The transition from v0.3.23 to v0.3.24 shows that the project no longer only needs more terminal shortcuts. It needs durable state and curated rule maintenance. New lessons from a chat must be reviewed at the end of the chat and folded into the next handoff state only when they remain valid. Duplicated, contradictory, or obsolete rules must not accumulate.
