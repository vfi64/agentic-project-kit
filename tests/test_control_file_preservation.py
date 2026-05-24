from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".agentic" / "control_file_preservation.yaml"


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_control_file_preservation_manifest_is_parseable_and_strict() -> None:
    data = _load_manifest()
    policy = data["policy"]
    assert policy["rule_id"] == "control-file-preservation"
    assert policy["no_hard_length_limit"] is True
    assert "Information preservation outranks compactness" in policy["length_policy"]
    assert "hard_length_limit_trimming" in policy["forbidden_mutation_modes"]


def test_protected_control_files_have_no_hard_length_limits() -> None:
    data = _load_manifest()
    protected = data["protected_files"]
    assert protected
    for entry in protected:
        assert entry["no_hard_length_limit"] is True
        assert entry["preservation_mode"] == "additive_or_explicit_migration"
        assert (ROOT / entry["path"]).exists(), entry["path"]


def test_protected_control_file_anchors_are_present() -> None:
    data = _load_manifest()
    for entry in data["protected_files"]:
        text = _read_text(entry["path"])
        for anchor in entry["required_anchors"]:
            assert anchor in text, f"missing preserved anchor {anchor!r} in {entry['path']}"


def test_control_file_migration_requires_explicit_successor_and_test() -> None:
    data = _load_manifest()
    requirements = data["migration_requirements"]["removed_anchor_requires"]
    assert requirements == [
        "removed_anchor",
        "successor_anchor",
        "rationale",
        "deterministic_test",
        "reviewer_visible_summary",
    ]
    assert "explicit successor" in data["migration_requirements"]["deletion_is_valid_only_if"]
