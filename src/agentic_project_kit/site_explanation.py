"""Bounded public explanations projected from repository evidence.

Historical reports are observations, not current remote-repository certification.
Only explicitly selected public fields reach HTML/JSON; private target identities,
runtime paths and raw reports are never copied into the website.
"""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import re
from string import Template
from urllib.parse import urlparse

import yaml

from agentic_project_kit.site_public_contract import release_section
from agentic_project_kit.site_workflow_figures import collect_figures, render_figures

DIRECTION = "docs/planning/PROJECT_DIRECTION.yaml"
GREENFIELD = "docs/reports/POST_V1_0_13_GF009_PRIVATE_RELEASED_PACKAGE_RETEST_20260916.json"
COMPARISON = "site/content/tool_comparison.yaml"


def collect_explanation(root: Path, *, version: str) -> dict[str, object]:
    """Read current authorities and retain explicit missing/invalid evidence states."""
    direction = _read(root, DIRECTION)
    plans = direction.get("plans", [])
    plans = plans if isinstance(plans, list) else []
    program = next((p for p in plans if isinstance(p, dict) and p.get("id") ==
                    "post-v1-0-4-hygiene-boundary-work-program"), {})
    slices = program.get("implementation_slices", [])
    slices = slices if isinstance(slices, list) else []
    b1 = next((p for p in slices if isinstance(p, dict) and p.get("id") == "B1"), {})
    cycles = b1.get("observed_cycles", [])
    cycles = cycles if isinstance(cycles, list) else []
    completed = []
    for cycle in cycles:
        if not isinstance(cycle, dict) or not str(cycle.get("state", "")).startswith("merged"):
            continue
        source = cycle.get("report")
        if _safe_source(root, source) is not None:
            completed.append(cycle)
    # Canonical observed_cycles is an ordered record, not an inferred filesystem scan.
    latest = completed[-1] if completed else {}
    delta = str(latest.get("seam_delta", ""))
    if not re.fullmatch(r"\d+\s*->\s*\d+", delta):
        delta = "not recorded"
    brownfield = {
        "status": "recorded" if latest else "unverified",
        "completed_observations": len(completed),
        "latest_cycle": str(latest.get("id", "not recorded")),
        "seam_delta": delta,
        "source": str(latest.get("report", DIRECTION)),
        "boundary": "Recorded maintenance observations in one familiar private repository; not an independent benchmark or general portability proof.",
    }
    gf = _read(root, GREENFIELD)
    gf_evidence = gf.get("evidence", {})
    gf_evidence = gf_evidence if isinstance(gf_evidence, dict) else {}
    required = ("workspace_init", "external_gates", "work_pr_ci", "work_pr_merge",
                "handoff_pr_ci", "handoff_pr_merge")
    gf_pass = gf.get("status") == "PASS" and all(gf_evidence.get(k) == "PASS" for k in required)
    gf_pass = gf_pass and gf_evidence.get("final_post_merge_check") == "PASS_NOOP"
    greenfield = {
        "status": "recorded_pass" if gf_pass else "unverified",
        "date": str(gf.get("date", "not recorded")),
        "package": str(gf.get("package", "not recorded")),
        "source": GREENFIELD,
        "boundary": "Historical released-package first-cycle work/PR/CI/merge/handoff retest in a private external repository; not a retest of every later release.",
    }
    paa = next((p for p in plans if isinstance(p, dict) and p.get("id") ==
                "proof-assurance-assessment"), {})
    phases = paa.get("phases", [])
    phases = phases if isinstance(phases, list) else []
    p0 = next((p for p in phases if isinstance(p, dict) and p.get("id") == "P0"), {})
    release = release_section(root, version)
    result = {
        "schema_version": 1,
        "kind": "site_explanation_projection",
        "greenfield": greenfield,
        "brownfield": brownfield,
        "release": release,
        "paa": {"status": str(paa.get("status", "not recorded")),
                "review": str(paa.get("decision_status", "not recorded")),
                "p0": str(p0.get("decision_status", "not recorded")), "source": DIRECTION},
        "comparisons": _comparison_rows(root),
    }
    template = root / 'site/templates/understand.html'
    if template.is_file() and '${workflow_figures}' in template.read_text():
        result['workflow_figures'] = collect_figures(root)
    if (root / "site/templates/evidence.html").is_file():
        from agentic_project_kit.site_safety_evidence import collect_safety_evidence
        result["safety_evidence"] = collect_safety_evidence(root)
    return result


def render_explanation(root: Path, projection: dict[str, object], *, repository_url: str,
                       product_name: str, version: str) -> str:
    template = Template((root / "site/templates/understand.html").read_text())
    return template.substitute(
        product_name=escape(product_name), package_version=escape(version),
        repository_url=escape(repository_url, quote=True),
        evidence_cards=render_evidence_cards(projection, repository_url=repository_url),
        comparison_rows=_render_comparisons(projection),
        workflow_figures=render_figures(projection['workflow_figures']) if 'workflow_figures' in projection else '',
    ).rstrip() + "\n"


def render_evidence_cards(projection: dict[str, object], *, repository_url: str) -> str:
    gf = projection["greenfield"]
    bf = projection["brownfield"]
    release = projection["release"]
    paa = projection["paa"]
    assert isinstance(gf, dict) and isinstance(bf, dict) and isinstance(release, dict) and isinstance(paa, dict)
    cards = []
    for title, data, summary in (
        ("Greenfield: installed release", gf,
         f"{gf['package']} · {gf['date']} · {gf['status']}"),
        ("Brownfield: recorded maintenance", bf,
         f"{bf['completed_observations']} merged observations · latest: {bf['latest_cycle']} · legacy seam count: {bf['seam_delta']}"),
    ):
        cards.append(_card(title, summary, str(data["boundary"]), _source_link(repository_url, str(data["source"]))))
    cards.append(render_release_card(release, repository_url=repository_url))
    cards.append(_card("Formal assurance: planning boundary",
                       f"PAA: {paa['status']} · review: {paa['review']} · P0: {paa['p0']}",
                       "PAA is shown from the canonical plan. A planning status is not an implemented verification capability or a proof of software correctness.",
                       _source_link(repository_url, DIRECTION)))
    return "\n".join(cards)


def _card(title: str, summary: str, boundary: str, link: str) -> str:
    return (f'<article class="panel"><h3>{escape(title)}</h3><p class="evidence-fact">{escape(summary)}</p>'
            f'<p>{escape(boundary)}</p><p>{link}</p></article>')


def _source_link(repository_url: str, source: str) -> str:
    return f'<a href="{escape(repository_url.rstrip("/") + "/blob/main/" + source, quote=True)}">Read the repository source</a>'


def _read(root: Path, source: str) -> dict:
    path = _safe_source(root, source)
    if path is None:
        return {}
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _safe_source(root: Path, source: object) -> Path | None:
    if not isinstance(source, str) or Path(source).is_absolute():
        return None
    path = (root / source).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return None
    return path


def _release_notes(root: Path, version: str) -> list[str]:
    return release_section(root, version)["notes"]


def render_release_card(release: dict, *, repository_url: str) -> str:
    version = str(release["version"])
    count = release["entry_count"]
    dated = release["date"] or "not recorded"
    entries = str(count) if count is not None else "not recorded"
    anchor = "v" + version.replace(".", "")
    if release["date"]:
        anchor += "---" + str(release["date"])
    link = repository_url.rstrip("/") + "/blob/main/CHANGELOG.md#" + anchor
    return ('<article class="panel"><p class="eyebrow">Release record</p>'
            f'<h3>Version {escape(version)}</h3><p>Date: {escape(dated)} · '
            f'{entries} entries in the CHANGELOG section.</p>'
            '<p>This counts top-level bullet lines, not the size of the changes.</p>'
            f'<p><a href="{escape(link, quote=True)}">Full release notes</a></p></article>')


def _comparison_rows(root: Path) -> list[dict[str, str]]:
    data = _read(root, COMPARISON)
    rows = data.get("tools", [])
    if not isinstance(rows, list):
        raise ValueError("tool comparison tools must be a list")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("tool comparison row must be a mapping")
        fields = ("name", "category", "focus", "relationship", "source", "reviewed_on")
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in fields):
            raise ValueError("tool comparison requires named, dated and sourced fields")
        url = urlparse(row["source"])
        if url.scheme != "https" or not url.netloc or url.username or url.password:
            raise ValueError("tool comparison source must be a public HTTPS URL")
        date.fromisoformat(row["reviewed_on"])
        result.append({key: row[key] for key in fields})
    return result


def _render_comparisons(projection: dict[str, object]) -> str:
    rows = projection["comparisons"]
    assert isinstance(rows, list)
    return "\n".join(
        '<tr>' + ''.join(f'<td>{escape(row[key])}</td>' for key in
                        ("name", "category", "focus", "relationship")) +
        f'<td><a href="{escape(row["source"], quote=True)}">Official documentation</a><br>'
        f'Reviewed {escape(row["reviewed_on"])}</td></tr>' for row in rows
    )
