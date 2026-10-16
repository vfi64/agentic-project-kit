#!/usr/bin/env python3
"""Reproduce the measurable parts of the 2026-10-15 self-hosting drift and quality audit (issue #2505).

Read-only: never edits a repository and never runs git mutations or agentic-kit commands.

Subcommands
  join     Kit finding status x consumer ledger, ID-exact; writes the public join CSV (IDs, statuses, dates only).
           The consumer ledger lives in a private repository, so this step needs a local copy of it.
  prs      Classify Kit pull requests of a date window by their changed files and CI runtime (GitHub REST via `gh api`).
  chains   Length of administrative refresh chains after each product commit on main (needs a Kit clone with history).
  hashes   SHA-256 of input artefacts, to compare with SOURCE_MANIFEST.json.

Examples
  python3 reproduce_drift_audit.py join --kit external-findings-status.json --consumer AGENTIC_KIT_GREENFIELD_FINDINGS.json --out join.csv
  python3 reproduce_drift_audit.py prs --repo vfi64/agentic-project-kit --from 2026-10-01 --to 2026-10-15 --cutoff 2026-10-15T19:00:41Z --out prs.json
  python3 reproduce_drift_audit.py chains --clone ../kit-history --out chains.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
ANCHOR = re.compile(r"\bGF-E\d+\b|adoption evidence")

# ---------------------------------------------------------------- join

def first_date(text: str):
    m = DATE.search(text or "")
    return dt.date.fromisoformat(m.group()) if m else None


def join(kit: dict, consumer: dict):
    kid = {x["id"]: x for x in kit.get("findings", [])}
    cid = {x["id"]: x for x in consumer.get("families", [])}
    if len(kid) != len(kit.get("findings", [])) or len(cid) != len(consumer.get("families", [])):
        raise SystemExit("duplicate finding IDs: join would be ambiguous")
    rows, lags = [], []
    for i in sorted(set(kid) | set(cid)):
        k, c = kid.get(i, {}), cid.get(i, {})
        vb = json.dumps(c.get("verified_by") or "", ensure_ascii=False)
        f, v = first_date(c.get("first_observed") or ""), first_date(vb)
        lag = (v - f).days if f and v else None
        if c.get("status") == "VERIFIED_FIXED" and lag is not None:
            lags.append(lag)
        a = ANCHOR.search(vb)
        verification = (k.get("external_retest") or {}).get("verification") or ""
        rows.append({
            "finding_id": i,
            "kit_state": k.get("kit_state", "ABSENT"),
            "kit_fixed_in": k.get("fixed_in", ""),
            "kit_external_fixture_pass": bool(re.search(r"\bpass(?:ed)?\b", verification, re.I)),
            "consumer_status": c.get("status", "ABSENT"),
            "consumer_severity": c.get("severity", ""),
            "consumer_first_observed": f.isoformat() if f else "",
            "consumer_verified_date": v.isoformat() if v and c.get("status") == "VERIFIED_FIXED" else "",
            "consumer_verified_anchor": a.group() if a and c.get("status") == "VERIFIED_FIXED" else "",
            "verified_elapsed_calendar_days": lag if lag is not None and c.get("status") == "VERIFIED_FIXED" else "",
        })
    combos = collections.Counter(f"{r['kit_state']} -> {r['consumer_status']}" for r in rows)
    summary = {
        "kit_findings": len(kid), "consumer_families": len(cid),
        "consumer_observations": len(consumer.get("observations", [])),
        "cross_status_counts": dict(sorted(combos.items())),
        "closed_to_open_with_kit_fixture_pass": [r["finding_id"] for r in rows if r["kit_state"] == "CLOSED"
                                                 and r["consumer_status"] == "OPEN" and r["kit_external_fixture_pass"]],
        "verified_fixed_with_both_dates": len(lags),
        "verified_elapsed_days_median": statistics.median(lags) if lags else None,
        "verified_elapsed_days_mean": round(statistics.mean(lags), 2) if lags else None,
        "verified_elapsed_days_distribution": sorted(lags),
    }
    return rows, summary


# ---------------------------------------------------------------- prs

TITLE = re.compile(r"refresh.*handoff|handoff.*refresh|refresh.*successor", re.I)
ADMIN = re.compile(r"^(\.agentic/handoff_state\.yaml|\.agentic/operational_handoff_state\.yaml|"
                   r"\.agentic/dpa/acceptance/current_handoff_operational_state\.json|docs/STATUS\.md|"
                   r"docs/handoff/[^/]+\.md|docs/reports/handoff-packages/latest/.+|"
                   r"docs/reports/terminal/post-pr\d+-successor-chat-handoff\.md|"
                   r"\.agentic/rule_ack/.+|\.agentic/compiled_agent_context\.yaml|\.agentic/communication_[a-z_]+\.(json|yaml))$")
REFRESH_TOPIC = re.compile(r"refresh|handoff|successor|settle|post-merge|freshness", re.I)


def gh(path: str):
    for _ in range(3):
        p = subprocess.run(["gh", "api", path], capture_output=True, text=True)
        if p.returncode == 0 and p.stdout.strip():
            return json.loads(p.stdout)
    raise SystemExit(f"gh api failed: {path}: {p.stderr.strip()}")


def classify(title: str, files: list[str]) -> str:
    if not files:
        return "UNKNOWN"
    admin = [f for f in files if ADMIN.match(f)]
    other = [f for f in files if not ADMIN.match(f)]
    if admin and not other:
        return "ADMIN_REFRESH_ONLY"
    if any(f.startswith(("src/", "tests/")) for f in other) and REFRESH_TOPIC.search(title):
        return "REPAIR_OF_REFRESH_DEFECT"
    return "PRODUCT_PLUS_HANDOFF" if admin else "OTHER"


def prs(repo: str, start: str, end: str, cutoff: str):
    out, page = [], 1
    while True:
        batch = gh(f"repos/{repo}/pulls?state=all&sort=created&direction=desc&per_page=100&page={page}")
        out += [p for p in batch if start <= p["created_at"][:10] <= end and p["created_at"] <= cutoff]
        if not batch or batch[-1]["created_at"][:10] < start:
            break
        page += 1
    rows = []
    for p in out:
        files = []
        for fp in range(1, 4):
            b = gh(f"repos/{repo}/pulls/{p['number']}/files?per_page=100&page={fp}")
            files += [f["filename"] for f in b]
            if len(b) < 100:
                break
        runs = gh(f"repos/{repo}/actions/runs?head_sha={p['head']['sha']}&per_page=50")["workflow_runs"]
        secs = []
        for r in runs:
            try:
                secs.append((dt.datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
                             - dt.datetime.fromisoformat(r["run_started_at"].replace("Z", "+00:00"))).total_seconds())
            except (KeyError, TypeError, ValueError):
                pass
        rows.append({"number": p["number"], "created": p["created_at"][:10], "merged": bool(p["merged_at"]),
                     "title_match": bool(TITLE.search(p["title"])), "class": classify(p["title"], files),
                     "files": len(files), "ci_runs": len(runs), "ci_seconds": round(sum(secs))})
    by = {}
    for k in sorted({r["class"] for r in rows}):
        sub = [r for r in rows if r["class"] == k]
        by[k] = {"prs": len(sub), "merged": sum(r["merged"] for r in sub), "ci_runs": sum(r["ci_runs"] for r in sub),
                 "ci_minutes_wallclock": round(sum(r["ci_seconds"] for r in sub) / 60, 1),
                 "median_ci_seconds_per_pr": statistics.median([r["ci_seconds"] for r in sub])}
    return {"window": [start, end], "cutoff": cutoff, "total": len(rows),
            "title_matches": sum(r["title_match"] for r in rows), "by_class": by,
            "title_matches_by_class": dict(collections.Counter(r["class"] for r in rows if r["title_match"])),
            "rows": sorted(rows, key=lambda r: r["number"])}


# ---------------------------------------------------------------- chains

REFRESH_SUBJECT = re.compile(r"^Refresh (handoff state|successor package|successor handoff) after PR ?\d+")
PRODUCT_SUBJECT = re.compile(r"\(#\d+\)\s*$")


def chains(clone: Path):
    log = subprocess.run(["git", "-C", str(clone), "log", "--first-parent", "--reverse", "--format=%cs%x1f%s", "origin/main"],
                         capture_output=True, text=True, check=True).stdout.splitlines()
    rows = [line.split("\x1f", 1) for line in log]
    kind = ["refresh" if REFRESH_SUBJECT.search(s) else ("product" if PRODUCT_SUBJECT.search(s) else "other") for _, s in rows]
    months = collections.defaultdict(collections.Counter)
    i = 0
    while i < len(rows):
        if kind[i] == "product":
            j = i + 1
            while j < len(rows) and kind[j] == "refresh":
                j += 1
            months[rows[i][0][:7]][min(j - i - 1, 3)] += 1
            i = j
        else:
            i += 1
    return {"definition": "per product commit on main: directly following refresh-only commits before the next "
                          "non-refresh commit; chain_3plus means three or more",
            "months": {m: {"product_commits": sum(c.values()), "chain_0": c[0], "chain_1": c[1], "chain_2": c[2],
                           "chain_3plus": c[3]} for m, c in sorted(months.items())}}


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("join")
    a.add_argument("--kit", type=Path, required=True)
    a.add_argument("--consumer", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    b = sp.add_parser("prs")
    b.add_argument("--repo", default="vfi64/agentic-project-kit")
    b.add_argument("--from", dest="start", required=True)
    b.add_argument("--to", dest="end", required=True)
    b.add_argument("--cutoff", default="9999")
    b.add_argument("--out", type=Path, required=True)
    c = sp.add_parser("chains")
    c.add_argument("--clone", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    d = sp.add_parser("hashes")
    d.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    if args.cmd == "join":
        rows, summary = join(json.loads(args.kit.read_text(encoding="utf-8")), json.loads(args.consumer.read_text(encoding="utf-8")))
        with args.out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(json.dumps(summary, indent=1))
    elif args.cmd == "prs":
        res = prs(args.repo, args.start, args.end, args.cutoff)
        args.out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    elif args.cmd == "chains":
        res = chains(args.clone)
        args.out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(res, indent=1))
    else:
        for f in args.files:
            print(hashlib.sha256(f.read_bytes()).hexdigest(), f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
