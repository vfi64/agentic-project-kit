from pathlib import Path


SRC_ROOT = Path("src/agentic_project_kit")


def typed_work_order_sources() -> list[Path]:
    direct = sorted(SRC_ROOT.glob("*typed*work*order*.py"))
    cli = sorted((SRC_ROOT / "cli_commands").glob("*work_order*.py"))
    return direct + cli


def test_typed_work_order_modules_are_present() -> None:
    sources = typed_work_order_sources()
    assert sources, "expected typed work order implementation modules"
    combined_names = "\n".join(str(path) for path in sources)
    assert "typed" in combined_names or "work_order" in combined_names


def test_typed_work_order_code_exposes_evidence_and_idempotency_terms() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in typed_work_order_sources())
    required_terms = ["evidence", "executed", "typed"]
    missing = [term for term in required_terms if term not in combined.lower()]
    assert not missing, f"missing typed work order baseline terms: {missing}"


def test_typed_work_order_has_dedicated_tests_beyond_this_baseline() -> None:
    tests = [path for path in Path("tests").glob("test_*.py") if path.name != Path(__file__).name]
    matching = []
    for path in tests:
        text = path.read_text(encoding="utf-8").lower()
        if "typed" in text and "work" in text and "order" in text:
            matching.append(path)
    assert matching, "expected at least one dedicated typed work order test file"
