"""Public explanations retain source scope and never copy private payloads."""
import json
from pathlib import Path

import pytest
import yaml

from agentic_project_kit.site_explanation import (
    COMPARISON, DIRECTION, GREENFIELD, collect_explanation, render_evidence_cards,
)


def write(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(data))


def test_canonical_observations_update_without_private_payload(tmp_path):
    report = "docs/reports/observation.md"
    write(tmp_path, report, {"secret": "/Users/private/target"})
    cycles = [{"id": "cycle-1", "state": "merged", "report": report,
               "seam_delta": "55 -> 44", "private_target": "PRIVATE_TARGET"},
              {"id": "pending", "state": "pending", "report": report},
              {"id": "missing", "state": "merged", "report": "missing.md"}]
    plan = {"plans": [{"id": "post-v1-0-4-hygiene-boundary-work-program",
                       "implementation_slices": [{"id": "B1", "observed_cycles": cycles}]}]}
    write(tmp_path, DIRECTION, plan)
    first = collect_explanation(tmp_path, version="1.0.23")
    assert first["brownfield"]["completed_observations"] == 1
    cycles.append({"id": "cycle-2", "state": "merged_verified", "report": report,
                   "seam_delta": "44 -> 40"})
    write(tmp_path, DIRECTION, plan)
    second = collect_explanation(tmp_path, version="1.0.23")
    assert second["brownfield"]["completed_observations"] == 2
    assert second["brownfield"]["seam_delta"] == "44 -> 40"
    public = json.dumps(second) + render_evidence_cards(second, repository_url="https://example.org/repo")
    assert "PRIVATE_TARGET" not in public
    assert "/Users/private" not in public


def test_greenfield_pass_requires_all_bounded_receipts(tmp_path):
    evidence = dict.fromkeys(("workspace_init", "external_gates", "work_pr_ci", "work_pr_merge",
                             "handoff_pr_ci", "handoff_pr_merge"), "PASS")
    evidence["final_post_merge_check"] = "PASS_NOOP"
    report = {"status": "PASS", "date": "2026-09-16", "package": "kit==old", "evidence": evidence}
    write(tmp_path, GREENFIELD, report)
    assert collect_explanation(tmp_path, version="new")["greenfield"]["status"] == "recorded_pass"
    evidence.pop("work_pr_merge")
    write(tmp_path, GREENFIELD, report)
    assert collect_explanation(tmp_path, version="new")["greenfield"]["status"] == "unverified"
    (tmp_path / GREENFIELD).write_text("{invalid")
    assert collect_explanation(tmp_path, version="new")["greenfield"]["status"] == "unverified"


def test_release_section_is_exact_and_missing_evidence_is_visible(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text("## Unreleased\n- future\n## v1.0.23 - date\n- current <script>\n## v1.0.2 - date\n- historic\n")
    result = collect_explanation(tmp_path, version="1.0.2")
    assert result["release"]["notes"] == ["historic"]
    assert result["brownfield"]["status"] == "unverified"
    result = collect_explanation(tmp_path, version="1.0.23")
    html = render_evidence_cards(result, repository_url="https://example.org/repo")
    assert "1 entries in the CHANGELOG section" in html
    assert "<script>" not in html
    assert result["release"]["notes"] == ["current <script>"]
    assert collect_explanation(tmp_path, version="1.0.24")["release"]["status"] == "unverified"


@pytest.mark.parametrize("field,value", [("source", "javascript:alert(1)"),
                                         ("source", "https://user:secret@example.org"),
                                         ("reviewed_on", "yesterday")])
def test_invalid_comparison_blocks_publication(tmp_path, field, value):
    row = dict.fromkeys(("name", "category", "focus", "relationship"), "description")
    row.update(source="https://example.org/docs", reviewed_on="2026-10-12")
    row[field] = value
    write(tmp_path, COMPARISON, {"tools": [row]})
    with pytest.raises(ValueError):
        collect_explanation(tmp_path, version="1")


def test_report_outside_repository_is_not_published(tmp_path):
    write(tmp_path, DIRECTION, {"plans": [{"id": "post-v1-0-4-hygiene-boundary-work-program",
        "implementation_slices": [{"id": "B1", "observed_cycles": [
            {"id": "unsafe", "state": "merged", "report": "/etc/passwd"}]}]}]})
    assert collect_explanation(tmp_path, version="1")["brownfield"]["completed_observations"] == 0


def test_real_sources_keep_paa_planned_and_all_explanation_anchors():
    root = Path(__file__).resolve().parents[1]
    result = collect_explanation(root, version="1.0.23")
    assert result["paa"] == {"status": "planned", "review": "review_required", "p0": "proposed", "source": DIRECTION}
    template = (root / "site/templates/understand.html").read_text()
    for anchor in ("audience", "benefits", "architecture", "controllers", "evidence", "comparison"):
        assert f'id="{anchor}"' in template
    assert all(row["source"].startswith("https://") for row in result["comparisons"])
    assert "ordinary browser chat" in template
    assert "does not establish engineering quality" in template
    manifest = json.loads((root / "site/pages_input_manifest.json").read_text())
    assert DIRECTION in manifest["site_input_paths"]
    assert GREENFIELD in manifest["site_input_paths"]
    assert result["brownfield"]["source"] in manifest["site_input_paths"]
