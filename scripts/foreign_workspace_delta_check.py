"""Local-only acceptance against a pinned old source tree and this candidate.

Uses identical synthetic Swift fixtures and shared dependency versions, in
separate CLI processes. No consumer checkout, network, publication or model run.
The baseline is a Git tag's sources, not a released-wheel packaging test.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

PROFILES = ("minimal", "code", "docs", "release")
PROJECT = """version: 1
project: {name: swift-fixture, description: bounded Swift acceptance, type: generic}
profiles: []
policy_packs: [solo-maintainer]
governance: {}
"""
FILES = {
    ".agentic/project.yaml": PROJECT,
    ".agentic/todo.yaml": "items: []\n",
    "Sources/Example.swift": "struct Example { let value = 1 }\n",
    "docs/planning/PLAN.md": "# Plan\n\nPreserve this reviewed project plan.\n",
    "docs/STATUS.md": "# Project Status\n\n## Current Goal\nVerify bootstrap.\n\n## Next Safe Step\nReview evidence.\n",
    "docs/handoff/CURRENT_HANDOFF.md": "# Current Handoff\n\n## Current\nBootstrap acceptance.\n\n## Next\nReview results.\n",
    "sentinel.yaml": "documents:\n  - path: docs/STATUS.md\n    required_sections: ['## Current Goal', '## Next Safe Step']\n",
}


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def fixture(root: Path) -> None:
    root.mkdir()
    git(root, "init", "-b", "work")
    git(root, "config", "user.name", "Kit Acceptance")
    git(root, "config", "user.email", "acceptance@example.invalid")
    for relative, text in FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initial Swift fixture")
    # Real uncommitted owner work must survive recovery and a selective commit.
    (root / "docs/planning/PLAN.md").write_text(FILES["docs/planning/PLAN.md"] + "\nOwner continuation.\n")


def invoke(root: Path, package_root: Path, records: list, *args: str, expected: int | None = 0) -> dict:
    env = {**os.environ, "PYTHONPATH": str(package_root / "src"), "GIT_TERMINAL_PROMPT": "0"}
    done = subprocess.run(["agentic-kit", *args], cwd=root, env=env, text=True, capture_output=True, timeout=180)
    try:
        payload = json.loads(done.stdout)
    except ValueError:
        payload = {}
    records.append({"command": ["agentic-kit", *args], "rc": done.returncode,
                    "result_status": payload.get("result_status", payload.get("status")),
                    "mode": payload.get("workspace_mode"),
                    "diagnostic": (done.stdout + done.stderr)[-1800:] if done.returncode else ""})
    if expected is not None and done.returncode != expected:
        raise ValueError(f"Unexpected rc for {args}: {done.returncode}: {(done.stdout + done.stderr)[-1500:]}")
    if expected == 0 and payload.get("result_status") in {"FAIL", "BLOCKED"}:
        raise ValueError(f"Blocked command despite rc 0: {args}")
    return payload


def negative_checks(root: Path, package: Path, records: list, *, baseline: bool) -> None:
    initial = git(root, "rev-parse", "HEAD")
    plan = invoke(root, package, records, "workspace", "init", "--type", "generic", "--json", expected=1)
    assert plan["code"] == "FOREIGN_AGENTIC"
    adopt = invoke(root, package, records, "workspace", "adopt", "--json")
    assert adopt["project"]["type"] == "generic"
    assert adopt["dpa_repo_adoption_assessment"]["result_status"] == "BLOCKED_FOR_DPA_REPO_ADOPTION"
    inventory = invoke(root, package, records, "rule-registry", "bootstrap", "--json", expected=None)
    assert records[-1]["rc"] != 0
    assert inventory["result_status"] == "BLOCKED"
    rules = invoke(root, package, records, "rules", "validate-sources", "--json", expected=1)
    assert rules["fail_closed"] is True
    assert rules["workspace_mode"] == ("self_hosting" if baseline else "partial_external_workspace")
    invoke(root, package, records, "rules", "acknowledge", "--json", expected=1)
    assert not (root / ".agentic/rule_ack/current.json").exists()
    invoke(root, package, records, "transfer", "commit", "--message", "must refuse", "--path", "docs/planning/PLAN.md", "--json", expected=2)
    assert git(root, "rev-parse", "HEAD") == initial
    for profile in PROFILES:
        check = invoke(root, package, records, "work", "check", "--profile", profile, "--json", expected=2)
        assert check["result_status"] == "BLOCKED"
        if not baseline:
            assert check["blockers"] == ["workspace-bootstrap-required"]
        else:
            assert "command-reference-check" in check["blockers"]


def acceptance(root: Path, package: Path, records: list) -> None:
    before = {p: (root / p).read_bytes() for p in FILES}
    plan = invoke(root, package, records, "workspace", "init", "--recover-partial", "--json")
    assert plan["result_status"] == "AWAITING_APPROVAL"
    invoke(root, package, records, "workspace", "init", "--recover-partial", "--execute",
           "--expected-signature", plan["approval_signature"], "--approved-by", "fixture-owner",
           "--consent-source", "isolated acceptance", "--json")
    assert all((root / p).read_bytes() == text for p, text in before.items())
    invoke(root, package, records, "commands", "sync-entrypoints", "--execute", "--json")
    inventory = invoke(root, package, records, "rule-registry", "bootstrap", "--json")
    invoke(root, package, records, "rule-registry", "bootstrap", "--execute", "--expected-signature", inventory["approval_signature"], "--json")
    invoke(root, package, records, "rule-registry", "check", "--json")
    invoke(root, package, records, "rules", "snapshot", "--json")
    invoke(root, package, records, "rules", "acknowledge", "--json")
    for profile in PROFILES:
        check = invoke(root, package, records, "work", "check", "--profile", profile, "--json")
        assert check["result_status"] == "PASS"
    (root / "reviewed.txt").write_text("Selective local commit acceptance.\n")
    invoke(root, package, records, "transfer", "commit", "--message", "Reviewed local change", "--path", "reviewed.txt", "--json")
    assert "docs/planning/PLAN.md" in git(root, "status", "--short")
    assert (root / "docs/planning/PLAN.md").read_bytes() == before["docs/planning/PLAN.md"]
    again = invoke(root, package, records, "workspace", "init", "--recover-partial", "--json")
    assert again["written"] is False
    assert not (root / "tests").exists()


def compare(root: Path, baseline_ref: str, output: Path) -> dict:
    if not __debug__:
        raise RuntimeError("Acceptance assertions require Python without -O.")
    baseline_commit = git(root, "rev-parse", f"{baseline_ref}^{{}}")
    result = {"baseline_commit": baseline_commit, "candidate_commit": git(root, "rev-parse", "HEAD"),
              "baseline_kind": "pinned Git sources; shared dependencies", "profiles": list(PROFILES),
              "consumer_checkout_mutated": False, "swift_compilation_verified": False,
              "result_status": "FAIL", "baseline_steps": [], "candidate_steps": []}
    try:
        with tempfile.TemporaryDirectory(prefix="kit-foreign-delta-") as tmp:
            base = Path(tmp)
            archived = subprocess.run(["git", "archive", baseline_commit, "src/agentic_project_kit"], cwd=root, capture_output=True, check=True).stdout
            old = base / "baseline-source"
            old.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
                archive.extractall(old, filter="data")
            result["baseline_archive_sha256"] = hashlib.sha256(archived).hexdigest()
            for name, source in (("baseline", old), ("candidate", root)):
                target = base / name
                fixture(target)
                negative_checks(target, source, result[name + "_steps"], baseline=name == "baseline")
                if name == "candidate":
                    acceptance(target, source, result["candidate_steps"])
            result["result_status"] = "PASS"
    except (OSError, ValueError, AssertionError, subprocess.SubprocessError) as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", default="v1.1.6")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = compare(Path(__file__).resolve().parents[1], args.baseline_ref, args.output)
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_steps")}))
    return 0 if result["result_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
