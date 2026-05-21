from agentic_project_kit.release_publish_core import expected_confirmation, normalize_version


def test_normalize_version_accepts_plain_and_tag():
    assert normalize_version("0.3.37") == ("0.3.37", "v0.3.37")
    assert normalize_version("v0.3.37") == ("0.3.37", "v0.3.37")


def test_expected_confirmation_uses_tag():
    assert expected_confirmation("v0.3.37") == "publish-v0.3.37"
