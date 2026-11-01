"""GF-095 disposable real-Git contract with an explicit installation test double.

No remote service or invoking installation is touched. Git operations are real;
PR observations and installation are doubles. Target check/doctor run in fresh
isolated Python processes and validate the original v1 byte snapshot. The real
released-wheel consumer rehearsal remains a separate release requirement.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from agentic_project_kit.kit_update_runtime import UpdateBlocked


def _digest(content):
    return hashlib.sha256(content).hexdigest()


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


class InstallationDouble:
    """Only the installer/probe boundary is synthetic; the updater is real."""

    def __init__(self, root, run, snapshot, target):
        self.root, self.git_run, self.snapshot, self.target = root, run, snapshot, target
        self.version = "1.1.11"
        self.failure = None
        self.fresh_checks = []

    def discover(self, root, **kwargs):
        from agentic_project_kit.kit_installation import InstallationObservation, InterpreterCandidate, KitInstallationResolution

        prefix = self.root / ".agentic/tmp/installation-double"
        item = InterpreterCandidate(prefix / "bin/python", "workspace_venv", prefix)
        observed = InstallationObservation(
            item, "FOUND", "installed", self.version, str(prefix), "/synthetic-base",
            str(prefix / "lib/site-packages"), str(prefix / "lib/site-packages/agentic_project_kit/__init__.py"),
            wheel_sha256=self.target.artifacts[0]["sha256"] if self.version == "1.1.10" else "",
        )
        return KitInstallationResolution("FOUND", observed, (observed,))

    def __call__(self, argv, **kwargs):
        if argv[0] == "git":
            return self.git_run(argv, **kwargs)
        data, text, code = None, "", 0
        if "-c" in argv and "m.distributions()" in argv[argv.index("-c") + 1]:
            data = {"python": "installation test double", "packages": [["agentic-project-kit", self.version]],
                    "projection_contract_version": 2 if self.version == "1.1.11" else 1}
        elif "-c" in argv and "managed_ci_template_text" in argv[argv.index("-c") + 1]:
            data = {"kit_written": False, "template": ""}
        elif "sync-entrypoints" in argv:
            data = {"result_status": "PASS", "manifest_sha": "1" * 12, "changed_paths": []}
        elif "pip" in argv and "install" in argv:
            code = int(self.failure == "install")
            if not code:
                self.version = "1.1.10"
        elif "check" in argv or "doctor" in argv:
            kind = "doctor" if "doctor" in argv else "check"
            # A fresh process independently reads the restored bytes. This is
            # explicitly a legacy CLI double, never a claim about the real wheel.
            script = (
                "import hashlib,json,pathlib,sys; root=pathlib.Path(sys.argv[1]); "
                "expected=json.loads(sys.argv[2]); "
                "ok=all((root/p).is_file() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h "
                "for p,h in expected.items()) and sys.argv[3]!='fail'; "
                "print(('Overall: '+('PASS' if ok else 'FAIL')) if sys.argv[4]=='doctor' "
                "else json.dumps({'status':'PASS' if ok else 'FAIL'})); sys.exit(0 if ok else 1)"
            )
            actual = subprocess.run(
                [sys.executable, "-I", "-c", script, str(self.root), json.dumps(self.snapshot),
                 "fail" if self.failure == kind else "ok", kind],
                cwd=self.root, capture_output=True, text=True, check=False,
            )
            self.fresh_checks.append({"kind": kind, "installed": self.version, "returncode": actual.returncode})
            return actual
        else:
            raise UpdateBlocked(f"installation_double_unexpected_command: {argv[:4]}")
        return subprocess.CompletedProcess(argv, code, json.dumps(data) if data is not None else text, "")


def prepare_return_fixture(root: Path, variables, env):
    from agentic_project_kit.external_handoff_projection import check_projection, write_external_package
    from agentic_project_kit.kit_return import (
        record_adoption, bind_adoption_pr, plan_return_revert, execute_return_revert,
        bind_return_pr, verify_install_return,
    )
    from agentic_project_kit.kit_update import run_kit_update
    from agentic_project_kit.kit_update_artifacts import PreparedTarget
    from agentic_project_kit.successor_handoff_package import _build_legacy_successor_handoff_package
    from agentic_project_kit.workspace import load_workspace
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init, CI_TEMPLATE_PATH, CI_INJECTION_TARGET

    def run(argv, **kwargs):
        return subprocess.run(argv, cwd=root, env={**env, "GIT_OPTIONAL_LOCKS": "0"},
                              text=not kwargs.get("binary", False), capture_output=True, check=False)

    def git(*args):
        result = run(["git", *args])
        if result.returncode:
            raise RuntimeError(f"local_git_failed: {args}: {result.stderr}")
        return result.stdout.strip()

    plan = build_workspace_init_plan(root, name="external", execute=True, inject_ci=True)
    execute_workspace_init(plan)
    ws = load_workspace(root)
    config = root / ".agentic/config.yaml"
    import yaml
    original_config = yaml.safe_load(config.read_bytes())
    original_config.pop("handoff", None)
    config.write_text(yaml.safe_dump(original_config, sort_keys=False))
    for name in (CI_TEMPLATE_PATH, CI_INJECTION_TARGET):
        path = root / name
        import re
        path.write_bytes(re.sub(rb"agentic-project-kit==[0-9.]+", b"agentic-project-kit==1.1.10", path.read_bytes()))
    # This internal renderer is retained for self-hosting. It is used only to
    # seed historical fixture bytes, never as an external generation route.
    git("add", "-A")
    git("commit", "-m", "Seed pinned workspace before historical handoff")
    legacy = _build_legacy_successor_handoff_package(root, load_workspace(root))
    for name, value in {
        "successor_context.yaml": legacy.context, "source_manifest.json": legacy.source_manifest,
        "validation_report.json": legacy.validation_report, "execution_contract.json": legacy.execution_contract,
    }.items():
        _write_json(ws.package_file(name), value)
    ws.package_file("successor_prompt.md").write_text(legacy.successor_prompt)
    for name, value in {
        "NEXT_CHAT_BOOTSTRAP.md": legacy.next_chat_bootstrap,
        "START_NEW_CHAT_PROMPT.md": legacy.start_new_chat_prompt,
        "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md": legacy.closeout_prompt,
    }.items():
        ws.handoff_file(name).write_text(value)
    git("add", "-A")
    git("commit", "-m", "Pinned v1 baseline")
    baseline = {name: (root / name).read_bytes() for name in git("ls-files").splitlines()}
    proof_dir = root / ".agentic/tmp/return-contract"
    proof_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {name: _digest(content) for name, content in baseline.items()}
    # Include the ignored runtime record in the verified backup, outside the
    # adoption write set. It must survive the return unchanged.
    runtime = root / ".agentic/tmp/legacy-runtime.json"
    _write_json(runtime, {"generated_head": git("rev-parse", "HEAD"), "status": "PASS"})
    backup = {**snapshot, runtime.relative_to(root).as_posix(): _digest(runtime.read_bytes())}
    _write_json(proof_dir / "v1-backup.json", backup)
    if not all((root / name).is_file() and _digest((root / name).read_bytes()) == digest for name, digest in backup.items()):
        raise RuntimeError("return_backup_incomplete")
    base_head = git("rev-parse", "HEAD")
    git("switch", "-c", "adoption")
    write_external_package(root)
    v2_pass = check_projection(root)["status"] == "PASS"
    for name in (CI_TEMPLATE_PATH, CI_INJECTION_TARGET):
        path = root / name
        path.write_bytes(path.read_bytes().replace(b"==1.1.10", b"==1.1.11"))
    paths = sorted(set(git("ls-files").splitlines()) | {
        path.relative_to(root).as_posix() for path in ws.handoff_dir().rglob("*") if path.is_file()
    })
    changed = [name for name in paths if snapshot.get(name) != _digest((root / name).read_bytes())]
    adoption_id = "a" * 32
    record_adoption(root, adoption_id=adoption_id, approval_signature="local-fixture-approval", plan={
        "installation": {"version": "1.1.10"}, "version": "1.1.11", "branch": "adoption", "head": base_head,
        "files_before": {name: snapshot.get(name) for name in changed}, "changed_paths": changed, "artifacts": [],
    })
    git("add", "-A")
    git("commit", "-m", "Candidate v2 adoption")
    bind_adoption_pr(root, branch="adoption", number=101, head=git("rev-parse", "HEAD"))
    git("switch", "main")
    git("merge", "--squash", "adoption")
    git("commit", "-m", "Squash adoption")
    adoption_merge = git("rev-parse", "HEAD")
    (root / "product.txt").write_text("Later unrelated product work\n")
    git("add", "product.txt")
    git("commit", "-m", "Later product work")
    git("push", "origin", "main")
    git("switch", "-c", "return")
    def observed(number):
        return {"number": number, "state": "MERGED", "baseRefName": "main", "mergeCommit": {"oid": adoption_merge}}
    before_return_blocked = False
    try:
        verify_install_return(root, adoption_id, "1.1.10", run=run, observe_pr=observed)
    except UpdateBlocked:
        before_return_blocked = True
    git("switch", "-c", "later-adoption-touch")
    config.write_bytes(config.read_bytes() + b"# Later authority change\n")
    git("add", ".agentic/config.yaml")
    git("commit", "-m", "Later adoption path change")
    touched_snapshot = {path.relative_to(root).as_posix(): _digest(path.read_bytes())
                        for path in root.rglob("*") if path.is_file()}
    later_touch_blocked = False
    try:
        plan_return_revert(root, adoption_id, run=run, observe_pr=observed)
    except UpdateBlocked as exc:
        later_touch_blocked = "adoption_paths_changed" in str(exc) and ".agentic/config.yaml" in str(exc)
    later_touch_unchanged = touched_snapshot == {
        path.relative_to(root).as_posix(): _digest(path.read_bytes()) for path in root.rglob("*") if path.is_file()
    }
    git("switch", "return")
    revert = plan_return_revert(root, adoption_id, run=run, observe_pr=observed)
    execute_return_revert(root, adoption_id, expected_signature=revert["approval_signature"], run=run, observe_pr=observed)
    restored = all((root / name).is_file() and _digest((root / name).read_bytes()) == digest for name, digest in backup.items())
    git("commit", "-m", "Prepared exact Kit return")
    return_head = git("rev-parse", "HEAD")
    bind_return_pr(root, branch="return", number=102, head=return_head, run=run)
    git("switch", "main")
    git("merge", "--squash", "return")
    git("commit", "-m", "Squash Kit return")
    git("push", "origin", "main")
    return_merge = git("rev-parse", "HEAD")
    def observe_return(number):
        return {"number": number, "state": "MERGED", "baseRefName": "main",
                "headRefOid": return_head, "mergeCommit": {"oid": return_merge}}
    wrong_version_blocked = False
    try:
        verify_install_return(root, adoption_id, "1.1.9", run=run, observe_pr=observe_return)
    except UpdateBlocked:
        wrong_version_blocked = True
    wheel = proof_dir / "agentic_project_kit-1.1.10-py3-none-any.whl"
    wheel.write_bytes(b"Explicit installation test double; not a released wheel")
    target = PreparedTarget(proof_dir / "stage/bin/python", (wheel,), ({
        "name": "agentic-project-kit", "version": "1.1.10", "filename": wheel.name,
        "sha256": _digest(wheel.read_bytes()), "url": "https://example.invalid/test-double.whl",
    },))
    installer = InstallationDouble(root, run, snapshot, target)
    options = {"run": installer, "prepare": lambda *args: target, "discover": installer.discover,
               "return_adoption": adoption_id, "observe_pr": observe_return}
    results = {}
    for failure in ("install", "check", "doctor", None):
        installer.failure = failure
        planned = run_kit_update(root, "1.1.10", **options)
        if planned["result_status"] != "AWAITING_APPROVAL":
            raise RuntimeError(f"return_double_plan_failed: {planned}")
        executed = run_kit_update(root, "1.1.10", execute=True, expected_signature=planned["approval_signature"], **options)
        results[failure or "success"] = executed
    actual = {
        "backup_complete": restored, "v2_pass": v2_pass,
        "original_v1_head_valid": bool(re.fullmatch(r"[0-9a-f]{40}", legacy.validation_report["generated_head"])),
        "product_preserved": (root / "product.txt").read_text() == "Later unrelated product work\n",
        "before_revert_blocked": before_return_blocked, "wrong_version_blocked": wrong_version_blocked,
        "later_touch_blocked": later_touch_blocked, "later_touch_unchanged": later_touch_unchanged,
        "install_failure_not_pass": results["install"]["result_status"] != "PASS",
        "check_failure_not_pass": results["check"]["result_status"] != "PASS",
        "doctor_failure_not_pass": results["doctor"]["result_status"] != "PASS",
        "return_pass": results["success"]["result_status"] == "PASS",
        "empty_changed_paths": results["success"]["changed_paths"] == [],
        "fresh_target_checks": installer.fresh_checks[-2:] == [
            {"kind": "check", "installed": "1.1.10", "returncode": 0},
            {"kind": "doctor", "installed": "1.1.10", "returncode": 0}],
        "new_kit_requires_migration": check_projection(root)["code"] == "NEEDS_PROJECTION_MIGRATION",
    }
    _write_json(proof_dir / "actual.json", actual)
    _write_json(proof_dir / "expected.json", {key: True for key in actual})
    _write_json(proof_dir / "installation-results.json", results)
    variables["fixture_head"] = return_merge
