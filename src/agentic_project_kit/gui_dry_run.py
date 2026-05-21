from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Sequence

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_presenter import build_no_window_presenter_result
from agentic_project_kit.gui_layout_plan import build_layout_plan, render_layout_plan
from agentic_project_kit.gui_tkinter_renderer import render_layout_to_tkinter, render_tkinter_result_summary
from agentic_project_kit.gui_window_guard import check_window_launch_ready, render_window_guard_result
from agentic_project_kit.gui_output_status_panel import build_output_status_panel, render_output_status_panel


@dataclass(frozen=True)
class GuiDryRunResult:
    ok: bool
    tkinter_available: bool
    action_registry_available: bool
    action_specs_available: bool
    presenter_available: bool
    presenter_action_count: int
    presenter_preview: str
    mode_guard_available: bool
    shell_adapters_absent: bool
    message: str

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


class DryRunRoot:
    def __init__(self) -> None:
        self.title_value = ""
        self.geometry_value = ""

    def title(self, value: str) -> None:
        self.title_value = value

    def geometry(self, value: str) -> None:
        self.geometry_value = value


def _module_available(name: str) -> bool:
    try:
        importlib.import_module(name)
    except Exception:
        return False
    return True


def _mode_guard_available(project_root: Path) -> bool:
    ns_path = project_root / "ns"
    if not ns_path.exists():
        return False
    ns_text = ns_path.read_text(encoding="utf-8")
    return "mode-check" in ns_text and "mode-write" in ns_text


def _shell_adapters_absent(project_root: Path) -> bool:
    return not any((project_root / "tools").glob("ns_*.sh"))


def run_gui_dry_run(project_root: Path | None = None) -> GuiDryRunResult:
    root = Path.cwd() if project_root is None else project_root
    tkinter_available = _module_available("tkinter")
    action_registry_available = _module_available("agentic_project_kit.action_registry")
    action_specs_available = _module_available("agentic_project_kit.action_specs")
    mode_guard_available = _mode_guard_available(root)
    shell_adapters_absent = _shell_adapters_absent(root)
    presenter = build_no_window_presenter_result(list_actions())
    ok = all((
        action_registry_available,
        action_specs_available,
        mode_guard_available,
        shell_adapters_absent,
        presenter.ok,
    ))
    message = "GUI dry-run passed without opening a window." if ok else "GUI dry-run failed."
    return GuiDryRunResult(
        ok=ok,
        tkinter_available=tkinter_available,
        action_registry_available=action_registry_available,
        action_specs_available=action_specs_available,
        presenter_available=presenter.ok,
        presenter_action_count=presenter.action_count,
        presenter_preview=presenter.rendered,
        mode_guard_available=mode_guard_available,
        shell_adapters_absent=shell_adapters_absent,
        message=message,
    )


def render_result(result: GuiDryRunResult) -> str:
    lines = [
        "GUI DRY RUN",
        "Safety: no window is opened; no files, branches, tags, releases, PRs, or remote state are changed.",
        f"tkinter_available={str(result.tkinter_available).lower()}",
        f"window_launch_ready={str(check_window_launch_ready().ok).lower()}",
        "tkinter_note=nonblocking for --dry-run; required only for real window launch",
        f"action_registry_available={str(result.action_registry_available).lower()}",
        f"action_specs_available={str(result.action_specs_available).lower()}",
        f"presenter_available={str(result.presenter_available).lower()}",
        f"presenter_action_count={result.presenter_action_count}",
        "presenter_preview_begin",
        result.presenter_preview,
        "presenter_preview_end",
        f"mode_guard_available={str(result.mode_guard_available).lower()}",
        f"shell_adapters_absent={str(result.shell_adapters_absent).lower()}",
        f"message={result.message}",
    ]
    plan = build_layout_plan()
    rendered = render_layout_to_tkinter(DryRunRoot(), plan)
    lines.extend([
        "output_status_panel_begin",
        render_output_status_panel(
            build_output_status_panel(
                branch="dry-run",
                dirty=False,
                latest_output="GUI dry-run initialized without executing an action.",
                terminal_log="NONE",
                terminal_log_remote="NONE",
                terminal_log_local="NONE",
                evidence_state="not_required",
                summary="No command summary exists in dry-run mode.",
            )
        ),
        "output_status_panel_end",
        "layout_plan_begin",
        render_layout_plan(plan),
        "layout_plan_end",
        "tkinter_render_begin",
        render_tkinter_result_summary(rendered),
        "tkinter_render_end",
        "window_guard_begin",
        render_window_guard_result(check_window_launch_ready()),
        "window_guard_end",
        "real_window_opened=false",
        "### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###",
    ])
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
