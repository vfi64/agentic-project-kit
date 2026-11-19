from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.workspace_init import (
    WorkspaceInitError,
    build_workspace_init_plan,
    execute_workspace_init,
    render_workspace_init_error,
    render_workspace_init_plan,
)
from agentic_project_kit.workspace_ci_update import (
    WorkspaceCiUpdateError,
    build_workspace_ci_update_plan,
    execute_workspace_ci_update,
    render_workspace_ci_update_error,
    render_workspace_ci_update_plan,
)
from agentic_project_kit.workspace_remove import (
    WorkspaceRemoveError,
    build_workspace_remove_plan,
    execute_workspace_remove,
    render_workspace_remove_error,
    render_workspace_remove_plan,
)
from agentic_project_kit.workspace_upgrade import (
    WorkspaceUpgradeError,
    build_workspace_upgrade_plan,
    execute_workspace_upgrade,
    render_workspace_upgrade_error,
    render_workspace_upgrade_plan,
)
from agentic_project_kit.workspace_adopt import (
    analyze_workspace_adoption,
    render_workspace_adopt_report,
)
from agentic_project_kit.workspace_dpa_intake import (
    READY_STATUS as DPA_INTAKE_READY_STATUS,
    build_workspace_dpa_intake_report,
    render_workspace_dpa_intake_report,
)
from agentic_project_kit.cli_commands.routed_output import emit_routed, human_reason, read_only_route
from agentic_project_kit.g3_remedies import routes_for

workspace_app = typer.Typer(help="Inspect and manage operating-layer workspaces.")

# G3 (owner plan 2026-11-13): the five workspace orchestrators print only through emit_routed, so a
# BLOCKED or FAIL result names the resolving Kit command or carries the human marker with a reason.
# Kit routes go to planning runs only (no --execute), which a session may start on its own.
# G3 remedy table (g3_remedies): the Kit command that resolves each error code.
INIT_ERROR_ROUTES = routes_for("workspace init")
UPGRADE_ERROR_ROUTES = routes_for("workspace upgrade")
REMOVE_ERROR_ROUTES = routes_for("workspace remove")
# KIT-GF-114: CI and pre-commit come after the recovery, through their own Kit route.
AFTER_RECOVERY = "After the signed recovery, inject CI with agentic-kit workspace ci-update --inject-ci --execute."


def _error_payload(kind: str, exc: Exception, routes: dict[str, tuple[str, ...]], root: Path) -> dict[str, object]:
    code = getattr(exc, "code", "FAIL")
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": kind,
        "result_status": "FAIL",
        "code": code,
        "error": str(exc),
    }
    if code in routes:
        payload.update(read_only_route(*routes[code], root=root))
    else:
        payload.update(human_reason(f"{code}: {exc}"))
    return payload


@workspace_app.command("adopt")
def workspace_adopt_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Analyze an existing repository without writing workspace files."""

    report = analyze_workspace_adoption(root.resolve())
    emit_routed(report.as_json_data(), json_output=json_output, text=render_workspace_adopt_report(report))


@workspace_app.command("dpa-intake")
def workspace_dpa_intake_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    validation_ref: Annotated[
        str | None,
        typer.Option(
            "--validation-ref",
            help="Optional exact current ref to record instead of repository HEAD.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Optional DPA intake evidence JSON path under docs/architecture/evidence/dpa/assessment/.",
        ),
    ] = None,
    write_evidence: Annotated[
        bool,
        typer.Option(
            "--write-evidence",
            help="Use the default bounded DPA intake evidence JSON path.",
        ),
    ] = False,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Write requested evidence output."),
    ] = False,
    require_ready: Annotated[
        bool,
        typer.Option(
            "--require-ready",
            help="Fail unless the target repo is ready for DPA intake adjudication.",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the deterministic Document Projection Architecture repository-intake orchestration."""

    report = build_workspace_dpa_intake_report(
        root.resolve(),
        validation_ref=validation_ref,
        output=output,
        write_evidence=write_evidence,
        execute=execute,
    )
    evidence_blocked = report.evidence_write is not None and report.evidence_write["result_status"] == "BLOCK"
    payload = report.as_json_data()
    if evidence_blocked:
        payload.update(human_reason(
            f"Evidence path refused ({report.evidence_write.get('reason', 'blocked')}); choose an --output "
            "under docs/architecture/evidence/dpa/assessment/."
        ))
    elif report.dpa_assessment.blocker_count:
        payload.update(human_reason(
            f"The DPA repository adoption assessment has {report.dpa_assessment.blocker_count} blocker(s); "
            "a maintainer adjudicates them before intake."
        ))
    emit_routed(
        payload,
        json_output=json_output,
        text=render_workspace_dpa_intake_report(report),
        blocked=report.result_status != DPA_INTAKE_READY_STATUS,
    )
    if evidence_blocked:
        raise typer.Exit(2)
    if require_ready and not report.ok:
        raise typer.Exit(1)


@workspace_app.command("init")
def workspace_init_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    name: Annotated[str | None, typer.Option("--name", help="Project name override.")] = None,
    project_type: Annotated[str | None, typer.Option("--type", help="Project type override: python, node, or generic.")] = None,
    profile: Annotated[str | None, typer.Option("--profile", help="Workspace profile override.")] = None,
    execute: Annotated[bool, typer.Option("--execute", help="Write the planned workspace files.")] = False,
    inject_ci: Annotated[bool, typer.Option("--inject-ci", help="Opt in to GitHub Actions workflow injection.")] = False,
    inject_pre_commit: Annotated[bool, typer.Option("--inject-pre-commit", help="Opt in to pre-commit snippet injection.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
    recover_partial: Annotated[bool, typer.Option("--recover-partial", help="Plan signed additive recovery of a generated external project.")] = False,
    expected_signature: Annotated[str, typer.Option("--expected-signature", help="Reviewed recovery plan signature.")] = "",
    approved_by: Annotated[str, typer.Option("--approved-by", help="Maintainer approving recovery.")] = "",
    consent_source: Annotated[str, typer.Option("--consent-source", help="Source of explicit recovery consent.")] = "",
    publication: Annotated[str | None, typer.Option(
        "--publication",
        help="Publication policy for the manifest: none, github, github+pypi, or github+pypi+zenodo (default).",
    )] = None,
) -> None:
    """Plan or create a bounded operating-layer workspace."""

    # The routes keep the chosen policy, so the recovery they name writes the same manifest.
    policy_words = ("--publication", publication) if publication else ()

    if recover_partial:
        from agentic_project_kit.workspace_recovery import recover_workspace
        if inject_ci or inject_pre_commit:
            # KIT-GF-115: the same recovery without the injection flags, then ci-update.
            payload = {"result_status": "BLOCKED", "written": False, "code": "RECOVERY_NO_INJECTION",
                       "reason": "Recovery does not inject CI or pre-commit files.",
                       "next_action": "Plan the recovery without --inject-ci/--inject-pre-commit. " + AFTER_RECOVERY,
                       **read_only_route(*INIT_ERROR_ROUTES["RECOVERY_NO_INJECTION"], *policy_words, root=root)}
        else:
            payload = recover_workspace(
                root, execute=execute, expected_signature=expected_signature,
                approved_by=approved_by, consent_source=consent_source,
                name=name, project_type=project_type, profile=profile, publication=publication,
            )
        if payload["result_status"] == "BLOCKED" and not payload.get("next_command"):
            payload.update(human_reason(str(payload.get("reason") or payload.get("next_action") or "Recovery blocked.")))
        # Recovery always answers in JSON (unchanged).
        payload = emit_routed(payload, json_output=True)
        if payload["result_status"] == "BLOCKED":
            raise typer.Exit(2)
        return

    try:
        plan = build_workspace_init_plan(
            root.resolve(),
            name=name,
            project_type=project_type,
            profile=profile,
            execute=execute,
            inject_ci=inject_ci,
            inject_pre_commit=inject_pre_commit,
            publication=publication,
        )
        if execute:
            execute_workspace_init(plan)
        emit_routed(
            plan.as_json_data(written=execute),
            json_output=json_output,
            text=render_workspace_init_plan(plan, written=execute),
        )
    except WorkspaceInitError as exc:
        from agentic_project_kit.workspace_recovery import generated_project_recoverable
        routes = dict(INIT_ERROR_ROUTES)
        if exc.code == "FOREIGN_AGENTIC" and not generated_project_recoverable(root.resolve()):
            routes.pop("FOREIGN_AGENTIC")  # a foreign .agentic/ stays with the person
        payload = _error_payload("workspace_init_result", exc, routes, root)
        if exc.code == "FOREIGN_AGENTIC" and "FOREIGN_AGENTIC" in routes:
            # KIT-GF-114: an init project is recovered, not initialized.
            payload.update(read_only_route(*routes["FOREIGN_AGENTIC"], *policy_words, root=root))
            payload["next_action"] = "This is a generated project: plan its signed recovery." + (
                " " + AFTER_RECOVERY if inject_ci else "")
        emit_routed(
            payload,
            json_output=json_output,
            text=render_workspace_init_error(exc),
        )
        raise typer.Exit(code=1) from exc


@workspace_app.command("remove")
def workspace_remove_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Remove exact Kit-generated workspace files."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or remove exact Kit-generated operating-layer workspace files."""

    try:
        plan = build_workspace_remove_plan(root.resolve(), execute=execute)
        if execute and plan.result_status == "PASS":
            execute_workspace_remove(plan)
        written = execute and plan.result_status == "PASS"
        payload = plan.as_json_data(written=written)
        if plan.result_status == "BLOCKED":
            found = "; ".join(f"{item.path}: {item.reason}" for item in plan.blockers[:3])
            payload.update(human_reason(f"{plan.message}" + (f" ({found})" if found else "")))
        emit_routed(payload, json_output=json_output, text=render_workspace_remove_plan(plan, written=written))
        if plan.result_status == "BLOCKED":
            raise typer.Exit(2)
    except WorkspaceRemoveError as exc:
        emit_routed(
            _error_payload("workspace_remove_result", exc, REMOVE_ERROR_ROUTES, root),
            json_output=json_output,
            text=render_workspace_remove_error(exc),
        )
        raise typer.Exit(code=1) from exc


@workspace_app.command("ci-update")
def workspace_ci_update_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Write the current managed CI template."),
    ] = False,
    inject_ci: Annotated[
        bool, typer.Option("--inject-ci", help="Opt in to creating a missing managed CI workflow.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or update the managed workspace CI template."""

    try:
        plan = build_workspace_ci_update_plan(root.resolve(), execute=execute, inject_ci=inject_ci)
        if execute and plan.result_status == "PASS":
            execute_workspace_ci_update(plan)
        written = execute and plan.result_status == "PASS" and bool(plan.changed_paths)
        if json_output:
            typer.echo(json.dumps(plan.as_json_data(written=written), indent=2, sort_keys=True))
        else:
            typer.echo(render_workspace_ci_update_plan(plan, written=written), nl=False)
        if plan.result_status == "BLOCKED":
            raise typer.Exit(2)
    except WorkspaceCiUpdateError as exc:
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "workspace_ci_update_result",
                        "result_status": "FAIL",
                        "code": exc.code,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            typer.echo(render_workspace_ci_update_error(exc), nl=False)
        raise typer.Exit(code=1) from exc


@workspace_app.command("upgrade")
def workspace_upgrade_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    execute: Annotated[
        bool, typer.Option("--execute", help="Write the upgraded manifest and backups.")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON.")
    ] = False,
) -> None:
    """Plan or run deterministic workspace manifest schema upgrades."""

    try:
        plan = build_workspace_upgrade_plan(root.resolve(), execute=execute)
        if execute:
            execute_workspace_upgrade(plan)
        written = execute and plan.requires_upgrade
        emit_routed(
            plan.as_json_data(written=written),
            json_output=json_output,
            text=render_workspace_upgrade_plan(plan, written=written),
        )
    except WorkspaceUpgradeError as exc:
        emit_routed(
            _error_payload("workspace_upgrade_result", exc, UPGRADE_ERROR_ROUTES, root),
            json_output=json_output,
            text=render_workspace_upgrade_error(exc),
        )
        raise typer.Exit(code=1) from exc
