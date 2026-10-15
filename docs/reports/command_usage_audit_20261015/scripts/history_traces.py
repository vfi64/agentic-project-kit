"""Extract executed agentic-kit invocations from all historical evidence versions.

Usage: python history_traces.py <kit_checkout_for_manifest> <history_clone> <hist_rows.tsv> <out.jsonl>

hist_rows.tsv: commit<TAB>iso_date<TAB>blob_oid<TAB>path  (one line per added/modified version)
Rules: "latest"/rolling files -> every version is one run; other files -> last version per path.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_traces import Matcher, extract  # noqa: E402

kit, hist, rows_path, out_path = map(Path, sys.argv[1:5])
m = Matcher(kit / "docs/reference/agentic-kit-commands.json")
rows = [ln.split("\t") for ln in rows_path.read_text().splitlines() if ln.strip()]
rows = [r for r in rows if "handoff-packages/" not in r[3]]


def rolling(p):
    n = p.lower()
    return "latest" in n or "last_result" in n or "current" in n.rsplit("/", 1)[-1]


# git log is newest-first: the first occurrence of a non-rolling path is its last version
seen_paths, selected = set(), []
for c, t, oid, p in rows:
    if rolling(p):
        selected.append((c, t, oid, p))
    elif p not in seen_paths:
        seen_paths.add(p)
        selected.append((c, t, oid, p))

proc = subprocess.Popen(["git", "-C", str(hist), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
n_exec = 0
with open(out_path, "w") as out:
    for c, t, oid, p in selected:
        proc.stdin.write((oid + "\n").encode())
        proc.stdin.flush()
        header = proc.stdout.readline().decode().split()
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        text = data.decode("utf-8", errors="replace")
        for cls, q, d in extract(text, p, m):
            if cls == "mention":
                continue
            n_exec += cls == "executed"
            out.write(json.dumps({"date": t[:10], "commit": c[:10], "path": p, "class": cls, "command": q}) + "\n")
proc.stdin.close()
print("selected versions", len(selected), "executed hits", n_exec)
