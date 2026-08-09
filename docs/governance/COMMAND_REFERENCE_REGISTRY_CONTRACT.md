# Command Reference Registry Contract

`docs/reference/agentic-kit-commands.json` is the machine-readable command registry for `agentic-kit`.

`docs/reference/AGENTIC_KIT_COMMANDS.md` is generated from that JSON file for human readers.

The registry must be generated from the real Typer/Click CLI registration state, not from a manual seed. The required source marker is `generated_from_typer_click_registry`.

## Command surface contract

Every generated command-reference entry must carry exactly one `surface` value:

- `orchestrator`: primary user-facing operation for a complete governed task or lifecycle step.
- `diagnostic`: primary diagnosis, inspection, status, readiness, audit, or evidence-reporting operation.
- `primitive`: public low-level command building block that may be used directly by expert users, CI, wrappers, or orchestration code.

Surface classification is separate from command safety. It describes user-facing role and disclosure level; it does not grant mutation permission and it does not change the `READ_ONLY`, `BOUNDED`, or `DESTRUCTIVE` safety contract.

Surface classification is intent-oriented. Primary work-entry, work-finish, workspace lifecycle, release lifecycle, handoff lifecycle, and dry-run-default maintenance workflows belong in `orchestrator` when they are the natural command a maintainer would ask for. Highly parameterized evidence, transfer, commit, branch, log, and file helpers remain `primitive` even when they are implemented as bounded mini-workflows. Status, check, audit, readiness, and reporting commands remain `diagnostic` unless their main purpose is to start or complete a governed lifecycle step. `diagnostic` must not be inferred from `READ_ONLY`, and `orchestrator` must not be inferred merely from the fact that implementation code calls multiple lower-level functions.

Surface classification does not by itself change the compatibility or deprecation contract of an existing public command. In particular, primitive does not mean unstable, deprecated, private, or unsupported. Any future stability or deprecation model must be introduced as its own explicit contract and gate, not inferred from `surface`.

`agentic-kit command-for` may use `surface` only after semantic task matching and safety or prerequisite checks. For equally suitable task matches it should prefer `orchestrator`, then `diagnostic`, then `primitive`; diagnostic task tags may prefer `diagnostic` first. Surface must not override a more exact task match, so an exact primitive match is not displaced by a broader orchestrator.

GUI and website projections must consume this same generated `surface` field. They may group commands as Primary (`orchestrator`), Diagnostics (`diagnostic`), and Expert / Low-level (`primitive`), but they must not maintain an independent list such as `ORCHESTRATORS = [...]` or infer stability from the GUI layer. GUI action registries may remain Bedienprojektionen with their own labels, access levels, and safety gates, but any `agentic-kit` wrapper they expose must resolve to a generated command-reference entry with a valid `surface`.

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
