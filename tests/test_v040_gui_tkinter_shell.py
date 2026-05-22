from agentic_project_kit.gui_tkinter_shell import (
    build_tkinter_shell_spec,
    build_windows_style_design_spec,
    configure_tkinter_root,
    create_tkinter_root,
    main,
    render_tkinter_shell_summary,
)


class FakeRoot:
    def __init__(self):
        self.title_value = None
        self.geometry_value = None

    def title(self, value):
        self.title_value = value

    def geometry(self, value):
        self.geometry_value = value


def test_build_tkinter_shell_spec_uses_presenter_contract():
    spec = build_tkinter_shell_spec()
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
    assert root.geometry_value == "1000x650"


def test_create_tkinter_root_accepts_factory_for_headless_tests():
    root = FakeRoot()
    assert create_tkinter_root(lambda: root) is root


def test_render_tkinter_shell_summary_is_deterministic():
    output = render_tkinter_shell_summary(build_tkinter_shell_spec())
    assert "TKINTER SHELL" in output
    assert "status=tkinter-shell-ready" in output
    assert "menu_count=4" in output
    assert "toolbar_button_count=" in output
    assert "action_button_count=" in output
    assert "destructive_actions_enabled=false" in output


def test_main_no_window_smoke(capsys):
    assert main(["--no-window-smoke"]) == 0
    output = capsys.readouterr().out
    assert "TKINTER SHELL" in output
    assert "### RESULT: PASS ###" in output


def test_windows_style_design_has_menu_bar_toolbar_buttons_and_tooltips():
    design = build_windows_style_design_spec()
    assert [menu.label for menu in design.menu_bar] == ["File", "Actions", "View", "Help"]
    assert all(button.tooltip for button in design.toolbar)
    assert all(button.tooltip for button in design.action_buttons)
    assert {button.command_id for button in design.toolbar} >= {"refresh-status", "doctor", "check-docs", "gui-dry-run"}
    assert any(button.command_id == "release-publish" and not button.enabled for button in design.action_buttons)
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

    monkeypatch.setattr(gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True))
    monkeypatch.setattr(gui_tkinter_shell, "render_window_guard_result", lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true")
    monkeypatch.setattr(gui_tkinter_shell, "create_tkinter_root", lambda: (_ for _ in ()).throw(RuntimeError("no display available")))
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

    monkeypatch.setattr(gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=False))
    monkeypatch.setattr(gui_tkinter_shell, "render_window_guard_result", lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=false")
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

    monkeypatch.setattr(gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True))
    monkeypatch.setattr(gui_tkinter_shell, "render_window_guard_result", lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true")
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

    monkeypatch.setattr(gui_tkinter_shell, "run_manual_launch", lambda: (True, "manual_launch_closed=true"))
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

    monkeypatch.setattr(gui_tkinter_shell, "check_window_launch_ready", lambda: SimpleNamespace(ok=True))
    monkeypatch.setattr(gui_tkinter_shell, "render_window_guard_result", lambda _guard: "GUI WINDOW GUARD" + chr(10) + "window_launch_ready=true")
    monkeypatch.setattr(gui_tkinter_shell, "create_tkinter_root", lambda: FakeRoot())
    monkeypatch.setattr(gui_tkinter_shell, "configure_tkinter_root", lambda _root, _spec: calls.append("configure"))
    monkeypatch.setattr(gui_tkinter_shell, "render_manual_launch_content", lambda _root: calls.append("visible-content"))

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
    manual_source = source[source.index("def render_manual_launch_content"):source.index("def run_manual_launch")]
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
    manual_source = source[source.index("def render_manual_launch_content"):source.index("def run_manual_launch")]
    assert "ReadableDisabled.TButton" in manual_source
    assert "style.map(\"ReadableDisabled.TButton\"" in manual_source
    assert manual_source.count("style=\"ReadableDisabled.TButton\"") >= 2
    assert "state=\"disabled\"" in manual_source


def test_cockpit_readiness_manual_gui_runner_executes_readonly_action():
    from agentic_project_kit import gui_tkinter_shell
    output = gui_tkinter_shell.run_cockpit_readiness_for_manual_gui()
    assert "action=cockpit-readiness" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "returncode=0" in output
    assert "output=cockpit-readiness: ready" in output


def test_manual_gui_keeps_only_cockpit_readiness_enabled():
    from pathlib import Path
    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[source.index("def render_manual_launch_content"):source.index("def run_manual_launch")]
    assert "command=run_cockpit_readiness_click" in manual_source
    assert "agent-run" in manual_source
    assert "state=\"disabled\"" in manual_source
    assert "remote/destructive actions remain disabled" in manual_source.lower()



def test_manual_gui_status_transition_contract_is_present():
    from pathlib import Path

    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")
    manual_source = source[source.index("def render_manual_launch_content"):source.index("def run_manual_launch")]

    assert "def set_status(value: str) -> None:" in manual_source
    assert "def run_cockpit_readiness_click() -> None:" in manual_source
    assert "Status: running | branch: main | action: cockpit-readiness" in manual_source
    assert "Status: success | branch: main | action: cockpit-readiness" in manual_source
    assert "Status: fail | branch: main | action: cockpit-readiness" in manual_source
    assert "command=run_cockpit_readiness_click" in manual_source
    assert "status_text = ttk.Label" in manual_source
