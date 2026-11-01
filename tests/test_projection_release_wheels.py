"""Disposable real wheels carry independent version and activation identities."""

import zipfile


def test_source_wheels_have_explicit_a_and_b_policy(tmp_path):
    from agentic_project_kit.greenfield_projection_wheels import build_fixture_wheels

    wheels = build_fixture_wheels(tmp_path)
    for version, active in (("1.1.11", False), ("1.1.12", True), ("1.1.11.post1", False)):
        with zipfile.ZipFile(wheels[version]) as wheel:
            assert f'__version__ = "{version}"' in wheel.read("agentic_project_kit/__init__.py").decode()
            assert f"EXTERNAL_PROJECTION_V2_ACTIVE = {active}" in wheel.read("agentic_project_kit/external_projection_policy.py").decode()
            assert f"Version: {version}\n" in wheel.read(f"agentic_project_kit-{version}.dist-info/METADATA").decode()
