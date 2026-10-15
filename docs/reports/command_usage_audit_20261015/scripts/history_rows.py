"""List every historical version of evidence files and batch-fetch their blobs (partial clone).

Usage: python history_rows.py <blobless clone> <out hist_rows.tsv>
Output columns: commit, ISO date, blob oid, path.
"""
import re
import subprocess
import sys

hist, out = sys.argv[1:3]
raw = subprocess.run(["git", "-C", hist, "log", "--format=C %H %cI", "--raw", "--no-abbrev", "--diff-filter=AM", "--",
                      "docs/reports/**", ".agentic/transfer/**"], capture_output=True, text=True, check=True).stdout
rows, cur = [], None
for line in raw.splitlines():
    if line.startswith("C "):
        _, h, t = line.split()
        cur = (h, t)
    elif line.startswith(":"):
        meta, path = line.split("\t", 1)
        oid = meta.split()[3]
        if "handoff-packages/" in path:
            continue
        if re.search(r"\.(log|json|txt)$", path) or (path.endswith(".md") and ("command_runs" in path or "/release/" in path)):
            rows.append((cur[0], cur[1], oid, path))
open(out, "w").write("\n".join("\t".join(r) for r in rows) + "\n")
oids = sorted({r[2] for r in rows})
subprocess.run(["git", "-C", hist, "-c", "fetch.negotiationAlgorithm=noop", "fetch", "-q", "--no-tags",
                "--no-write-fetch-head", "--filter=blob:none", "--stdin", "origin"],
               input="\n".join(oids) + "\n", text=True, check=False)
print(len(rows), "versions", len(oids), "blobs")
