"""Shared navigation, bounded detail selection, historical privacy and link safety."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
from urllib.parse import unquote, urlsplit

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest, manifest_identity
from agentic_project_kit.site_command_details import collect_command_details, detail_filename
from agentic_project_kit.site_generator import build_site, collect_site_foundation_metadata, _build_quickstart_projection
from agentic_project_kit.site_history import collect_history, render_history, ARCHIVE, HISTORY, METRICS, ARCHITECTURE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("w134-site") / "site"
    result = build_site(ROOT, output_dir=out, build_commit="a" * 40)
    assert result.ok, result.report.blockers
    return out


def test_detail_selection_is_exact_union_of_shared_routes_and_tested_quickstart(built):
    manifest = load_manifest(ROOT)
    quick = json.loads((built / "quickstart/quickstart.json").read_text())
    expected = {r["command"] for r in manifest["task_routes"]["routes"]} | {
        c["qualified_name"] for f in quick["flows"] for c in f["commands"]}
    details = json.loads((built / "commands/details.json").read_text())
    assert {c["command"] for c in details["commands"]} == expected
    assert details["execution_authorized"] is False
    assert len({c["file"] for c in details["commands"]}) == len(expected)
    for c in details["commands"]:
        assert (built / "commands" / c["file"]).is_file()
    finish = (built / "commands" / detail_filename("agentic-kit work finish")).read_text()
    assert "<code>--dry-run, --execute</code>" in finish
    assert "<code>--merge, --no-merge</code>" in finish
    tasks = json.loads((built / "commands/tasks.json").read_text())
    assigned = {r["command"] for r in tasks["routes"]}
    assert assigned.isdisjoint(tasks["unassigned_commands"])
    assert assigned | set(tasks["unassigned_commands"]) == {c["qualified_name"] for c in manifest["commands"]}
    html = (built / "commands/guided.html").read_text()
    assert html.count('class="task-card"') == len(tasks["routes"])
    assert '<summary>All orchestrators and filters</summary>' in html
    assert "Unassigned commands" in html and 'aria-live="polite"' in html


def test_every_displayed_help_example_runs_without_mutation(built, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    details = json.loads((built / "commands/details.json").read_text())
    for c in details["commands"]:
        assert c["help_example"][0] == "agentic-kit"
        result = CliRunner().invoke(app, c["help_example"][1:])
        assert result.exit_code == 0, result.output
    assert not list(tmp_path.iterdir())


def test_provided_manifest_drives_navigation_and_details_together(tmp_path):
    manifest = copy.deepcopy(load_manifest(ROOT))
    entry = next(c for c in manifest["commands"] if c["qualified_name"] == "agentic-kit work finish")
    entry["when_to_use"] = 'Changed metadata <script>alert("x")</script>'
    manifest["meta"]["manifest_sha"] = manifest_identity(manifest)
    report = collect_site_foundation_metadata(ROOT, manifest=manifest, build_commit="a" * 40)
    assert report.ok, report.blockers
    result = build_site(ROOT, output_dir=tmp_path / "out", manifest=manifest, build_commit="a" * 40)
    assert result.ok
    tasks = json.loads((tmp_path / "out/commands/tasks.json").read_text())
    assert tasks["manifest_sha"] == manifest["meta"]["manifest_sha"]
    page = (tmp_path / "out/commands" / detail_filename(entry["qualified_name"])).read_text()
    assert "Changed metadata &lt;script&gt;" in page
    assert '<script>alert("x")</script>' not in page


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.lang = None
        self.labels = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag in {"a", "img", "link", "script"}:
            self.links.append(attrs.get("href", attrs.get("src", "")))
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "label" and attrs.get("for"):
            self.labels.append(attrs["for"])


def test_all_generated_links_assets_fragments_and_control_labels_resolve(built):
    pages = {}
    for path in built.rglob("*.html"):
        parsed = Links()
        parsed.feed(path.read_text())
        assert parsed.lang == "en", path
        assert len(parsed.ids) == len(set(parsed.ids)), path
        assert set(parsed.labels) <= set(parsed.ids), path
        pages[path.resolve()] = parsed
    for path, parsed in pages.items():
        for link in parsed.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if target.is_dir():
                target /= "index.html"
            assert target.is_relative_to(built.resolve()) and target.exists(), (path, link)
            if parts.fragment and target.suffix == ".html":
                assert unquote(parts.fragment) in pages[target].ids, (path, link)


def history_fixture(tmp_path):
    for name in ("site/content/history_sources.json", "site/templates/history.html",
                 ARCHIVE + "SOURCE_MANIFEST.json", ARCHIVE + HISTORY, ARCHIVE + METRICS, ARCHITECTURE):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def test_history_only_exports_public_selection_and_keeps_evidence_classes(built):
    payload = json.loads((built / "history/history.json").read_text())
    page = (built / "history/index.html").read_text()
    text = json.dumps(payload) + page
    for private in ("private_sources", "Comm-SCI", "agp-cockpit", "/Users/", "P02", "consumer_blob"):
        assert private not in text
    assert payload["first_release"]["evidence_class"] == "archive-reported Git event"
    assert payload["testimony"]["evidence_class"] == "author testimony"
    assert payload["architecture_adoption"]["evidence_class"] == "normative decision"
    assert "not elapsed working time" in page
    assert "no process-isolation or universal-lock claim" in page
    assert "Current source-tree package" in page and "Historical snapshot" in page


@pytest.mark.parametrize("which", [HISTORY, METRICS, "SOURCE_MANIFEST.json"])
def test_changed_historical_evidence_blocks_until_rebound(tmp_path, which):
    root = history_fixture(tmp_path)
    path = root / (ARCHIVE + which)
    path.write_text(path.read_text() + "\nchanged source")
    with pytest.raises(ValueError, match="changed"):
        collect_history(root, load_manifest(ROOT))


def test_historical_numbers_are_read_from_bound_data(tmp_path):
    root = history_fixture(tmp_path)
    metrics_path = root / (ARCHIVE + METRICS)
    metrics = json.loads(metrics_path.read_text())
    metrics["pr_overhead_oct_01_15"]["by_class"]["ADMIN_REFRESH_ONLY"]["prs"] = 42
    metrics_path.write_text(json.dumps(metrics))
    source_path = root / (ARCHIVE + "SOURCE_MANIFEST.json")
    source = json.loads(source_path.read_text())
    source["archive_files"][METRICS] = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    source_path.write_text(json.dumps(source))
    binding_path = root / "site/content/history_sources.json"
    binding = json.loads(binding_path.read_text())
    binding["sha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    binding_path.write_text(json.dumps(binding))
    projection = collect_history(root, load_manifest(ROOT))
    html = render_history(root, projection, product_name="Kit", version="1.2.3", repository_url="https://example.invalid/repo")
    assert "42 refresh-only PRs" in html


def test_missing_command_metadata_blocks_detail_projection():
    manifest = load_manifest(ROOT)
    report = collect_site_foundation_metadata(ROOT, build_commit="a" * 40)
    quick = _build_quickstart_projection(report.metadata, report.command_catalog)
    quick["flows"][0]["commands"][0]["qualified_name"] = "agentic-kit does-not-exist"
    with pytest.raises(ValueError, match="absent"):
        collect_command_details(manifest, quick)
