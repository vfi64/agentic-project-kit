import subprocess
import sys
from types import SimpleNamespace

import pytest

from agentic_project_kit.gui_guided import GUIDED_TABS, GuidedKitGui, main
from agentic_project_kit.gui_cockpit import CockpitGui
from agentic_project_kit.gui_cockpit_header import CockpitHeaderMixin
from agentic_project_kit.gui_task_editor import TaskEditorState
from tests.test_gui_cockpit import (
    _FakeRoot, _FakeTkWidget, _clean_gui_gatekeeper_status, _init_git_repo,
    _install_fake_tk, _mode_option,
)


class Notebook(_FakeTkWidget):
    def add(self, widget, **kwargs):
        self.config.setdefault("tabs", []).append((widget, kwargs))

    def select(self, widget=None):
        if widget is not None:
            self.config["selection"] = widget
        return self.config.get("selection")


@pytest.fixture
def gui(monkeypatch, tmp_path):
    _install_fake_tk(monkeypatch)
    ttk = sys.modules["tkinter.ttk"]
    ttk.Notebook = Notebook
    ttk.Panedwindow = Notebook
    monkeypatch.setattr(CockpitHeaderMixin, "_start_from_ref_options", lambda self: ("latest main",))
    monkeypatch.setattr("agentic_project_kit.gui_cockpit.read_panel_state", lambda root: {})
    monkeypatch.setattr("agentic_project_kit.gui_cockpit.write_panel_state", lambda root, state: root / "panel.json")
    monkeypatch.setattr("agentic_project_kit.gui_guided.TkServiceBridge.call", lambda self, operation, **kwargs: operation())
    monkeypatch.setattr("agentic_project_kit.gui_guided.apply_guided_theme", lambda root: None)
    original_configure = _FakeTkWidget.configure

    def configure_live(widget, **kwargs):
        assert widget.exists, "Attempt to configure a destroyed widget"
        return original_configure(widget, **kwargs)

    monkeypatch.setattr(_FakeTkWidget, "configure", configure_live)
    return GuidedKitGui(_FakeRoot(), tmp_path, gatekeeper_status=_clean_gui_gatekeeper_status())


@pytest.mark.parametrize("mode", ["file_transfer", "remote", "copy_paste"])
@pytest.mark.parametrize("level", ["basic", "advanced", "maintainer"])
def test_tabs_keep_existing_actions_and_visibility(gui, mode, level):
    gui.mode_var.set(_mode_option(gui, mode))
    gui.update_mode_explanation()
    gui.access_level_var.set(level)
    gui.update_access_level()
    assert tuple(gui.tabs) == tuple(key for key, label in GUIDED_TABS)
    assert gui.communication_frame is not None
    assert gui.next_step_frame is not None
    assert gui.output_frame.winfo_exists()
    assert (gui.action_table_frame is not None) == (level != "basic")
    assert gui.task_text is not None
    assert gui.basic_view.communication_mode == mode
    assert GuidedKitGui.confirm_work_finish is CockpitGui.confirm_work_finish
    assert GuidedKitGui.confirm_create_release is CockpitGui.confirm_create_release
    assert GuidedKitGui.confirm_discard_changes is CockpitGui.confirm_discard_changes


def test_draft_survives_visibility_mode_and_panel_rebuilds(gui):
    gui.task_text.insert("1.0", "Preserve this task")
    gui.task_editor_state = TaskEditorState.SENT
    original_output = gui.output_frame
    gui.access_level_var.set("advanced")
    gui.update_access_level()
    assert gui.current_task_body() == "Preserve this task"
    assert gui.task_editor_state == TaskEditorState.SENT
    assert gui.task_text.cget("state") == "disabled"
    gui.mode_var.set(_mode_option(gui, "remote"))
    gui.update_mode_explanation()
    gui.mode_var.set(_mode_option(gui, "file_transfer"))
    gui.update_mode_explanation()
    assert gui.current_task_body() == "Preserve this task"
    assert gui.task_editor_state == TaskEditorState.SENT
    assert gui.output_frame is original_output


def test_rebuild_invalidates_all_approvals(gui):
    gui.pending_finish_preview = {"signature": "old"}
    gui.pending_discard_preview = {"signature": "old"}
    gui.pending_release_preview = {"signature": "old"}
    gui._rebuild_main_content()
    assert gui.pending_finish_preview is None
    assert gui.pending_discard_preview is None
    assert gui.pending_release_preview is None
    assert gui.work_finish_confirm_button.cget("state") == "disabled"


def test_project_switch_does_not_leak_draft_or_approval(gui, tmp_path):
    target = _init_git_repo(tmp_path / "other")
    gui.task_text.insert("1.0", "Private task in first repository")
    gui.pending_finish_preview = {"signature": "old"}
    assert gui.switch_project_root(target)
    assert gui.current_task_body() == ""
    assert gui.pending_finish_preview is None
    assert gui.project_root == target


def test_invalid_project_keeps_current_draft(gui, tmp_path):
    gui.task_text.insert("1.0", "Keep current task")
    assert not gui.switch_project_root(tmp_path / "absent")
    assert gui.current_task_body() == "Keep current task"


def test_project_switch_is_blocked_while_running(gui, tmp_path):
    gui.service_bridge.busy = True
    assert not gui.switch_project_root(tmp_path / "other")
    assert gui.project_root == tmp_path


def test_make_changes_selects_work_tab_and_focuses_editor(gui):
    gui.focus_make_changes()
    assert gui.notebook.select() is gui.tab_viewports["work"]
    assert gui.task_text.cget("focused") is True


def test_basic_diagnostics_can_be_selected_without_hidden_action_widgets(gui):
    gui._select_action("gate.doctor")
    assert gui.selected_action_id() == "gate.doctor"
    assert gui.basic_view.access_level == "basic"


def test_scroll_is_local_and_zero_delta_does_nothing(gui):
    canvas = gui.tab_canvases["work"]
    gui._scroll_tab(SimpleNamespace(delta=0, num=None), canvas)
    assert "yview_scroll" not in canvas.config
    gui._scroll_tab(SimpleNamespace(delta=-120, num=None), canvas)
    assert canvas.config["yview_scroll"] == (1, "units")
    assert "yview_scroll" not in gui.tab_canvases["standard"].config


def test_chat_handoff_uses_canonical_wrapper(gui, monkeypatch):
    calls = []
    monkeypatch.setattr(gui, "_agentic_command", lambda *args: calls.append(args) or subprocess.CompletedProcess(args, 0, "prompt", ""))
    gui.show_chat_handoff()
    assert calls == [("transfer", "chat-switch-complete", "--render-prompt")]


def test_entrypoint_passes_root_without_import_side_effects(monkeypatch, tmp_path):
    _install_fake_tk(monkeypatch)
    calls = []
    monkeypatch.setattr("agentic_project_kit.gui_guided.GuidedKitGui", lambda root, project: calls.append(project))
    main(["--root", str(tmp_path)])
    assert calls == [tmp_path]


def test_help_does_not_initialize_tk(monkeypatch):
    monkeypatch.setitem(sys.modules, "tkinter", None)
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_theme_sets_explicit_readable_tk_colors_in_dark_desktop(monkeypatch):
    from agentic_project_kit.gui_guided_theme import apply_guided_theme
    settings = {}

    class Style:
        def __init__(self, root):
            pass

        def theme_names(self):
            return ("clam", "aqua")

        def theme_use(self, name):
            settings["theme"] = name

        def configure(self, name, **kwargs):
            settings[name] = kwargs

        def map(self, name, **kwargs):
            settings[name + ".map"] = kwargs

    monkeypatch.setitem(sys.modules, "tkinter", SimpleNamespace(ttk=SimpleNamespace(Style=Style)))
    monkeypatch.setitem(sys.modules, "tkinter.ttk", SimpleNamespace(Style=Style))
    root = SimpleNamespace(option_add=lambda key, value: settings.update({key: value}))
    apply_guided_theme(root)
    assert settings["*Label.foreground"] == "#202b33"
    assert settings["*Text.background"] == "#ffffff"
    assert settings["theme"] == "clam"


@pytest.mark.parametrize("kind", ["work", "release"])
def test_failed_process_cannot_enable_confirmation_even_with_pass_payload(gui, kind):
    payload = '{"result_status":"PASS","action":"work-finish","dry_run":true,"version":"1.2.3","paths":["README.md"]}'
    completed = subprocess.CompletedProcess([], 1, payload, "process failed")
    if kind == "work":
        gui._write_work_command_result(completed, allow_confirm_from_preview=True)
        assert gui.pending_finish_preview is None
    else:
        gui._write_release_result(completed, preview=True)
        assert gui.pending_release_preview is None
    assert gui.activity_log.entries()[-1].status == "ERROR"


def test_invalid_work_output_is_error_and_clears_previous_preview(gui):
    gui.pending_finish_preview = {"signature": "old"}
    gui._write_work_command_result(subprocess.CompletedProcess([], 0, "not JSON", ""))
    assert gui.pending_finish_preview is None
    assert gui.activity_log.entries()[-1].status == "ERROR"


def test_task_staging_uses_workspace_owned_temporary_directory(gui, monkeypatch, tmp_path):
    staging = tmp_path / "owned-temp"
    monkeypatch.setattr("agentic_project_kit.gui_cockpit_task.load_workspace", lambda root: SimpleNamespace(tmp=lambda: staging))
    calls = []
    monkeypatch.setattr(gui, "_agentic_command", lambda *args: calls.append(args) or subprocess.CompletedProcess(args, 0, '{"result_status":"PASS","remote_readable":true}', ""))
    gui.task_text.insert("1.0", "bounded task")
    gui.send_user_task()
    assert (staging / "gui-task-editor-current-task.md").read_text() == "bounded task\n"
    assert str(staging / "gui-task-editor-current-task.md") in calls[0]
    assert not (tmp_path / "tmp" / "gui-task-editor-current-task.md").exists()


@pytest.mark.parametrize("kind", ["finish", "discard", "release"])
def test_repository_change_during_preview_never_enables_confirmation(gui, monkeypatch, kind):
    signatures = iter(["before", "during", "after"])
    monkeypatch.setattr(gui, "_work_cycle_signature", lambda: next(signatures))
    action = "work-finish" if kind == "finish" else "work-discard-changes"
    payload = '{"result_status":"PASS","action":"' + action + '","dry_run":true,"version":"1.2.3","paths":["README.md"]}'
    monkeypatch.setattr(gui, "_agentic_command", lambda *args: subprocess.CompletedProcess(args, 0, payload, ""))
    if kind == "finish":
        monkeypatch.setattr(gui, "_current_finish_args", lambda **kwargs: ("work", "finish", "--json"))
        gui.preview_work_finish()
        assert gui.pending_finish_preview is None
    elif kind == "discard":
        gui.preview_discard_changes()
        assert gui.pending_discard_preview is None
    else:
        monkeypatch.setattr(gui, "_current_release_version", lambda: "1.2.3")
        gui.preview_create_release()
        assert gui.pending_release_preview is None
    assert gui.activity_log.entries()[-1].status == "BLOCKED"
