import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys
import types

from agentic_project_kit.cockpit import BOUNDED, READ_ONLY, CockpitAction, CockpitActionResult
from agentic_project_kit.gui_activity_log import normalize_activity_status
from agentic_project_kit.gui_cockpit import (
    CockpitGui,
    HEADER_TEXT,
    THEME,
    action_tree_columns,
    action_tree_tag_colors,
    action_tree_visible_rows,
    build_gui_action_views,
    explain_safety,
    format_action_details,
    format_action_result,
    main,
)
from agentic_project_kit.gui_cockpit_common import build_collapsible_group
from agentic_project_kit.gui_cockpit_actions import CockpitActionsMixin
from agentic_project_kit.gui_cockpit_header import CockpitHeaderMixin
from agentic_project_kit.gui_cockpit_sidebar import CockpitSidebarMixin
from agentic_project_kit.gui_cockpit_task import CockpitTaskMixin
from agentic_project_kit.gui_panel_state import PANEL_STATE_RELATIVE_PATH, read_panel_state, write_panel_state
from agentic_project_kit.gui_open_folder import open_folder_in_file_manager


COCKPIT_SOURCE_PATHS = (
    Path("src/agentic_project_kit/gui_cockpit.py"),
    Path("src/agentic_project_kit/gui_cockpit_header.py"),
    Path("src/agentic_project_kit/gui_cockpit_sidebar.py"),
    Path("src/agentic_project_kit/gui_cockpit_actions.py"),
    Path("src/agentic_project_kit/gui_cockpit_task.py"),
)
COMMUNICATION_MODE_IDS = ("file_transfer", "remote", "copy_paste")
ACCESS_LEVELS = ("basic", "advanced", "maintainer")
GUI_VISIBILITY_GROUPS = (
    "work_cycle",
    "communication",
    "next_step",
    "task_editor",
    "action_table",
    "advanced_tools",
    "file_browser",
    "copy_paste_tools",
    "output",
)


class _FakeStringVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class _FakeTkWidget:
    def __init__(self, master: object | None = None, **kwargs: object) -> None:
        self.master = master
        self.children: list[_FakeTkWidget] = []
        self.mapped = False
        self.exists = True
        self.text_content = ""
        self.config: dict[str, object] = dict(kwargs)
        self.bindings: dict[str, object] = {}
        self.pack_kwargs: dict[str, object] = {}
        self.grid_kwargs: dict[str, object] = {}
        self.created_windows: dict[int, dict[str, object]] = {}
        if hasattr(master, "children"):
            master.children.append(self)  # type: ignore[attr-defined]

    def pack(self, **kwargs: object) -> None:
        self.pack_kwargs = dict(kwargs)
        self.mapped = True

    def grid(self, **kwargs: object) -> None:
        self.grid_kwargs = dict(kwargs)
        self.mapped = True

    def pack_forget(self) -> None:
        self.mapped = False

    def pack_propagate(self, _flag: bool) -> None:
        return

    def bind(self, event: str, callback: object) -> None:
        self.bindings[event] = callback

    def __getitem__(self, key: str) -> object:
        return self.config.get(key, "")

    def configure(self, **kwargs: object) -> None:
        self.config.update(kwargs)

    def cget(self, key: str) -> object:
        return self.config.get(key, "")

    def columnconfigure(self, *_args: object, **_kwargs: object) -> None:
        return

    def destroy(self) -> None:
        self.exists = False
        self.mapped = False
        for child in self.children:
            child.destroy()

    def winfo_children(self) -> list["_FakeTkWidget"]:
        return [child for child in self.children if child.exists]

    def winfo_exists(self) -> int:
        return int(self.exists)

    def winfo_ismapped(self) -> int:
        return int(self.mapped)

    def winfo_screenwidth(self) -> int:
        return 1400

    def winfo_screenheight(self) -> int:
        return 900

    def winfo_reqwidth(self) -> int:
        return 240

    def winfo_reqheight(self) -> int:
        return 80

    def winfo_rootx(self) -> int:
        return 0

    def winfo_rooty(self) -> int:
        return 0

    def winfo_height(self) -> int:
        return 20

    def title(self, value: str) -> None:
        self.config["title"] = value

    def geometry(self, value: str) -> None:
        self.config["geometry"] = value

    def minsize(self, width: int, height: int) -> None:
        self.config["minsize"] = (width, height)

    def withdraw(self) -> None:
        return

    def update(self) -> None:
        return

    def update_idletasks(self) -> None:
        return

    def clipboard_clear(self) -> None:
        self.config["clipboard"] = ""

    def clipboard_append(self, text: str) -> None:
        self.config["clipboard"] = text

    def create_rectangle(self, *_args: object, **_kwargs: object) -> int:
        return 1

    def create_oval(self, *_args: object, **_kwargs: object) -> int:
        return 1

    def create_window(self, *_args: object, **kwargs: object) -> int:
        window_id = len(self.created_windows) + 1
        self.created_windows[window_id] = dict(kwargs)
        return window_id

    def itemconfigure(self, item: int, **kwargs: object) -> None:
        self.created_windows.setdefault(item, {}).update(kwargs)
        return

    def bbox(self, *_args: object) -> tuple[int, int, int, int]:
        return (0, 0, 100, 100)

    def yview(self, *_args: object) -> None:
        return

    def yview_scroll(self, units: int, what: str) -> None:
        self.config["yview_scroll"] = (units, what)

    def yview_moveto(self, fraction: float) -> None:
        self.config["yview_moveto"] = fraction

    def set(self, *_args: object) -> None:
        return

    def start(self, *_args: object) -> None:
        self.config["started"] = True

    def stop(self) -> None:
        self.config["started"] = False

    def insert(self, _index: object, text: str) -> None:
        self.text_content += text

    def delete(self, *_args: object) -> None:
        self.text_content = ""

    def get(self, *_args: object) -> str:
        return self.text_content

    def see(self, *_args: object) -> None:
        return

    def curselection(self) -> tuple[int, ...]:
        return ()

    def focus_set(self) -> None:
        self.config["focused"] = True


class _FakeRoot(_FakeTkWidget):
    pass


def _install_fake_tk(monkeypatch) -> None:
    ttk = types.SimpleNamespace(
        Button=_FakeTkWidget,
        Combobox=_FakeTkWidget,
        Entry=_FakeTkWidget,
        Progressbar=_FakeTkWidget,
        Scrollbar=_FakeTkWidget,
        Separator=_FakeTkWidget,
    )
    fake_tk = types.SimpleNamespace(
        Tk=_FakeRoot,
        Toplevel=_FakeTkWidget,
        Frame=_FakeTkWidget,
        Canvas=_FakeTkWidget,
        Label=_FakeTkWidget,
        Button=_FakeTkWidget,
        Text=_FakeTkWidget,
        Listbox=_FakeTkWidget,
        StringVar=_FakeStringVar,
        ttk=ttk,
        BOTH="both",
        X="x",
        Y="y",
        LEFT="left",
        RIGHT="right",
        TOP="top",
        VERTICAL="vertical",
        HORIZONTAL="horizontal",
        WORD="word",
        GROOVE="groove",
        FLAT="flat",
        NORMAL="normal",
        DISABLED="disabled",
        W="w",
        E="e",
        NW="nw",
        ALL="all",
    )
    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    monkeypatch.setitem(sys.modules, "tkinter.ttk", ttk)


def _mode_option(gui: CockpitGui, mode_id: str) -> str:
    mode = next(mode for mode in gui.basic_view.communication_modes if mode.mode_id == mode_id)
    return f"{mode.label}: {mode.role}"


def _build_headless_cockpit(
    monkeypatch,
    *,
    communication_mode: str,
    access_level: str,
    panel_state: dict[str, bool] | None = None,
) -> CockpitGui:
    _install_fake_tk(monkeypatch)
    monkeypatch.setattr(CockpitHeaderMixin, "_start_from_ref_options", lambda _self: ("latest main",))
    state = dict(panel_state or {})
    monkeypatch.setattr("agentic_project_kit.gui_cockpit.read_panel_state", lambda _root: dict(state))

    def write_state(_root: Path, new_state: dict[str, bool]) -> Path:
        state.clear()
        state.update(new_state)
        return Path("tmp/gui-panel-state.json")

    monkeypatch.setattr("agentic_project_kit.gui_cockpit.write_panel_state", write_state)
    root = _FakeRoot()
    gui = CockpitGui(root, project_root=Path("."))
    gui.mode_var.set(_mode_option(gui, communication_mode))
    gui.update_mode_explanation()
    gui.access_level_var.set(access_level)
    gui.update_access_level()
    return gui


def _group_is_visible(gui: CockpitGui, group_id: str) -> bool:
    frame = gui.gui_group_frames.get(group_id)
    return bool(frame is not None and frame.winfo_exists() and frame.winfo_ismapped())


def _group_is_expanded(gui: CockpitGui, group_id: str) -> bool:
    return bool(getattr(gui, f"{group_id}_expanded", False))


def _visibility_matrix_expected() -> dict[tuple[str, str], dict[str, bool]]:
    expected: dict[tuple[str, str], dict[str, bool]] = {}
    for mode in COMMUNICATION_MODE_IDS:
        for level in ACCESS_LEVELS:
            advanced = level in {"advanced", "maintainer"}
            expected[(mode, level)] = {
                "work_cycle": True,
                "communication": True,
                "next_step": True,
                "task_editor": True,
                "action_table": advanced,
                "advanced_tools": advanced,
                "file_browser": advanced,
                "copy_paste_tools": True,
                "output": True,
            }
    return expected


def test_visibility_matrix_covers_all_nine_combinations() -> None:
    expected = _visibility_matrix_expected()

    assert len(expected) == 9
    assert set(expected) == {
        (mode, level) for mode in COMMUNICATION_MODE_IDS for level in ACCESS_LEVELS
    }


def test_gui_builds_headless_for_every_mode_and_level(monkeypatch) -> None:
    for mode in COMMUNICATION_MODE_IDS:
        for level in ACCESS_LEVELS:
            gui = _build_headless_cockpit(monkeypatch, communication_mode=mode, access_level=level)

            assert gui.basic_view.communication_mode == mode
            assert gui.basic_view.access_level == level


def test_visibility_matrix_core_groups_always_visible(monkeypatch) -> None:
    for mode in COMMUNICATION_MODE_IDS:
        for level in ACCESS_LEVELS:
            gui = _build_headless_cockpit(monkeypatch, communication_mode=mode, access_level=level)

            for group_id in ("work_cycle", "communication", "next_step", "task_editor", "output"):
                assert _group_is_visible(gui, group_id), (mode, level, group_id)


def test_visibility_matrix_basic_hides_advanced_groups(monkeypatch) -> None:
    for mode in COMMUNICATION_MODE_IDS:
        gui = _build_headless_cockpit(monkeypatch, communication_mode=mode, access_level="basic")

        for group_id in ("action_table", "advanced_tools", "file_browser"):
            assert not _group_is_visible(gui, group_id), (mode, "basic", group_id)


def test_visibility_matrix_advanced_shows_advanced_groups(monkeypatch) -> None:
    for mode in COMMUNICATION_MODE_IDS:
        for level in ("advanced", "maintainer"):
            gui = _build_headless_cockpit(monkeypatch, communication_mode=mode, access_level=level)

            assert _group_is_visible(gui, "action_table"), (mode, level, "action_table")
            assert _group_is_visible(gui, "advanced_tools"), (mode, level, "advanced_tools")
            assert _group_is_visible(gui, "file_browser"), (mode, level, "file_browser")


def test_visibility_matrix_matches_expected_default_state(monkeypatch) -> None:
    expected = _visibility_matrix_expected()

    for (mode, level), matrix in expected.items():
        gui = _build_headless_cockpit(monkeypatch, communication_mode=mode, access_level=level)
        actual = {group_id: _group_is_visible(gui, group_id) for group_id in GUI_VISIBILITY_GROUPS}

        assert actual == matrix


def test_collapsible_group_toggles_content_not_titlebar(monkeypatch) -> None:
    _install_fake_tk(monkeypatch)
    calls: list[str] = []
    root = _FakeRoot()

    group = build_collapsible_group(
        root,
        group_id="task_editor",
        title="Task",
        expanded=False,
        on_toggle=lambda group_id: calls.append(group_id),
    )

    assert group.frame.winfo_ismapped()
    assert group.titlebar.winfo_ismapped()
    assert not group.body.winfo_ismapped()
    button = group.titlebar.winfo_children()[0]
    button.config["command"]()
    assert calls == ["task_editor"]


def test_mode_file_transfer_expands_task_editor_by_default(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")

    assert _group_is_expanded(gui, "task_editor")
    assert not _group_is_expanded(gui, "copy_paste_tools")


def test_mode_copy_paste_expands_copy_paste_tools_by_default(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="copy_paste", access_level="basic")

    assert not _group_is_expanded(gui, "task_editor")
    assert _group_is_expanded(gui, "copy_paste_tools")


def test_mode_remote_collapses_task_and_copy_paste_by_default(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="remote", access_level="basic")

    assert not _group_is_expanded(gui, "task_editor")
    assert not _group_is_expanded(gui, "copy_paste_tools")


def test_user_override_persists_to_tmp_file(tmp_path: Path) -> None:
    target = write_panel_state(tmp_path, {"task_editor": False, "copy_paste_tools": True})

    assert target == tmp_path / PANEL_STATE_RELATIVE_PATH
    assert read_panel_state(tmp_path) == {"copy_paste_tools": True, "task_editor": False}


def test_user_override_uses_manifest_tmp_namespace(tmp_path: Path) -> None:
    manifest = tmp_path / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )

    target = write_panel_state(tmp_path, {"task_editor": True})

    assert target == tmp_path / ".agentic/tmp/gui-panel-state.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["state_path"] == ".agentic/tmp/gui-panel-state.json"
    assert read_panel_state(tmp_path) == {"task_editor": True}


def test_user_override_survives_mode_change(monkeypatch) -> None:
    gui = _build_headless_cockpit(
        monkeypatch,
        communication_mode="remote",
        access_level="basic",
        panel_state={"task_editor": True},
    )

    assert _group_is_expanded(gui, "task_editor")
    gui.mode_var.set(_mode_option(gui, "copy_paste"))
    gui.update_mode_explanation()

    assert _group_is_expanded(gui, "task_editor")
    assert _group_is_expanded(gui, "copy_paste_tools")


def test_persisted_state_restored_on_rebuild(monkeypatch) -> None:
    gui = _build_headless_cockpit(
        monkeypatch,
        communication_mode="file_transfer",
        access_level="basic",
        panel_state={"task_editor": False, "copy_paste_tools": True},
    )

    assert not _group_is_expanded(gui, "task_editor")
    assert _group_is_expanded(gui, "copy_paste_tools")


def test_corrupt_panel_state_file_does_not_crash(tmp_path: Path) -> None:
    path = tmp_path / PANEL_STATE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    assert read_panel_state(tmp_path) == {}


def test_access_level_existence_unchanged(monkeypatch) -> None:
    basic = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    advanced = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="advanced")

    assert not _group_is_visible(basic, "advanced_tools")
    assert not _group_is_visible(basic, "file_browser")
    assert _group_is_visible(advanced, "advanced_tools")
    assert _group_is_visible(advanced, "file_browser")


def test_access_level_change_rebuilds_right_pane_visibility(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")

    assert not _group_is_visible(gui, "action_table")
    assert not _group_is_visible(gui, "advanced_tools")

    gui.access_level_var.set("advanced")
    gui.update_access_level()

    assert gui.basic_view.access_level == "advanced"
    assert _group_is_visible(gui, "action_table")
    assert _group_is_visible(gui, "advanced_tools")

    gui.access_level_var.set("basic")
    gui.update_access_level()

    assert gui.basic_view.access_level == "basic"
    assert not _group_is_visible(gui, "action_table")
    assert not _group_is_visible(gui, "advanced_tools")


def _cockpit_sources() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in COCKPIT_SOURCE_PATHS)


class _FakeVar:
    def __init__(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class _FakeButton:
    def __init__(self) -> None:
        self.state = "disabled"

    def configure(self, **kwargs: object) -> None:
        if "state" in kwargs:
            self.state = str(kwargs["state"])


class _GcHarness(CockpitActionsMixin):
    def __init__(self) -> None:
        self.gc_cutoff_var = _FakeVar("2026-06-28T21:00:00Z")
        self.gc_confirm_delete_button = _FakeButton()
        self.pending_gc_preview = None
        self.calls: list[tuple[str, ...]] = []
        self.output: list[str] = []

    def _agentic_command(self, *parts: str) -> subprocess.CompletedProcess[str]:
        self.calls.append(parts)
        payload = (
            '{"candidate_count": 1, "dry_run": true, "result_status": "PASS"}'
            if "--execute" not in parts
            else '{"candidate_count": 1, "dry_run": false, "result_status": "PASS"}'
        )
        return subprocess.CompletedProcess(parts, 0, payload, "")

    def write_output(self, text: str) -> None:
        self.output.append(text)


class _ReleaseHarness(CockpitActionsMixin):
    def __init__(self) -> None:
        self.release_version_var = _FakeVar("0.5.0")
        self.release_confirm_button = _FakeButton()
        self.pending_release_preview = None
        self.calls: list[tuple[str, ...]] = []
        self.output: list[str] = []
        self.signature = "main::clean"

    def _agentic_command(self, *parts: str) -> subprocess.CompletedProcess[str]:
        self.calls.append(parts)
        if parts[:2] == ("release", "ready"):
            return subprocess.CompletedProcess(
                parts,
                0,
                '{"action": "release-ready", "result_status": "PASS", "version": "0.5.0", "blockers": []}',
                "",
            )
        if parts[:2] == ("release", "prepare"):
            return subprocess.CompletedProcess(
                parts,
                0,
                '{"action": "release-prepare", "result_status": "PASS", "version": "0.5.0", "blockers": []}',
                "",
            )
        return subprocess.CompletedProcess(parts, 2, "", "unexpected command")

    def _work_cycle_signature(self) -> str:
        return self.signature

    def write_output(self, text: str) -> None:
        self.output.append(text)


class _HelpHarness(CockpitActionsMixin):
    def __init__(self) -> None:
        self.output: list[str] = []

    def write_output(self, text: str) -> None:
        self.output.append(text)


def test_gui_action_views_reuse_cockpit_action_metadata() -> None:
    actions = [
        CockpitAction(
            "demo.status",
            "Demo status",
            "demo",
            ("demo", "status"),
            READ_ONLY,
            "Inspect demo state.",
            "Inspect demo state",
        ),
        CockpitAction(
            "demo.go",
            "Demo go",
            "demo",
            ("demo", "go"),
            BOUNDED,
            "Run bounded demo step.",
            "Run demo step",
        ),
    ]

    views = build_gui_action_views(actions)

    assert views[0].action_id == "demo.status"
    assert views[0].label == "Demo status"
    assert views[0].command == ("demo", "status")
    assert views[0].short_description == "Inspect demo state"
    assert views[0].can_run_by_default is True
    assert views[1].action_id == "demo.go"
    assert views[1].safety == BOUNDED
    assert views[1].can_run_by_default is False


def test_gui_action_views_include_existing_registry_actions() -> None:
    views = build_gui_action_views()
    ids = {view.action_id for view in views}

    assert "git.status" in ids
    assert "workflow.go" in ids
    workflow_go = next(view for view in views if view.action_id == "workflow.go")
    assert workflow_go.can_run_by_default is False


def test_format_action_result_includes_safety_and_output_fields() -> None:
    result = CockpitActionResult(
        action_id="git.status",
        allowed=True,
        executed=True,
        returncode=0,
        stdout="clean\n",
        stderr="",
        message="Cockpit action executed.",
    )

    text = format_action_result(result)

    assert "action_id=git.status" in text
    assert "allowed=true" in text
    assert "executed=true" in text
    assert "returncode=0" in text
    assert "Cockpit action executed." in text
    assert "stdout:" in text
    assert "clean" in text


def test_format_action_result_preserves_blocked_action_message() -> None:
    result = CockpitActionResult(
        action_id="workflow.go",
        allowed=False,
        executed=False,
        returncode=None,
        stdout="",
        stderr="",
        message="Blocked bounded cockpit action without explicit allow flag: workflow.go",
    )

    text = format_action_result(result)

    assert "allowed=false" in text
    assert "executed=false" in text
    assert "returncode=None" in text
    assert "Blocked bounded cockpit action" in text


def test_gui_module_main_is_importable_without_starting_tk() -> None:
    assert callable(main)


def test_basic_cockpit_window_uses_option_menu_traffic_light_and_tooltips() -> None:
    init_source = _cockpit_sources()

    assert "ttk.Combobox" in init_source
    assert "create_oval" in init_source
    assert "traffic_light_fill" in init_source
    assert "attach_tooltip" in init_source
    assert "[x]" not in init_source


def test_gui_tests_do_not_require_project_root_mutation(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    build_gui_action_views([])
    after = sorted(tmp_path.iterdir())

    assert after == before




def test_explain_safety_distinguishes_default_and_blocked_actions() -> None:
    assert "Safe default" in explain_safety(READ_ONLY)
    assert "Blocked by default" in explain_safety(BOUNDED)
    assert "Blocked" in explain_safety("destructive")
    assert "unknown safety class" in explain_safety("mystery")


def test_format_action_details_includes_clear_safety_explanation() -> None:
    action = CockpitAction(
        "demo.go",
        "Demo go",
        "demo",
        ("demo", "go"),
        BOUNDED,
        "Run bounded demo step.",
        "Run demo step",
    )
    view = build_gui_action_views([action])[0]
    text = format_action_details(view)
    assert "action_id=demo.go" in text
    assert "short_description=Run demo step" in text
    assert "can_run_by_default=false" in text
    assert "safety_explanation=Blocked by default" in text


def test_format_action_result_marks_blocked_status_explicitly() -> None:
    result = CockpitActionResult("workflow.go", False, False, None, "", "", "Blocked bounded cockpit action without explicit allow flag: workflow.go")
    text = format_action_result(result)
    assert "status=blocked" in text
    assert "allowed=false" in text
    assert "executed=false" in text


def test_gui_basic_cockpit_header_text_is_project_specific() -> None:
    assert HEADER_TEXT == "Agentic Project Kit — Cockpit"


def test_gui_action_cards_are_four_rows_and_scrollable() -> None:
    source = _cockpit_sources()

    assert action_tree_visible_rows() == 4
    assert THEME.action_card_height == 23
    assert THEME.action_scrollbar_width == 18
    assert "THEME.action_list_width" in source
    assert "action_list_height = THEME.action_rows_visible * THEME.action_card_height" in source
    assert "action_shell_width = THEME.action_list_width + THEME.action_scrollbar_width" in source
    assert "height=action_list_height" in source
    assert "ttk.Scrollbar" in source
    assert "yscrollcommand" in source
    assert "_bind_action_card_scroll_events" in source
    assert "action_card_container" in source
    assert "ttk.Treeview" not in source


def test_cockpit_tk_widgets_do_not_use_parent_keyword() -> None:
    source = _cockpit_sources()

    forbidden = (
        "tk.Frame(parent=",
        "tk.Canvas(parent=",
        "tk.Label(parent=",
        "tk.Button(parent=",
        "tk.Text(parent=",
        "tk.Listbox(parent=",
    )
    for fragment in forbidden:
        assert fragment not in source


def test_cockpit_gui_composes_focused_mixins() -> None:
    assert issubclass(CockpitGui, CockpitHeaderMixin)
    assert issubclass(CockpitGui, CockpitSidebarMixin)
    assert issubclass(CockpitGui, CockpitActionsMixin)
    assert issubclass(CockpitGui, CockpitTaskMixin)


def test_cockpit_build_methods_live_in_focused_modules() -> None:
    assert CockpitGui._build_header is CockpitHeaderMixin._build_header
    assert CockpitGui._build_work_cycle_bar is CockpitHeaderMixin._build_work_cycle_bar
    assert CockpitGui._build_sidebar is CockpitSidebarMixin._build_sidebar
    assert CockpitGui._build_next_step_panel is CockpitActionsMixin._build_next_step_panel
    assert CockpitGui._build_action_cards is CockpitActionsMixin._build_action_cards
    assert CockpitGui._build_task_editor is CockpitTaskMixin._build_task_editor
    assert CockpitGui._build_copy_paste_tools is CockpitTaskMixin._build_copy_paste_tools
    assert CockpitGui._build_file_browser is CockpitTaskMixin._build_file_browser
    assert CockpitGui._build_output_panel is CockpitTaskMixin._build_output_panel


def test_cockpit_places_central_next_step_before_actions() -> None:
    source = inspect.getsource(CockpitGui._build_main_content)
    all_sources = _cockpit_sources()

    assert "self._build_primary_status_row(self.main_area)" in source
    assert "if self._advanced_access_visible():" in source
    assert "self._build_action_cards(self.main_area)" in source
    assert source.index("self._build_primary_status_row(self.main_area)") < source.index("if self._advanced_access_visible():")
    assert "NEXT STEP" in all_sources
    assert "show_next_step_details" in all_sources
    assert "show_cockpit_help" in all_sources
    assert "self._build_recommended_card(sidebar)" not in all_sources


def test_cockpit_places_communication_and_next_step_in_two_columns(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")

    assert getattr(gui.communication_frame.master, "_primary_status_column") == "communication"
    assert getattr(gui.next_step_frame.master, "_primary_status_column") == "next_step"
    assert gui.communication_frame.master.grid_kwargs["column"] == 0
    assert gui.next_step_frame.master.grid_kwargs["column"] == 1


def test_cockpit_primary_status_cards_expand_to_equal_column_height(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")

    assert gui.communication_frame.pack_kwargs["fill"] == "both"
    assert gui.communication_frame.pack_kwargs["expand"] is True
    assert gui.next_step_frame.pack_kwargs["fill"] == "both"
    assert gui.next_step_frame.pack_kwargs["expand"] is True


def test_advanced_action_cards_keep_visible_scroll_container_height(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="advanced")

    assert gui.action_scroll_shell.config["width"] == THEME.action_list_width + THEME.action_scrollbar_width
    assert gui.action_scroll_shell.config["height"] == THEME.action_rows_visible * THEME.action_card_height
    assert gui.action_card_canvas.config["width"] == THEME.action_list_width
    assert gui.action_card_canvas.config["height"] == THEME.action_rows_visible * THEME.action_card_height
    assert gui.action_scroll_shell.pack_kwargs["fill"] == "both"


def test_advanced_action_cards_support_separate_mousewheel_scrolling(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="advanced")

    for event_name in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        assert event_name in gui.action_card_canvas.bindings
        assert event_name in gui.action_card_container.bindings
        assert event_name in next(iter(gui.action_card_widgets.values())).bindings

    assert gui._on_action_card_mousewheel(types.SimpleNamespace(delta=-120, num=None)) == "break"
    assert gui.action_card_canvas.config["yview_scroll"] == (1, "units")


def test_cockpit_main_area_is_vertically_scrollable_and_output_reachable() -> None:
    source = _cockpit_sources()

    assert "main_canvas" in source
    assert "main_scrollbar" in source
    assert "self._build_task_editor(self.main_area)\n        self._build_copy_paste_tools(self.main_area)\n        self._build_output_panel(self.main_area)" in source


def test_basic_view_hides_action_table_and_advanced_tools() -> None:
    source = inspect.getsource(CockpitGui._build_main_content)

    assert "if self._advanced_access_visible():" in source
    assert "self._build_action_cards(self.main_area)" in source
    assert "self._build_advanced_tools(self.main_area)" in source
    assert source.index("if self._advanced_access_visible():") < source.index("self._build_task_editor")


def test_basic_view_shows_work_cycle_communication_task_and_output() -> None:
    source = _cockpit_sources()

    assert "self._build_work_cycle_bar(shell)" in source
    assert "self._build_primary_status_row(self.main_area)" in source
    assert "self._build_communication_panel(communication_column)" in source
    assert "self._build_next_step_panel(next_step_column)" in source
    assert "self._build_task_editor(self.main_area)" in source
    assert "self._build_copy_paste_tools(self.main_area)" in source
    assert "self._build_output_panel(self.main_area)" in source


def test_advanced_view_shows_action_table() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_action_cards)

    assert "Advanced: individual actions" in source
    assert "Inspect" in source
    assert "Run read-only" in source


def test_inspect_button_bound_to_inspect_selected() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_action_cards)

    assert 'text="Inspect"' in source
    assert "command=self.inspect_selected" in source


def test_advanced_tools_start_collapsed() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_advanced_tools)

    assert 'group_id="advanced_tools"' in source
    assert "self._build_collapsible_group" in source
    assert "advanced_tools_expanded" not in _cockpit_sources()


def test_cockpit_file_browser_is_read_only_for_tmp_and_handoff_files() -> None:
    source = _cockpit_sources()

    assert "COPY / PASTE FILES" in source
    assert "read-only local browser" in source
    assert "load_workspace" in source
    assert "workspace.tmp()" in source
    assert "workspace.handoff_dir()" in source
    assert "workspace.handoff_packages_latest()" in source
    assert "Copy path" in source
    assert "Copy file" in source
    assert "delete" not in inspect.getsource(CockpitTaskMixin._build_file_browser).lower()


def test_cockpit_output_header_has_busy_feedback() -> None:
    source = _cockpit_sources()

    assert "busy_status_var" in source
    assert "ttk.Progressbar" in source
    assert "Running:" in source


def _walk_widgets(widget: _FakeTkWidget) -> list[_FakeTkWidget]:
    found = [widget]
    for child in widget.winfo_children():
        found.extend(_walk_widgets(child))
    return found


def test_user_action_entry_rendered_right_aligned(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.log_action("Check")

    widgets = _walk_widgets(gui.activity_container)
    user_bubbles = [widget for widget in widgets if getattr(widget, "_activity_actor", "") == "user"]
    assert user_bubbles
    assert any(getattr(widget, "_activity_anchor", "") == "e" for widget in user_bubbles)
    assert any(widget.pack_kwargs.get("side") == "right" for widget in user_bubbles)


def test_kit_result_entry_rendered_left_with_status_badge(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.log_result("Check", "PASS", "result_status=PASS")

    widgets = _walk_widgets(gui.activity_container)
    kit_bubbles = [widget for widget in widgets if getattr(widget, "_activity_actor", "") == "kit"]
    badges = [widget for widget in widgets if getattr(widget, "_activity_status_badge", "") == "PASS"]
    assert kit_bubbles
    assert any(getattr(widget, "_activity_anchor", "") == "w" for widget in kit_bubbles)
    assert any(widget.pack_kwargs.get("side") == "left" for widget in kit_bubbles)
    assert badges


def test_each_result_entry_has_its_own_copy_button(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.log_result("First", "INFO", "first body")
    gui.log_result("Second", "INFO", "second body")

    copy_buttons = [widget for widget in _walk_widgets(gui.activity_container) if hasattr(widget, "_activity_copy_body")]
    assert [button._activity_copy_body for button in copy_buttons] == ["first body", "second body"]


def test_copy_button_copies_only_that_entry_body(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.log_result("First", "INFO", "first body")
    gui.log_result("Second", "INFO", "second body")
    copy_buttons = [widget for widget in _walk_widgets(gui.activity_container) if hasattr(widget, "_activity_copy_body")]

    copy_buttons[1].config["command"]()

    assert gui.root.config["clipboard"] == "second body"


def test_explicit_status_takes_precedence_over_heuristic() -> None:
    assert normalize_activity_status("PASS", "Traceback: boom") == "PASS"


def test_heuristic_status_used_only_without_explicit_status() -> None:
    assert normalize_activity_status(None, "Traceback: boom") == "ERROR"
    assert normalize_activity_status("", "result_status=PASS") == "PASS"


def test_open_logs_folder_targets_tmp_dir(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    captured: list[Path] = []
    monkeypatch.setattr("agentic_project_kit.gui_cockpit_task.open_folder_in_file_manager", captured.append)

    gui.open_logs_folder()

    assert captured == [Path(".").resolve() / "tmp"]
    assert gui.activity_log.entries()[-1].body == "Opened logs folder: tmp/"


def test_open_folder_helper_platform_dispatch(monkeypatch, tmp_path: Path) -> None:
    subprocess_calls: list[tuple[str, ...]] = []
    windows_calls: list[str] = []
    monkeypatch.setattr(
        "agentic_project_kit.gui_open_folder.subprocess.run",
        lambda command, check: subprocess_calls.append(tuple(command)),
    )
    monkeypatch.setattr(
        "agentic_project_kit.gui_open_folder.os.startfile",
        lambda path: windows_calls.append(str(path)),
        raising=False,
    )

    monkeypatch.setattr("agentic_project_kit.gui_open_folder.sys.platform", "darwin")
    open_folder_in_file_manager(tmp_path / "mac")
    monkeypatch.setattr("agentic_project_kit.gui_open_folder.sys.platform", "win32")
    open_folder_in_file_manager(tmp_path / "win")
    monkeypatch.setattr("agentic_project_kit.gui_open_folder.sys.platform", "linux")
    open_folder_in_file_manager(tmp_path / "linux")

    assert subprocess_calls[0] == ("open", str(tmp_path / "mac"))
    assert windows_calls == [str(tmp_path / "win")]
    assert subprocess_calls[1] == ("xdg-open", str(tmp_path / "linux"))


def test_clear_empties_log_and_view(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()
    gui.log_result("Check", "PASS", "body")

    gui.clear_activity_log()

    assert gui.activity_log.entries() == ()
    assert gui.activity_container.winfo_children() == []


def test_existing_messages_still_appear_as_entries(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.write_output("legacy text")

    assert gui.activity_log.entries()[-1].body == "legacy text"


def test_activity_log_headless_scrollregion_is_set(monkeypatch) -> None:
    gui = _build_headless_cockpit(monkeypatch, communication_mode="file_transfer", access_level="basic")
    gui.clear_activity_log()

    gui.log_action("Check")
    gui.log_result("Check", "PASS", "done")

    assert gui.activity_canvas.config["scrollregion"] == (0, 0, 100, 100)
    assert gui.activity_canvas.config["yview_moveto"] == 1.0


def test_cockpit_help_placeholder_points_to_authoritative_sources() -> None:
    gui = _HelpHarness()

    gui.show_cockpit_help()

    text = "".join(gui.output)
    assert "under construction" in text.lower()
    assert "https://github.com/vfi64/agentic-project-kit" in text
    assert "10.5281/zenodo.20101359" in text
    assert "10.5281/zenodo.20917074" in text
    assert "Volker Fickert" in text


def test_gc_button_runs_dry_run_first() -> None:
    gui = _GcHarness()

    gui.preview_log_cleanup()

    assert gui.calls == [
        (
            "artifact-gc",
            "--local-tmp-contents",
            "--older-than",
            "2026-06-28T21:00:00Z",
            "--json",
        )
    ]
    assert "--execute" not in gui.calls[0]
    assert gui.gc_confirm_delete_button.state == "normal"


def test_gc_confirm_only_after_preview() -> None:
    gui = _GcHarness()

    gui.confirm_log_cleanup()
    assert gui.calls == []

    gui.preview_log_cleanup()
    gui.confirm_log_cleanup()

    assert gui.calls[1] == (
        "artifact-gc",
        "--local-tmp-contents",
        "--older-than",
        "2026-06-28T21:00:00Z",
        "--execute",
        "--json",
    )
    assert gui.gc_confirm_delete_button.state == "disabled"


def test_gc_button_uses_local_modes_only() -> None:
    source = inspect.getsource(CockpitActionsMixin._gc_command_args)

    assert '"--local-tmp-contents"' in source
    assert "remote" not in source.lower()


def test_gc_button_tooltip_states_local_only() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_release_and_cleanup_tools)

    assert "Clean local tmp" in source
    assert "Deletes local tmp/ candidates only" in source
    assert "Never touches the remote repository" in source


def test_create_release_rejects_invalid_version_format() -> None:
    gui = _ReleaseHarness()
    gui.release_version_var.set("0.5")

    gui.preview_create_release()

    assert gui.calls == []
    assert gui.release_confirm_button.state == "disabled"
    assert any("X.Y.Z" in line for line in gui.output)


def test_create_release_runs_readiness_check_first() -> None:
    gui = _ReleaseHarness()

    gui.preview_create_release()

    assert gui.calls == [("release", "ready", "--version", "0.5.0", "--json")]
    assert gui.release_confirm_button.state == "normal"


def test_create_release_confirm_only_after_successful_preview() -> None:
    gui = _ReleaseHarness()

    gui.confirm_create_release()
    assert gui.calls == []

    gui.preview_create_release()
    gui.confirm_create_release()

    assert gui.calls[1] == (
        "release",
        "prepare",
        "--version",
        "0.5.0",
        "--write",
        "--json",
    )


def test_create_release_confirm_blocked_when_version_changed_after_preview() -> None:
    gui = _ReleaseHarness()

    gui.preview_create_release()
    gui.release_version_var.set("0.6.0")
    gui.confirm_create_release()

    assert gui.calls == [("release", "ready", "--version", "0.5.0", "--json")]
    assert gui.release_confirm_button.state == "disabled"
    assert any("Version or state changed" in line for line in gui.output)


def test_create_release_does_not_publish_or_tag() -> None:
    gui = _ReleaseHarness()

    gui.preview_create_release()
    gui.confirm_create_release()

    flat = " ".join(part for call in gui.calls for part in call)
    assert "publish" not in flat
    assert "tag" not in flat


def test_create_release_button_is_bounded_class() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_release_and_cleanup_tools)

    assert "Create release" in source
    assert "Confirm create release" in source
    assert "_build_release_creation_panel" not in _cockpit_sources()


def test_discard_is_advanced_destructive_tool_not_work_cycle_button() -> None:
    header_source = inspect.getsource(CockpitHeaderMixin._build_work_cycle_bar)
    advanced_source = inspect.getsource(CockpitActionsMixin._build_discard_tools)

    assert "Discard all changes" not in header_source
    assert "DESTRUCTIVE" in advanced_source
    assert "Discard all changes" in advanced_source
    assert "Confirm discard" in advanced_source


def test_show_how_it_works_renders_walkthrough_and_example_for_selected_mode() -> None:
    source = inspect.getsource(CockpitSidebarMixin.show_communication_walkthrough)

    assert "communication_mode_walkthrough_steps(selected)" in source
    assert "communication_mode_example(selected)" in source
    assert "HOW IT WORKS" in source


def test_mode_change_updates_explanation_and_next_step_together() -> None:
    source = inspect.getsource(CockpitSidebarMixin.update_mode_explanation)

    assert "self.mode_explanation_var.set(communication_mode_explanation(selected))" in source
    assert "self.mode_next_step_var.set(communication_mode_next_step_hint(selected))" in source
    assert "self.mode_example_var.set(communication_mode_example(selected))" in source


def test_access_level_still_does_not_override_safety_gating() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_discard_tools)
    confirm_source = inspect.getsource(CockpitHeaderMixin.confirm_discard_changes)

    assert "state=tk.NORMAL if self._discard_available() else tk.DISABLED" in source
    assert "--execute" in confirm_source
    assert "expected-signature" in confirm_source


def test_create_release_starts_with_version_dialog() -> None:
    source = inspect.getsource(CockpitActionsMixin.start_create_release)

    assert "simpledialog.askstring" in source
    assert "Enter target version" in source
    assert "self.preview_create_release()" in source


def test_gui_cockpit_header_importable_without_tkinter(monkeypatch) -> None:
    module_name = "_agentic_project_kit_gui_cockpit_header_without_tkinter_probe"
    module_path = Path("src/agentic_project_kit/gui_cockpit_header.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "tkinter", None)
    monkeypatch.setitem(sys.modules, module_name, module)

    spec.loader.exec_module(module)

    assert hasattr(module, "CockpitHeaderMixin")


def test_gui_output_uses_readable_large_font_and_panel_height() -> None:
    assert THEME.output_height == 20
    assert THEME.output_font == ("TkFixedFont", 10)
    assert THEME.body_font == ("TkDefaultFont", 10)


def test_gui_theme_action_rows_visible() -> None:
    assert THEME.action_rows_visible == 4


def test_action_tree_hides_raw_command_column() -> None:
    assert action_tree_columns() == ("action", "what_it_does", "safety")
    assert "command" not in action_tree_columns()


def test_action_tree_has_safety_color_tags() -> None:
    assert action_tree_tag_colors() == {
        "read_only": THEME.color_read_only,
        "bounded": THEME.color_bounded,
        "destructive": THEME.color_destructive,
    }
