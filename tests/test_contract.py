from pathlib import Path

from agentic_project_kit.contract import (
    build_contract_data,
    contract_summary,
    default_profiles,
    recommended_policy_packs,
    render_contract_yaml,
    validate_project_contract,
    load_project_contract,
)


def test_default_profiles_keep_python_as_profile_not_core():
    assert default_profiles("python-cli", github_actions=True) == (
        "generic-git-repo",
        "markdown-docs",
        "python-cli",
        "git-github",
    )
    assert default_profiles("generic", github_actions=False) == (
        "generic-git-repo",
        "markdown-docs",
    )


def test_recommended_policy_packs_are_contextual():
    assert recommended_policy_packs(
        "python-cli",
        github_actions=True,
        logging_evidence=True,
    ) == ("starter", "solo-maintainer", "agentic-development")
    assert recommended_policy_packs(
        "generic",
        github_actions=False,
        logging_evidence=False,
    ) == ("starter", "solo-maintainer", "documentation-governed")


def test_contract_roundtrip_and_summary(tmp_path: Path):
    data = build_contract_data(
        name="demo",
        description="Demo",
        project_type="python-cli",
        profiles=("generic-git-repo", "python-cli"),
        policy_packs=("starter", "solo-maintainer"),
    )
    assert validate_project_contract(data) == []
    assert "profiles: generic-git-repo, python-cli" in contract_summary(data)

    path = tmp_path / ".agentic"
    path.mkdir()
    (path / "project.yaml").write_text(render_contract_yaml(data), encoding="utf-8")
    loaded = load_project_contract(tmp_path)
    assert loaded == data


def test_contract_validation_rejects_unknown_ids():
    data = build_contract_data(
        name="demo",
        description="Demo",
        project_type="python-cli",
        profiles=("unknown-profile",),
        policy_packs=("unknown-policy",),
    )

    errors = validate_project_contract(data)

    assert "unknown profile: unknown-profile" in errors
    assert "unknown policy pack: unknown-policy" in errors
