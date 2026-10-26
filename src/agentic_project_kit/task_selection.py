"""Pure finite task selection. No I/O, command construction or execution authority."""

from __future__ import annotations

import re

INPUT_TYPES = {
    "nonempty_string",
    "positive_integer",
    "full_commit",
    "stable_version",
    "nonempty_string_list",
}
PHASES = {"diagnostic", "planning", "guarded"}


def valid_value(value, kind) -> bool:
    if kind == "boolean":
        return type(value) is bool
    if isinstance(kind, list):
        return type(value) is str and value in kind
    if kind == "positive_integer":
        return type(value) is int and value > 0
    if kind == "nonempty_string":
        return isinstance(value, str) and bool(value.strip())
    if kind == "full_commit":
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    if kind == "stable_version":
        return isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+", value) is not None
    if kind == "nonempty_string_list":
        return (
            isinstance(value, list)
            and bool(value)
            and all(valid_value(v, "nonempty_string") for v in value)
        )
    return False


def validate_routes(proposal: dict, manifest: dict) -> list[str]:
    errors = []
    if not isinstance(proposal, dict) or not isinstance(manifest, dict):
        return ["proposal and manifest must be objects"]
    entries = manifest.get("commands")
    if not isinstance(entries, list) or any(
        not isinstance(c, dict) or not isinstance(c.get("qualified_name"), str) for c in entries
    ):
        return ["invalid command inventory"]
    if len({c["qualified_name"] for c in entries}) != len(entries):
        errors.append("duplicate manifest command")
    if not isinstance(manifest.get("meta"), dict) or not manifest["meta"].get("manifest_sha"):
        errors.append("missing manifest identity")
    if type(proposal.get("schema_version")) is not int or proposal.get("schema_version") != 1:
        errors.append("unsupported task route schema")
    for command in entries:
        params = command.get("params")
        if (
            command.get("safety") not in ("READ_ONLY", "BOUNDED", "DESTRUCTIVE")
            or command.get("surface") not in ("orchestrator", "primitive", "diagnostic")
            or type(command.get("dry_run_available")) is not bool
            or not isinstance(command.get("remote_effects"), list)
            or not command["remote_effects"]
            or not isinstance(params, list)
            or any(
                not isinstance(p, dict)
                or not isinstance(p.get("name"), str)
                or type(p.get("required")) is not bool
                for p in params
            )
        ):
            return [*errors, "invalid command contract"]
    commands = {c["qualified_name"]: c for c in entries}
    schema = proposal.get("facts_schema")
    routes = proposal.get("routes")
    if not isinstance(schema, dict) or not isinstance(routes, list) or not routes:
        return [*errors, "invalid fact schema or route list"]
    if any(
        v != "boolean"
        and (not isinstance(v, list) or not v or any(not isinstance(x, str) for x in v))
        for v in schema.values()
    ):
        errors.append("invalid fact type")
    for route in routes:
        if not isinstance(route, dict):
            errors.append("invalid route")
            continue
        task, phase = route.get("task"), route.get("phase")
        if (
            not isinstance(task, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]*", task)
            or not isinstance(phase, str)
            or phase not in PHASES
        ):
            errors.append("invalid task identity or phase")
        name = route.get("command")
        command = commands.get(name) if isinstance(name, str) else None
        if command is None:
            errors.append("missing manifest command")
            continue
        if phase == "diagnostic" and command.get("safety") != "READ_ONLY":
            errors.append("diagnostic route is not READ_ONLY")
        if phase == "planning" and command.get("dry_run_available") is not True:
            errors.append("planning route lacks declared preview")
        if route.get("command") == "agentic-kit release run" and phase != "guarded":
            errors.append("release run prepares local state before its signed gates")
        conditions, inputs = route.get("when"), route.get("inputs")
        if not isinstance(conditions, dict) or any(
            k not in schema or not valid_value(v, schema[k]) for k, v in conditions.items()
        ):
            errors.append("invalid fact predicate")
        params = {p["name"] for p in command.get("params", [])}
        if not isinstance(inputs, dict) or any(
            k not in params
            or not isinstance(v, str)
            or v not in INPUT_TYPES
            or k
            in {"execute", "expected_signature", "approved_by", "consent_source", "allow_execute"}
            for k, v in inputs.items()
        ):
            errors.append("invalid parameter binding")
        elif any(p["required"] and p["name"] not in inputs for p in command.get("params", [])):
            errors.append("missing required command input")
    return errors


def result(status: str, **detail) -> dict:
    return {
        "result_status": status,
        "selection_schema_version": 1,
        "execution_authorized": False,
        **detail,
    }


def manifest_route_errors(manifest: dict) -> list[str]:
    """Shared envelope validation for both consumers, including malformed JSON shapes."""
    from .command_manifest import manifest_identity

    if not isinstance(manifest, dict) or not isinstance(manifest.get("meta"), dict):
        return ["invalid manifest envelope"]
    if (
        manifest.get("schema_version") != 3
        or manifest["meta"].get("schema_version") != 2
        or not isinstance(manifest.get("task_routes"), dict)
    ):
        return ["task selection requires manifest schema 3 / metadata schema 2"]
    try:
        identity = manifest_identity(manifest)
    except (TypeError, ValueError):
        return ["invalid manifest identity content"]
    if manifest["meta"].get("manifest_sha") != identity:
        return ["manifest identity mismatch"]
    return validate_routes(manifest["task_routes"], manifest)


def evaluate_routes(manifest: dict, task: str, facts: dict, inputs: dict, context: dict) -> dict:
    problems = manifest_route_errors(manifest)
    if problems:
        return result("INVALID_INPUT", reasons=problems)
    proposal = manifest["task_routes"]
    if not isinstance(task, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", task):
        return result("INVALID_INPUT", reasons=["malformed task identity"])
    routes = [r for r in proposal["routes"] if r["task"] == task]
    if not routes:
        return result("UNKNOWN_TASK")
    if not isinstance(facts, dict) or not isinstance(inputs, dict) or not isinstance(context, dict):
        return result("INVALID_INPUT", reasons=["facts, inputs and context must be objects"])
    identity = manifest.get("meta", {}).get("manifest_sha")
    if (
        not context.get("manifest_sha")
        or not context.get("observed_head")
        or not context.get("current_head")
    ):
        return result("NEEDS_FACTS", reasons=["fresh identity required"])
    if (
        context["manifest_sha"] != identity
        or not valid_value(context["observed_head"], "full_commit")
        or not valid_value(context["current_head"], "full_commit")
    ):
        return result("INVALID_INPUT", reasons=["identity invalid"])
    if not context.get("root") or context.get("root") != context.get("current_root"):
        return result("NEEDS_FACTS", reasons=["root identity missing or stale"])
    if context["observed_head"] != context["current_head"]:
        return result("NEEDS_FACTS", reasons=["observed facts are stale"])
    if any(
        k not in proposal["facts_schema"]
        or (v is not None and not valid_value(v, proposal["facts_schema"][k]))
        for k, v in facts.items()
    ):
        return result("INVALID_INPUT", reasons=["malformed or unknown fact"])
    candidates, unknown = [], set()
    for route in routes:
        conditions = route["when"]
        if any(facts.get(k) is not None and facts[k] != v for k, v in conditions.items()):
            continue
        missing = {k for k in conditions if facts.get(k) is None}
        if missing:
            unknown.update(missing)
        else:
            candidates.append(route)
    # An unresolved alternative may overlap a known match: do not pick early.
    if unknown:
        return result("NEEDS_FACTS", missing=sorted(unknown))
    if not candidates:
        return result("BLOCKED", reasons=["known state incompatible"])
    if len(candidates) > 1:
        return result("AMBIGUOUS", commands=sorted(r["command"] for r in candidates))
    route = candidates[0]
    required = route["inputs"]
    if any(k not in required or not valid_value(v, required[k]) for k, v in inputs.items()):
        return result("INVALID_INPUT", reasons=["malformed or unknown input"])
    missing = sorted(set(required) - set(inputs))
    if missing:
        return result("NEEDS_INPUTS", missing=missing)
    if task in {"complete_open_pr", "settle_merged_pr"}:
        number = inputs.get("pr_number", inputs.get("after_pr"))
        pr = context.get("pr") or {}
        if (
            pr.get("number") != number
            or not pr.get("repository")
            or pr.get("repository") != context.get("repository")
            or not valid_value(pr.get("head"), "full_commit")
            or ("expected_head_sha" in inputs and pr["head"] != inputs["expected_head_sha"])
        ):
            return result("NEEDS_FACTS", reasons=["PR identity missing or stale"])
    command = next(c for c in manifest["commands"] if c["qualified_name"] == route["command"])
    return result(
        "MATCH",
        command=command["qualified_name"],
        phase=route["phase"],
        contract={
            k: command[k] for k in ("safety", "surface", "remote_effects", "dry_run_available")
        },
    )
