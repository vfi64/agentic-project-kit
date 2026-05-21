from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class GuiDryRunResult:
    ok: bool
    tkinter_available: bool
    action_registry_available: bool
    action_specs_available: bool
    mode_guard_available: bool
    shell_adapters_absent: bool
    message: str

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


def _can_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except Exception:
        return False
    return True


def run_gui_dry_run(project_root: Path | None = None) -> GuiDryRunResult:
    root = Path.cwd() if project_root is None else project_root
    tkinter_available = _can_import("tkinter")
    action_registry_available = _can_import("agentic_project_kit.action_registry")
    action_specs_available = _can_import("agentic_project_kit.action_specs")
    ns_path = root / "ns"
    ns_text = ns_path.read_text(encoding="utf-8") if ns_path.exists() else ""
    mode_guard_available = "mode-check" in ns_text and "mode-write" in ns_text
    tools_dir = root / "tools"
    shell_adapters_absent = not any(tools_dir.glob("ns_*.sh")) if tools_dir.exists() else True
    ok = all((
        action_registry_available,
        action_specs_available,
        mode_guard_available,
        shell_adapters_absent,
    ))
    message = "GUI dry-run passed without opening a window." if ok else "GUI dry-run failed before window launch."
    return GuiDryRunResult(
        ok=ok,
        tkinter_available=tkinter_available,
        action_registry_available=action_registry_available,
        action_specs_available=action_specs_available,
        mode_guard_available=mode_guard_available,
        shell_adapters_absent=shell_adapters_absent,
        message=message,
    )


def render_result(result: GuiDryRunResult) -> str:
    lines = [
        "GUI DRY RUN",
        "Safety: no window is opened; no files, branches, tags, releases, PRs, or remote state are changed.",
        f"tkinter_available={str(result.tkinter_available).lower()}",
        f"window_launch_ready={str(result.tkinter_available).lower()}",
        "tkinter_note=nonblocking for --dry-run; required only for real window launch",
        f"action_registry_available={str(result.action_registry_available).lower()}",
        f"action_specs_available={str(result.action_specs_available).lower()}",
        f"mode_guard_available={str(result.mode_guard_available).lower()}",
        f"shell_adapters_absent={str(result.shell_adapters_absent).lower()}",
        f"message={result.message}",
        "### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args and args != ["--dry-run"]:
        print("ERROR: usage: python -m agentic_project_kit.gui_dry_run --dry-run")
        print("### RESULT: FAIL ###")
        return 2
    result = run_gui_dry_run()
    print(render_result(result))
    return result.exit_code


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
