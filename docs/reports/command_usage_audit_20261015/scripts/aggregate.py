"""Aggregate orchestrator usage into per-command table + summary.

Usage: python aggregate.py <repo_root> <result.json> <out_csv> <out_summary_json>
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

repo = Path(sys.argv[1])
res = json.load(open(sys.argv[2]))
manifest = json.load(open(repo / "docs/reference/agentic-kit-commands.json"))["commands"]
by = {c["qualified_name"]: c for c in manifest}
orch = {q for q, c in by.items() if c["surface"] == "orchestrator"}
R = res["orchestrators"]

# Data-driven extension: workflow go -> tools/workflow_runner.py step vocabulary
WORKFLOW_GO_DATA = {"agentic-kit check-docs", "agentic-kit doctor"}

direct = {}
for q, v in R.items():
    d = set(v["subprocess"]) | set(v["inprocess_callback"]) | set(v["inprocess_core"])
    if q == "agentic-kit workflow go":
        d |= WORKFLOW_GO_DATA
    d.discard(q)
    direct[q] = d

# transitive through every command (an orchestrator may call a diagnostic that calls further commands)
trans = {}
for q in direct:
    seen, stack = set(), [q]
    while stack:
        x = stack.pop()
        for y in direct.get(x, ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    seen.discard(q)
    trans[q] = seen

used_by_direct = defaultdict(set)
used_by_trans = defaultdict(set)
channel = defaultdict(set)
for q in direct:
    if q not in orch:
        continue
    for c in direct[q]:
        used_by_direct[c].add(q)
    for c in trans[q]:
        used_by_trans[c].add(q)
    for c in R[q]["subprocess"]:
        channel[c].add("subprocess")
    for c in R[q]["inprocess_core"] + R[q]["inprocess_callback"]:
        channel[c].add("inprocess")
for c in WORKFLOW_GO_DATA:
    channel[c].add("workflow-data")

text_only = defaultdict(set)
for q, v in R.items():
    if q not in orch:
        continue
    for c in v["text_mentions_only"]:
        if c not in trans[q]:
            text_only[c].add(q)

code_invoked_anywhere = set(res["global_refs"])

rows = []
for c in manifest:
    q = c["qualified_name"]
    rows.append(
        {
            "command": q,
            "surface": c["surface"],
            "safety": c["safety"],
            "remote_effects": ",".join(c["remote_effects"]),
            "used_by_n_orchestrators_direct": len(used_by_direct[q]),
            "used_by_n_orchestrators_transitive": len(used_by_trans[q]),
            "channel": ",".join(sorted(channel[q])),
            "used_by_orchestrators": "; ".join(sorted(x.replace("agentic-kit ", "") for x in used_by_trans[q])),
            "only_recommended_in_orchestrator_text": "; ".join(sorted(x.replace("agentic-kit ", "") for x in text_only[q])) if not used_by_trans[q] else "",
            "invoked_as_argv_anywhere_in_package": q in code_invoked_anywhere,
            "orchestrator_uses_n_commands_transitive": len(trans[q]) if q in orch else "",
        }
    )
rows.sort(key=lambda r: (-r["used_by_n_orchestrators_transitive"], r["surface"], r["command"]))
with open(sys.argv[3], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# summary
def surf(cmds):
    out = defaultdict(int)
    for x in cmds:
        out[by[x]["surface"]] += 1
    return dict(out)

all_used = {q for q, v in used_by_trans.items() if v}
non_orch = {q for q in by if q not in orch}
summary = {
    "commit_note": "static analysis of vfi64/agentic-project-kit HEAD",
    "manifest_surfaces": surf(by),
    "used_by_any_orchestrator_transitive": len(all_used),
    "used_surfaces": surf(all_used),
    "non_orchestrator_total": len(non_orch),
    "non_orchestrator_used": len(non_orch & all_used),
    "non_orchestrator_unused": len(non_orch - all_used),
    "unused_surfaces": surf(non_orch - all_used),
    "unused_but_invoked_elsewhere_in_code": len((non_orch - all_used) & code_invoked_anywhere),
    "unused_only_text_recommended": len({q for q in non_orch - all_used if text_only[q]}),
    "orchestrators_called_by_other_orchestrators": sorted(orch & all_used),
    "orchestrators_using_no_other_command": sorted(q for q in orch if not trans[q]),
    "per_orchestrator": {q: {"direct": len(direct[q]), "transitive": len(trans[q])} for q in sorted(orch)},
    "orchestrators_using_no_other_command_direct": sorted(q for q in orch if not direct[q]),
    "top_used": [(q, len(used_by_trans[q])) for q in sorted(all_used, key=lambda x: -len(used_by_trans[x]))[:20]],
}
json.dump(summary, open(sys.argv[4], "w"), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k not in ("per_orchestrator",)}, indent=1))
