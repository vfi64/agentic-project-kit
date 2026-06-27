from pathlib import Path

from agentic_project_kit.cockpit import BOUNDED, READ_ONLY, CockpitAction, CockpitActionResult
from agentic_project_kit.gui_cockpit import (
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
    source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")
    init_source = source[source.index("class CockpitGui") :]

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
    source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")

    assert action_tree_visible_rows() == 4
    assert "ttk.Scrollbar" in source
    assert "yscrollcommand" in source
    assert "action_card_container" in source
    assert "ttk.Treeview" not in source


def test_gui_output_uses_readable_large_font_and_panel_height() -> None:
    assert THEME.output_height == 9
    assert THEME.output_font == ("TkFixedFont", 13)


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
