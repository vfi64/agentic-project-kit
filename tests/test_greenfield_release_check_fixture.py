import pytest
import yaml
from agentic_project_kit.greenfield_retest_release_check import (
    FIXTURE,
    guard_index,
    release_effects,
)


def test_only_loopback_fixture_can_classify_optional_network_reads_as_local():
    status = {"path": ["kit", "status"], "remote_effects": ["network_read"]}
    update = {"path": ["kit", "update"], "remote_effects": ["network_read"]}
    assert release_effects("agentic-kit kit status --json", status) == ["none"]
    assert release_effects("agentic-kit kit status --check-release --json", status) == [
        "network_read"
    ]
    assert release_effects("agentic-kit kit status --check-release --json", status, FIXTURE) == [
        "none"
    ]
    assert release_effects("agentic-kit kit update --latest --json", update, FIXTURE) == ["none"]
    for flags in ["--latest --execute", "--version 1.1.8", "--latest --root /another"]:
        assert release_effects("agentic-kit kit update " + flags, update, FIXTURE) == [
            "network_read"
        ]


@pytest.mark.parametrize("change", ["index", "interpreter", "execute", "root", "offline_root", "route"])
def test_loopback_fixture_refuses_changed_bindings_or_effectful_commands(tmp_path, change):
    config = {"kit": {"interpreter": "owned-python", "index_url": "http://127.0.0.1:1234/simple"}}
    path = tmp_path / ".agentic/config.yaml"
    path.parent.mkdir()
    argv = ["agentic-kit", "kit", "update", "--latest", "--json"]
    if change == "index":
        config["kit"]["index_url"] = "https://example.invalid/simple"
    if change == "interpreter":
        config["kit"]["interpreter"] = "another-python"
    if change == "execute":
        argv.append("--execute")
    if change == "root":
        argv += ["--root", "/another"]
    if change == "offline_root":
        argv = ["agentic-kit", "kit", "status", "--root", "/another", "--json"]
    if change == "route":
        argv = ["agentic-kit", "release-publish"]
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError):
        guard_index(tmp_path, "owned-python", "http://127.0.0.1:1234/simple", argv)
