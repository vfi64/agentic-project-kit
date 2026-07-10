from __future__ import annotations

from datetime import date as date_cls
import json
from pathlib import Path
import subprocess

import typer

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
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Plan by default. Use --execute to commit, push, and merge."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Finish a human work slice by planning or executing commit, push, PR, merge, and post-merge checks."""
    selected_paths = paths or []
    steps: list[dict[str, object]] = [
        _run_step("repo-status", _agentic("transfer", "repo-status")),
        _run_step("protected-diff-plan", _agentic("transfer", "protected-diff-plan", "--label", branch.replace("/", "-"))),
    ]
    if not selected_paths:
        steps.append({"name": "path-selection", "argv": [], "returncode": 2, "ok": False, "allowed_returncodes": [0], "stdout": "", "stderr": "At least one --path is required for work finish."})
    if not dry_run and all(step["ok"] for step in steps):
        steps.extend(
            [
                _run_step("commit", _agentic("transfer", "commit", "--branch", branch, "--message", message, *_path_args(selected_paths))),
                _run_step("rules-acknowledge", _agentic("rules", "acknowledge")),
                _run_step("push-current", _agentic("transfer", "push-current", "--branch", branch)),
                _run_step("pr-create-complete", _agentic("transfer", "pr-create-complete", "--title", title, "--body", f"Human workflow finish: {title}", "--base", "main", "--head", branch, "--merge-method", merge_method, "--post-merge-complete", "--skip-llm-context-gate", "--timeout-seconds", "300", "--interval-seconds", "10", "--json")),
                _run_step("sync-main", _agentic("transfer", "sync-main")),
                _run_step("post-merge-check", _agentic("transfer", "post-merge-check")),
                _run_step("repo-status", _agentic("transfer", "repo-status")),
            ]
        )
    payload = _payload("work-finish", steps, dry_run=dry_run, extra={"branch": branch, "paths": [str(path) for path in selected_paths], "title": title})
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
    release_prep_argv = _agentic("release-prep", "--version", version, "--date", release_date, "--summary-lines-from", str(summary_lines_path), "--json")
    if dry_run:
        release_prep_argv.insert(-1, "--dry-run")
    steps.append(_run_step("release-prep", release_prep_argv))
    payload = _payload("release-prepare", steps, dry_run=dry_run, extra={"version": version, "from_tag": effective_from_tag, "to_ref": to_ref, "date": release_date, "summary_lines_path": str(summary_lines_path)})
    _emit(payload, json_output=json_output)
    _exit_if_blocked(payload)
