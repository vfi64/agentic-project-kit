#!/usr/bin/env python3
"""Create the offline sandbox origin used by run_simulation.py.

Steps: seed a bare repo from the Kit checkout's HEAD tree (one commit "Seed simulation baseline (#2505)",
tag v<version>), clone it through the rewritten GitHub URL, acknowledge rules and let the Kit's own
post-merge-settle create and merge the administrative handoff refresh PR via the fake gh. The resulting
bare repo and fake-gh database are the pristine starting state for every scenario.

Usage: python make_sandbox.py --kit-root <checkout> --kit-python <venv python> --dir <sandbox dir>
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE_URL = "https://github.com/sim/kit-sim.git"


def run(argv, cwd, env, check=True):
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    print(f"$ {' '.join(argv)}  -> rc={p.returncode}")
    if check and p.returncode != 0:
        print(p.stdout[-2000:], p.stderr[-2000:])
        sys.exit(p.returncode)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit-root", required=True)
    ap.add_argument("--kit-python", required=True)
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    root = Path(a.kit_root).resolve()
    d = Path(a.dir).resolve()
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    origin = d / "origin.git"
    gitcfg = d / "gitconfig"
    gitcfg.write_text(f'[user]\n\tname = Kit Simulation\n\temail = sim@example.invalid\n'
                      f'[url "{origin}"]\n\tinsteadOf = {REMOTE_URL}\n[init]\n\tdefaultBranch = main\n')
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": str(gitcfg), "PATH": f"{HERE}:{Path(a.kit_python).parent}:" + env["PATH"],
                "FAKE_GH_DB": str(d / "gh-pristine.json"), "FAKE_GH_ORIGIN": str(origin)})
    env.pop("VIRTUAL_ENV", None)
    version = run(["git", "-C", str(root), "describe", "--tags", "--abbrev=0"], d, env, check=False).stdout.strip() or "v0.0.0"

    seed = d / "seed"
    seed.mkdir()
    run(["git", "init", "-q", "-b", "main"], seed, env)
    archive = subprocess.run(["git", "-C", str(root), "archive", "HEAD"], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x"], input=archive, cwd=seed, check=True)
    run(["git", "add", "-A"], seed, env)
    run(["git", "commit", "-q", "-m", "Seed simulation baseline (#2505)"], seed, env)
    run(["git", "tag", version], seed, env)
    run(["git", "clone", "-q", "--bare", str(seed), str(origin)], d, env)
    shutil.rmtree(seed)

    (d / "gh-pristine.json").write_text(json.dumps({"next": 2506, "prs": {}}))
    work = d / "seedwork"
    run(["git", "clone", "-q", REMOTE_URL, str(work)], d, env)
    (work / ".venv").symlink_to(Path(a.kit_python).parent.parent)
    with open(work / ".git" / "info" / "exclude", "a") as fh:
        fh.write("\n.venv\n")
    env["PYTHONPATH"] = str(work / "src")
    run(["agentic-kit", "rules", "acknowledge"], work, env)
    p = run(["agentic-kit", "transfer", "post-merge-settle", "--after-pr", "2505"], work, env, check=False)
    print(p.stdout[-800:])
    shutil.copytree(origin, d / "origin-pristine.git", symlinks=True)
    print(f"PRISTINE={d / 'origin-pristine.git'}\nGH_SEED={d / 'gh-pristine.json'}\nGITCONFIG={gitcfg}")
    return 0 if "COMPLETE" in p.stdout or "READY" in p.stdout else 2


if __name__ == "__main__":
    raise SystemExit(main())
