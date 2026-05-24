from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RULE_PRESERVATION = Path(".agentic/rule_preservation.yaml")

@dataclass(frozen=True)
class RulePreservationFinding:
    rule_id: str
    path: str
    message: str

def load_rule_registry(path: Path = RULE_PRESERVATION) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError(f"{path}: rules must be a non-empty list")
    return data

def validate_rule_preservation(path: Path = RULE_PRESERVATION) -> list[RulePreservationFinding]:
    data = load_rule_registry(path)
    findings: list[RulePreservationFinding] = []
    seen: set[str] = set()
    for rule in data["rules"]:
        if not isinstance(rule, dict):
            findings.append(RulePreservationFinding("<invalid>", str(path), "rule entry must be a mapping"))
            continue
        rule_id = str(rule.get("id", ""))
        if not rule_id:
            findings.append(RulePreservationFinding("<missing>", str(path), "rule id missing"))
            continue
        if rule_id in seen:
            findings.append(RulePreservationFinding(rule_id, str(path), "duplicate rule id"))
        seen.add(rule_id)
        if rule.get("status") != "active":
            continue
        surfaces = rule.get("surfaces") or []
        terms = rule.get("required_terms") or []
        if not surfaces or not terms:
            findings.append(RulePreservationFinding(rule_id, str(path), "active rule needs surfaces and required_terms"))
            continue
        combined: list[str] = []
        for surface in surfaces:
            surface_path = Path(str(surface))
            if not surface_path.exists():
                findings.append(RulePreservationFinding(rule_id, str(surface_path), "surface missing"))
                continue
            combined.append(surface_path.read_text(encoding="utf-8"))
        haystack = "\n".join(combined)
        for term in terms:
            if str(term) not in haystack:
                findings.append(RulePreservationFinding(rule_id, str(path), f"required term missing: {term}"))
    return findings
