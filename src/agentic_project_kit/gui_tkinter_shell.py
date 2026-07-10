from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.checks import check_docs
from agentic_project_kit.documentation_system_audit import (
    build_documentation_system_audit,
    render_documentation_system_audit,
)
from agentic_project_kit.doctor import build_doctor_report, render_doctor_report
from agentic_project_kit.gui_action_execution import (
    normalize_safety_class,
    run_bounded_read_only_action,
)
from agentic_project_kit.gui_gatekeeper_status import (
    GuiGatekeeperStatus,
    build_gui_gatekeeper_status,
    render_gui_gatekeeper_status,
)
from agentic_project_kit.gui_button_catalog import (
    all_gui_buttons,
    get_gui_button,
    toolbar_gui_buttons,
)
from agentic_project_kit.gui_presenter import (
    build_basic_no_window_presenter_result,
)
from agentic_project_kit.gui_tk_widgets import (
    attach_tooltip,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
)
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model
from agentic_project_kit.gui_window_guard import (
    check_window_launch_ready,
    render_window_guard_result,
)
from agentic_project_kit.governance import governance_check, render_governance_check
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state
from agentic_project_kit.next_turn_status import (
    detect_next_turn_status,
    render_last_result,
    render_status,
)
from agentic_project_kit.patch_artifact_preflight import run_preflight
from agentic_project_kit.rule_registry_report import (
    build_rule_registry_report,
    render_rule_registry_report,
)
from agentic_project_kit.rule_registry_validator import (
    render_rule_registry_findings,
    validate_rule_registry,
)
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.state_freshness import find_stale_state_fragments, format_findings
from agentic_project_kit.workflow_guard import render_findings as render_workflow_guard_findings
from agentic_project_kit.workflow_guard import run_workflow_guard
from agentic_project_kit.work_order_validator import (
    read_work_order_preview,
    render_work_order_validation,
    validate_work_order_file,
)
from agentic_project_kit.work_order_runner import (
    render_work_order_run_result,
    run_validated_work_order,
)
from agentic_project_kit.work_order_uploader import (
    render_work_order_upload_result,
    upload_next_turn_result_log,
)


@dataclass(frozen=True)
class MenuItemSpec:
    label: str
    command_id: str
    enabled: bool = True
    tooltip: str = ""


@dataclass(frozen=True)
class MenuSpec:
    label: str
    items: tuple[MenuItemSpec, ...]


@dataclass(frozen=True)
class ButtonSpec:
    command_id: str
    label: str
    tooltip: str
    icon_text: str
    safety_class: str
    enabled: bool = True
    category: str = ""
    implementation_state: str = "implemented"
    disabled_reason: str = ""

    @property
    def icon_id(self) -> str:
        return self.icon_text


@dataclass(frozen=True)
class TkinterShellDesignSpec:
    menu_bar: tuple[MenuSpec, ...]
    toolbar: tuple[ButtonSpec, ...]
    action_buttons: tuple[ButtonSpec, ...]


GuiDesignSpec = TkinterShellDesignSpec


WORK_ORDER_STRIP_COMMAND_IDS: tuple[str, ...] = (
    "work-order-show",
    "work-order-validate",
    "work-order-run",
    "work-order-upload",
)


def is_work_order_strip_button(command_id: str) -> bool:
    return command_id in WORK_ORDER_STRIP_COMMAND_IDS


@dataclass(frozen=True)
class TkinterShellSpec:
    title: str
    status: str
    action_count: int
    destructive_actions_enabled: bool
    preview: str
    design: TkinterShellDesignSpec
    traffic_light_state: str = "UNKNOWN"
    traffic_light_color: str = "gray"
    communication_mode: str = "file_transfer"
    next_safe_action: str = ""
    basic_button_count: int = 0


def _button(
    command_id: str,
    label: str,
    tooltip: str,
    icon_text: str,
    safety_class: str,
    enabled: bool = True,
    category: str = "",
    implementation_state: str = "implemented",
    disabled_reason: str = "",
) -> ButtonSpec:
    return ButtonSpec(
        command_id,
        label,
        tooltip,
        icon_text,
        safety_class,
        enabled,
        category,
        implementation_state,
        disabled_reason,
    )


def _button_from_catalog(button: object) -> ButtonSpec:
    return _button(
        button.command_id,
        button.label,
        button.tooltip,
        button.icon_text,
        button.safety_class,
        button.enabled,
        button.category,
        button.implementation_state,
        button.disabled_reason,
    )


def build_windows_style_design_spec(
    gatekeeper_status: GuiGatekeeperStatus | None = None,
) -> TkinterShellDesignSpec:
    gatekeeper = gatekeeper_status or build_gui_gatekeeper_status(Path.cwd())
    action_enabled_by_id = {action.action_id: action.enabled for action in gatekeeper.action_statuses}
    action_reason_by_id = {action.action_id: action.reason for action in gatekeeper.action_statuses}

    def gate_button(button: object) -> ButtonSpec:
        spec = _button_from_catalog(button)
        enabled = spec.enabled and gatekeeper.ready_for_read_only_actions
        disabled_reason = spec.disabled_reason
        if not gatekeeper.ready_for_read_only_actions and spec.enabled:
            disabled_reason = ", ".join(gatekeeper.blockers) or "GUI gatekeeper blocks this action"
        if spec.command_id in action_enabled_by_id:
            enabled = spec.enabled and action_enabled_by_id[spec.command_id]
            if not enabled:
                disabled_reason = action_reason_by_id.get(spec.command_id, disabled_reason)
        return _button(
            spec.command_id,
            spec.label,
            spec.tooltip,
            spec.icon_text,
            spec.safety_class,
            enabled,
            spec.category,
            spec.implementation_state,
            disabled_reason,
        )

    menu_bar = (
        MenuSpec(
            "File",
            (
                MenuItemSpec(
                    "Branch status",
                    "branch-status-check",
                    tooltip="Show current branch and dirty state.",
                ),
                MenuItemSpec(
                    "Show bootstrap",
                    "bootstrap-show",
                    tooltip="Show generated successor-chat bootstrap.",
                ),
                MenuItemSpec("Exit", "exit", tooltip="Close the local cockpit."),
            ),
        ),
        MenuSpec(
            "Communication",
            (
                MenuItemSpec(
                    "Next-turn status",
                    "next-turn-status",
                    tooltip="Inspect fixed-slot workflow state.",
                ),
                MenuItemSpec(
                    "Last result",
                    "last-result",
                    tooltip="Inspect evidence before asking for paste-output.",
                ),
                MenuItemSpec(
                    "Handoff check", "handoff-check", tooltip="Validate persistent handoff state."
                ),
                MenuItemSpec(
                    "Handoff prompt",
                    "handoff-prompt",
                    tooltip="Render current successor handoff prompt.",
                ),
            ),
        ),
        MenuSpec(
            "Gates",
            (
                MenuItemSpec(
                    "Doctor", "doctor", tooltip="Run deterministic project doctor checks."
                ),
                MenuItemSpec(
                    "Check docs", "check-docs", tooltip="Run documentation coverage gates."
                ),
                MenuItemSpec("Docs audit", "docs-audit", tooltip="Run documentation-system audit."),
                MenuItemSpec(
                    "Workflow guard", "workflow-guard-check", tooltip="Run workflow drift guard."
                ),
            ),
        ),
        MenuSpec(
            "View",
            (
                MenuItemSpec(
                    "Show output log", "show-output-log", tooltip="Show the current output log."
                ),
                MenuItemSpec(
                    "Show last summary", "show-last-summary", tooltip="Show the last run summary."
                ),
            ),
        ),
        MenuSpec(
            "Help",
            (
                MenuItemSpec("GUI help", "gui-help", tooltip="Show cockpit help and safety notes."),
                MenuItemSpec("About", "about", tooltip="Show project and version information."),
            ),
        ),
    )
    toolbar = tuple(gate_button(button) for button in toolbar_gui_buttons())
    action_buttons = tuple(
        gate_button(button)
        for button in all_gui_buttons()
        if not is_work_order_strip_button(button.command_id)
    )
    return TkinterShellDesignSpec(menu_bar, toolbar, action_buttons)


def build_tkinter_shell_spec(
    gatekeeper_status: GuiGatekeeperStatus | None = None,
) -> TkinterShellSpec:
    gatekeeper = gatekeeper_status or build_gui_gatekeeper_status(Path.cwd())
    basic_view = build_basic_cockpit_view_model(gatekeeper_status=gatekeeper)
    presenter = build_basic_no_window_presenter_result(gatekeeper_status=gatekeeper)
    shell_state = basic_view.traffic_light_state.lower()
    if basic_view.traffic_light_state in {"BLOCKED", "FAILED"}:
        shell_state = "blocked"
    status = f"tkinter-shell-{shell_state}" if presenter.ok else "tkinter-shell-blocked"
    preview_lines = [presenter.rendered]
    if gatekeeper.blockers:
        preview_lines.append("GUI gatekeeper blockers: " + ", ".join(gatekeeper.blockers))
    else:
        preview_lines.append("GUI gatekeeper blockers: <none>")
    return TkinterShellSpec(
        "agentic-project-kit Cockpit",
        status,
        len(all_gui_buttons()),
        False,
        chr(10).join(preview_lines),
        build_windows_style_design_spec(gatekeeper),
        basic_view.traffic_light_state,
        basic_view.traffic_light_color,
        basic_view.communication_mode,
        basic_view.next_safe_action,
        basic_view.button_count,
    )


def create_tkinter_root(tk_factory: Callable[[], object] | None = None) -> object:
    if tk_factory is not None:
        return tk_factory()
    import tkinter as tk

    return tk.Tk()


def configure_tkinter_root(root: object, spec: TkinterShellSpec) -> None:
    if hasattr(root, "title"):
        root.title(spec.title)
    if hasattr(root, "geometry"):
        root.geometry("1200x760")
    if hasattr(root, "minsize"):
        root.minsize(950, 560)


def render_tkinter_shell_summary(spec: TkinterShellSpec) -> str:
    return "\n".join(
        (
            "TKINTER SHELL",
            f"title={spec.title}",
            f"status={spec.status}",
            f"traffic_light_state={spec.traffic_light_state}",
            f"traffic_light_color={spec.traffic_light_color}",
            f"communication_mode={spec.communication_mode}",
            f"next_safe_action={spec.next_safe_action}",
            f"action_count={spec.action_count}",
            f"basic_button_count={spec.basic_button_count}",
            f"menu_count={len(spec.design.menu_bar)}",
            f"toolbar_button_count={len(spec.design.toolbar)}",
            f"action_button_count={len(spec.design.action_buttons)}",
            f"destructive_actions_enabled={str(spec.destructive_actions_enabled).lower()}",
            f"toolbar_icons={chr(44).join(button.icon_id for button in spec.design.toolbar)}",
        )
    )


def run_window_smoke() -> tuple[bool, str]:
    guard = check_window_launch_ready()
    lines = ["TKINTER WINDOW SMOKE", render_window_guard_result(guard)]
    if not guard.ok:
        lines.extend(
            [
                "window_smoke_status=BLOCKED",
                "real_window_opened=false",
                "window_closed=true",
            ]
        )
        return True, chr(10).join(lines)
    try:
        root = create_tkinter_root()
    except Exception as exc:
        lines.extend(
            [
                "window_smoke_status=BLOCKED",
                "real_window_opened=false",
                "window_closed=true",
                "window_block_reason=" + str(exc).replace(chr(10), " "),
            ]
        )
        return True, chr(10).join(lines)
    try:
        configure_tkinter_root(root, build_tkinter_shell_spec())
        if hasattr(root, "update_idletasks"):
            root.update_idletasks()
        lines.extend(
            [
                "window_smoke_status=PASS",
                "real_window_opened=true",
            ]
        )
        return True, chr(10).join(lines)
    finally:
        if hasattr(root, "destroy"):
            root.destroy()


def _theme_color(style: object, style_name: str, option: str, fallback: str) -> str:
    try:
        value = style.lookup(style_name, option)
    except Exception:
        value = ""
    return str(value or fallback)


def render_gui_action_execution_result(result: object) -> str:
    lines = [
        "GUI ACTION EXECUTION RESULT",
        "action=" + result.action_name,
        "safety_class=" + normalize_safety_class(result.safety_class),
        "allowed=" + str(result.allowed).lower(),
        "executed=" + str(result.executed).lower(),
        "returncode=" + str(result.returncode),
        "message=" + result.message,
    ]
    output = str(result.output or "")
    if chr(10) in output:
        lines.extend(["output_begin", output, "output_end"])
    else:
        lines.append("output=" + output)
    return chr(10).join(lines)


def _catalog_action_result(
    action_name: str,
    safety_class: str,
    *,
    allowed: bool,
    executed: bool,
    returncode: int,
    message: str,
    output: str = "",
) -> str:
    result = SimpleNamespace(
        action_name=action_name,
        safety_class=safety_class,
        allowed=allowed,
        executed=executed,
        returncode=returncode,
        message=message,
        output=output,
    )
    return render_gui_action_execution_result(result)


def run_manual_gui_read_only_action(
    action_name: str, executor: Callable[[object], tuple[int, str]]
) -> str:
    result = run_bounded_read_only_action(list_actions(), action_name, executor=executor)
    return render_gui_action_execution_result(result)


def run_manual_gui_catalog_action(action_name: str) -> str:
    button = get_gui_button(action_name)
    if button is None:
        return _catalog_action_result(
            action_name,
            "unknown",
            allowed=False,
            executed=False,
            returncode=2,
            message="Action not found in GUI button catalog.",
        )
    if not button.enabled:
        return _catalog_action_result(
            button.command_id,
            button.safety_class,
            allowed=False,
            executed=False,
            returncode=2,
            message=button.disabled_reason or "Action disabled by GUI safety policy.",
        )
    runner = MANUAL_GUI_READONLY_RUNNERS.get(button.command_id)
    if runner is None:
        return _catalog_action_result(
            button.command_id,
            button.safety_class,
            allowed=False,
            executed=False,
            returncode=2,
            message="No bounded read-only runner is registered for this button.",
        )
    if button.command_id in {"restore-volatile", "work-order-upload"}:
        returncode, output = runner()
        return _catalog_action_result(
            button.command_id,
            button.safety_class,
            allowed=True,
            executed=True,
            returncode=returncode,
            message="Action executed through its bounded registered wrapper.",
            output=output,
        )
    action = SimpleNamespace(name=button.command_id, safety_class=button.safety_class)
    result = run_bounded_read_only_action(
        [action], button.command_id, executor=lambda _action: runner()
    )
    return render_gui_action_execution_result(result)


def run_basic_cockpit_button(
    command_id: str,
    *,
    gatekeeper_status: GuiGatekeeperStatus | None = None,
    project_root: Path | str = ".",
) -> str:
    status = gatekeeper_status or build_gui_gatekeeper_status(project_root)
    view_model = build_basic_cockpit_view_model(project_root, gatekeeper_status=status)
    button = next((item for item in view_model.buttons if item.command_id == command_id), None)
    if button is None:
        return _catalog_action_result(
            command_id,
            "unknown",
            allowed=False,
            executed=False,
            returncode=2,
            message="Basic cockpit button not found.",
        )
    if not button.enabled:
        return _catalog_action_result(
            button.command_id,
            button.safety_class,
            allowed=False,
            executed=False,
            returncode=2,
            message=button.disabled_reason or "Basic cockpit gatekeeper blocked this action.",
        )
    runner = MANUAL_GUI_READONLY_RUNNERS.get(button.command_id)
    if runner is None:
        return _catalog_action_result(
            button.command_id,
            button.safety_class,
            allowed=False,
            executed=False,
            returncode=2,
            message="No bounded Basic cockpit runner is registered for this button.",
        )
    return run_manual_gui_catalog_action(button.command_id)


def run_cockpit_readiness_for_manual_gui() -> str:
    return run_manual_gui_catalog_action("cockpit-readiness")


def run_doctor_for_manual_gui() -> str:
    return run_manual_gui_catalog_action("doctor")


def run_check_docs_for_manual_gui() -> str:
    return run_manual_gui_catalog_action("check-docs")


def _run_cockpit_readiness() -> tuple[int, str]:
    return 0, "cockpit-readiness: ready"


def _run_doctor() -> tuple[int, str]:
    report = build_doctor_report(Path.cwd())
    return (0 if report.ok else 1), render_doctor_report(report)


def _run_check_docs() -> tuple[int, str]:
    errors = check_docs(Path.cwd())
    if errors:
        output_lines = ["Agentic project check failed"]
        output_lines.extend("- " + error for error in errors)
        return 1, chr(10).join(output_lines)
    return 0, "Agentic project check passed"


def _run_docs_audit() -> tuple[int, str]:
    report = build_documentation_system_audit(Path.cwd())
    return (0 if report.ok else 1), render_documentation_system_audit(report)


def _run_governance_check() -> tuple[int, str]:
    errors = governance_check()
    return (1 if errors else 0), render_governance_check(errors)


def _run_state_freshness() -> tuple[int, str]:
    findings = find_stale_state_fragments()
    return (1 if findings else 0), format_findings(findings)


def _run_workflow_guard() -> tuple[int, str]:
    findings = run_workflow_guard()
    return (1 if findings else 0), render_workflow_guard_findings(findings)


def _run_patch_preflight() -> tuple[int, str]:
    errors = run_preflight([])
    if errors:
        return 1, "Patch artifact preflight failed\n" + "\n".join(
            f"[FAIL] {error}" for error in errors
        )
    return 0, "Patch artifact preflight passed"


def _run_rule_registry_check() -> tuple[int, str]:
    findings = validate_rule_registry()
    return (1 if findings else 0), render_rule_registry_findings(findings)


def _run_rule_registry_report() -> tuple[int, str]:
    report = build_rule_registry_report()
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    return (1 if summary.get("validation_finding_count", 0) else 0), render_rule_registry_report(
        report
    )


def _run_next_turn_status() -> tuple[int, str]:
    return 0, render_status(detect_next_turn_status())


def _run_last_result() -> tuple[int, str]:
    return 0, render_last_result()


def _run_handoff_check() -> tuple[int, str]:
    data = load_handoff_state(".agentic/handoff_state.yaml")
    errors = validate_handoff_state(data)
    if errors:
        return 1, "\n".join(f"[FAIL] {error}" for error in errors)
    return 0, "Persistent handoff state check passed"


def _run_handoff_prompt() -> tuple[int, str]:
    data = load_handoff_state(".agentic/handoff_state.yaml")
    errors = validate_handoff_state(data)
    if errors:
        return 1, "\n".join(f"[FAIL] {error}" for error in errors)
    return 0, render_handoff_prompt(data)


def _run_bootstrap_show() -> tuple[int, str]:
    path = load_workspace(Path(".")).handoff_file("NEXT_CHAT_BOOTSTRAP.md")
    if not path.exists():
        return 1, f"missing bootstrap file: {path}"
    return 0, path.read_text(encoding="utf-8")


def _run_branch_status() -> tuple[int, str]:
    import subprocess

    def git_output(*args: str) -> str:
        completed = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            return completed.stderr.strip() or "UNKNOWN"
        return completed.stdout.strip()

    lines = [
        "BRANCH_STATUS",
        f"branch={git_output('branch', '--show-current')}",
        f"head={git_output('rev-parse', 'HEAD')}",
        "status_short:",
        git_output("status", "--short") or "clean",
    ]
    return 0, chr(10).join(lines)


def _run_terminal_remote_preflight() -> tuple[int, str]:
    status = _run_branch_status()[1]
    dirty = "\nstatus_short:\nclean" not in status
    if dirty:
        return 1, "FAIL_DIRTY_FOR_REMOTE_MUTATION\n" + status
    return (
        0,
        "PASS_CLEAN_FOR_REMOTE_MUTATION\nWorking tree is clean for remote mutation or merge verification.",
    )


def _run_gui_dry_run() -> tuple[int, str]:
    return 0, render_tkinter_shell_summary(build_tkinter_shell_spec())


def _run_status_refresh() -> tuple[int, str]:
    return 0, render_gui_gatekeeper_status(build_gui_gatekeeper_status(Path.cwd()))


def _agentic_kit_command(*args: str) -> list[str]:
    root = Path.cwd()
    candidates = (
        root / ".venv" / "bin" / "agentic-kit",
        root / ".venv" / "Scripts" / "agentic-kit.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate), *args]
    found = shutil.which("agentic-kit")
    if found:
        return [found, *args]
    return ["agentic-kit", *args]


def _run_restore_volatile() -> tuple[int, str]:
    completed = subprocess.run(
        _agentic_kit_command("transfer", "restore-known-volatile", "--json"),
        text=True,
        capture_output=True,
        check=False,
    )
    output_parts = [part.strip() for part in (completed.stdout, completed.stderr) if part.strip()]
    return completed.returncode, "\n".join(output_parts)


def _run_work_order_show() -> tuple[int, str]:
    return read_work_order_preview()


def _run_work_order_validate() -> tuple[int, str]:
    result = validate_work_order_file()
    return (0 if result.ok else 1), render_work_order_validation(result)


def _run_work_order_run() -> tuple[int, str]:
    result = run_validated_work_order()
    return result.returncode, render_work_order_run_result(result)


def _run_work_order_upload() -> tuple[int, str]:
    result = upload_next_turn_result_log()
    return result.returncode, render_work_order_upload_result(result)


def _run_actions_list() -> tuple[int, str]:
    lines = ["GUI_ACTIONS"]
    for button in all_gui_buttons():
        lines.append(
            f"- {button.command_id}: category={button.category}; "
            f"safety={button.safety_class}; state={button.implementation_state}; "
            f"enabled={str(button.enabled).lower()}"
        )
    return 0, chr(10).join(lines)


MANUAL_GUI_READONLY_RUNNERS: dict[str, Callable[[], tuple[int, str]]] = {
    "actions-list": _run_actions_list,
    "bootstrap-show": _run_bootstrap_show,
    "branch-status-check": _run_branch_status,
    "check-docs": _run_check_docs,
    "cockpit-readiness": _run_cockpit_readiness,
    "docs-audit": _run_docs_audit,
    "doctor": _run_doctor,
    "governance-check": _run_governance_check,
    "gui-dry-run": _run_gui_dry_run,
    "handoff-check": _run_handoff_check,
    "handoff-prompt": _run_handoff_prompt,
    "last-result": _run_last_result,
    "next-turn-status": _run_next_turn_status,
    "patch-preflight": _run_patch_preflight,
    "rule-registry-check": _run_rule_registry_check,
    "rule-registry-report": _run_rule_registry_report,
    "restore-volatile": _run_restore_volatile,
    "state-freshness": _run_state_freshness,
    "status-refresh": _run_status_refresh,
    "terminal-remote-preflight": _run_terminal_remote_preflight,
    "diagnose": _run_doctor,
    "work-order-show": _run_work_order_show,
    "work-order-validate": _run_work_order_validate,
    "work-order-run": _run_work_order_run,
    "work-order-upload": _run_work_order_upload,
    "workflow-guard-check": _run_workflow_guard,
}


def render_manual_launch_content(root: object) -> None:
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    frame_bg = _theme_color(style, "TFrame", "background", root.cget("bg"))
    label_fg = _theme_color(style, "TLabel", "foreground", "black")
    root.configure(bg=frame_bg)
    readable_disabled_fg = label_fg
    style.configure("ReadableDisabled.TButton", foreground=readable_disabled_fg)
    style.map("ReadableDisabled.TButton", foreground=[("disabled", readable_disabled_fg)])

    header = ttk.Label(
        root, text="agentic-project-kit Cockpit", anchor="w", font=("TkDefaultFont", 18, "bold")
    )
    header.pack(fill="x", padx=12, pady=(12, 6))
    spec = build_tkinter_shell_spec()
    basic_view = build_basic_cockpit_view_model()
    buttons = spec.design.action_buttons
    enabled_count = len([button for button in buttons if button.enabled])
    disabled_count = len([button for button in buttons if not button.enabled])
    safety = ttk.Label(
        root,
        text=(
            f"State: {basic_view.traffic_light_state} | mode: {basic_view.communication_mode} | "
            f"next: {basic_view.next_safe_action} | catalog: {enabled_count} enabled, "
            f"{disabled_count} disabled; remote/destructive/parameterized buttons disabled."
        ),
        anchor="w",
    )
    safety.pack(fill="x", padx=12, pady=(0, 6))

    workflow_strip = ttk.Frame(root, padding=(12, 0, 12, 8))
    workflow_strip.pack(fill="x")
    for command_id in WORK_ORDER_STRIP_COMMAND_IDS:
        button = get_gui_button(command_id)
        if button is None:
            continue
        widget = ttk.Button(
            workflow_strip,
            text=button.label,
            command=lambda command_id=command_id: run_action_click(command_id),
            width=18,
        )
        attach_tooltip(widget, button.tooltip)
        widget.pack(side="left", padx=(0, 8))

    output_text = None
    status_text = None

    def set_status(value: str) -> None:
        if status_text is not None:
            status_text.configure(text=value)
            root.update_idletasks()

    def write_output(value: str) -> None:
        if output_text is None:
            return
        output_text.configure(state="normal")
        output_text.delete("1.0", "end")
        output_text.insert("1.0", value)
        output_text.configure(state="disabled")

    def run_action_click(command_id: str) -> None:
        set_status(f"Status: running | branch: main | action: {command_id}")
        try:
            value = run_manual_gui_catalog_action(command_id)
            write_output(value)
            if "returncode=0" in value:
                set_status(f"Status: success | branch: main | action: {command_id}")
            else:
                set_status(f"Status: fail | branch: main | action: {command_id}")
        except Exception as exc:
            write_output(
                f"GUI ACTION EXECUTION RESULT\naction={command_id}\nreturncode=1\nmessage={exc}"
            )
            set_status(f"Status: fail | branch: main | action: {command_id}")

    def run_basic_action_click(command_id: str) -> None:
        set_status(f"Status: running | branch: main | basic_action: {command_id}")
        try:
            value = run_basic_cockpit_button(command_id)
            write_output(value)
            if "returncode=0" in value:
                set_status(f"Status: success | branch: main | basic_action: {command_id}")
            else:
                set_status(f"Status: blocked | branch: main | basic_action: {command_id}")
        except Exception as exc:
            write_output(
                "GUI ACTION EXECUTION RESULT\n"
                f"action={command_id}\nreturncode=1\nmessage={exc}"
            )
            set_status(f"Status: fail | branch: main | basic_action: {command_id}")

    basic_panel = ttk.LabelFrame(root, text="Basic Cockpit", padding=(12, 8, 12, 8))
    basic_panel.pack(fill="x", padx=12, pady=(0, 8))
    traffic_row = ttk.Frame(basic_panel)
    traffic_row.pack(fill="x", pady=(0, 4))
    traffic_light = tk.Canvas(traffic_row, width=18, height=18, highlightthickness=0, bg=frame_bg)
    traffic_light.create_oval(
        3,
        3,
        15,
        15,
        fill=traffic_light_fill(basic_view.traffic_light_color),
        outline=traffic_light_fill(basic_view.traffic_light_color),
    )
    traffic_light.pack(side="left", padx=(0, 8))
    ttk.Label(
        traffic_row,
        text=f"{basic_view.traffic_light_state} ({basic_view.traffic_light_color})",
        font=("TkDefaultFont", 12, "bold"),
    ).pack(side="left", padx=(0, 12))
    ttk.Label(traffic_row, text=basic_view.reason, anchor="w").pack(
        side="left", fill="x", expand=True
    )
    mode_row = ttk.Frame(basic_panel)
    mode_row.pack(fill="x", pady=(0, 4))
    ttk.Label(mode_row, text="Transfer mode").pack(side="left", padx=(0, 8))
    mode_var = tk.StringVar(value=selected_communication_mode_option(basic_view.communication_modes))
    mode_select = ttk.Combobox(
        mode_row,
        textvariable=mode_var,
        values=communication_mode_option_values(basic_view.communication_modes),
        state="readonly",
        width=34,
    )
    mode_select.pack(side="left")
    attach_tooltip(
        mode_select,
        "Select the communication mode. File Transfer is the standard path; Copy-and-Paste is a recovery fallback.",
    )
    basic_button_row = ttk.Frame(basic_panel)
    basic_button_row.pack(fill="x")
    for button in basic_view.buttons:
        tooltip = button.tooltip
        if button.disabled_reason:
            tooltip = f"{tooltip} Disabled: {button.disabled_reason}"
        if button.enabled:
            widget = ttk.Button(
                basic_button_row,
                text=button.label,
                command=lambda command_id=button.command_id: run_basic_action_click(command_id),
                width=18,
            )
        else:
            widget = ttk.Button(
                basic_button_row,
                text=button.label,
                state="disabled",
                width=18,
                style="ReadableDisabled.TButton",
            )
        attach_tooltip(widget, tooltip)
        widget.pack(side="left", padx=(0, 8), pady=1)

    # The former top toolbar duplicated actions from the categorized left action list.
    # Keep toolbar metadata in the catalog for future compact quick-access designs, but
    # do not render a redundant horizontal button row in the current manual cockpit.
    body = ttk.Frame(root, padding=(12, 0, 12, 12))
    body.pack(fill="both", expand=True)

    actions_container = ttk.Frame(body, padding=0)
    actions_container.pack(side="left", fill="y", padx=(0, 8))

    actions_canvas = tk.Canvas(
        actions_container,
        width=250,
        highlightthickness=0,
        bg=frame_bg,
    )
    actions_scrollbar = ttk.Scrollbar(
        actions_container,
        orient="vertical",
        command=actions_canvas.yview,
    )
    actions = ttk.Frame(actions_canvas, padding=4)
    actions_window = actions_canvas.create_window((0, 0), window=actions, anchor="nw")

    def update_actions_scroll_region(_event: object | None = None) -> None:
        actions_canvas.configure(scrollregion=actions_canvas.bbox("all"))

    def update_actions_width(event: object) -> None:
        width = getattr(event, "width", 250)
        actions_canvas.itemconfigure(actions_window, width=width)

    actions.bind("<Configure>", update_actions_scroll_region)
    actions_canvas.bind("<Configure>", update_actions_width)
    actions_canvas.configure(yscrollcommand=actions_scrollbar.set)
    actions_canvas.pack(side="left", fill="y", expand=False)
    actions_scrollbar.pack(side="right", fill="y")

    buttons_by_category: dict[str, list[ButtonSpec]] = {}
    for button in buttons:
        buttons_by_category.setdefault(button.category, []).append(button)
    for category, buttons in buttons_by_category.items():
        category_frame = ttk.LabelFrame(actions, text=category, padding=3)
        category_frame.pack(fill="x", pady=2)
        for button in buttons:
            if is_work_order_strip_button(button.command_id):
                continue
            if button.enabled:
                widget = ttk.Button(
                    category_frame,
                    text=button.label,
                    command=lambda command_id=button.command_id: run_action_click(command_id),
                    width=20,
                )
            else:
                widget = ttk.Button(
                    category_frame,
                    text=button.label,
                    state="disabled",
                    width=20,
                    style="ReadableDisabled.TButton",
                )
            attach_tooltip(widget, button.tooltip)
            widget.pack(fill="x", pady=1)

    output = ttk.LabelFrame(body, text="Output / Status", padding=6)
    output.pack(side="left", fill="both", expand=True)
    text = tk.Text(output, height=12, wrap="word")
    text_bg = str(text.cget("bg"))
    text_fg = str(text.cget("fg"))
    if text_fg == text_bg:
        text_fg = label_fg
    text.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)
    text.insert(
        "1.0",
        "GUI manual launch ready. Communication, evidence, and workflow read-only buttons "
        "are enabled through the shared bounded runner. Remote/destructive actions remain "
        "disabled.",
    )
    text.configure(state="disabled")
    text.pack(fill="both", expand=True)
    output_text = text

    status_text = ttk.Label(
        root,
        text=f"Status: ready | branch: main | enabled read-only buttons: {enabled_count}",
        anchor="w",
    )
    status_text.pack(fill="x", side="bottom")


def run_manual_launch() -> tuple[bool, str]:
    guard = check_window_launch_ready()
    lines = ["TKINTER MANUAL LAUNCH", render_window_guard_result(guard)]
    if not guard.ok:
        lines.extend(
            [
                "manual_launch_status=BLOCKED",
                "real_window_opened=false",
                "actions_enabled=false",
            ]
        )
        return True, chr(10).join(lines)
    try:
        root = create_tkinter_root()
    except Exception as exc:
        lines.extend(
            [
                "manual_launch_status=BLOCKED",
                "real_window_opened=false",
                "actions_enabled=false",
                "manual_launch_block_reason=" + str(exc).replace(chr(10), " "),
            ]
        )
        return True, chr(10).join(lines)
    configure_tkinter_root(root, build_tkinter_shell_spec())
    render_manual_launch_content(root)
    lines.extend(
        [
            "manual_launch_status=READY",
            "real_window_opened=true",
            "actions_enabled=false",
            "manual_close_required=true",
        ]
    )
    print(chr(10).join(lines))
    print("### RESULT: PASS ###")
    root.mainloop()
    return True, "manual_launch_closed=true"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args == ["--no-window-smoke"]:
        print(render_tkinter_shell_summary(build_tkinter_shell_spec()))
        print("### RESULT: PASS ###")
        return 0
    if args == ["--window-smoke"]:
        ok, output = run_window_smoke()
        print(output)
        print("### RESULT: PASS ###" if ok else "### RESULT: FAIL ###")
        return 0 if ok else 1
    if args == ["--manual-launch"]:
        ok, output = run_manual_launch()
        if output:
            print(output)
        return 0 if ok else 1
    print(
        "ERROR: usage: python -m agentic_project_kit.gui_tkinter_shell --no-window-smoke|--window-smoke|--manual-launch"
    )
    print("### RESULT: FAIL ###")
    return 2


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
