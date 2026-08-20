from __future__ import annotations

from datetime import date as date_cls
import hashlib
import json
from pathlib import Path
import re
import subprocess

import typer

from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_release_blockers
from agentic_project_kit.release_metadata_authority_gate import release_anchor_changes
from agentic_project_kit.work_discard_changes import discard_all_changes
from agentic_project_kit.workspace import load_workspace

work_app = typer.Typer(help="Human-friendly meta commands for patch, PR, and recovery workflows.")
release_flow_app = typer.Typer(help="Human-friendly meta commands for release readiness and preparation.")


def _run_step(name: str, argv: list[str], *, allowed_returncodes: set[int] | None = None) -> dict[str, object]:
    allowed = allowed_returncodes or {0}
    completed = subprocess.run(argv, text=True, capture_output=True)
    return {
        "name": name,
        "argv": argv,
        "returncode": completed.returncode,
        "ok": completed.returncode in allowed,
        "allowed_returncodes": sorted(allowed),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _payload(action: str, steps: list[dict[str, object]], *, dry_run: bool = False, extra: dict[str, object] | None = None) -> dict[str, object]:
    blockers = [str(step["name"]) for step in steps if not step["ok"]]
    result_status = "PASS" if not blockers else "BLOCKED"
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": f"human_{action.replace('-', '_')}_result",
        "action": action,
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": dry_run,
        "blockers": blockers,
        "steps": steps,
        "next_action": "Workflow completed." if result_status == "PASS" else "Inspect and fix blocked workflow steps.",
    }
    if extra:
        payload.update(extra)
    return payload


def _emit(payload: dict[str, object], *, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    typer.echo(f"STATE={payload['result_status']}")
    typer.echo(f"RETURNCODE={payload['returncode']}")
    if payload["blockers"]:
        typer.echo("BLOCKERS=" + ",".join(str(item) for item in payload["blockers"]))
    typer.echo(f"NEXT={payload['next_action']}")


def _exit_if_blocked(payload: dict[str, object]) -> None:
    if payload["result_status"] != "PASS":
        raise typer.Exit(code=int(payload["returncode"]))


def _agentic(*parts: str) -> list[str]:
    return ["./.venv/bin/agentic-kit", *parts]


def _python(*parts: str) -> list[str]:
    return ["./.venv/bin/python", *parts]


def _latest_release_tag() -> str:
    completed = subprocess.run(["git", "tag", "--sort=-creatordate"], text=True, capture_output=True)
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        tag = line.strip()
        if tag.startswith("v"):
            return tag
    return ""


def _path_args(paths: list[Path]) -> list[str]:
    args: list[str] = []
    for path in paths:
        args.extend(["--path", str(path)])
    return args


HANDOFF_CLOSEOUT_PATHS = [
    Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md"),
    Path("docs/reports/handoff-packages/latest/execution_contract.json"),
    Path("docs/reports/handoff-packages/latest/source_manifest.json"),
    Path("docs/reports/handoff-packages/latest/successor_context.yaml"),
    Path("docs/reports/handoff-packages/latest/successor_prompt.md"),
    Path("docs/reports/handoff-packages/latest/validation_report.json"),
]


def _extract_pr_number(text: str) -> int | None:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError:
        payload = {}
    candidates = [text]
    if isinstance(payload, dict):
        for key in ("stdout", "url"):
            value = payload.get(key)
            if isinstance(value, str):
                candidates.append(value)
    for candidate in candidates:
        match = re.search(r"/pull/(\d+)\b", candidate)
        if match:
            return int(match.group(1))
        match = re.search(r"(?m)^PR=(\d+)\s*$", candidate)
        if match:
            return int(match.group(1))
    return None


def _current_head_sha_step() -> dict[str, object]:
    return _run_step("resolve-head-sha", ["git", "rev-parse", "HEAD"])


def _remote_preflight_step() -> dict[str, object]:
    return _run_step("remote-preflight", ["git", "ls-remote", "--exit-code", "origin", "HEAD"])


def _handoff_projection_status_step() -> dict[str, object]:
    return _run_step(
        "handoff-projection-status",
        ["git", "status", "--short", "--", *[str(path) for path in HANDOFF_CLOSEOUT_PATHS]],
    )


def _noop_step(name: str, message: str) -> dict[str, object]:
    return {
        "name": name,
        "argv": [],
        "returncode": 0,
        "ok": True,
        "allowed_returncodes": [0],
        "stdout": message,
        "stderr": "",
    }


def _open_pr_closeout_body(title: str) -> str:
    return (
        f"Human workflow finish: {title}\n\n"
        "## Open PR Closeout / Handoff\n\n"
        "- Open PR closeout: final-head CI must be green before review or merge.\n"
        "- Post-merge handoff: pending until this PR is merged.\n"
        "- After merge: run `agentic-kit transfer post-merge-complete --after-pr <PR_NUMBER>` "
        "with the concrete PR number, or use `agentic-kit transfer pr-closeout-complete --after-pr <PR_NUMBER>`.\n"
    )


def _failed_local_step(name: str, message: str) -> dict[str, object]:
    return {
        "name": name,
        "argv": [],
        "returncode": 2,
        "ok": False,
        "allowed_returncodes": [0],
        "stdout": "",
        "stderr": message,
    }


def _open_pr_closeout_marker_step(
    *,
    pr_number: int,
    expected_head_sha: str,
) -> dict[str, object]:
    command = [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--json",
        "number,state,isDraft,headRefOid,body,url",
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    ok = completed.returncode == 0
    findings: list[str] = []
    if ok:
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            payload = {}
            findings.append(f"body_lookup_json_invalid:{exc}")
        body = str(payload.get("body") or "")
        state = str(payload.get("state") or "").upper()
        head_ref_oid = str(payload.get("headRefOid") or "")
        required_terms = (
            "## Open PR Closeout / Handoff",
            "Open PR closeout: final-head CI must be green",
            "Post-merge handoff: pending until this PR is merged.",
            "agentic-kit transfer post-merge-complete --after-pr",
        )
        if state != "OPEN":
            findings.append(f"pr_state_not_open:{state or 'missing'}")
        if expected_head_sha and head_ref_oid != expected_head_sha:
            findings.append("head_sha_mismatch")
        for term in required_terms:
            if term not in body:
                findings.append(f"missing_body_term:{term}")
        ok = not findings
        stdout = "\n".join(
            (
                "OPEN_PR_CLOSEOUT_CHECK",
                f"pr={pr_number}",
                f"state={state or 'missing'}",
                f"head_ref_oid={head_ref_oid or 'missing'}",
                f"expected_head_sha={expected_head_sha or 'missing'}",
                f"body_terms_present={str(not findings).lower()}",
                f"finding_count={len(findings)}",
                *(f"finding={finding}" for finding in findings),
            )
        ) + "\n"
    else:
        stdout = completed.stdout

    return {
        "name": "open-pr-closeout",
        "argv": command,
        "returncode": 0 if ok else completed.returncode or 2,
        "ok": ok,
        "allowed_returncodes": [0],
        "stdout": stdout,
        "stderr": completed.stderr,
    }


def _changed_paths_against(base_ref: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base_ref],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout.strip() or f"git diff failed for {base_ref}")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _compact_step_for_report(step: dict[str, object]) -> dict[str, object]:
    stdout = str(step.get("stdout") or "")
    stderr = str(step.get("stderr") or "")
    stdout_lines = [line for line in stdout.splitlines() if line.strip()]
    stderr_lines = [line for line in stderr.splitlines() if line.strip()]
    return {
        "name": step.get("name"),
        "argv": step.get("argv"),
        "returncode": step.get("returncode"),
        "ok": step.get("ok"),
        "allowed_returncodes": step.get("allowed_returncodes"),
        "stdout_length": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stdout_last_line": stdout_lines[-1][:500] if stdout_lines else "",
        "stderr_length": len(stderr),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        "stderr_last_line": stderr_lines[-1][:500] if stderr_lines else "",
    }


def _write_release_prepare_report_step(
    *,
    version: str,
    release_date: str,
    from_tag: str,
    to_ref: str,
    summary_lines_path: Path,
    prior_steps: list[dict[str, object]],
    base_ref: str = "origin/main",
) -> dict[str, object]:
    workspace = load_workspace(Path("."), suppress_legacy_profile_warning=True)
    report_path = workspace.reports_dir() / "release" / f"release-prepare-{version}.json"
    try:
        changed_paths = _changed_paths_against(base_ref)
        payload = {
            "schema_version": 1,
            "kind": "release_prepare_evidence",
            "version": version,
            "date": release_date,
            "from_tag": from_tag,
            "to_ref": to_ref,
            "base_ref": base_ref,
            "summary_lines_path": str(summary_lines_path),
            "authorized_route": "agentic-kit release-prep",
            "changed_paths_against_base": changed_paths,
            "release_metadata_anchor_paths": release_anchor_changes(changed_paths),
            "steps": [_compact_step_for_report(step) for step in prior_steps],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, RuntimeError) as exc:
        return {
            "name": "release-prepare-report",
            "argv": ["agentic-kit", "release", "prepare", "--write", "--json"],
            "returncode": 2,
            "ok": False,
            "allowed_returncodes": [0],
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "name": "release-prepare-report",
        "argv": ["agentic-kit", "release", "prepare", "--write", "--json"],
        "returncode": 0,
        "ok": True,
        "allowed_returncodes": [0],
            "stdout": workspace.path_text(report_path) + "\n",
        "stderr": "",
    }


def _doc_lifecycle_release_review_step(version: str) -> dict[str, object]:
    blockers = build_doc_lifecycle_release_blockers(Path("."), version=version)
    lines = [
        "DOC_LIFECYCLE_RELEASE_REVIEW",
        f"STATUS={'BLOCKED' if blockers else 'PASS'}",
        f"BLOCKER_COUNT={len(blockers)}",
    ]
    for finding in blockers:
        lines.append(f"BLOCKER={finding.code}|{finding.path}|{finding.message}")
    if blockers:
        lines.append("NEXT=Run docs lifecycle sweep before release readiness.")
    return {
        "name": "doc-lifecycle-release-review",
        "argv": ["agentic-kit", "doc-lifecycle-audit", "--json", "--current-version", version],
        "returncode": 2 if blockers else 0,
        "ok": not blockers,
        "allowed_returncodes": [0],
        "stdout": "\n".join(lines) + "\n",
        "stderr": "",
    }


@work_app.command("start")
def work_start_command(
    branch: str = typer.Option(..., "--branch", help="Feature branch to create or switch to."),
    kind: str = typer.Option("patch", "--kind", help="Human label for the work kind."),
    from_ref: str = typer.Option("main", "--from-ref", help="Start new work from this tag or branch ref."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Start a human patch/slice workflow with the safe standard startup sequence."""
    base_ref = from_ref.strip() or "main"
    steps = [
        _run_step("sync-main", _agentic("transfer", "sync-main")),
        _run_step("rules-acknowledge", _agentic("rules", "acknowledge")),
        _run_step("post-merge-check", _agentic("transfer", "post-merge-check")),
        _run_step("repo-status", _agentic("transfer", "repo-status")),
    ]
    if all(step["ok"] for step in steps):
        exists = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
        if exists.returncode == 0:
            steps.append(_run_step("git-switch-branch", ["git", "switch", branch]))
        else:
            steps.append(
                _run_step(
                    "branch-create",
                    _agentic("transfer", "branch-create", branch, "--start-point", base_ref),
                )
            )
    payload = _payload("work-start", steps, extra={"branch": branch, "from_ref": base_ref, "work_kind": kind})
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@work_app.command("check")
def work_check_command(
    profile: str = typer.Option("code", "--profile", help="Check profile: minimal, code, docs, or release."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Run common human workflow gates without committing or pushing."""
    steps: list[dict[str, object]] = [
        _run_step("repo-status", _agentic("transfer", "repo-status")),
        _run_step("command-reference-check", _agentic("transfer", "command-reference-check", "--json")),
    ]
    if profile in {"code", "release"}:
        steps.extend(
            [
                _run_step("ruff", _python("-m", "ruff", "check", ".")),
                _run_step("pytest-core", _python("-m", "pytest", "tests/test_transfer_startup_hardening_commands.py", "tests/test_agentic_kit_command_reference_is_current.py", "-q")),
            ]
        )
    if profile in {"docs", "release"}:
        steps.extend(
            [
                _run_step("docs-audit", _agentic("docs-audit")),
                _run_step("audit-doc-currency", _agentic("audit-doc-currency")),
                _run_step("audit-ns-legacy-references", _agentic("audit-ns-legacy-references")),
            ]
        )
    if profile == "release":
        steps.append(_run_step("standard-error-scan", _agentic("transfer", "standard-error-scan", "--json"), allowed_returncodes={0}))
    payload = _payload("work-check", steps, extra={"profile": profile})
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@work_app.command("finish")
def work_finish_command(
    branch: str = typer.Option(..., "--branch", help="Feature branch to finish."),
    title: str = typer.Option(..., "--title", help="Pull request title."),
    message: str = typer.Option(..., "--message", help="Commit message."),
    paths: list[Path] | None = typer.Option(None, "--path", help="Path to include in the commit. Repeatable."),
    merge_method: str = typer.Option("squash", "--merge-method", help="PR merge method."),
    merge: bool = typer.Option(
        False,
        "--merge/--no-merge",
        help=(
            "Open a review PR with explicit pending-handoff closeout markers by default. "
            "Use --merge only for an explicitly authorized merge and post-merge closeout."
        ),
    ),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Plan by default. Use --execute to commit, push, and publish."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Finish a human work slice by planning or executing commit, push, PR, merge, and closeout checks."""
    selected_paths = paths or []
    pr_number: int | None = None
    expected_head_sha = ""
    steps: list[dict[str, object]] = [
        _run_step("repo-status", _agentic("transfer", "repo-status")),
        _run_step("protected-diff-plan", _agentic("transfer", "protected-diff-plan", "--label", branch.replace("/", "-"))),
    ]
    if not selected_paths:
        steps.append({"name": "path-selection", "argv": [], "returncode": 2, "ok": False, "allowed_returncodes": [0], "stdout": "", "stderr": "At least one --path is required for work finish."})
    if not dry_run and all(step["ok"] for step in steps):
        steps.append(_remote_preflight_step())
        if all(step["ok"] for step in steps):
            steps.append(_run_step("rules-acknowledge", _agentic("rules", "acknowledge")))
        if all(step["ok"] for step in steps):
            steps.append(_run_step("commit", _agentic("transfer", "commit", "--branch", branch, "--message", message, *_path_args(selected_paths))))
        if all(step["ok"] for step in steps):
            steps.append(_run_step("rules-acknowledge-post-work-commit", _agentic("rules", "acknowledge")))
        if all(step["ok"] for step in steps):
            steps.append(_run_step("handoff-refresh", _agentic("transfer", "chat-switch-complete", "--render-prompt")))
        if all(step["ok"] for step in steps):
            handoff_status = _handoff_projection_status_step()
            steps.append(handoff_status)
            if handoff_status["ok"] and str(handoff_status.get("stdout") or "").strip():
                steps.append(
                    _run_step(
                        "handoff-commit",
                        _agentic(
                            "transfer",
                            "commit",
                            "--branch",
                            branch,
                            "--message",
                            f"Refresh handoff for {title}",
                            *_path_args(HANDOFF_CLOSEOUT_PATHS),
                        ),
                    )
                )
            elif handoff_status["ok"]:
                steps.append(_noop_step("handoff-commit", "No handoff projection changes to commit.\n"))
        if all(step["ok"] for step in steps):
            head_sha_step = _current_head_sha_step()
            expected_head_sha = str(head_sha_step["stdout"]).strip()
            steps.append(head_sha_step)
        if all(step["ok"] for step in steps):
            steps.append(_run_step("rules-acknowledge-post-closeout", _agentic("rules", "acknowledge")))
        if all(step["ok"] for step in steps):
            steps.append(_run_step("push-current", _agentic("transfer", "push-current", "--branch", branch)))
        if all(step["ok"] for step in steps):
            if merge:
                steps.extend(
                    [
                        _run_step("pr-create-complete", _agentic("transfer", "pr-create-complete", "--title", title, "--body", f"Human workflow finish: {title}", "--base", "main", "--head", branch, "--merge-method", merge_method, "--post-merge-complete", "--skip-llm-context-gate", "--timeout-seconds", "300", "--interval-seconds", "10", "--json")),
                        _run_step("sync-main", _agentic("transfer", "sync-main")),
                        _run_step("post-merge-check", _agentic("transfer", "post-merge-check")),
                        _run_step("repo-status", _agentic("transfer", "repo-status")),
                    ]
                )
            else:
                pr_create_step = _run_step(
                    "pr-create",
                    _agentic(
                        "transfer",
                        "pr-create",
                        "--title",
                        title,
                        "--body",
                        _open_pr_closeout_body(title),
                        "--base",
                        "main",
                        "--head",
                        branch,
                        "--skip-llm-context-gate",
                        "--json",
                    ),
                )
                steps.append(pr_create_step)
                if pr_create_step["ok"]:
                    pr_number = _extract_pr_number(str(pr_create_step.get("stdout") or ""))
                    if pr_number is None:
                        steps.append(_failed_local_step("pr-number", "Could not determine PR number from transfer pr-create output."))
                    else:
                        steps.append(
                            _run_step(
                                "pr-wait-ci",
                                _agentic(
                                    "transfer",
                                    "pr-wait-ci",
                                    str(pr_number),
                                    "--expected-head-sha",
                                    expected_head_sha,
                                    "--timeout-seconds",
                                    "300",
                                    "--interval-seconds",
                                    "10",
                                    "--json",
                                ),
                            )
                        )
                        if all(step["ok"] for step in steps):
                            steps.append(
                                _run_step(
                                    "pr-status",
                                    _agentic(
                                        "transfer",
                                        "pr-status",
                                        str(pr_number),
                                        "--expected-head-sha",
                                        expected_head_sha,
                                        "--no-failed-log-fetch",
                                        "--json",
                                    ),
                                )
                            )
                        if all(step["ok"] for step in steps):
                            steps.append(_open_pr_closeout_marker_step(pr_number=pr_number, expected_head_sha=expected_head_sha))
    completion_mode = "merge_and_post_merge" if merge else "open_pr_pending_handoff"
    next_action = (
        "Open PR is published and CI-green; post-merge handoff remains pending until merge."
        if not merge
        else None
    )
    payload = _payload(
        "work-finish",
        steps,
        dry_run=dry_run,
        extra={
            "branch": branch,
            "paths": [str(path) for path in selected_paths],
            "title": title,
            "completion_mode": completion_mode,
            "merge": merge,
            "pr_number": pr_number,
            "expected_head_sha": expected_head_sha,
            "post_merge_handoff": "pending_until_merge" if not merge else "handled_by_post_merge_complete",
        },
    )
    if next_action and payload["result_status"] == "PASS":
        payload["next_action"] = next_action
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@work_app.command("recover")
def work_recover_command(json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON.")) -> None:
    """Run safe recovery/status commands after interrupted work."""
    steps = [
        _run_step("restore-known-volatile", _agentic("transfer", "restore-known-volatile", "--json")),
        _run_step("normalize-session", _agentic("transfer", "normalize-session", "--repair-known-volatile")),
        _run_step("repo-status", _agentic("transfer", "repo-status")),
        _run_step("conflict-status", _agentic("transfer", "conflict-status", "--json"), allowed_returncodes={0, 2}),
        _run_step("patch-cycle-status", _agentic("transfer", "patch-cycle-status", "--include-ci", "--json"), allowed_returncodes={0, 2}),
    ]
    payload = _payload(
        "work-recover",
        steps,
        extra={
            "destructive_actions_allowed": False,
            "discard_all_available": False,
            "discard_all_next_action": (
                "Use a separate explicitly destructive workflow; work recover never "
                "runs reset, clean, checkout, or broad restore over product files."
            ),
        },
    )
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@work_app.command("discard-changes")
def work_discard_changes_command(
    execute: bool = typer.Option(False, "--execute", help="Discard all feature-branch changes. Dry-run is the default."),
    expected_signature: str = typer.Option(
        "",
        "--expected-signature",
        help="Optional dry-run signature that must match before execute.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Preview or execute the explicit destructive discard-all workflow."""
    payload = discard_all_changes(
        Path("."),
        execute=execute,
        expected_signature=expected_signature,
    )
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@release_flow_app.command("ready")
def release_ready_command(
    version: str = typer.Option(..., "--version", help="Target release version."),
    from_tag: str = typer.Option("", "--from-tag", help="Previous release tag. Defaults to latest local v* git tag."),
    to_ref: str = typer.Option("main", "--to-ref", help="Target ref."),
    date: str = typer.Option("", "--date", help="Release date. Defaults to today."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Run release readiness through the standard-error scan wrapper."""
    release_date = date or date_cls.today().isoformat()
    effective_from_tag = from_tag or _latest_release_tag()
    steps = [
        _run_step("sync-main", _agentic("transfer", "sync-main")),
        _run_step("standard-error-scan", _agentic("transfer", "standard-error-scan", "--before-release", "--version", version, "--from-tag", effective_from_tag, "--to-ref", to_ref, "--date", release_date, "--json"), allowed_returncodes={0}),
        _doc_lifecycle_release_review_step(version),
        _run_step("release-status", _agentic("release-status", "--include-remote", "--json"), allowed_returncodes={0, 2}),
    ]
    payload = _payload("release-ready", steps, extra={"version": version, "from_tag": effective_from_tag, "to_ref": to_ref, "date": release_date})
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)


@release_flow_app.command("prepare")
def release_prepare_command(
    version: str = typer.Option(..., "--version", help="Target release version."),
    from_tag: str = typer.Option("", "--from-tag", help="Previous release tag. Defaults to latest local v* git tag."),
    to_ref: str = typer.Option("main", "--to-ref", help="Target ref."),
    date: str = typer.Option("", "--date", help="Release date. Defaults to today."),
    dry_run: bool = typer.Option(True, "--dry-run/--write", help="Dry-run by default. Use --write to update release metadata."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Generate release summary evidence and run release-prep safely."""
    release_date = date or date_cls.today().isoformat()
    effective_from_tag = from_tag or _latest_release_tag()
    summary_lines_path = load_workspace(Path(".")).tmp_file(f"release-{version.replace('.', '')}-summary-lines.json")
    steps = [
        _run_step("release-notes-generate", _agentic("release-notes-generate", "--version", version, "--from-tag", effective_from_tag, "--to-ref", to_ref, "--include-github-metadata", "--summary-lines-json", str(summary_lines_path), "--json"))
    ]
    if all(step["ok"] for step in steps):
        release_prep_argv = _agentic(
            "release-prep",
            "--version",
            version,
            "--date",
            release_date,
            "--summary-lines-from",
            str(summary_lines_path),
            "--json",
        )
        if dry_run:
            release_prep_argv.insert(-1, "--dry-run")
        steps.append(_run_step("release-prep", release_prep_argv))
    if not dry_run and all(step["ok"] for step in steps):
        steps.append(
            _run_step(
                "commands-sync-entrypoints",
                _agentic("commands", "sync-entrypoints", "--execute", "--json"),
            )
        )
    evidence_path = ""
    if not dry_run and all(step["ok"] for step in steps):
        report_step = _write_release_prepare_report_step(
            version=version,
            release_date=release_date,
            from_tag=effective_from_tag,
            to_ref=to_ref,
            summary_lines_path=summary_lines_path,
            prior_steps=list(steps),
        )
        if report_step["ok"]:
            evidence_path = str(report_step["stdout"]).strip()
        steps.append(report_step)
    payload = _payload(
        "release-prepare",
        steps,
        dry_run=dry_run,
        extra={
            "version": version,
            "from_tag": effective_from_tag,
            "to_ref": to_ref,
            "date": release_date,
            "summary_lines_path": str(summary_lines_path),
            "evidence_path": evidence_path,
        },
    )
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)
