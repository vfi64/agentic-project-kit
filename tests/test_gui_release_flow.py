from agentic_project_kit.gui_release_flow import (
    humanize_release_result,
    normalize_release_version,
    release_prepare_args,
    release_preview_signature,
    release_ready_args,
)


def test_release_version_normalization_accepts_x_y_z_only() -> None:
    assert normalize_release_version(" 0.5.0 ") == "0.5.0"
    assert normalize_release_version("v0.5.0") is None
    assert normalize_release_version("0.5") is None
    assert normalize_release_version("0.5.0.dev1") is None


def test_release_gui_command_args_use_existing_wrappers() -> None:
    assert release_ready_args("0.5.0") == ("release", "ready", "--version", "0.5.0", "--json")
    assert release_prepare_args("0.5.0") == (
        "release",
        "prepare",
        "--version",
        "0.5.0",
        "--write",
        "--json",
    )
    assert "publish" not in release_prepare_args("0.5.0")
    assert "tag" not in release_prepare_args("0.5.0")


def test_release_preview_signature_includes_version_and_state() -> None:
    assert release_preview_signature(version="0.5.0", state_signature="main::clean") == "0.5.0::main::clean"


def test_release_humanizer_allows_confirm_only_after_pass_preview() -> None:
    message = humanize_release_result(
        {"result_status": "PASS", "version": "0.5.0", "blockers": []},
        preview=True,
    )

    assert message.allow_confirm is True
    assert "readiness passed" in message.headline.lower()


def test_release_humanizer_blocks_failed_preview() -> None:
    message = humanize_release_result(
        {"result_status": "BLOCKED", "version": "0.5.0", "blockers": ["standard-error-scan"]},
        preview=True,
    )

    assert message.allow_confirm is False
    assert message.blockers == ("standard-error-scan",)

