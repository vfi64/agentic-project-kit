#!/usr/bin/env python3
"""Runner: static + dynamic + historical audit of which Kit commands the orchestrators use.

Each step runs only if the previous one returned rc=0; control output goes to <out>/run.log.

Stages (static always; others opt-in):
  static   map_callbacks -> analyze -> aggregate                      (~1 min)
  tests    pytest under the runtime tracer                             (~10 min, --with-tests)
  sim      sandbox (make_sandbox) + golden path + orchestrator sweep   (~45 min, --with-sim)
  history  evidence-log extraction + commit signatures from a full
           blobless clone of the Kit repository                        (~3 min, --history-clone)
  compare  joins everything into kit_command_usage_dynamic.csv

Usage:
  python3 run_usage_audit.py --repo <Kit checkout> --kit-python <venv python with Kit + dev deps>
         [--with-tests] [--with-sim] [--history-clone <blobless clone>] [--out usage-audit-out]

Make a history clone once with:
  git clone --filter=blob:none --no-checkout https://github.com/vfi64/agentic-project-kit <dir>
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--kit-python", default=None)
    ap.add_argument("--out", default="usage-audit-out", type=Path)
    ap.add_argument("--with-tests", action="store_true")
    ap.add_argument("--with-sim", action="store_true")
    ap.add_argument("--history-clone", type=Path, default=None)
    a = ap.parse_args()

    repo = a.repo.resolve()
    kp = a.kit_python or str(repo / ".venv" / "bin" / "python")
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    py = [sys.executable, "-I"]
    tracer_env = {"KIT_TRACE_TARGETS": str(out / "targets.json"), "PYTHONPATH": str(HERE / "tracer")}

    steps: list[tuple[str, list[str], Path, dict]] = [
        ("map-callbacks", [kp, str(HERE / "map_callbacks.py"), str(out / "callbacks.json")], repo, {}),
        ("analyze", py + [str(HERE / "analyze.py"), str(repo), str(out / "callbacks.json"), str(out / "result.json")], out, {}),
        ("aggregate", py + [str(HERE / "aggregate.py"), str(repo), str(out / "result.json"),
                            str(out / "kit_command_usage.csv"), str(out / "summary.json")], out, {}),
        ("build-targets", [kp, str(HERE / "build_targets.py"), str(out / "callbacks.json"), str(out / "result.json"),
                           str(out / "targets.json")], repo, {}),
    ]
    if a.with_tests:
        steps.append(("pytest-traced", [kp, "-m", "pytest", "-q", "-n", "auto", "-p", "no:cacheprovider"], repo,
                      {**tracer_env, "KIT_TRACE_LOG": str(out / "trace_tests.jsonl")}))
    if a.with_sim:
        sb = out / "sandbox"
        steps.append(("make-sandbox", py + [str(HERE / "sim" / "make_sandbox.py"), "--kit-root", str(repo),
                                            "--kit-python", kp, "--dir", str(sb)], out, {}))
        steps.append(("simulate", py + [str(HERE / "sim" / "run_simulation.py"), "--kit-python", kp, "--kit-root", str(repo),
                                        "--origin", str(sb / "origin.git"), "--pristine", str(sb / "origin-pristine.git"),
                                        "--gh-seed", str(sb / "gh-pristine.json"), "--out", str(out / "sim"),
                                        "--targets", str(out / "targets.json"), "--tracer-dir", str(HERE / "tracer"),
                                        "--scenario", "all"], out, {}))
        steps.append(("clean-sim-trace", py + ["-c", (
            "import json,sys; src,dst=sys.argv[1:3]; "
            "open(dst,'w').writelines(l for l in open(src) if not json.loads(l).get('test'))"),
            str(out / "sim" / "trace.jsonl"), str(out / "trace_sim.jsonl")], out, {}))
    if a.history_clone:
        hc = a.history_clone.resolve()
        steps.append(("history-rows", py + [str(HERE / "history_rows.py"), str(hc), str(out / "hist_rows.tsv")], out, {}))
        steps.append(("history-traces", py + [str(HERE / "history_traces.py"), str(repo), str(hc), str(out / "hist_rows.tsv"),
                                              str(out / "hist_traces.jsonl")], out, {}))
        steps.append(("commit-signatures", py + [str(HERE / "commit_signatures.py"), str(hc), str(out / "commit_signatures.csv"),
                                                 str(out / "commit_monthly.json")], out, {}))
    for name in ("trace_tests.jsonl", "trace_sim.jsonl", "hist_traces.jsonl"):
        p = out / name
        if not p.exists():
            p.write_text("")
    steps.append(("compare", py + [str(HERE / "compare_sources.py"), str(repo), str(out / "kit_command_usage.csv"),
                                   str(out / "trace_tests.jsonl"), str(out / "trace_sim.jsonl"), str(out / "hist_traces.jsonl"),
                                   str(out / "commit_signatures.csv"), str(out / "kit_command_usage_dynamic.csv"),
                                   str(out / "dynamic_summary.json")], out, {}))

    log = out / "run.log"
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True)
    with log.open("w", encoding="utf-8") as fh:
        fh.write(f"started={datetime.now().isoformat()} repo={repo} head={head.stdout.strip()}\n")
        for name, argv, cwd, extra in steps:
            env = {**os.environ, **extra}
            fh.write(f"\n=== {name}: {' '.join(argv)}\n")
            fh.flush()
            proc = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True)
            fh.write(proc.stdout[-20000:])
            fh.write(proc.stderr[-20000:])
            fh.write(f"rc={proc.returncode}\n")
            fh.flush()
            # a traced pytest run may contain environment-dependent failures; the trace is still valid
            if proc.returncode != 0 and name != "pytest-traced":
                print(f"STEP {name} FAILED rc={proc.returncode}; see {log}")
                return proc.returncode
            print(f"step {name}: rc={proc.returncode}")
        fh.write(f"\nfinished={datetime.now().isoformat()}\n")
    print(f"OK. Result: {out / 'kit_command_usage_dynamic.csv'}  summary: {out / 'dynamic_summary.json'}  log: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
