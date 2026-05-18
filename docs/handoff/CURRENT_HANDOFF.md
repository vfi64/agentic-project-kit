# Current Handoff

## Repository

- Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`.
- Remote: `github.com:vfi64/agentic-project-kit`.
- Default branch: `main`.

## Safe state

- `main` is clean and current at `17a2e8e Record v0.3.24 DOI metadata (#341)`.
- `v0.3.24` is released.
- Release tag `v0.3.24` points to `39603bf Prepare v0.3.24 release metadata (#340)`.
- GitHub Release `v0.3.24` exists.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Zenodo v0.3.24 DOI: `10.5281/zenodo.20270197`.
- Post-release verification: PASS.
- Local validation after PR #341: `319 passed`, ruff PASS, check-docs PASS, doctor PASS.

## Completed since previous handoff

- v0.3.24 release was prepared, published, and post-release verified.
- PR #341 recorded v0.3.24 DOI metadata and was merged.
- v0.3.24 DOI metadata closeout is complete.
- The next feature direction was narrowed from generic GUI/Cockpit work to durable handoff state and checked action objects.

## Next work order

1. Create `feature/persistent-handoff-state`.
2. Add `.agentic/handoff_state.yaml` as the structured handoff source of truth.
3. Add read-only handoff commands first: `handoff-show`, `handoff-check`, `handoff-prompt`.
4. Add rule lifecycle hygiene: `active`, `superseded`, `historical`.
5. Ensure chat-end lessons are curated into the YAML state and generated handoff prompt without redundant, inconsistent, or obsolete rules.
6. Only after that, build parameterized Git/PR/release/DOI actions.
7. Continue GUI/Cockpit mutation controls only after durable handoff state and parameterized actions exist.

## Binding workflow rules

- Do not develop directly on `main`.
- Use feature/documentation branches, local gates, PR, CI, merge, and main verification.
- Prefer `./ns` and project-local `.venv` tooling over global commands.
- Terminal blocks must be quoting-safe.
- No heredocs.
- No risky multiline `python -c` commands.
- No `exit` at the end of terminal blocks.
- End blocks with PASS/FAIL/PENDING markers and the note: `Terminal bleibt offen. Kein exit am Blockende.`
- Do not print PASS unconditionally after failing commands; use `set -e` or explicit status handling in future checked actions.
- Relevant terminal output should become committed/pushed evidence, not only chat text.

## First instruction for the next feature slice

Work first on `feature/persistent-handoff-state`. Keep the MVP read-only. Do not start GUI mutation controls or release-cycle automation until the persistent handoff state and rule lifecycle hygiene exist.
