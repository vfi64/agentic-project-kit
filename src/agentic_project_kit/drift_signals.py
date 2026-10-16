"""Known drift classes as read-only measurements (plan step drift-and-repeated-failure-checks).

The self-hosting drift audit (docs/reports/self-hosting/DRIFT_QUALITY_AUDIT_20261015.md) found
three measurable drift classes. Each signal below names its denominator; no general drift rate
is reported.

- ``release_projection``: the handoff ``release`` block against the Kit's release evidence
  (HD-08 class). Denominator: the keys of the release block.
- ``refresh_chains``: refresh-only commits that follow a product merge on the first-parent
  history. A chain of two or more refreshes means the first refresh did not settle the state.
  Denominator: product merges in the window.
- ``consumer_status``: findings the Kit marks CLOSED that a consumer ledger still marks OPEN.
  Denominator: Kit findings present in the consumer ledger. The consumer ledger is private and
  owned by the consumer, so it is read only from a path the maintainer passes.

The signals are report-only: they measure, they do not block.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

REFRESH_SUBJECT = re.compile(r"^Refresh (handoff state|successor package|successor handoff) after PR ?\d+")
PRODUCT_SUBJECT = re.compile(r"\(#\d+\)\s*$")
HANDOFF_STATE = Path(".agentic/handoff_state.yaml")


def release_projection_signal(root: Path) -> dict[str, Any]:
    from agentic_project_kit.handoff_release_facts import release_section_values, sync_release_section

    path = root / HANDOFF_STATE
    values = release_section_values(root)
    if not path.exists() or not values:
        return {"status": "not_measured", "reason": "no handoff state or no verified release evidence"}
    text = path.read_text(encoding="utf-8")
    synced = sync_release_section(text, root)
    drifted: list[str] = []
    if synced != text:
        current = (yaml.safe_load(text) or {}).get("release") or {}
        expected = (yaml.safe_load(synced) or {}).get("release") or {}
        drifted = sorted(key for key in expected if str(current.get(key)) != str(expected.get(key)))
    return {
        "status": "drift" if drifted else "consistent",
        "denominator": "release block keys backed by release evidence",
        "checked_keys": len(values),
        "drifted_keys": drifted,
    }


def refresh_chain_signal(root: Path, *, limit: int = 300) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "log", "--first-parent", "--reverse", f"-{limit}", "--format=%cs%x1f%s", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {"status": "not_measured", "reason": "git history unavailable"}
    rows = [line.split("\x1f", 1) for line in completed.stdout.splitlines() if "\x1f" in line]
    kinds = [
        "refresh" if REFRESH_SUBJECT.search(subject) else "product" if PRODUCT_SUBJECT.search(subject) else "other"
        for _, subject in rows
    ]
    counts = {"chain_0": 0, "chain_1": 0, "chain_2": 0, "chain_3plus": 0}
    long_chains: list[dict[str, Any]] = []
    index = 0
    while index < len(rows):
        if kinds[index] != "product":
            index += 1
            continue
        end = index + 1
        while end < len(rows) and kinds[end] == "refresh":
            end += 1
        length = end - index - 1
        counts["chain_3plus" if length >= 3 else f"chain_{length}"] += 1
        if length >= 2:
            long_chains.append({"date": rows[index][0], "product_subject": rows[index][1], "refreshes": length})
        index = end
    products = sum(counts.values())
    return {
        "status": "drift" if long_chains else "consistent",
        "denominator": "product merges on the first-parent history window",
        "window_commits": len(rows),
        "product_merges": products,
        **counts,
        "chain_2plus_share": round((counts["chain_2"] + counts["chain_3plus"]) / products, 4) if products else None,
        "recent_long_chains": long_chains[-5:],
    }


def consumer_status_signal(consumer_ledger: Path | None) -> dict[str, Any]:
    if consumer_ledger is None:
        return {"status": "not_measured", "reason": "pass --consumer-ledger with the consumer's findings ledger"}
    from agentic_project_kit.greenfield_status import read_status

    kit = {finding["id"]: finding for finding in read_status()["findings"]}
    try:
        consumer_data = json.loads(consumer_ledger.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "not_measured", "reason": f"consumer ledger unreadable: {type(exc).__name__}"}
    consumer = {
        str(family.get("id")): str(family.get("status") or "")
        for family in consumer_data.get("families", [])
        if isinstance(family, dict)
    }
    shared = sorted(set(kit) & set(consumer))
    closed_open = [fid for fid in shared if kit[fid].get("kit_state") == "CLOSED" and consumer[fid] == "OPEN"]
    return {
        "status": "drift" if closed_open else "consistent",
        "denominator": "Kit findings present in the consumer ledger",
        "shared_findings": len(shared),
        "kit_closed_consumer_open": closed_open,
        "status_authority": "consumer decides VERIFIED_FIXED; this signal only lists disagreements",
    }


def drift_signals(root: Path, *, consumer_ledger: Path | None = None) -> dict[str, Any]:
    signals = {
        "release_projection": release_projection_signal(root),
        "refresh_chains": refresh_chain_signal(root),
        "consumer_status": consumer_status_signal(consumer_ledger),
    }
    return {
        "schema_version": 1,
        "kind": "drift_signals",
        "result_status": "PASS",
        "report_only": True,
        "drift_signal_count": sum(1 for signal in signals.values() if signal.get("status") == "drift"),
        "signals": signals,
    }


def render_drift_signals(report: dict[str, Any]) -> str:
    lines = [
        "DRIFT_SIGNALS",
        f"STATUS={report['result_status']}",
        "REPORT_ONLY=true",
        f"DRIFT_SIGNAL_COUNT={report['drift_signal_count']}",
    ]
    for name, signal in report["signals"].items():
        details = {key: value for key, value in signal.items() if key not in {"status", "recent_long_chains"}}
        lines.append(f"SIGNAL={name}|{signal['status']}|{json.dumps(details, sort_keys=True)}")
    return "\n".join(lines)
