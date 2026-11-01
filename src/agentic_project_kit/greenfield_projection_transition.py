"""Real A/B/A-prime installation contract; only PR observations are synthetic."""

from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import venv

from agentic_project_kit.greenfield_projection_wheels import build_fixture_wheels, dependency_wheels


@contextmanager
def _index(base):
    wheels = base / "wheels"
    kits = build_fixture_wheels(wheels)
    dependencies = dependency_wheels(wheels)
    for path in [*kits.values(), *dependencies]:
        name = path.name.split("-", 1)[0].replace("_", "-")
        page = base / "simple" / name / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with page.open("a") as stream:
            stream.write(f'<a href="../../wheels/{path.name}#sha256={digest}">{path.name}</a>\n')

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(base)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/simple", wheels, kits
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


class _Workspace:
    def __init__(self, root, wheels, env):
        self.root, self.env = root, env
        root.mkdir(parents=True)
        venv.EnvBuilder(with_pip=True).create(root / ".venv")
        self.python = root / ".venv/bin/python"
        self.call([str(self.python), "-I", "-m", "pip", "--isolated", "install", "--no-index", "--find-links", str(wheels), "agentic-project-kit==1.1.11"])
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Local fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def call(self, argv, *, allow_failure=False):
        result = subprocess.run(argv, cwd=self.root, env=self.env, capture_output=True, text=True, timeout=600)
        if result.returncode and not allow_failure:
            raise RuntimeError(f"fixture subprocess failed: {argv[:5]}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
        return result

    def git(self, *args):
        return self.call(["git", *args]).stdout.strip()

    def script(self, code, *args):
        result = self.call([str(self.python), "-I", "-c", code, *map(str, args)])
        return json.loads(result.stdout)

    def cli(self, *args, allow_failure=False):
        return self.call([str(self.python), "-I", "-m", "agentic_project_kit.cli", *args], allow_failure=allow_failure)

    def initialize(self, url):
        self.script(r"""
import json,pathlib,sys,yaml
from agentic_project_kit.workspace_init import build_workspace_init_plan,execute_workspace_init
r=pathlib.Path.cwd(); execute_workspace_init(build_workspace_init_plan(r,name='external',execute=True,inject_ci=True))
p=r/'.agentic/config.yaml'; c=yaml.safe_load(p.read_bytes()); c['kit']={'interpreter':sys.executable,'index_url':sys.argv[1]}; p.write_text(yaml.safe_dump(c,sort_keys=False))
with (r/'.gitignore').open('a') as f: f.write('\n/.venv/\n')
print(json.dumps({'status':'PASS'}))
""", url)
        self.cli("commands", "sync-entrypoints", "--execute", "--json")
        self.git("add", ".")
        self.git("commit", "-m", "Seed external workspace")
        self.cli("transfer", "prepare-successor-handoff", "--json")
        self.git("add", ".")
        self.git("commit", "-m", "Pinned v1 handoff")
        origin = self.root.parent / (self.root.name + "-origin.git")
        self.git("clone", "--bare", ".", str(origin))
        self.git("remote", "add", "origin", str(origin))
        self.git("fetch", "origin")
        # Origin identity is a durable projection input, so generate once more.
        self.cli("transfer", "prepare-successor-handoff", "--json")
        self.git("add", ".")
        if self.git("status", "--porcelain"):
            self.git("commit", "-m", "Bind local origin")
        self.git("push", "origin", "main")

    def update(self, version, *, unsupported=False):
        return self.script("""
import json,pathlib,sys
from agentic_project_kit.kit_update import run_kit_update
if sys.argv[2]=='unsupported':
 import agentic_project_kit.kit_update_projection as p
 p.preview_target_projection=lambda *a,**k: {}
r=pathlib.Path.cwd(); plan=run_kit_update(r,sys.argv[1])
assert plan['result_status']=='AWAITING_APPROVAL',plan
result=run_kit_update(r,sys.argv[1],execute=True,expected_signature=plan['approval_signature'])
print(json.dumps({'plan':plan,'result':result}))
""", version, "unsupported" if unsupported else "normal")

    def checks(self):
        assert json.loads(self.cli("check", "--json").stdout)["status"] == "PASS"
        assert self.cli("doctor").stdout.strip().endswith("Overall: PASS")

    def snapshot(self):
        return {p: (self.root / p).read_bytes() for p in self.git("ls-files").splitlines()}

    def squash(self, branch, message):
        head = self.git("rev-parse", "HEAD")
        self.git("switch", "main")
        self.git("merge", "--squash", branch)
        self.git("commit", "-m", message)
        self.git("push", "origin", "main")
        return head, self.git("rev-parse", "HEAD")


def run_transition(base: Path) -> dict:
    """All installation and checks run from noneditable, workspace-owned wheels."""
    base.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "PIP_CONFIG_FILE": os.devnull, "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    env.pop("PYTHONPATH", None)
    with _index(base / "index") as (url, wheels, kits):
        ws = _Workspace(base / "consumer", wheels, env)
        ws.initialize(url)
        baseline = ws.snapshot()
        ws.git("switch", "-c", "adoption")
        adopted = ws.update("1.1.12")
        assert adopted["result"]["result_status"] == "PASS", adopted
        paths = adopted["result"]["changed_paths"]
        assert ".agentic/config.yaml" in paths and ".gitignore" in paths, paths
        assert any(p.endswith("successor_context.yaml") for p in paths)
        adoption_id = adopted["result"]["adoption_id"]
        ws.checks()
        ws.git("add", ".")
        ws.git("commit", "-m", "Adopt active B")
        ws.script("""
import json,pathlib,subprocess,sys
from agentic_project_kit.kit_return import bind_adoption_pr
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
bind_adoption_pr(pathlib.Path.cwd(),branch='adoption',number=101,head=head)
print(json.dumps({'status':'PASS'}))
""")
        _, adoption_merge = ws.squash("adoption", "Squash B adoption")
        (ws.root / "product.txt").write_text("Unrelated later product work\n")
        ws.git("add", "product.txt")
        ws.git("commit", "-m", "Later product squash")
        ws.git("push", "origin", "main")
        post_merge = json.loads(ws.cli("transfer", "post-merge-check", "--json").stdout)
        assert post_merge["result_status"] == "PASS", post_merge
        ws.git("switch", "-c", "return")
        reverted = ws.script("""
import json,pathlib,sys
from agentic_project_kit.kit_return import run_return_revert
observe=lambda n: {'number':n,'state':'MERGED','baseRefName':'main','mergeCommit':{'oid':sys.argv[2]}}
r=pathlib.Path.cwd(); p=run_return_revert(r,sys.argv[1],observe_pr=observe)
assert p['result_status']=='AWAITING_APPROVAL',p
x=run_return_revert(r,sys.argv[1],execute=True,expected_signature=p['approval_signature'],observe_pr=observe)
print(json.dumps(x))
""", adoption_id, adoption_merge)
        assert reverted["result_status"] == "REVERT_PREPARED", reverted
        for path, content in baseline.items():
            assert (ws.root / path).read_bytes() == content, path
        ws.git("commit", "-m", "Exact evidence-bound return")
        ws.script("""
import json,pathlib,subprocess
from agentic_project_kit.kit_return import bind_return_pr
from agentic_project_kit.kit_update_runtime import UpdateRunner
r=pathlib.Path.cwd(); run=UpdateRunner(r,r/'.agentic/tmp/bind-return.jsonl')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
bind_return_pr(r,branch='return',number=102,head=head,run=run)
print(json.dumps({'status':'PASS'}))
""")
        return_head, return_merge = ws.squash("return", "Squash return")
        returned = ws.script("""
import json,pathlib,sys
from agentic_project_kit.kit_return import run_install_return
observe=lambda n: {'number':n,'state':'MERGED','baseRefName':'main','headRefOid':sys.argv[2],'mergeCommit':{'oid':sys.argv[3]}}
r=pathlib.Path.cwd(); p=run_install_return(r,sys.argv[1],observe_pr=observe)
assert p['result_status']=='AWAITING_APPROVAL',p
x=run_install_return(r,sys.argv[1],execute=True,expected_signature=p['approval_signature'],observe_pr=observe)
print(json.dumps(x))
""", adoption_id, return_head, return_merge)
        assert returned["result_status"] == "PASS", returned
        ws.checks()
        for path, content in baseline.items():
            assert (ws.root / path).read_bytes() == content, path
        assert (ws.root / "product.txt").read_text() == "Unrelated later product work\n"
        ws.cli("transfer", "prepare-successor-handoff", "--json")
        regenerated = json.loads((ws.root / ".agentic/state/handoff/packages/latest/validation_report.json").read_bytes())
        assert "generated_head" in regenerated and "input_digest" not in regenerated, regenerated
        ws.git("add", ".")
        ws.git("commit", "-m", "Generate v1 under returned A")
        ws.git("switch", "-c", "a-prime")
        prime = ws.update("1.1.11.post1")
        assert prime["result"]["result_status"] == "PASS", prime
        assert not any("handoff" in p or p == ".agentic/config.yaml" for p in prime["result"]["changed_paths"]), prime
        legacy = _Workspace(base / "legacy", wheels, env)
        legacy.initialize(url)
        legacy.git("switch", "-c", "direct-jump")
        first = legacy.update("1.1.12", unsupported=True)
        assert first["result"]["result_status"] == "BLOCKED", first
        diagnosis = legacy.cli("check", "--json", allow_failure=True)
        assert diagnosis.returncode and "NEEDS_PROJECTION_MIGRATION" in diagnosis.stdout, diagnosis.stdout
        assert "adoption_id" not in first["result"], first
        legacy.cli("transfer", "prepare-successor-handoff", "--json")
        repeated = legacy.update("1.1.12")
        assert repeated["result"]["result_status"] == "PASS", repeated
        assert repeated["result"]["changed_paths"] == [], repeated
        legacy.checks()
        return {"a_to_b": "PASS", "return_to_a": "PASS", "a_to_a_prime": "PASS", "legacy_completion": "PASS",
                "installer": "real_wheels", "planner": "installed_predecessor_A", "pr_observation": "test_double",
                "wheel_sha256": {v: hashlib.sha256(p.read_bytes()).hexdigest() for v, p in kits.items()}}
