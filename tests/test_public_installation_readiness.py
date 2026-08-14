from pathlib import Path

import yaml


def test_release_workflow_prepares_gated_trusted_publishing_without_token_secret() -> None:
    text = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "publish_target:" in text
    assert "twine check dist/*" in text
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "repository-url: https://test.pypi.org/legacy/" in text
    assert "PYPI_TRUSTED_PUBLISHING_ENABLED" in text
    assert "id-token: write" in text
    assert "secrets.PYPI_TOKEN" not in text
    assert "password:" not in text


def test_public_installation_docs_do_not_claim_current_pypi_install() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("site/templates/quickstart.html").read_text(encoding="utf-8")
    index = Path("site/templates/index.html").read_text(encoding="utf-8")
    claims = Path("site/templates/claims.html").read_text(encoding="utf-8")

    source_install = "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
    templated_source_install = "${package_name} @ git+${repository_url}.git@main"

    assert source_install in readme
    assert templated_source_install in quickstart
    assert templated_source_install in index
    assert "The public PyPI package is not published yet" in readme
    assert "Direct PyPI installation is planned, not claimed yet" in quickstart
    assert "Direct PyPI installation is not claimed until PyPI package availability evidence is verified." in claims


def test_site_claims_track_source_install_and_planned_pypi_publication() -> None:
    data = yaml.safe_load(Path("site/content/claims.yaml").read_text(encoding="utf-8"))
    claims = {claim["id"]: claim for claim in data["claims"]}

    assert claims["public-source-install-documented"]["required"] is True
    assert claims["pypi-trusted-publishing-ready"]["required"] is False
    assert claims["pypi-package-installable"]["planned"] is True


def test_dockerfile_supports_local_source_image_contract() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "git" in dockerfile
    assert "gh" in dockerfile
    assert "openssh-client" in dockerfile
    assert "python -m pip install ." in dockerfile
    assert 'ENTRYPOINT ["agentic-kit"]' in dockerfile
    assert "USER kit" in dockerfile


def test_selfhosting_manifest_is_upgraded_to_current_schema_with_backup() -> None:
    manifest = yaml.safe_load(Path(".agentic/config.yaml").read_text(encoding="utf-8"))
    backup = yaml.safe_load(Path(".agentic/config.yaml.bak.v1").read_text(encoding="utf-8"))

    assert manifest["kit_schema_version"] == 2
    assert backup["kit_schema_version"] == 1
    assert manifest["hygiene"]["doc_lifecycle"] == "warn"
