from __future__ import annotations

import pytest

from agentic_project_kit.repo_identity import detect_origin_github_repo


@pytest.mark.parametrize("url_first", [False, True])
def test_origin_identity_accepts_multiple_fetch_values_without_subprocess(tmp_path, monkeypatch, url_first):
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    url = "    url = https://github.com/example/fixture.git\n"
    fetches = (
        "    fetch = +refs/heads/main:refs/remotes/origin/main\n"
        "    fetch = +refs/heads/feature/*:refs/remotes/origin/feature/*\n"
    )
    config = gitdir / "config"
    text = '[remote "origin"]\n' + (url + fetches if url_first else fetches + url)
    config.write_text(text)

    def unexpected_subprocess(*args, **kwargs):
        pytest.fail("Valid multi-valued Git config must not require a subprocess fallback")

    monkeypatch.setattr("agentic_project_kit.repo_identity.subprocess.run", unexpected_subprocess)

    assert detect_origin_github_repo(tmp_path) == "example/fixture"
    assert config.read_text() == text


def test_origin_identity_treats_percent_in_git_values_literally(tmp_path):
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    (gitdir / "config").write_text(
        '[remote "origin"]\n    url = https://github.com/example/fixture%2Dname.git\n'
    )
    assert detect_origin_github_repo(tmp_path) == "example/fixture%2Dname"

