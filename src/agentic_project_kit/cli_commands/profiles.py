from __future__ import annotations

import typer
from rich.console import Console

from agentic_project_kit.contract import PROFILE_DEFINITIONS, POLICY_PACK_DEFINITIONS

console = Console()


def register_profile_commands(app: typer.Typer) -> None:
    app.command("profile-explain")(profile_explain_command)


def profile_explain_command() -> None:
    """List available project profiles and policy packs."""
    console.print("Project profiles:")
    for profile_id, definition in PROFILE_DEFINITIONS.items():
        description = getattr(definition, "description", str(definition))
        console.print(f"- {profile_id}: {description}")

    console.print("")
    console.print("Policy packs:")
    for policy_pack_id, definition in POLICY_PACK_DEFINITIONS.items():
        description = getattr(definition, "description", str(definition))
        console.print(f"- {policy_pack_id}: {description}")
