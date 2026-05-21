from agentic_project_kit.gui_tkinter_shell import (
    build_tkinter_shell_spec,
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
    assert root.geometry_value == "900x600"


def test_create_tkinter_root_accepts_factory_for_headless_tests():
    root = FakeRoot()
    assert create_tkinter_root(lambda: root) is root


def test_render_tkinter_shell_summary_is_deterministic():
    output = render_tkinter_shell_summary(build_tkinter_shell_spec())
    assert "TKINTER SHELL" in output
    assert "status=tkinter-shell-ready" in output
    assert "destructive_actions_enabled=false" in output


def test_main_no_window_smoke(capsys):
    assert main(["--no-window-smoke"]) == 0
    output = capsys.readouterr().out
    assert "TKINTER SHELL" in output
    assert "### RESULT: PASS ###" in output
