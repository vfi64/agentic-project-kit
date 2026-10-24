"""Deterministic public identity and bounded release evidence, without network access."""
from __future__ import annotations

from datetime import date
from html import escape
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import yaml


def normalized_name(value: str) -> str:
    """Trim, lowercase and collapse whitespace to hyphens; preserve other characters."""
    return re.sub(r"\s+", "-", value.strip().lower())


def product_title(root: Path, package_name: str) -> str:
    try:
        titles = re.findall(r"^# ([^\n]+)$", (root / "README.md").read_text(), re.MULTILINE)
        citation = yaml.safe_load((root / "CITATION.cff").read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError("product identity sources are missing or unreadable") from exc
    if len(titles) != 1 or not isinstance(citation, dict):
        raise ValueError("product identity needs exactly one README H1 and a CITATION mapping")
    title = titles[0].strip()
    citation_title = citation.get("title")
    if not isinstance(citation_title, str) or not (
        normalized_name(title) == package_name == normalized_name(citation_title)
    ):
        raise ValueError("README, project.name and CITATION product identities disagree")
    return title


def release_section(root: Path, version: str) -> dict:
    result = {"version": version, "date": None, "entry_count": None, "notes": [],
              "source": "CHANGELOG.md", "status": "unverified"}
    if version.casefold() == "unreleased":
        return result
    try:
        text = (root / "CHANGELOG.md").read_text()
    except OSError:
        return result
    match = re.search(r"^## v?\[?" + re.escape(version) +
                      r"\]?(?=\s|$)([^\n]*)\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if match is None:
        return result
    notes = []
    in_fence = False
    for line in match.group(2).splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^\s+[-*+]\s", line) or re.match(r"^\s*\d+[.)]\s", line):
            raise ValueError("unsupported nested or numbered CHANGELOG bullet")
        if re.match(r"^[*+]\s", line):
            raise ValueError("unsupported CHANGELOG bullet marker; expected top-level '- '")
        if line.startswith("- "):
            notes.append(line[2:].strip().replace("`", ""))
    found_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", match.group(1))
    dated = date.fromisoformat(found_date.group()).isoformat() if found_date else None
    return {**result, "status": "recorded", "date": dated,
            "entry_count": len(notes), "notes": notes}


def publication_evidence(root: Path, version: str) -> dict:
    source = f"docs/reports/release/release-run-{version}.json"
    result = {"status": "unverified", "version": version, "source": source,
              "boundary": "Workflow completion does not prove index visibility or installability."}
    try:
        data = json.loads((root / source).read_text())
    except (OSError, ValueError):
        return result
    if not isinstance(data, dict):
        return result
    steps = data.get("steps")
    workflow = data.get("package_index_workflow")
    if not isinstance(steps, dict) or not isinstance(workflow, dict):
        return result
    step = steps.get("C3")
    if not isinstance(step, dict):
        return result
    if (data.get("version") == version and data.get("tag") == f"v{version}"
            and "pypi" in str(data.get("publication_policy", "")).split("+")
            and step.get("result_status") == "PASS" and step.get("returncode") == 0
            and not step.get("blockers") and workflow.get("file") == "release.yml"
            and workflow.get("publish_target_pypi") is True):
        result["status"] = "verified"
    return result


def publication_text(evidence: dict) -> str:
    if evidence["status"] != "verified":
        return "PyPI publication workflow evidence for this version is unverified."
    return (f"The PyPI publication workflow for version {evidence['version']} completed "
            "successfully in the release run (C3). Index visibility and installability "
            "are separate checks.")


def scoped_claim_counts(report) -> str:
    labels = {"technical": "Technical", "documentation": "Documentation",
              "historical-observation": "Historical observations"}
    rows = []
    for scope, label in labels.items():
        counts = {status: sum(c.scope == scope and c.status == status for c in report.claims)
                  for status in ("verified", "unverified", "planned")}
        rows.append(f'<article data-claim-scope="{scope}"><h3>{label}</h3><p>' +
                    " · ".join(f'{count} {escape(status)}' for status, count in counts.items()) +
                    '</p></article>')
    return "\n".join(rows)


def projection_provenance(build_commit: str) -> str:
    if build_commit == "docs-pages-fallback":
        return "Projection: Pages fallback · Source commit: not provided"
    commit = build_commit if re.fullmatch(r"[0-9a-f]{7,40}", build_commit) else "not provided"
    return f"Projection: site build · Source commit: {commit}"


def self_hosting_case(root: Path, version: str, repository_url: str) -> str:
    """Derive bounded GF-078 facts; archive evidence is a separate Git observation."""
    catalog_source = "src/agentic_project_kit/reference/external-findings-status.json"
    try:
        catalog = json.loads((root / catalog_source).read_text())
        records = catalog.get("findings", [])
        finding = next(r for r in records if r.get("id") == "KIT-GF-078")
        source = str(finding["report"])
        report_path = (root / source).resolve()
        if not report_path.is_relative_to(root.resolve()):
            return ""
        report = report_path.read_text()
        release_source = f"docs/reports/release/release-run-{version}.json"
        release = json.loads((root / release_source).read_text())
    except (OSError, ValueError, StopIteration, KeyError, TypeError):
        return ""
    if not all(term in report for term in ("300", "900", "tests/test_release_run_ci_wait.py")):
        return ""
    if not (root / "tests/test_release_run_ci_wait.py").is_file():
        return ""
    steps = release.get("steps") or {}
    complete = (publication_evidence(root, version)["status"] == "verified"
                and all(isinstance(steps.get(s), dict) and steps[s].get("result_status") == "PASS"
                        and steps[s].get("returncode") == 0 for s in ("B4", "D4", "D5")))
    archive = "Archive merge: no matching retained Git/PR observation."
    archive_source = "docs/reports/website_entry_20261024/archive_observation.json"
    try:
        observation = json.loads((root / archive_source).read_text())
    except (OSError, ValueError):
        observation = {}
    commit = observation.get("merge_commit", "")
    number = observation.get("pr_number")
    if (observation.get("version") == version and observation.get("merged") is True
            and observation.get("repository") == urlsplit(repository_url).path.strip("/")
            and observation.get("evidence_path") == release_source
            and observation.get("evidence_sha256") == hashlib.sha256((root / release_source).read_bytes()).hexdigest()
            and isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)
            and isinstance(number, int)):
        archive = (f'Archive merge, separately recorded from Git/PR evidence: <a href="{escape(repository_url, quote=True)}/commit/{commit}">'
                   f'PR #{number}</a>.')
    outcome = "completed release steps B4, D4 and D5" if complete else "release-step evidence unverified"
    return ('<article class="panel"><p class="eyebrow">Self-hosting case: KIT-GF-078</p>'
            '<h3>CI needed longer than the release waited</h3>'
            '<p>The 300-second CI wait interrupted DOI and archive closeout in an earlier release. '
            f'The finding records the repair in {escape(str(finding.get("fixed_in", "not recorded")))}: '
            'a 900-second wait and bounded resume checks.</p>'
            f'<p>Regression boundary: <a href="{escape(repository_url, quote=True)}/blob/main/tests/test_release_run_ci_wait.py">CI-wait regression tests</a>. '
            f'Release {escape(version)}: {outcome}. {archive}</p>'
            '<p>This does not prove every recovery branch ran, general failure prevention, or a consumer retest.</p>'
            f'<p><a href="{escape(repository_url, quote=True)}/blob/main/{escape(source, quote=True)}">Finding report</a> · '
            f'<a href="{escape(repository_url, quote=True)}/blob/main/{release_source}">Release-step evidence</a></p></article>')
