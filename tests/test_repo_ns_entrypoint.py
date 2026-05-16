from pathlib import Path


def test_repo_ns_entrypoint_exists_and_is_executable() -> None:
    ns = Path("ns")
    assert ns.exists()
    assert ns.stat().st_mode & 0o111


def test_repo_ns_entrypoint_delegates_to_next_step() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "tools/next-step.py" in text
    assert "\"$@\"" in text
    assert ".venv/bin/python" in text


def test_repo_ns_menu_exists_and_is_executable() -> None:
    menu = Path("ns-menu")
    assert menu.exists()
    assert menu.stat().st_mode & 0o111


def test_repo_ns_menu_exposes_expected_shortcuts_without_heredocs() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "#!/usr/bin/env zsh" in text
    assert "./ns state" in text
    assert "./ns list" in text
    assert "./ns show" in text
    assert "./ns run <work-item-name>" in text
    assert "./ns upload" in text
    assert "./ns fail" in text
    assert "./ns cleanup" in text
    assert "<<" not in text
    assert "python -c" not in text



def test_repo_ns_entrypoint_exposes_cockpit_shortcuts() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "agentic-kit cockpit status" in text
    assert "agentic-kit cockpit actions" in text


def test_repo_ns_menu_exposes_cockpit_shortcuts_without_heredocs() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "./ns cockpit" in text
    assert "./ns actions" in text
    assert "run_ns cockpit" in text
    assert "run_ns actions" in text
    assert "<<" not in text
    assert "python -c" not in text
