"""Join static, test-trace, simulation-trace and historical evidence per Kit command.

Usage: python compare_sources.py <kit_root> <static_csv> <trace_tests.jsonl> <trace_sim.jsonl>
                                 <hist_traces.jsonl> <commit_signatures.csv> <out_csv> <out_summary.json>
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

kit, static_csv, t_tests, t_sim, hist, commits, out_csv, out_sum = sys.argv[1:9]
m = {c["qualified_name"]: c for c in json.load(open(Path(kit) / "docs/reference/agentic-kit-commands.json"))["commands"]}
orch = {q for q, c in m.items() if c["surface"] == "orchestrator"}
static = {r["command"]: r for r in csv.DictReader(open(static_csv))}


def load_trace(path):
    recs = [json.loads(line) for line in open(path)] if Path(path).exists() else []
    invoked = Counter(x["command"] for x in recs if x["kind"] == "cli")
    within = defaultdict(set)
    for x in recs:
        for a in x["ancestry"]:
            if a in orch and a != x["command"]:
                within[x["command"]].add(a)
    return recs, invoked, within


tr, t_inv, t_within = load_trace(t_tests)
sr, s_inv, s_within = load_trace(t_sim)
hrecs = [json.loads(line) for line in open(hist)]
h_runs = defaultdict(set)
for x in hrecs:
    if x["class"] == "executed":
        h_runs[x["command"]].add((x["commit"], x["path"]))

rows = []
for q, c in m.items():
    st = static.get(q, {})
    rows.append({
        "command": q, "surface": c["surface"], "safety": c["safety"],
        "static_used_by_orchestrators": int(st.get("used_by_n_orchestrators_transitive") or 0),
        "tests_invoked_count": t_inv.get(q, 0),
        "tests_used_inside_orchestrators": len(t_within.get(q, ())),
        "sim_invoked_count": s_inv.get(q, 0),
        "sim_used_inside_orchestrators": len(s_within.get(q, ())),
        "sim_orchestrators": "; ".join(sorted(x.replace("agentic-kit ", "") for x in s_within.get(q, ()))),
        "history_evidence_runs": len(h_runs.get(q, ())),
    })


def tier(r):
    if r["surface"] == "orchestrator":
        return "orchestrator"
    if r["sim_used_inside_orchestrators"] or r["history_evidence_runs"]:
        return "A: dynamically used (simulation or real evidence)"
    if r["static_used_by_orchestrators"]:
        return "B: reachable from orchestrators, not exercised"
    if r["tests_invoked_count"]:
        return "C: only exercised by tests"
    return "D: never exercised anywhere"


for r in rows:
    r["tier"] = tier(r)
rows.sort(key=lambda r: (r["tier"], -r["sim_invoked_count"], r["command"]))
with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

non = [r for r in rows if r["surface"] != "orchestrator"]
summary = {
    "tiers": dict(Counter(r["tier"] for r in rows)),
    "tiers_by_surface": {t: dict(Counter(r["surface"] for r in non if r["tier"] == t)) for t in sorted({r["tier"] for r in non})},
    "static_used_nonorch": sum(1 for r in non if r["static_used_by_orchestrators"]),
    "sim_used_inside_orch_nonorch": sum(1 for r in non if r["sim_used_inside_orchestrators"]),
    "sim_invoked_any": sum(1 for r in rows if r["sim_invoked_count"]),
    "tests_invoked_any": sum(1 for r in rows if r["tests_invoked_count"]),
    "history_executed_any": sum(1 for r in rows if r["history_evidence_runs"]),
    "dynamic_not_static": sorted(r["command"] for r in non if r["sim_used_inside_orchestrators"] and not r["static_used_by_orchestrators"]),
    "static_not_dynamic": sorted(r["command"] for r in non if r["static_used_by_orchestrators"] and not r["sim_used_inside_orchestrators"]),
    "orchestrators_sim_invoked": sum(1 for q in orch if s_inv.get(q)),
}
json.dump(summary, open(out_sum, "w"), indent=1)
print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, list)}, indent=1))
print("dynamic_not_static", len(summary["dynamic_not_static"]), "static_not_dynamic", len(summary["static_not_dynamic"]))
