"""Historical safety evidence, projected without raw logs or current-security claims."""
import hashlib
import json
import re
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import quote

BINDINGS = "site/content/safety_evidence_sources.json"


def _source(root: Path, binding: dict) -> str:
    path = binding["path"]
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not path.startswith("docs/reports/"):
        raise ValueError("safety evidence source escapes public reports")
    data = resolved.read_bytes()
    if hashlib.sha256(data).hexdigest() != binding["sha256"] or not re.fullmatch(r"[a-f0-9]{40}", binding["revision"]):
        raise ValueError("safety evidence changed: review source binding before publishing")
    return data.decode("utf-8")


def benchmark(data: dict) -> dict:
    rows = data["results"]
    if data.get("kind") != "gate_benchmark_part1" or not isinstance(rows, list):
        raise ValueError("invalid historical benchmark")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)) or data["scenario_count"] != len(rows):
        raise ValueError("benchmark scenario inventory disagrees")
    public = []
    for r in rows:
        skipped = bool(r.get("skipped"))
        detected = not skipped and r.get("control_returncode") == 0 and r.get("control_quiet") is True and r.get("fault_marker_seen") is True
        if r.get("detected") is not detected:
            raise ValueError("benchmark detection disagrees with control and fault observations")
        public.append({"id": r["id"], "fault_class": r["fault_class"], "detected": detected,
                       "applicable": not skipped, "control_returncode": r.get("control_returncode"),
                       "control_quiet": r.get("control_quiet") is True})
    detected = sum(r["detected"] for r in public)
    if detected != data["detected_count"]:
        raise ValueError("benchmark detection total disagrees")
    revision = data["sandbox_head"]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("benchmark sandbox revision missing")
    return {"detected": detected, "applicable": sum(r["applicable"] for r in public),
            "scenario_count": len(rows), "sandbox_revision": revision,
            "runtime": data.get("kit_under_test", "Editable development runtime; exact runtime revision not recorded"),
            "scenarios": public}


def review_rows(text: str) -> tuple[list[dict], list[dict]]:
    rows = []
    for line in text.splitlines():
        if line.startswith("| WOTB-"):
            cells = [x.strip().replace("`", "") for x in line.strip("|").split("|")]
            if len(cells) != 5:
                raise ValueError("historical finding table shape changed")
            rows.append(dict(zip(("id", "severity", "area", "gap", "probe"), cells, strict=True)))
    if [r["id"] for r in rows] != [f"WOTB-{i:02}" for i in range(1, 10)]:
        raise ValueError("expected reviewed WOTB-01 through WOTB-09")
    section = text.split("## Status after the first hardening slice", 1)[1].split("## Limits", 1)[0]
    groups = []
    for block in re.split(r"(?m)(?=^- \*\*Closed)", section)[1:]:
        header = block.splitlines()[0]
        ids = [f"WOTB-{i}" for i in re.findall(r"(?:WOTB)?-(\d{2})", header)]
        summary = " ".join(line.strip().removeprefix("- ") for line in block.splitlines()
                           if line.startswith("  - ")).replace("`", "")
        groups.append({"ids": ids, "summary": summary})
    if sorted(x for group in groups for x in group["ids"]) != sorted(r["id"] for r in rows):
        raise ValueError("historical mitigation coverage incomplete")
    return rows, groups


def collect_safety_evidence(root: Path) -> dict:
    bindings = json.loads((root / BINDINGS).read_text())
    keys = ("review", "baseline", "development", "method", "context_pilot")
    if set(bindings) != set(keys):
        raise ValueError("safety evidence source inventory changed")
    raw = {key: _source(root, bindings[key]) for key in keys}
    rows, groups = review_rows(raw["review"])
    dates = [re.search(r"\d{4}-\d{2}-\d{2}", raw[k].splitlines()[0]) for k in ("review", "method")]
    if not all(dates) or dates[0].group() != dates[1].group():
        raise ValueError("historical observation dates disagree")
    baseline, development = (benchmark(json.loads(raw[k])) for k in ("baseline", "development"))
    if [r["id"] for r in baseline["scenarios"]] != [r["id"] for r in development["scenarios"]]:
        raise ValueError("benchmark scenarios differ")
    return {"schema_version": 1, "kind": "historical_safety_evidence", "scope": "historical-observation", "observation_date": dates[0].group(),
            "findings": rows, "mitigations": groups, "baseline": baseline,
            "development": development, "sources": bindings}


def render_safety_evidence(root: Path, data: dict, *, repository_url: str, product_name: str) -> str:
    findings = "".join('<tr>' + ''.join(f'<td>{escape(row[k])}</td>' for k in ("id", "severity", "area", "gap")) + '</tr>'
                       for row in data["findings"])
    mitigations = "".join(f'<article class="panel"><h3>{escape(", ".join(g["ids"]))}</h3><p>{escape(g["summary"])}</p></article>'
                          for g in data["mitigations"])
    scenarios = "".join(f'<tr><td>{escape(a["id"])}</td><td>{escape(a["fault_class"])}</td>'
                         f'<td>{_outcome(a)}</td><td>{_outcome(b)}</td></tr>'
                         for a, b in zip(data["baseline"]["scenarios"], data["development"]["scenarios"], strict=True))
    sources = "".join(f'<li><a href="{escape(repository_url, quote=True)}/blob/{s["revision"]}/{quote(s["path"], safe="/")}">{escape(key)}</a>'
                      f' · source revision <code>{s["revision"]}</code> · SHA-256 <code>{s["sha256"]}</code></li>'
                      for key, s in data["sources"].items())
    baseline, development = data["baseline"], data["development"]
    return Template((root / "site/templates/evidence.html").read_text()).substitute(
        product_name=escape(product_name), findings=findings, mitigations=mitigations,
        finding_count=len(data["findings"]), observation_date=data["observation_date"],
        baseline_runtime=escape(baseline["runtime"]),
        baseline_skipped=baseline["scenario_count"] - baseline["applicable"],
        baseline_total=baseline["scenario_count"],
        scenarios=scenarios, sources=sources,
        baseline_count=f'{baseline["detected"]} of {baseline["applicable"]}',
        development_count=f'{development["detected"]} of {development["applicable"]}',
        baseline_revision=baseline["sandbox_revision"], development_revision=development["sandbox_revision"],
        development_runtime=escape(development["runtime"]),
    ).rstrip() + "\n"


def _outcome(row: dict) -> str:
    if not row["applicable"]:
        return "Not applicable (not injected)"
    if row["detected"]:
        return "Detected with clean control"
    if row["control_returncode"] != 0:
        return "Not detected; control failed or gate absent"
    return "Not detected"
