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
