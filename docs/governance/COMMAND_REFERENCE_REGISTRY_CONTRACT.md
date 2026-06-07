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
