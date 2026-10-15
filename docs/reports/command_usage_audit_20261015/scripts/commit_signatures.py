"""Classify every commit on main by the Kit code path that produced it (commit-message signatures).

Signatures are taken from message templates in the Kit source (see SIGNATURES).
Usage: python commit_signatures.py <history_clone> <out.csv> <out_monthly.json>
"""
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict

hist, out_csv, out_month = sys.argv[1:4]

# (label, regex on subject, regex on body or None, producing code path)
SIGNATURES = [
    ("admin-refresh-pr", r"^Refresh handoff state after PR ?\d+", None,
     "transfer_repo_actions.admin_refresh_pr <- transfer admin-refresh-pr / post-merge-settle / pr-closeout-complete / post-merge-complete / pr-complete"),
    ("successor-package-refresh", r"^Refresh successor package after PR ?\d+", None,
     "transfer_repo_actions.successor_package_refresh_pr <- post-merge-settle / post-merge lifecycle"),
    ("successor-handoff-refresh", r"^Refresh successor handoff after PR ?\d+", None, "legacy handoff refresh (pre-admin-refresh)"),
    ("release-run:prepare", r"^Prepare release \d+\.\d+\.\d+", None, "release_run B4 (work finish)"),
    ("release-run:doi", r"^Record DOI for release \d+\.\d+\.\d+", None, "release_run D4 (work finish)"),
    ("remote-next:publish", r"^Publish (final )?remote-next", None, "transfer_remote_next"),
    ("legacy-release-metadata", r"^(Prepare v\d+\.\d+\.\d+ .*release|Record v\d+\.\d+\.\d+ DOI|Finalize state after v|Close out v\d|Update docs with v|Prepare v\d+\.\d+\.\d+ release|Release \d+\.\d+\.\d+|Prepare release v)", None,
     "pre-release-run release flow"),
    ("merge-verification-log", r"^(Record|Preserve) .*(merge verification|closeout evidence|post-merge main verification)", None, "evidence finalize-log era"),
    ("manual-merge-commit", r"^Merge pull request #\d+", None, "GitHub merge commit (not Kit squash path)"),
]
WORK_FINISH_BODY = re.compile(r"^\* Refresh handoff for ", re.M)

raw = subprocess.run(["git", "-C", hist, "log", "--first-parent", "--format=%x1e%H%x1f%cI%x1f%s%x1f%b"],
                     capture_output=True, text=True).stdout
rows = []
for rec in raw.split("\x1e")[1:]:
    h, t, s, b = rec.split("\x1f", 3)
    label = None
    for lab, sre, bre, _ in SIGNATURES:
        if re.search(sre, s):
            label = lab
            break
    pr = re.search(r"\(#(\d+)\)\s*$", s)
    wf = bool(WORK_FINISH_BODY.search(b))
    if label is None:
        label = "product-pr" if pr else "direct-commit"
    rows.append({"date": t[:10], "commit": h[:10], "pr": pr.group(1) if pr else "", "label": label,
                 "work_finish_signature": wf, "subject": s})

with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

month = defaultdict(Counter)
for r in rows:
    m = r["date"][:7]
    month[m][r["label"]] += 1
    if r["label"] in ("product-pr", "release-run:prepare", "release-run:doi") and r["work_finish_signature"]:
        month[m]["product-pr via work finish"] += 1
first_wf = min((r["date"] for r in rows if r["work_finish_signature"]), default=None)
first_rr = min((r["date"] for r in rows if r["label"].startswith("release-run")), default=None)
summary = {"months": {k: dict(v) for k, v in sorted(month.items())}, "total": dict(Counter(r["label"] for r in rows)),
           "first_work_finish_signature": first_wf, "first_release_run_signature": first_rr,
           "signatures": {lab: src for lab, _, _, src in SIGNATURES}}
json.dump(summary, open(out_month, "w"), indent=1)
print(json.dumps(summary["total"], indent=1), first_wf, first_rr)
