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

