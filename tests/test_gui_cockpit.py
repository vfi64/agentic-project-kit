import inspect
from pathlib import Path
import subprocess

from agentic_project_kit.cockpit import BOUNDED, READ_ONLY, CockpitAction, CockpitActionResult
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
from agentic_project_kit.gui_cockpit_actions import CockpitActionsMixin
from agentic_project_kit.gui_cockpit_header import CockpitHeaderMixin
from agentic_project_kit.gui_cockpit_sidebar import CockpitSidebarMixin
from agentic_project_kit.gui_cockpit_task import CockpitTaskMixin


COCKPIT_SOURCE_PATHS = (
    Path("src/agentic_project_kit/gui_cockpit.py"),
    Path("src/agentic_project_kit/gui_cockpit_header.py"),
    Path("src/agentic_project_kit/gui_cockpit_sidebar.py"),
    Path("src/agentic_project_kit/gui_cockpit_actions.py"),
    Path("src/agentic_project_kit/gui_cockpit_task.py"),
)


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
    assert "ttk.Scrollbar" in source
    assert "yscrollcommand" in source
    assert "action_card_container" in source
    assert "ttk.Treeview" not in source


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
    assert CockpitGui._build_output_panel is CockpitTaskMixin._build_output_panel


def test_cockpit_places_central_next_step_before_actions() -> None:
    source = _cockpit_sources()

    assert "self._build_next_step_panel(main_area)\n        self._build_action_cards(main_area)" in source
    assert "NEXT STEP" in source
    assert "show_next_step_details" in source
    assert "show_cockpit_help" in source
    assert "self._build_recommended_card(sidebar)" not in source


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
            "--tmp-logs",
            "--local-tmp",
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
        "--tmp-logs",
        "--local-tmp",
        "--older-than",
        "2026-06-28T21:00:00Z",
        "--execute",
        "--json",
    )
    assert gui.gc_confirm_delete_button.state == "disabled"


def test_gc_button_uses_local_modes_only() -> None:
    source = inspect.getsource(CockpitActionsMixin._gc_command_args)

    assert '"--tmp-logs"' in source
    assert '"--local-tmp"' in source
    assert "remote" not in source.lower()


def test_gc_button_tooltip_states_local_only() -> None:
    source = inspect.getsource(CockpitActionsMixin._build_action_cards)

    assert "Clean up logs" in source
    assert "Deletes local log files only" in source
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
    source = inspect.getsource(CockpitActionsMixin._build_release_creation_panel)

    assert "Create release" in source
    assert "bounded" in source
    assert "Does not publish or tag" in source


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
