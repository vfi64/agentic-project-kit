from pathlib import Path


def test_agents_md_uses_project_root_placeholder_for_next_step_setup() -> None:
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "cd <your-project-root>" in text


def test_agents_md_does_not_use_maintainer_specific_setup_path() -> None:
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit" not in text
