from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
import importlib
from pathlib import Path

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_presenter import build_no_window_presenter_result
from agentic_project_kit.gui_action_execution import run_bounded_read_only_action
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

# GUI_EXECUTION_RESULT_WIRING_OVERRIDE_BEGIN
_run_gui_dry_run_base = run_gui_dry_run
_render_result_base = render_result

def run_gui_dry_run(project_root: Path | None = None, *, action_name: str | None = None):
    base_result = _run_gui_dry_run_base(project_root)
    if not action_name:
        return base_result
    execution_result = run_bounded_read_only_action(list_actions(), action_name)
    return SimpleNamespace(base_result=base_result, execution_result=execution_result)

def render_result(result) -> str:
    base_result = getattr(result, "base_result", result)
    output = _render_result_base(base_result)
    execution = getattr(result, "execution_result", None)
    if execution is None:
        return output
    lines = output.splitlines()
    safety_class = str(getattr(execution.safety_class, "value", execution.safety_class)).strip().lower().replace("_", "-").rsplit(".", 1)[-1]
    execution_lines = [
        "execution_result_begin",
        "GUI ACTION EXECUTION RESULT",
        f"action={execution.action_name}",
        f"safety_class={safety_class}",
        f"allowed={str(execution.allowed).lower()}",
        f"executed={str(execution.executed).lower()}",
        f"returncode={execution.returncode}",
        f"message={execution.message}",
        f"output={execution.output}",
        "execution_result_end",
    ]
    if "real_window_opened=false" in lines:
        index = lines.index("real_window_opened=false")
        lines[index:index] = execution_lines
    else:
        lines.extend(execution_lines)
    return chr(10).join(lines)

def _render_help() -> str:
    return chr(10).join([
        "usage: ./ns gui [--dry-run] [--action ACTION_NAME]",
        "Safety: help only; no window is opened and no action is executed.",
        "options:",
        "  --help, -h              Show this help and exit successfully.",
        "  --dry-run               Render the no-window GUI dry-run.",
        "  --action ACTION_NAME    Include a bounded action execution result.",
        "### RESULT: PASS ###",
    ])


def main(argv: list[str] | None = None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    action_name = None
    if args in (["--help"], ["-h"]):
        print(_render_help())
        return 0
    if args == ["--dry-run"]:
        args = []
    if args:
        if len(args) == 2 and args[0] == "--action":
            action_name = args[1]
        else:
            print("usage: ./ns gui [--dry-run] [--action ACTION_NAME]")
            print("### RESULT: FAIL ###")
            return 2
    print(render_result(run_gui_dry_run(action_name=action_name)))
    return 0
# GUI_EXECUTION_RESULT_WIRING_OVERRIDE_END

if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
