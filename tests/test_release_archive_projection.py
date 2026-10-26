"""E1 binds current publication evidence to the optional canonical site projection."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from agentic_project_kit.docs_pages_projection import (
    DOCS_PAGES_FALLBACK_EXPECTED_PATHS, refresh_docs_pages_fallback,
)
from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from agentic_project_kit.release_run_evidence import evidence_path
from agentic_project_kit.site_generator import build_docs_pages_fallback
from test_release_run_evidence import prepared
from test_site_generator import _write_site_fixture


def site_archive(root):
    run = prepared(root)
    _write_site_fixture(root)
    script = root / "site/scripts/build.py"
    script.parent.mkdir()
    script.write_text("# Presence marker; the installed canonical renderer is used.\n")
    (root / "site/templates/index.html").write_text("$publication_text")
    run.state["c3_dispatch"] = {"workflow": {"file": "release.yml", "inputs": ["publish_target=pypi"]}}
    run._save_state()
    assert build_docs_pages_fallback(root).ok
    assert "unverified" in (root / "docs/site/index.html").read_text()
    return run


def options(root, **extra):
    return ReleaseRunOptions(version="1.2.3", root=root, approved_by="owner",
                             consent_source="offline regression", **extra)


def test_e1_renders_after_evidence_and_selects_projection_before_finish(tmp_path):
    run = site_archive(tmp_path)
    before = (tmp_path / "docs/site/index.html").read_bytes()
    plan = run_release(options(tmp_path), runner=run.runner)
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert plan["gate"]["projection_paths"] == list(DOCS_PAGES_FALLBACK_EXPECTED_PATHS)
    assert (tmp_path / "docs/site/index.html").read_bytes() == before
    original = run.runner

    def runner(argv, cwd):
        if "work" in argv and "finish" in argv:
            assert "workflow for version 1.2.3 completed successfully" in (cwd / "docs/site/index.html").read_text()
            selected = [argv[i + 1] for i, arg in enumerate(argv) if arg == "--path"]
            assert set(DOCS_PAGES_FALLBACK_EXPECTED_PATHS) <= set(selected)
            assert evidence_path("1.2.3") in selected
        return original(argv, cwd)

    result = run_release(options(tmp_path, execute=True,
                         expected_signature=plan["gate"]["approval_signature"]), runner=runner)
    assert result["result_status"] == "PASS"
    content = (tmp_path / evidence_path("1.2.3")).read_bytes()
    assert hashlib.sha256(content).hexdigest() == plan["gate"]["evidence_sha256"]
    assert json.loads(content)["steps"]["C3"]["result_status"] == "PASS"
    first = (tmp_path / "docs/site/site.json").read_bytes()
    assert build_docs_pages_fallback(tmp_path).ok
    assert (tmp_path / "docs/site/site.json").read_bytes() == first


@pytest.mark.parametrize("failure", ["blocker", "exception"])
def test_render_failure_preserves_evidence_and_never_finishes(tmp_path, monkeypatch, failure):
    run = site_archive(tmp_path)
    plan = run_release(options(tmp_path), runner=run.runner)

    def fail(root):
        assert (root / evidence_path("1.2.3")).is_file()
        if failure == "exception":
            raise OSError("fixture failure")
        return SimpleNamespace(ok=False, blockers=("fixture failure",))

    monkeypatch.setattr("agentic_project_kit.site_generator.build_docs_pages_fallback", fail)
    result = run_release(options(tmp_path, execute=True,
                         expected_signature=plan["gate"]["approval_signature"]), runner=run.runner)
    assert result["result_status"] == "BLOCKED"
    assert any("docs_pages_fallback:" in x for x in result["blockers"])
    assert not any("finish" in c or "push-current" in c for c in run.runner.calls)
    content = (tmp_path / evidence_path("1.2.3")).read_bytes()
    assert hashlib.sha256(content).hexdigest() == plan["gate"]["evidence_sha256"]
    assert result["finished_steps"] == list(run.sequence)


def test_projection_presence_is_bound_to_approval(tmp_path):
    run = prepared(tmp_path)
    plan = run_release(options(tmp_path), runner=run.runner)
    assert plan["gate"]["projection_paths"] == []
    script = tmp_path / "site/scripts/build.py"
    script.parent.mkdir(parents=True)
    script.write_text("# Site appeared after approval.\n")
    result = run_release(options(tmp_path, execute=True,
                         expected_signature=plan["gate"]["approval_signature"]), runner=run.runner)
    assert result["result_status"] == "BLOCKED"
    assert not (tmp_path / evidence_path("1.2.3")).exists()
    assert not any("work" in c for c in run.runner.calls)


def test_external_archive_does_not_invoke_site_renderer(tmp_path, monkeypatch):
    run = prepared(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("No optional site: must not invoke its renderer")

    monkeypatch.setattr("agentic_project_kit.site_generator.build_docs_pages_fallback", forbidden)
    plan = run_release(options(tmp_path), runner=run.runner)
    result = run_release(options(tmp_path, execute=True,
                         expected_signature=plan["gate"]["approval_signature"]), runner=run.runner)
    assert result["result_status"] == "PASS"
    assert not (tmp_path / "docs/site").exists()


def test_projection_refuses_foreign_output_paths(tmp_path, monkeypatch):
    script = tmp_path / "site/scripts/build.py"
    script.parent.mkdir(parents=True)
    script.write_text("# optional site\n")
    monkeypatch.setattr("agentic_project_kit.site_generator.build_docs_pages_fallback",
                        lambda root: SimpleNamespace(ok=True, files=("../foreign",)))
    blockers, paths = refresh_docs_pages_fallback(tmp_path)
    assert blockers == ("docs_pages_fallback:output-path-escape",)
    assert paths == ()


def test_projection_cannot_change_signed_evidence(tmp_path, monkeypatch):
    run = site_archive(tmp_path)
    plan = run_release(options(tmp_path), runner=run.runner)

    def corrupt(root):
        (root / evidence_path("1.2.3")).write_text("unexpected renderer mutation")
        return SimpleNamespace(ok=True, files=("site/index.html",))

    monkeypatch.setattr("agentic_project_kit.site_generator.build_docs_pages_fallback", corrupt)
    result = run_release(options(tmp_path, execute=True,
                         expected_signature=plan["gate"]["approval_signature"]), runner=run.runner)
    assert result["result_status"] == "BLOCKED"
    assert "archive-projection-evidence-drift" in result["blockers"]
    assert not any("finish" in c for c in run.runner.calls)
