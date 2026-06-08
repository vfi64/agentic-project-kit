# Command Reference Registry Contract

`docs/reference/agentic-kit-commands.json` is the machine-readable command registry for `agentic-kit`.

`docs/reference/AGENTIC_KIT_COMMANDS.md` is generated from that JSON file for human readers.

The registry must be generated from the real Typer/Click CLI registration state, not from a manual seed. The required source marker is `generated_from_typer_click_registry`.

Required maintenance path:

1. Change the CLI command implementation.
2. Run `scripts/generate_agentic_kit_command_reference.py`.
3. Commit the updated JSON and generated Markdown together with the code change.
4. Keep `tests/test_agentic_kit_command_reference_is_current.py` green.

The staleness test is the binding guard: if a command is added, removed, renamed, or its parameters change, the generated registry and Markdown must be updated in the same change.

## Transfer wrapper command layer

The generated command reference is also the registry anchor for the transfer wrapper command layer.

`agentic-kit transfer` commands are bounded workflow entry points. They are the preferred durable path for chat-guided local work, transfer evidence, guarded PR completion, protected-diff planning, patch work orders, branch cleanup, and later GUI expansion.

For the completed pre-GUI wrapper set, workflows should prefer documented transfer wrappers such as `transfer sync-main`, `transfer remote-work-start`, `transfer pr-create-complete`, `transfer protected-diff-plan`, `transfer work-order-patch`, `transfer rebase-on-upstream`, `transfer conflict-status`, `transfer conflict-resolve-file`, `transfer delete-merged-work-branch`, and `transfer evidence-pr-complete`.

The GUI must not introduce a second command system. GUI dispatch must map to generated command-reference entries or registered Python actions with explicit safety classes, preconditions, and tests. Raw shell, raw git, raw GitHub, and manual evidence choreography are fallback or implementation details, not GUI-facing workflow contracts.
