"""Public, bounded historical selection; never copy raw private-source records."""
from __future__ import annotations

from datetime import date
from html import escape
import hashlib
import json
from pathlib import Path
import re
from string import Template
from urllib.parse import quote
from .site_public_contract import projection_provenance

ARCHIVE = "docs/reports/self-hosting/"
HISTORY = "HISTORICAL_DEVELOPMENT_20261015.md"
METRICS = "DRIFT_METRICS_20261015.json"
ARCHITECTURE = "docs/architecture/KIT_AS_OS_ARCHITECTURE.md"


def _bytes(root: Path, path: str) -> bytes:
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("history source escapes repository")
    return resolved.read_bytes()


def _reported_may_event(text: str, label: str, version_pattern: str) -> dict:
    row = next(line for line in text.splitlines() if line.startswith("|") and label in line)
    when = re.search(r"(\d+)\\?\.\s+Mai\s+(\d{4})", row)
    version = re.search(version_pattern, row)
    if when is None or version is None:
        raise ValueError("historical event shape changed; review extraction")
    return {"date": date(int(when[2]), 5, int(when[1])).isoformat(), "version": version[1],
            "evidence_class": "archive-reported Git event"}


def collect_history(root: Path, manifest: dict) -> dict:
    binding = json.loads((root / "site/content/history_sources.json").read_text())
    if binding.get("path") != ARCHIVE + "SOURCE_MANIFEST.json" or not re.fullmatch(r"[a-f0-9]{40}", str(binding.get("revision", ""))):
        raise ValueError("invalid historical archive binding")
    raw_manifest = _bytes(root, binding["path"])
    if hashlib.sha256(raw_manifest).hexdigest() != binding["sha256"]:
        raise ValueError("historical archive identity changed; review binding")
    archive = json.loads(raw_manifest)
    if archive.get("kind") != "self_hosting_archive_source_manifest":
        raise ValueError("invalid self-hosting archive")
    raw = {}
    sources = {"archive": binding}
    for name in (HISTORY, METRICS):
        data = _bytes(root, ARCHIVE + name)
        digest = hashlib.sha256(data).hexdigest()
        if digest != archive["archive_files"][name]:
            raise ValueError("historical archive member changed: " + name)
        raw[name] = data.decode("utf-8")
        sources[name] = {"path": ARCHIVE + name, "sha256": digest, "revision": binding["revision"]}
    text = raw[HISTORY]
    metrics = json.loads(raw[METRICS])
    if metrics.get("kind") != "self_hosting_drift_quality_metrics" or "AU03" not in text:
        raise ValueError("historical metric/testimony contract missing")
    architecture = _bytes(root, ARCHITECTURE)
    if not all(term in architecture.decode() for term in ("guest", ".agentic/", "operating mode")):
        raise ValueError("operating-layer architecture contract changed")
    sources["architecture"] = {"path": ARCHITECTURE, "sha256": hashlib.sha256(architecture).hexdigest(), "revision": "main", "scope": "current moving source"}
    adopted = re.search(r"angenommen\s+(\d{4}-\d{2}-\d{2})", architecture.decode())
    if adopted is None:
        raise ValueError("architecture adoption date missing")
    counts = {surface: sum(c["surface"] == surface for c in manifest["commands"])
              for surface in ("orchestrator", "diagnostic", "primitive")}
    observation = metrics["pr_overhead_oct_01_15"]
    # Export only these public fields. private_sources and raw archive prose never leave this collector.
    return {"schema_version": 1, "kind": "bounded_history_projection",
            "snapshot": {"version": archive["kit"]["kit_version"], "analysis_base": archive["kit"]["analysis_base"],
                         "audit_date": metrics["audit_date"], "measurement_date": metrics["measurement_date"]},
            "first_commit": _reported_may_event(text, "Erster Kit-Commit", r"Version\s+(\d+\.\d+\.\d+)"),
            "first_release": _reported_may_event(text, "Erster Release", r"v(\d+\.\d+\.\d+)"),
            "architecture_adoption": {"date": adopted[1], "evidence_class": "normative decision"},
            "testimony": {"evidence_class": "author testimony", "source_marker": "AU03",
                          "summary": "The author describes self-hosting as a major contributor to solo development speed. That counterfactual has not been quantified."},
            "overhead": {"window": observation["window"], "total_prs": observation["total"],
                         "admin_refresh_prs": observation["by_class"]["ADMIN_REFRESH_ONLY"]["prs"],
                         "evidence_class": "historical classification"},
            "current_command_surfaces": counts, "manifest_sha": manifest["meta"]["manifest_sha"], "sources": sources}


def render_history(root: Path, data: dict, *, product_name: str, version: str, repository_url: str, build_commit: str = "") -> str:
    events = "".join(f'<li><strong>{escape(data[key]["date"])}</strong> — {label} {escape(data[key].get("version", ""))}'
                     f' <small>({escape(data[key]["evidence_class"])})</small></li>'
                     for key, label in (("first_commit", "First Kit commit:"), ("first_release", "First published release:"),
                                        ("architecture_adoption", "Operating-layer architecture adopted:")))
    sources = "".join(f'<li><a href="{escape(repository_url, quote=True)}/blob/{s["revision"]}/{quote(s["path"], safe="/")}">{escape(s["path"])}</a>'
                      f' · {escape(s.get("scope", "pinned historical source"))} · SHA-256 <code>{s["sha256"]}</code></li>'
                      for s in data["sources"].values())
    surfaces = "".join(f'<li>{count} {escape(surface)} commands</li>' for surface, count in data["current_command_surfaces"].items())
    return Template((root / "site/templates/history.html").read_text()).substitute(
        product_name=escape(product_name), package_version=escape(version), events=events,
        archive_version=escape(data["snapshot"]["version"]), audit_date=escape(data["snapshot"]["audit_date"]),
        testimony=escape(data["testimony"]["summary"]), manifest_sha=escape(data["manifest_sha"]), surfaces=surfaces,
        admin_prs=data["overhead"]["admin_refresh_prs"], total_prs=data["overhead"]["total_prs"],
        window=escape(" to ".join(data["overhead"]["window"])), sources=sources,
        provenance=escape(projection_provenance(build_commit)),
    ).rstrip() + "\n"
