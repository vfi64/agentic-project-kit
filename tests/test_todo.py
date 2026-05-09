from pathlib import Path

import yaml

from agentic_project_kit.todo import complete_item, list_items, load_todo, render_markdown


def test_complete_item_updates_status_and_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    todo_dir = tmp_path / ".agentic"
    todo_dir.mkdir()
    todo_path = todo_dir / "todo.yaml"
    todo_path.write_text(
        """
items:
  - id: BOOT-001
    title: Choose license
    owner: human
    priority: high
    status: open
    evidence_required: LICENSE reviewed
""".strip()
        + "\n",
        encoding="utf-8",
    )

    item = complete_item("BOOT-001", evidence="LICENSE reviewed")

    assert item["status"] == "done"
    assert item["evidence"] == "LICENSE reviewed"
    assert "completed_at" in item

    data = yaml.safe_load(todo_path.read_text(encoding="utf-8"))
    assert data["items"][0]["status"] == "done"


def test_list_items_hides_done_by_default():
    data = {
        "items": [
            {"id": "A", "status": "done"},
            {"id": "B", "status": "open"},
        ]
    }

    assert [item["id"] for item in list_items(data)] == ["B"]
    assert [item["id"] for item in list_items(data, include_done=True)] == ["A", "B"]


def test_render_markdown_from_todo_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agentic").mkdir()
    Path(".agentic/todo.yaml").write_text(
        """
items:
  - id: BOOT-001
    title: Choose license
    owner: human
    priority: high
    status: done
    evidence_required: LICENSE reviewed
    evidence: LICENSE reviewed
""".strip()
        + "\n",
        encoding="utf-8",
    )

    text = render_markdown()

    assert "**BOOT-001** Choose license" in text
    assert "Evidence: `LICENSE reviewed`" in text
    assert Path("docs/TODO.md").exists()


def test_load_todo_requires_items_list(tmp_path):
    path = tmp_path / "todo.yaml"
    path.write_text("items: {}\n", encoding="utf-8")

    try:
        load_todo(path)
    except ValueError as exc:
        assert "items" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
