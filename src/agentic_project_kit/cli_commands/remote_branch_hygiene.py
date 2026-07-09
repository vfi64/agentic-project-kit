from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.remote_branch_hygiene import (
    analyze_remote_branch_hygiene,
    build_remote_branch_hygiene_evidence_report_payload,
    collect_remote_branch_hygiene_inputs,
    delete_remote_branch,
    render_remote_branch_hygiene_report,
    report_as_json_data,
    write_remote_branch_hygiene_evidence_report,
)


def register_remote_branch_hygiene_command(app: typer.Typer) -> None:
    app.command("remote-branch-hygiene")(remote_branch_hygiene_command)
    app.command("remote-branch-hygiene-report")(remote_branch_hygiene_report_command)
    app.command("remote-branch-hygiene-apply")(remote_branch_hygiene_apply_command)


def remote_branch_hygiene_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Dry-run remote branch hygiene classification for K3."""
    remote_branches, open_pr_heads = collect_remote_branch_hygiene_inputs(project_root.resolve())
    report = analyze_remote_branch_hygiene(remote_branches, open_pr_heads)
    if json_output:
        typer.echo(json.dumps(report_as_json_data(report), indent=2, sort_keys=True))
    else:
        typer.echo(render_remote_branch_hygiene_report(report), nl=False)

def _assert_safe_output_path(project_root: Path, output_path: Path) -> Path:
    resolved_root = project_root.resolve()
    resolved = output_path.resolve()
    safe_roots = (
        resolved_root / "tmp",
        resolved_root / "docs" / "reports",
        resolved_root / ".agentic",
    )
    if not any(resolved == root or root in resolved.parents for root in safe_roots):
        safe = ", ".join(str(root) for root in safe_roots)
        raise typer.BadParameter(f"output path must be below one of: {safe}")
    return resolved


def remote_branch_hygiene_report_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    output_path: Path = typer.Option(..., "--output"),
    execute: bool = typer.Option(False, "--execute"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Write a K3 remote branch hygiene evidence report only with --execute."""
    root = project_root.resolve()
    remote_branches, open_pr_heads = collect_remote_branch_hygiene_inputs(root)
    report = analyze_remote_branch_hygiene(remote_branches, open_pr_heads)
    safe_output = _assert_safe_output_path(root, output_path)

    if execute:
        write_remote_branch_hygiene_evidence_report(safe_output, report)
        mode = "execute"
        mutation = "evidence-report-write"
        written = True
    else:
        mode = "dry-run"
        mutation = "none"
        written = False

    payload = {
        "schema_version": 1,
        "kind": "k3_remote_branch_hygiene_report_write_result",
        "mode": mode,
        "mutation": mutation,
        "result_status": "PASS",
        "written": written,
        "output_path": str(safe_output),
        "report": build_remote_branch_hygiene_evidence_report_payload(report),
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("K3_REMOTE_BRANCH_HYGIENE_REPORT")
        typer.echo(f"MODE: {mode}")
        typer.echo(f"MUTATION: {mutation}")
        typer.echo(f"WRITTEN: {str(written).lower()}")
        typer.echo(f"OUTPUT: {safe_output}")

def _branch_name_is_single_remote_ref(branch: str) -> bool:
    return branch.startswith("origin/") and branch not in {"origin", "origin/HEAD", "origin/main"} and "," not in branch


def _find_safe_delete_candidate(report, branch: str):
    if not _branch_name_is_single_remote_ref(branch):
        raise typer.BadParameter("only must be one non-protected origin/<name> remote branch")
    for finding in report.findings:
        if finding.branch == branch:
            if finding.proposed_action != "candidate-delete-merged-remote-branch":
                raise typer.BadParameter(f"{branch} is not a safe delete candidate")
            if finding.has_open_pr:
                raise typer.BadParameter(f"{branch} is not a safe delete candidate")
            if not finding.merged_to_origin_main:
                raise typer.BadParameter(f"{branch} is not a safe delete candidate")
            return finding
    raise typer.BadParameter(f"branch not found in current hygiene report: {branch}")


def remote_branch_hygiene_apply_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    only: str = typer.Option(..., "--only"),
    execute: bool = typer.Option(False, "--execute"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Safely apply exactly one remote branch deletion candidate."""
    root = project_root.resolve()
    remote_branches, open_pr_heads = collect_remote_branch_hygiene_inputs(root)
    report = analyze_remote_branch_hygiene(remote_branches, open_pr_heads)
    finding = _find_safe_delete_candidate(report, only)

    if execute:
        delete_remote_branch(root, finding.branch)
        mode = "execute"
        mutation = "delete-single-remote-branch"
        deleted = True
    else:
        mode = "dry-run"
        mutation = "none"
        deleted = False

    payload = {
        "schema_version": 1,
        "kind": "k3_remote_branch_hygiene_apply_result",
        "mode": mode,
        "mutation": mutation,
        "result_status": "PASS",
        "branch": finding.branch,
        "short_name": finding.short_name,
        "deleted": deleted,
        "safety_class": finding.safety_class,
        "reason": finding.reason,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("K3_REMOTE_BRANCH_HYGIENE_APPLY")
        typer.echo(f"MODE: {mode}")
        typer.echo(f"MUTATION: {mutation}")
        typer.echo(f"BRANCH: {finding.branch}")
        typer.echo(f"DELETED: {str(deleted).lower()}")
