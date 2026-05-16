# Local Cockpit Foundation

Lifecycle: active
Owner: agentic-project-kit
Last-reviewed: 2026-05-16

## Goal

The local cockpit is the planned control layer for professional single-user project operation. It should reduce fragile copy-and-paste workflows by exposing structured, inspectable project actions that can be reused by the CLI, shell entrypoints, menus, and a later Tkinter UI.

## Foundation scope

The v0.3.14 foundation is intentionally read-only by default. It introduces a shared action inventory and a central cockpit status command. It does not yet execute destructive git, release, or cleanup actions.

## Adapter model

- Core actions: stable metadata and status builders in Python modules.
- CLI adapter: Typer commands expose status and action inventory.
- Shell adapter: existing `./ns` entrypoints remain available and can later migrate toward the shared action layer.
- Tkinter adapter: future UI should consume the same action layer instead of assembling shell snippets.

## Safety model

Actions are classified by safety:

- `read_only`: inspection commands only.
- `bounded`: constrained workflow actions with existing safety checks.
- `destructive`: future actions that mutate branches, tags, releases, or remote state and must require explicit user intent.

## Non-goals for v0.3.14

- No large Tkinter implementation.
- No automatic PR merge, tag, release, or remote deletion flow.
- No shell-quoting based command synthesis.
- No replacement of `./ns`; migration should be incremental.
