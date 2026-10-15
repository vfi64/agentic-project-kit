#!/usr/bin/env python3
"""Offline dynamic simulation of Kit orchestrators with runtime tracing.

Sandbox: local bare origin (rewritten from https://github.com/sim/kit-sim.git via url.insteadOf),
fake `gh`, the Kit venv linked as .venv, tracer via PYTHONPATH/sitecustomize.

Scenarios:
  golden   - realistic lifecycle: session-start, work start, edit, work finish (plan + execute),
             post-merge-settle, sync-main, release ready/prepare/run (plan only), docs sweep, ...
  sweep    - every orchestrator once, fresh sandbox each, in its default (safe/plan) mode with
             minimal required arguments.

Usage: python run_simulation.py --kit-python <venv python> --origin <bare.git> --out <dir>
                                --targets <targets.json> --tracer-dir <dir> [--scenario golden|sweep|all]
Each step's argv, rc, and output tail go to <out>/simulation.log (JSON lines in steps.jsonl).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE_URL = "https://github.com/sim/kit-sim.git"


def sh(argv, cwd, env, timeout=600):
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = 124, exc.stdout or "", f"TIMEOUT after {timeout}s"
        out = out if isinstance(out, str) else out.decode(errors="replace")
    return rc, out, err, round(time.time() - t0, 1)


class Sim:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.steps = open(self.out / "steps.jsonl", "a")
        self.log = open(self.out / "simulation.log", "a")
        self.gitcfg = self.out / "gitconfig"
        self.gitcfg.write_text(
            f'[user]\n\tname = Kit Simulation\n\temail = sim@example.invalid\n'
            f'[url "{Path(a.origin).resolve()}"]\n\tinsteadOf = {REMOTE_URL}\n'
            f'[init]\n\tdefaultBranch = main\n[advice]\n\tdetachedHead = false\n'
        )

    def env(self, scenario):
        e = dict(os.environ)
        venv_bin = str(Path(self.a.kit_python).parent)
        e["PATH"] = f"{HERE}:{venv_bin}:" + e["PATH"]
        e["GIT_CONFIG_GLOBAL"] = str(self.gitcfg)
        e["FAKE_GH_DB"] = str(self.out / f"gh-{scenario}.json")
        e["FAKE_GH_ORIGIN"] = str(Path(self.a.origin).resolve())
        e["FAKE_GH_LOG"] = str(self.out / "gh_calls.jsonl")
        e["KIT_TRACE_LOG"] = str(self.out / "trace.jsonl")
        e["KIT_TRACE_TARGETS"] = str(Path(self.a.targets).resolve())
        e["PYTHONPATH"] = str(Path(self.a.tracer_dir).resolve())  # extended with <work>/src per clone
        e["SIM_SCENARIO"] = scenario
        e.pop("KIT_TRACE_PARENT", None)
        e.pop("VIRTUAL_ENV", None)
        e["GH_TOKEN"] = "fake"
        e["CI"] = ""
        return e

    def reset_origin(self):
        origin = Path(self.a.origin).resolve()
        pristine = Path(self.a.pristine).resolve()
        if origin.exists():
            shutil.rmtree(origin)
        shutil.copytree(pristine, origin, symlinks=True)

    def fresh_clone(self, name):
        self.reset_origin()
        work = self.out / "work" / name
        if work.exists():
            shutil.rmtree(work)
        work.parent.mkdir(parents=True, exist_ok=True)
        env = self.env(name)
        sh(["git", "clone", "-q", REMOTE_URL, str(work)], self.out, env)
        venv = Path(self.a.kit_python).parent.parent
        (work / ".venv").symlink_to(venv)
        # run the sandbox's own Kit source (release steps change it), not the editable install
        env["PYTHONPATH"] = env["PYTHONPATH"] + os.pathsep + str(work / "src")
        # keep .venv out of git status in case the repo does not ignore symlinks
        with open(work / ".git" / "info" / "exclude", "a") as fh:
            fh.write("\n.venv\n")
        db = self.out / f"gh-{name}.json"
        if self.a.gh_seed:
            shutil.copy(self.a.gh_seed, db)
        elif db.exists():
            db.unlink()
        return work, env

    def step(self, scenario, label, argv, cwd, env, timeout=600):
        env = dict(env)
        env["SIM_STEP"] = label
        rc, out, err, dt = sh(argv, cwd, env, timeout)
        rec = {"scenario": scenario, "step": label, "argv": argv, "rc": rc, "seconds": dt,
               "stdout_tail": out[-1500:], "stderr_tail": err[-1500:]}
        self.steps.write(json.dumps(rec) + "\n")
        self.steps.flush()
        self.log.write(f"\n=== [{scenario}] {label}: {' '.join(argv)}\nrc={rc} ({dt}s)\n{out[-800:]}\n{err[-800:]}\n")
        self.log.flush()
        print(f"[{scenario}] {label:40} rc={rc} {dt}s", flush=True)
        return rc, out

    # ------------------------------------------------------------------ golden path
    def golden(self):
        sc = "golden"
        work, env = self.fresh_clone(sc)
        k = "agentic-kit"
        self.step(sc, "rules acknowledge", [k, "rules", "acknowledge"], work, env)
        self.step(sc, "chat session-start", [k, "chat", "session-start"], work, env)
        self.step(sc, "transfer sync-main", [k, "transfer", "sync-main"], work, env)
        # Follow the Kit's own NEXT guidance with orchestrators only, as an LLM driver would:
        # settle post-merge state, recover volatile projections, sync main, then retry work start.
        last_pr = 2506
        for attempt in range(1, 4):
            rc, _ = self.step(sc, f"work start (try {attempt})", [k, "work", "start", "--branch", "feature/sim-1", "--json"], work, env)
            if rc == 0:
                break
            db = json.load(open(env["FAKE_GH_DB"])) if Path(env["FAKE_GH_DB"]).exists() else {"prs": {}}
            merged = [int(n) for n, p in db["prs"].items() if p["state"] == "MERGED"]
            last_pr = max(merged) if merged else last_pr
            self.step(sc, f"post-merge-settle (prep {attempt})", [k, "transfer", "post-merge-settle", "--after-pr", str(last_pr)], work, env, timeout=1200)
            self.step(sc, f"work recover (prep {attempt})", [k, "work", "recover", "--json"], work, env)
            self.step(sc, f"transfer sync-main (prep {attempt})", [k, "transfer", "sync-main"], work, env)
        # a neutral product change that does not touch the documentation registry
        note = work / "src" / "agentic_project_kit" / "__init__.py"
        note.write_text(note.read_text() + "\n# simulation marker\n")
        self.step(sc, "work finish (plan)", [k, "work", "finish", "--branch", "feature/sim-1", "--title", "Add simulation note",
                                             "--message", "Add simulation note", "--path", "src/agentic_project_kit/__init__.py",
                                             "--release-note-category", "Changed", "--json"], work, env)
        rc, out = self.step(sc, "work finish (execute)", [k, "work", "finish", "--branch", "feature/sim-1", "--title", "Add simulation note",
                                                          "--message", "Add simulation note", "--path", "src/agentic_project_kit/__init__.py",
                                                          "--release-note-category", "Changed", "--execute", "--json"], work, env, timeout=1200)
        db = json.load(open(env["FAKE_GH_DB"])) if Path(env["FAKE_GH_DB"]).exists() else {"prs": {}}
        merged = [int(n) for n, p in db["prs"].items() if p["state"] == "MERGED"]
        if merged:
            self.step(sc, "post-merge-settle", [k, "transfer", "post-merge-settle", "--after-pr", str(max(merged))], work, env, timeout=1200)
        self.step(sc, "transfer sync-main (2)", [k, "transfer", "sync-main"], work, env)
        self.step(sc, "docs lifecycle sweep", [k, "docs", "lifecycle", "sweep"], work, env)
        self.step(sc, "release ready", [k, "release", "ready", "--version", "1.0.26", "--summary-line", "Add simulation note", "--summary-line", "Bounded read-only safety guard without remote effects", "--json"], work, env)
        self.step(sc, "release prepare", [k, "release", "prepare", "--version", "1.0.26", "--summary-line", "Add simulation note", "--summary-line", "Bounded read-only safety guard without remote effects", "--json"], work, env)
        rc, out_rr = self.step(sc, "release run (plan)", [k, "release", "run", "--version", "1.0.26", "--summary-line", "Add simulation note", "--summary-line", "Bounded read-only safety guard without remote effects", "--json"], work, env, timeout=1200)
        # drive the governed release run through its approval gates, as the Cockpit release button does
        base = [k, "release", "run", "--version", "1.0.26", "--summary-line", "Add simulation note",
                "--summary-line", "Bounded read-only safety guard without remote effects", "--json"]
        for i in range(1, 9):
            try:
                payload = json.loads(out_rr)
            except Exception:
                break
            if payload.get("result_status") != "AWAITING_APPROVAL":
                break
            sig = (payload.get("gate") or {}).get("approval_signature") or ""
            if not sig:
                import re as _re
                m = _re.search(r"--expected-signature (\S+)", payload.get("next_action") or "")
                sig = m.group(1) if m else ""
            gate = payload.get("current_step") or "?"
            rc, out_rr = self.step(sc, f"release run (approve {gate})", base + ["--execute", "--expected-signature", sig,
                                   "--approved-by", "simulation", "--consent-source", "simulation-run"], work, env, timeout=1500)
        self.step(sc, "transfer chat-switch-complete", [k, "transfer", "chat-switch-complete", "--json"], work, env)

    # ------------------------------------------------------------------ sweep
    def sweep(self):
        manifest = json.load(open(Path(self.a.kit_root) / "docs/reference/agentic-kit-commands.json"))["commands"]
        orch = [c for c in manifest if c["surface"] == "orchestrator"]
        defaults = {"--branch": "feature/sim-sweep", "--version": "1.0.26", "--after-pr": "1", "--title": "Sim",
                    "--message": "Sim", "--path": "README.md", "branch": "feature/sim-sweep", "--pr": "1",
                    "pr_number": "1", "--name": "sim", "--repo": "sim/kit-sim2", "--target": ".", "target": ".",
                    "--summary-line": "Sim", "--slice": "sim-slice", "--evidence-branch": "evidence/sim"}
        done = set()
        steps_file = self.out / "steps.jsonl"
        if self.a.resume and steps_file.exists():
            done = {json.loads(line)["scenario"] for line in open(steps_file) if line.strip()}
        for c in orch:
            name = c["qualified_name"]
            sc = "sweep:" + name.replace("agentic-kit ", "").replace(" ", "-")
            if sc in done:
                continue
            work, env = self.fresh_clone(sc.replace(":", "_"))
            argv = ["agentic-kit", *c["path"]]
            for p in c["params"]:
                if not p.get("required"):
                    continue
                is_arg = p.get("param_type") == "TyperArgument"
                key = p.get("name") if is_arg else (p.get("opts") or [p.get("name")])[0]
                val = defaults.get(key) or defaults.get(p.get("name")) or "sim"
                if is_arg:
                    argv.append(val)
                else:
                    argv += [key, val]
            self.step(sc, name.replace("agentic-kit ", ""), argv, work, env, timeout=900)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit-python", required=True)
    ap.add_argument("--kit-root", required=True)
    ap.add_argument("--origin", required=True)
    ap.add_argument("--pristine", required=True, help="bare repo copied over --origin before every scenario")
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--gh-seed", default=None, help="fake-gh database matching the pristine origin")
    ap.add_argument("--tracer-dir", required=True)
    ap.add_argument("--scenario", default="all")
    ap.add_argument("--resume", action="store_true", help="skip sweep scenarios already present in steps.jsonl")
    a = ap.parse_args()
    s = Sim(a)
    if a.scenario in ("golden", "all"):
        s.golden()
    if a.scenario in ("sweep", "all"):
        s.sweep()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
