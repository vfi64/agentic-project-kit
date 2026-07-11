from pathlib import Path

from agentic_project_kit.gui_tkinter_shell import (
    WORK_ORDER_STRIP_COMMAND_IDS,
    build_tkinter_shell_spec,
    build_windows_style_design_spec,
    configure_tkinter_root,
    create_tkinter_root,
    main,
    render_tkinter_shell_summary,
    run_instruction_lint_clipboard,
)
from agentic_project_kit.gui_button_catalog import (
    all_gui_buttons,
    disabled_gui_button_ids,
    enabled_gui_button_ids,
    toolbar_gui_buttons,
)



def clean_gui_gatekeeper_status():
    from agentic_project_kit.gui_gatekeeper_status import (
        GuiGatekeeperActionStatus,
        GuiGatekeeperStatus,
    )

    return GuiGatekeeperStatus(
        branch="main",
        git_dirty=False,
        workflow_state="IDLE",
        current_work_present=True,
        current_work_state="READY",
        ready_for_read_only_actions=True,
        ready_for_mutating_actions=False,
        action_statuses=(
            GuiGatekeeperActionStatus(
                action_id="doctor",
                safety_class="read-only",
                mutation_scope="none",
                enabled=True,
                reason="read-only action allowed in clean GUI gatekeeper state",
            ),
        ),
        blockers=(),
    )


class FakeRoot:
    def __init__(self):
        self.title_value = None
        self.geometry_value = None

    def title(self, value):
        self.title_value = value

    def geometry(self, value):
        self.geometry_value = value

    def minsize(self, width, height):
        self.minsize_value = (width, height)


def test_build_tkinter_shell_spec_uses_presenter_contract():
    spec = build_tkinter_shell_spec(clean_gui_gatekeeper_status())
    assert spec.title == "agentic-project-kit Cockpit"
    assert spec.status == "tkinter-shell-ready"
    assert spec.action_count >= 1
    assert spec.destructive_actions_enabled is False
    assert "agentic-project-kit Cockpit" in spec.preview


def test_configure_tkinter_root_is_testable_without_opening_window():
    spec = build_tkinter_shell_spec()
    root = FakeRoot()
    configure_tkinter_root(root, spec)
    assert root.title_value == "agentic-project-kit Cockpit"
    assert root.geometry_value == "1200x760"
    assert root.minsize_value == (950, 560)


def test_create_tkinter_root_accepts_factory_for_headless_tests():
    root = FakeRoot()
    assert create_tkinter_root(lambda: root) is root


def test_render_tkinter_shell_summary_is_deterministic():
    output = render_tkinter_shell_summary(build_tkinter_shell_spec(clean_gui_gatekeeper_status()))
    assert "TKINTER SHELL" in output
    assert "status=tkinter-shell-ready" in output
    assert "menu_count=5" in output
    assert f"toolbar_button_count={len(toolbar_gui_buttons())}" in output
    assert f"action_button_count={len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])}" in output
    assert "destructive_actions_enabled=false" in output


def test_main_no_window_smoke(capsys):
    assert main(["--no-window-smoke"]) == 0
    output = capsys.readouterr().out
    assert "TKINTER SHELL" in output
    assert "### RESULT: PASS ###" in output


def test_windows_style_design_has_menu_bar_toolbar_buttons_and_tooltips():
    design = build_windows_style_design_spec(clean_gui_gatekeeper_status())
    assert [menu.label for menu in design.menu_bar] == [
        "File",
        "Communication",
        "Gates",
        "View",
        "Help",
    ]
    assert all(button.tooltip for button in design.toolbar)
    assert all(button.tooltip for button in design.action_buttons)
    assert {button.command_id for button in design.toolbar} == {
        button.command_id for button in toolbar_gui_buttons()
    }
    assert len(design.action_buttons) == len([button for button in all_gui_buttons() if button.command_id not in WORK_ORDER_STRIP_COMMAND_IDS])
    assert set(enabled_gui_button_ids()) >= {
        "branch-status-check",
        "next-turn-status",
        "last-result",
        "handoff-check",
        "doctor",
        "check-docs",
        "docs-audit",
        "workflow-guard-check",
    }
    assert {"agent-run", "merge-if-green", "release-publish"} <= set(disabled_gui_button_ids())
    assert all(
        button.safety_class == "read-only" or button.command_id == "restore-volatile"
        for button in design.action_buttons
        if button.enabled
    )
    assert any(
        button.command_id == "restore-volatile"
        and button.safety_class == "bounded-mutation"
        and button.enabled
        for button in design.action_buttons
    )
    assert any(
        button.command_id == "release-publish" and not button.enabled
        for button in design.action_buttons
    )
    assert any(button.icon_text for button in design.toolbar)


def test_main_window_smoke_is_guarded_and_non_crashing(capsys):
    assert main(["--window-smoke"]) == 0
    output = capsys.readouterr().out
    assert "TKINTER WINDOW SMOKE" in output
    assert "GUI WINDOW GUARD" in output
    assert "real_window_opened=" in output
    assert "### RESULT: PASS ###" in output


def test_main_rejects_unknown_tkinter_shell_argument(capsys):
    assert main(["--window-smoke-like"]) == 2
    output = capsys.readouterr().out
    assert "--no-window-smoke|--window-smoke" in output
    assert "### RESULT: FAIL ###" in output


def test_window_smoke_blocks_when_tk_root_creation_fails(monkeypatch):
    from types import SimpleNamespace

    from agentic_project_kit import gui_tkinter_shell

    monkeypatch.setattr(
        gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True)
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "render_window_guard_result",
        lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true",
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "create_tkinter_root",
        lambda: (_ for _ in ()).throw(RuntimeError("no display available")),
    )
    ok, output = gui_tkinter_shell.run_window_smoke()

    assert ok is True
    assert "window_launch_ready=true" in output
    assert "window_smoke_status=BLOCKED" in output
    assert "real_window_opened=false" in output
    assert "window_closed=true" in output
    assert "window_block_reason=no display available" in output


def test_manual_launch_blocks_when_guard_blocks(monkeypatch):
    from types import SimpleNamespace
    from agentic_project_kit import gui_tkinter_shell

    monkeypatch.setattr(
        gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=False)
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "render_window_guard_result",
        lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=false",
    )
    ok, output = gui_tkinter_shell.run_manual_launch()

    assert ok is True
    assert "manual_launch_status=BLOCKED" in output
    assert "real_window_opened=false" in output
    assert "actions_enabled=false" in output


def test_manual_launch_ready_path_uses_mainloop_without_actions(monkeypatch, capsys):
    from types import SimpleNamespace
    from agentic_project_kit import gui_tkinter_shell

    class FakeRoot:
        def mainloop(self):
            return None

    monkeypatch.setattr(
        gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True)
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "render_window_guard_result",
        lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true",
    )
    monkeypatch.setattr(gui_tkinter_shell, "create_tkinter_root", lambda: FakeRoot())
    monkeypatch.setattr(gui_tkinter_shell, "configure_tkinter_root", lambda _root, _spec: None)
    monkeypatch.setattr(gui_tkinter_shell, "render_manual_launch_content", lambda _root: None)
    ok, output = gui_tkinter_shell.run_manual_launch()
    printed = capsys.readouterr().out

    assert ok is True
    assert output == "manual_launch_closed=true"
    assert "manual_launch_status=READY" in printed
    assert "actions_enabled=false" in printed
    assert "manual_close_required=true" in printed
    assert "### RESULT: PASS ###" in printed


def test_main_manual_launch_route_uses_guarded_runner(monkeypatch, capsys):
    from agentic_project_kit import gui_tkinter_shell

    monkeypatch.setattr(
        gui_tkinter_shell, "run_manual_launch", lambda: (True, "manual_launch_closed=true")
    )
    assert gui_tkinter_shell.main(["--manual-launch"]) == 0
    output = capsys.readouterr().out
    assert "manual_launch_closed=true" in output


def test_manual_launch_ready_path_renders_visible_content(monkeypatch, capsys):
    from types import SimpleNamespace
    from agentic_project_kit import gui_tkinter_shell

    calls = []

    class FakeRoot:
        def mainloop(self):
            calls.append("mainloop")

    monkeypatch.setattr(
        gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True)
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "render_window_guard_result",
        lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true",
    )
    monkeypatch.setattr(gui_tkinter_shell, "create_tkinter_root", lambda: FakeRoot())
    monkeypatch.setattr(
        gui_tkinter_shell, "configure_tkinter_root", lambda _root, _spec: calls.append("configure")
    )
    monkeypatch.setattr(
        gui_tkinter_shell,
        "render_manual_launch_content",
        lambda _root: calls.append("visible-content"),
    )

    ok, output = gui_tkinter_shell.run_manual_launch()
    printed = capsys.readouterr().out

    assert ok is True
    assert output == "manual_launch_closed=true"
    assert calls == ["configure", "visible-content", "mainloop"]
    assert "manual_launch_status=READY" in printed
    assert "actions_enabled=false" in printed


def test_manual_launch_content_uses_ttk_theme_defaults():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]
    assert "from tkinter import ttk" in manual_source
    assert "ttk.Label(" in manual_source
    assert "ttk.Button(" in manual_source
    assert "ttk.LabelFrame(" in manual_source
    assert "#f2f2f2" not in manual_source
    assert "#e6e6e6" not in manual_source
    assert "#dddddd" not in manual_source


def test_manual_launch_disabled_buttons_use_readable_theme_style():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]
    assert "ReadableDisabled.TButton" in manual_source
    assert 'style.map("ReadableDisabled.TButton"' in manual_source
    assert manual_source.count('style="ReadableDisabled.TButton"') >= 1
    assert 'state="disabled"' in manual_source


def test_cockpit_readiness_manual_gui_runner_executes_readonly_action():
    from agentic_project_kit import gui_tkinter_shell

    output = gui_tkinter_shell.run_cockpit_readiness_for_manual_gui()
    assert "action=cockpit-readiness" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "returncode=0" in output
    assert "output=cockpit-readiness: ready" in output


def test_manual_gui_keeps_remote_destructive_actions_disabled():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]
    assert "run_action_click(command_id)" in manual_source
    assert "buttons_by_category" in manual_source
    assert "agent-run" in {button.command_id for button in all_gui_buttons()}
    assert 'state="disabled"' in manual_source
    assert "remote/destructive/parameterized buttons disabled" in manual_source.lower()


def test_manual_gui_status_transition_contract_is_present():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]

    assert "def set_status(value: str) -> None:" in manual_source
    assert "def run_action_click(command_id: str) -> None:" in manual_source
    assert "Status: running | branch: main | action: {command_id}" in manual_source
    assert "Status: success | branch: main | action: {command_id}" in manual_source
    assert "Status: fail | branch: main | action: {command_id}" in manual_source
    assert "run_manual_gui_catalog_action(command_id)" in manual_source
    assert "status_text = ttk.Label" in manual_source


def test_doctor_manual_gui_runner_executes_readonly_action():
    from agentic_project_kit.gui_tkinter_shell import run_doctor_for_manual_gui

    output = run_doctor_for_manual_gui()
    assert "action=doctor" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "Agentic project doctor report" in output


def test_manual_gui_doctor_status_transition_contract_is_present():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]
    assert "doctor" in {button.command_id for button in all_gui_buttons()}
    assert "run_action_click(command_id)" in manual_source
    assert "Status: running | branch: main | action: {command_id}" in manual_source


def test_manual_gui_uses_shared_readonly_runner_abstraction():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    assert "def run_manual_gui_read_only_action(" in source
    assert "def render_gui_action_execution_result(" in source
    import ast

    tree = ast.parse(source)
    bounded_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_bounded_read_only_action"
    ]
    assert len(bounded_calls) == 2
    assert 'return run_manual_gui_catalog_action("cockpit-readiness")' in source
    assert 'return run_manual_gui_catalog_action("doctor")' in source
    assert 'return run_manual_gui_catalog_action("check-docs")' in source


def test_shared_readonly_runner_formats_single_and_multiline_output():
    from types import SimpleNamespace
    from agentic_project_kit.gui_tkinter_shell import render_gui_action_execution_result

    single = render_gui_action_execution_result(
        SimpleNamespace(
            action_name="x",
            safety_class="read_only",
            allowed=True,
            executed=True,
            returncode=0,
            message="ok",
            output="one",
        )
    )
    multi = render_gui_action_execution_result(
        SimpleNamespace(
            action_name="x",
            safety_class="read_only",
            allowed=True,
            executed=True,
            returncode=0,
            message="ok",
            output="one\ntwo",
        )
    )
    assert "output=one" in single
    assert "output_begin\none\ntwo\noutput_end" in multi


def test_check_docs_action_is_registered_readonly():
    from agentic_project_kit.action_registry import get_action

    action = get_action("check-docs")
    assert action is not None
    assert action.safety_class.value == "read-only"
    assert action.mutation_scope == "none"


def test_check_docs_manual_gui_runner_executes_readonly_action():
    from agentic_project_kit.gui_tkinter_shell import run_check_docs_for_manual_gui

    output = run_check_docs_for_manual_gui()
    assert "action=check-docs" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "returncode=0" in output
    assert "Agentic project check passed" in output


def test_manual_gui_catalog_runs_communication_buttons_readonly():
    from agentic_project_kit.gui_tkinter_shell import run_manual_gui_catalog_action

    for command_id in ("branch-status-check", "next-turn-status", "last-result", "handoff-check"):
        output = run_manual_gui_catalog_action(command_id)
        assert f"action={command_id}" in output
        assert "safety_class=read-only" in output
        assert "allowed=true" in output
        assert "executed=true" in output


def test_manual_gui_instruction_lint_clipboard_smoke_headless():
    from agentic_project_kit.command_manifest import load_manifest
    from agentic_project_kit.instruction_lint import command_manifest_ack_line

    manifest = load_manifest(Path(".").resolve())
    text = f"{command_manifest_ack_line(manifest)}\nagentic-kit transfer repo-status --json\n"

    output = run_instruction_lint_clipboard(lambda: text)

    assert "action=instruction-lint-clipboard" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "returncode=0" in output
    assert "STATUS=PASS" in output


def test_manual_gui_instruction_lint_clipboard_reports_empty_clipboard():
    output = run_instruction_lint_clipboard(lambda: "")

    assert "action=instruction-lint-clipboard" in output
    assert "executed=false" in output
    assert "returncode=1" in output
    assert "clipboard empty/unavailable" in output


def test_manual_gui_catalog_runs_work_order_validation_readonly():
    from agentic_project_kit.gui_tkinter_shell import run_manual_gui_catalog_action

    output = run_manual_gui_catalog_action("work-order-validate")

    assert "action=work-order-validate" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "WORK_ORDER_VALIDATION" in output
    assert "missing work order file" in output


def test_manual_gui_catalog_runs_work_order_runner_with_validation_block():
    from agentic_project_kit.gui_tkinter_shell import run_manual_gui_catalog_action

    output = run_manual_gui_catalog_action("work-order-run")

    assert "action=work-order-run" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "WORK_ORDER_RUN_RESULT" in output
    assert "validation_ok=false" in output


def test_manual_gui_catalog_runs_work_order_upload_with_missing_log_block(tmp_path, monkeypatch):
    import subprocess

    from agentic_project_kit.gui_tkinter_shell import run_manual_gui_catalog_action

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "README.md").write_text("repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.chdir(repo)

    output = run_manual_gui_catalog_action("work-order-upload")

    assert "action=work-order-upload" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "WORK_ORDER_UPLOAD_RESULT" in output
    assert "missing result log" in output


def test_manual_gui_catalog_blocks_planned_mutating_buttons():
    from agentic_project_kit.gui_tkinter_shell import run_manual_gui_catalog_action

    output = run_manual_gui_catalog_action("merge-if-green")
    assert "action=merge-if-green" in output
    assert "safety_class=remote-mutation" in output
    assert "allowed=false" in output
    assert "executed=false" in output
    assert "merge remains gated outside the GUI" in output


def test_manual_gui_check_docs_status_transition_contract_is_present():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[
        source.index("def render_manual_launch_content") : source.index("def run_manual_launch")
    ]
    assert "check-docs" in {button.command_id for button in all_gui_buttons()}
    assert "run_action_click(command_id)" in manual_source
    assert "Status: success | branch: main | action: {command_id}" in manual_source

def test_work_order_strip_command_ids_are_not_empty():
    from agentic_project_kit.gui_tkinter_shell import WORK_ORDER_STRIP_COMMAND_IDS

    assert WORK_ORDER_STRIP_COMMAND_IDS == (
        "work-order-show",
        "work-order-validate",
        "work-order-run",
        "work-order-upload",
    )


def test_tkinter_shell_spec_reflects_gatekeeper_dirty_blocker():
    from agentic_project_kit.gui_gatekeeper_status import GuiGatekeeperActionStatus, GuiGatekeeperStatus

    gatekeeper = GuiGatekeeperStatus(
        branch="feature/dirty",
        git_dirty=True,
        workflow_state="IDLE",
        current_work_present=True,
        current_work_state="READY",
        ready_for_read_only_actions=False,
        ready_for_mutating_actions=False,
        action_statuses=(
            GuiGatekeeperActionStatus(
                action_id="doctor",
                safety_class="read-only",
                mutation_scope="none",
                enabled=False,
                reason="read-only action blocked because working tree is dirty",
            ),
        ),
        blockers=("working tree is dirty",),
    )

    spec = build_tkinter_shell_spec(gatekeeper)

    assert spec.status == "tkinter-shell-blocked"
    assert "GUI gatekeeper blockers: working tree is dirty" in spec.preview
    doctor = next(button for button in spec.design.action_buttons if button.command_id == "doctor")
    assert doctor.enabled is False
    assert doctor.disabled_reason == "read-only action blocked because working tree is dirty"


def test_tkinter_shell_spec_keeps_readonly_enabled_when_gatekeeper_clean():
    gatekeeper = clean_gui_gatekeeper_status()

    spec = build_tkinter_shell_spec(gatekeeper)

    assert spec.status == "tkinter-shell-ready"
    doctor = next(button for button in spec.design.action_buttons if button.command_id == "doctor")
    assert doctor.enabled is True
