from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_generator():
    path = Path("scripts/generate_agentic_kit_command_reference.py")
    spec = importlib.util.spec_from_file_location("command_reference_generator", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_agentic_kit_command_reference_is_current() -> None:
    generator = _load_generator()

    generated = generator.build_reference()
    committed = json.loads(generator.JSON_PATH.read_text(encoding="utf-8"))

    assert committed == generated
    assert generator.MD_PATH.read_text(encoding="utf-8") == generator.render_markdown(generated)

    names = {(item["group"], item["name"]) for item in generated["commands"]}
    assert ("transfer", "pr-complete") in names
    assert ("transfer", "pr-wait-ci") in names
    assert ("transfer", "pr-merge-safe") in names
    assert ("transfer", "post-merge-complete") in names

    qualified = {item["qualified_name"] for item in generated["commands"]}
    assert "agentic-kit transfer pr-complete" in qualified
    assert "agentic-kit transfer post-merge-complete" in qualified
    assert "agentic-kit release-plan" in qualified
    assert "agentic-kit release-preflight" in qualified
    assert "agentic-kit release-check" in qualified
    assert "agentic-kit release prepare" in qualified
    assert "agentic-kit release ready" in qualified
    assert "agentic-kit work start" in qualified
    assert "agentic-kit work check" in qualified
    assert "agentic-kit work finish" in qualified
    assert "agentic-kit work recover" in qualified
    assert "agentic-kit release check" not in qualified


def test_command_reference_registry_contract_exists() -> None:
    text = Path("docs/governance/COMMAND_REFERENCE_REGISTRY_CONTRACT.md").read_text(encoding="utf-8")
    assert "generated_from_typer_click_registry" in text
    assert "tests/test_agentic_kit_command_reference_is_current.py" in text
