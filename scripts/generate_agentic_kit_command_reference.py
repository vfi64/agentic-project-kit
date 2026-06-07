from __future__ import annotations

import json
from pathlib import Path

COMMAND_REFERENCE = {
    "schema_version": 1,
    "source": "manual_seed_until_introspection_is_added",
    "commands": [
        {
            "group": "transfer",
            "name": "pr-complete",
            "purpose": "Wait for PR CI, merge safely, sync main, acknowledge rules, and run post-merge completion.",
            "parameters": [
                {"name": "pr_number", "required": True, "meaning": "Pull request number to complete."},
                {"name": "--expected-head-sha", "required": False, "meaning": "Expected PR head SHA; use a full SHA or current alias where supported."},
                {"name": "--merge-method", "required": False, "meaning": "GitHub merge method, usually squash."},
            ],
        },
        {
            "group": "transfer",
            "name": "pr-wait-ci",
            "purpose": "Wait until PR checks are ready.",
            "parameters": [
                {"name": "pr_number", "required": True, "meaning": "Pull request number."},
                {"name": "--expected-head-sha", "required": False, "meaning": "Expected PR head SHA."},
            ],
        },
        {
            "group": "transfer",
            "name": "pr-merge-safe",
            "purpose": "Merge a green PR through the guarded merge path.",
            "parameters": [
                {"name": "pr_number", "required": True, "meaning": "Pull request number."},
                {"name": "--expected-head-sha", "required": False, "meaning": "Expected PR head SHA."},
                {"name": "--merge-method", "required": False, "meaning": "GitHub merge method."},
            ],
        },
        {
            "group": "transfer",
            "name": "post-merge-complete",
            "purpose": "Complete the post-merge lifecycle after a PR merge.",
            "parameters": [
                {"name": "--after-pr", "required": True, "meaning": "The PR number whose merge triggered the lifecycle."},
            ],
        },
    ],
}


def render_markdown(data: dict) -> str:
    lines = [
        "# Agentic Kit Command Reference",
        "",
        "Generated from `docs/reference/agentic-kit-commands.json`.",
        "",
    ]
    for command in data["commands"]:
        full_name = f"agentic-kit {command['group']} {command['name']}"
        lines += [
            f"## `{full_name}`",
            "",
            command["purpose"],
            "",
            "| Parameter | Required | Meaning |",
            "|---|---:|---|",
        ]
        for param in command["parameters"]:
            required = "yes" if param["required"] else "no"
            lines.append(f"| `{param['name']}` | {required} | {param['meaning']} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ref_dir = Path("docs/reference")
    ref_dir.mkdir(parents=True, exist_ok=True)
    json_path = ref_dir / "agentic-kit-commands.json"
    md_path = ref_dir / "AGENTIC_KIT_COMMANDS.md"

    json_path.write_text(json.dumps(COMMAND_REFERENCE, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(COMMAND_REFERENCE), encoding="utf-8")


if __name__ == "__main__":
    main()
