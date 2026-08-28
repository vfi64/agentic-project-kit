from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


FULL_CI = "FULL_CI"
ADMIN_REFRESH_LIGHT = "ADMIN_REFRESH_LIGHT"
TREE_PROOF = "TREE_PROOF"
BUILD_REQUIRED = "BUILD_REQUIRED"
BUILD_SKIPPED = "BUILD_SKIPPED"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

PAGES_INPUT_MANIFEST = Path("site/pages_input_manifest.json")

ADMIN_REFRESH_BRANCH_RE = re.compile(
    r"^(?:docs|codex)/post-pr(?P<pr>[1-9][0-9]*)-(?:handoff-refresh|successor-package-refresh)$"
)
POST_PR_REPORT_RE = re.compile(r"^docs/reports/terminal/post-pr(?P<pr>[1-9][0-9]*)-successor-chat-handoff\.md$")

ADMIN_REFRESH_CURRENT_HANDOFF_PATHS = frozenset(
    {
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        ".agentic/dpa/acceptance/current_handoff_operational_state.json",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    }
)

ADMIN_REFRESH_SUCCESSOR_PACKAGE_PATHS = frozenset(
    {
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/reports/handoff-packages/latest/execution_contract.json",
        "docs/reports/handoff-packages/latest/source_manifest.json",
        "docs/reports/handoff-packages/latest/successor_context.yaml",
        "docs/reports/handoff-packages/latest/successor_prompt.md",
        "docs/reports/handoff-packages/latest/validation_report.json",
    }
)

MAIN_PUSH_DEDUPE_UNSAFE_PREFIXES = (
    ".github/workflows/",
    "src/",
    "tests/",
    "docs/architecture/",
    "docs/governance/",
    "docs/planning/",
    "site/",
)

MAIN_PUSH_DEDUPE_UNSAFE_FILES = frozenset(
    {
        "AGENTS.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "README.md",
        "SECURITY.md",
        "pyproject.toml",
        "docs/DOCUMENTATION_COVERAGE.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml",
        "docs/TEST_GATES.md",
    }
)


@dataclass(frozen=True)
class CiPolicyDecision:
    schema_version: int
    kind: str
    status: str
    mode: str
    reasons: tuple[str, ...]
    changed_paths: tuple[str, ...] = ()
    matched_paths: tuple[str, ...] = ()
    missing_paths: tuple[str, ...] = ()
    unexpected_paths: tuple[str, ...] = ()
    invalid_paths: tuple[str, ...] = ()
    diagnostic_only: bool = False
    mutation: str = "none"

    @property
    def ok(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _decision(
    *,
    kind: str,
    status: str,
    mode: str,
    reasons: Iterable[str],
    changed_paths: Iterable[str] = (),
    matched_paths: Iterable[str] = (),
    missing_paths: Iterable[str] = (),
    unexpected_paths: Iterable[str] = (),
    invalid_paths: Iterable[str] = (),
    diagnostic_only: bool = False,
    mutation: str = "none",
) -> CiPolicyDecision:
    return CiPolicyDecision(
        schema_version=1,
        kind=kind,
        status=status,
        mode=mode,
        reasons=tuple(reasons),
        changed_paths=tuple(changed_paths),
        matched_paths=tuple(matched_paths),
        missing_paths=tuple(missing_paths),
        unexpected_paths=tuple(unexpected_paths),
        invalid_paths=tuple(invalid_paths),
        diagnostic_only=diagnostic_only,
        mutation=mutation,
    )


def normalize_changed_paths(paths: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized: list[str] = []
    invalid: list[str] = []
    for raw in paths:
        value = str(raw).strip().replace("\\", "/")
        if not value:
            continue
        parts = value.split("/")
        if value.startswith("/") or ".." in parts:
            invalid.append(value)
            continue
        normalized.append(value)
    return tuple(sorted(dict.fromkeys(normalized))), tuple(sorted(dict.fromkeys(invalid)))


def read_changed_paths(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines())


def admin_refresh_expected_paths(source_pr: int) -> tuple[str, ...]:
    del source_pr
    return tuple(sorted(ADMIN_REFRESH_SUCCESSOR_PACKAGE_PATHS))


def admin_refresh_current_handoff_paths() -> tuple[str, ...]:
    return tuple(sorted(ADMIN_REFRESH_CURRENT_HANDOFF_PATHS))


def admin_refresh_expected_path_variants(source_pr: int) -> tuple[tuple[str, tuple[str, ...]], ...]:
    del source_pr
    return (
        ("successor-package-refresh", tuple(sorted(ADMIN_REFRESH_SUCCESSOR_PACKAGE_PATHS))),
        ("current-handoff-refresh", tuple(sorted(ADMIN_REFRESH_CURRENT_HANDOFF_PATHS))),
    )


def _closest_admin_refresh_variant(
    actual: set[str],
    variants: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[str, set[str]]:
    ranked = sorted(
        ((len(actual ^ set(paths)), name, set(paths)) for name, paths in variants),
        key=lambda item: (item[0], item[1]),
    )
    _, name, expected = ranked[0]
    return name, expected


def source_pr_from_admin_refresh_context(
    *,
    branch: str = "",
    changed_paths: Iterable[str] = (),
    source_pr: int | None = None,
) -> int | None:
    if source_pr is not None and source_pr > 0:
        return source_pr
    match = ADMIN_REFRESH_BRANCH_RE.match(branch)
    if match:
        return int(match.group("pr"))
    found: set[int] = set()
    for path in changed_paths:
        report = POST_PR_REPORT_RE.match(path)
        if report:
            found.add(int(report.group("pr")))
    if len(found) == 1:
        return found.pop()
    return None


def classify_admin_refresh_light(
    changed_paths: Iterable[str],
    *,
    branch: str = "",
    source_pr: int | None = None,
    validation_status: str = "",
) -> CiPolicyDecision:
    paths, invalid = normalize_changed_paths(changed_paths)
    if invalid:
        return _decision(
            kind="admin_refresh_light_ci",
            status="PASS",
            mode=FULL_CI,
            reasons=("invalid changed paths require full CI",),
            changed_paths=paths,
            invalid_paths=invalid,
        )
    resolved_pr = source_pr_from_admin_refresh_context(
        branch=branch,
        changed_paths=paths,
        source_pr=source_pr,
    )
    if resolved_pr is None:
        return _decision(
            kind="admin_refresh_light_ci",
            status="PASS",
            mode=FULL_CI,
            reasons=("source PR could not be proven from branch or post-pr report path",),
            changed_paths=paths,
        )
    actual = set(paths)
    if validation_status != "PASS":
        return _decision(
            kind="admin_refresh_light_ci",
            status="PASS",
            mode=FULL_CI,
            reasons=("successor package validation is not PASS",),
            changed_paths=paths,
        )
    variants = admin_refresh_expected_path_variants(resolved_pr)
    for mutation, variant_paths in variants:
        expected = set(variant_paths)
        if actual == expected:
            return _decision(
                kind="admin_refresh_light_ci",
                status="PASS",
                mode=ADMIN_REFRESH_LIGHT,
                reasons=(f"exact {mutation} path set for PR {resolved_pr}",),
                changed_paths=paths,
                matched_paths=tuple(sorted(actual)),
                mutation=mutation,
            )
    closest_name, expected = _closest_admin_refresh_variant(actual, variants)
    missing = tuple(sorted(expected - actual))
    unexpected = tuple(sorted(actual - expected))
    reasons: list[str] = [f"admin refresh path set does not match exact {closest_name} variant"]
    if missing:
        reasons.append("admin refresh changed-path set is missing expected generated paths")
    if unexpected:
        reasons.append("admin refresh changed-path set contains non-allowlisted paths")
    return _decision(
        kind="admin_refresh_light_ci",
        status="PASS",
        mode=FULL_CI,
        reasons=reasons,
        changed_paths=paths,
        missing_paths=missing,
        unexpected_paths=unexpected,
    )


def _path_matches(path: str, rule: str) -> bool:
    normalized_rule = rule.strip().replace("\\", "/")
    if not normalized_rule:
        return False
    if normalized_rule.endswith("/"):
        return path.startswith(normalized_rule)
    return path == normalized_rule or path.startswith(f"{normalized_rule}/")


def load_pages_input_manifest(path: Path = PAGES_INPUT_MANIFEST) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 1, "_load_error": f"cannot load Pages input manifest: {exc}"}


def validate_pages_input_manifest(data: dict[str, Any]) -> tuple[str, ...]:
    findings: list[str] = []
    if data.get("_load_error"):
        findings.append(str(data["_load_error"]))
    if data.get("schema_version") != 1:
        findings.append("schema_version must be 1")
    for key in ("site_input_paths", "release_state_paths", "workflow_paths", "required_pull_request_test_paths"):
        value = data.get(key)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
            findings.append(f"{key} must be a non-empty string list")
    return tuple(findings)


def classify_pages_build(
    changed_paths: Iterable[str],
    *,
    event_name: str,
    manifest: dict[str, Any],
) -> CiPolicyDecision:
    paths, invalid = normalize_changed_paths(changed_paths)
    manifest_findings = validate_pages_input_manifest(manifest)
    if invalid or manifest_findings:
        return _decision(
            kind="pages_path_gate",
            status="PASS",
            mode=BUILD_REQUIRED,
            reasons=(*manifest_findings, "invalid or unverifiable input requires Pages build"),
            changed_paths=paths,
            invalid_paths=invalid,
        )
    if event_name == "workflow_dispatch":
        return _decision(
            kind="pages_path_gate",
            status="PASS",
            mode=BUILD_REQUIRED,
            reasons=("manual workflow_dispatch explicitly requires Pages build",),
            changed_paths=paths,
        )
    if not paths:
        return _decision(
            kind="pages_path_gate",
            status="PASS",
            mode=BUILD_REQUIRED,
            reasons=("changed paths are unavailable; fail closed to Pages build",),
            changed_paths=paths,
        )
    rules = tuple(
        item
        for key in ("site_input_paths", "release_state_paths", "workflow_paths")
        for item in manifest.get(key, [])
        if isinstance(item, str)
    )
    matched = tuple(sorted(path for path in paths if any(_path_matches(path, rule) for rule in rules)))
    if matched:
        return _decision(
            kind="pages_path_gate",
            status="PASS",
            mode=BUILD_REQUIRED,
            reasons=("changed paths touch generated-site inputs or release/version state",),
            changed_paths=paths,
            matched_paths=matched,
        )
    return _decision(
        kind="pages_path_gate",
        status="PASS",
        mode=BUILD_SKIPPED,
        reasons=("no generated-site input, release/version, or Pages workflow path changed",),
        changed_paths=paths,
    )


def _is_main_push_dedupe_unsafe(path: str) -> bool:
    return path in MAIN_PUSH_DEDUPE_UNSAFE_FILES or any(
        path.startswith(prefix) for prefix in MAIN_PUSH_DEDUPE_UNSAFE_PREFIXES
    )


def classify_main_push_tree_proof(
    changed_paths: Iterable[str],
    *,
    event_name: str,
    final_tree_sha: str = "",
    tested_tree_sha: str = "",
    pr_checks_passed: bool | None = None,
) -> CiPolicyDecision:
    paths, invalid = normalize_changed_paths(changed_paths)
    if event_name != "push":
        return _decision(
            kind="main_push_tree_proof",
            status="PASS",
            mode=FULL_CI,
            reasons=("not a push event; full CI remains the required path",),
            changed_paths=paths,
        )
    reasons: list[str] = []
    if invalid:
        reasons.append("invalid changed paths require full CI")
    unsafe = tuple(path for path in paths if _is_main_push_dedupe_unsafe(path))
    if unsafe:
        reasons.append("workflow, code, test, release, governance, architecture, manifest, or site paths changed")
    if not final_tree_sha or not tested_tree_sha:
        reasons.append("final and tested tree SHAs are required for a safe equivalence proof")
    elif final_tree_sha != tested_tree_sha:
        reasons.append("final main tree does not match tested PR integration tree")
    if pr_checks_passed is not True:
        reasons.append("successful PR checks were not proven")
    if reasons:
        return _decision(
            kind="main_push_tree_proof",
            status="PASS",
            mode=FULL_CI,
            reasons=reasons,
            changed_paths=paths,
            matched_paths=unsafe,
            invalid_paths=invalid,
        )
    return _decision(
        kind="main_push_tree_proof",
        status="PASS",
        mode=TREE_PROOF,
        reasons=("final main tree matches the tested PR integration tree and PR checks passed",),
        changed_paths=paths,
    )


FAILURE_PATTERNS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "registry-counter-drift",
        ("scope decision", "registry counter", "doc_registry_scope_decision", "scope_decision"),
        "generated documentation-registry scope counters are stale or malformed",
        "Repair doc-registry projection drift on a branch and rerun registry gates.",
    ),
    (
        "stale-llm-context-carrier",
        ("command_manifest_ack", "llm context", "successor package", "handoff package ack"),
        "generated LLM context or successor handoff carrier is stale",
        "Refresh generated handoff/context projections, inspect the diff, and rerun handoff gates.",
    ),
    (
        "dirty-volatile-carrier",
        ("dirty volatile", "known volatile", "volatile carrier"),
        "volatile carrier state is dirty",
        "Normalize known volatile files before continuing.",
    ),
    (
        "missing-checks",
        ("expected check missing", "no status checks", "missing check"),
        "required GitHub check evidence is missing",
        "Wait for or restore the required check before merge or dedupe decisions.",
    ),
    (
        "queued-stuck-run",
        ("queued", "in_progress", "no-job", "stuck"),
        "workflow run is queued, stuck, or has no job evidence",
        "Inspect the run and preserve failure evidence before retrying.",
    ),
    (
        "pages-deploy-issue",
        ("pages", "deploy-pages", "pages-build-deployment"),
        "GitHub Pages build or deployment failed",
        "Inspect Pages run logs and rerun only after the source cause is understood.",
    ),
    (
        "timeout",
        ("timeout", "timed_out", "deadline"),
        "workflow or gate timed out",
        "Record timeout evidence and split runtime diagnosis from product repair.",
    ),
    (
        "test-failure",
        ("pytest", "test failed", "tests failed", "assertionerror", "failed tests"),
        "test failure",
        "Reproduce the failing test on a branch before proposing repairs.",
    ),
)


def classify_failure_class(text: str) -> tuple[str, str, str]:
    lowered = text.lower()
    for failure_class, needles, suspected_root_cause, next_safe_action in FAILURE_PATTERNS:
        if any(needle in lowered for needle in needles):
            return failure_class, suspected_root_cause, next_safe_action
    return (
        "unknown",
        "failure class is not recognized by the diagnostic registry",
        "Preserve logs, classify manually, then add a deterministic pattern if recurring.",
    )


def build_failure_record(
    *,
    workflow_run_id: str,
    failing_job: str,
    message: str,
    evidence_pointers: Iterable[str],
) -> dict[str, Any]:
    failure_class, suspected_root_cause, next_safe_action = classify_failure_class(message)
    pointers = tuple(pointer for pointer in evidence_pointers if pointer)
    record = {
        "schema_version": 1,
        "kind": "ci_workflow_failure_record",
        "status": "PASS" if workflow_run_id and failing_job and pointers else "BLOCK",
        "mode": DIAGNOSTIC_ONLY,
        "diagnostic_only": True,
        "mutation": "none",
        "workflow_run_id": workflow_run_id,
        "failing_job": failing_job,
        "failure_class": failure_class,
        "evidence_pointers": list(pointers),
        "suspected_root_cause": suspected_root_cause,
        "next_safe_action": next_safe_action,
    }
    if record["status"] == "BLOCK":
        record["blockers"] = [
            item
            for item, value in (
                ("workflow_run_id", workflow_run_id),
                ("failing_job", failing_job),
                ("evidence_pointers", pointers),
            )
            if not value
        ]
    else:
        record["blockers"] = []
    return record


def receipt_store_decision() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "refresh_receipt_store_decision",
        "status": "PASS",
        "decision": "defer_replacement_keep_current_refresh_pr_mechanism",
        "evidence": "docs/reports/POST_V1_0_6_REFRESH_RECEIPT_FEASIBILITY_20260827.md",
        "exactly_one_receipt": "not_proven",
        "append_only_enforcement": "not_proven",
        "successor_read_path_discovery": "not_proven",
        "current_refresh_mechanism_removed": False,
        "next_safe_action": "Prototype receipt validation before replacing admin refresh PRs.",
    }


def _write_json_or_stdout(payload: dict[str, Any], output: str) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def _bool_from_cli(value: str) -> bool | None:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic CI runtime policy helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin = subparsers.add_parser("admin-refresh")
    admin.add_argument("--changed-paths-file", required=True)
    admin.add_argument("--branch", default="")
    admin.add_argument("--source-pr", type=int)
    admin.add_argument("--validation-status", default="")
    admin.add_argument("--output", default="")

    pages = subparsers.add_parser("pages")
    pages.add_argument("--changed-paths-file", required=True)
    pages.add_argument("--event-name", required=True)
    pages.add_argument("--manifest", default=str(PAGES_INPUT_MANIFEST))
    pages.add_argument("--output", default="")

    main_push = subparsers.add_parser("main-push")
    main_push.add_argument("--changed-paths-file", required=True)
    main_push.add_argument("--event-name", required=True)
    main_push.add_argument("--final-tree", default="")
    main_push.add_argument("--tested-tree", default="")
    main_push.add_argument("--pr-checks-passed", default="unknown")
    main_push.add_argument("--output", default="")

    failure = subparsers.add_parser("failure-record")
    failure.add_argument("--workflow-run-id", required=True)
    failure.add_argument("--failing-job", required=True)
    failure.add_argument("--message", required=True)
    failure.add_argument("--evidence", action="append", default=[])
    failure.add_argument("--output", default="")

    receipt = subparsers.add_parser("receipt-decision")
    receipt.add_argument("--output", default="")

    args = parser.parse_args(argv)
    if args.command == "admin-refresh":
        payload = classify_admin_refresh_light(
            read_changed_paths(Path(args.changed_paths_file)),
            branch=args.branch,
            source_pr=args.source_pr,
            validation_status=args.validation_status,
        ).as_dict()
    elif args.command == "pages":
        payload = classify_pages_build(
            read_changed_paths(Path(args.changed_paths_file)),
            event_name=args.event_name,
            manifest=load_pages_input_manifest(Path(args.manifest)),
        ).as_dict()
    elif args.command == "main-push":
        payload = classify_main_push_tree_proof(
            read_changed_paths(Path(args.changed_paths_file)),
            event_name=args.event_name,
            final_tree_sha=args.final_tree,
            tested_tree_sha=args.tested_tree,
            pr_checks_passed=_bool_from_cli(args.pr_checks_passed),
        ).as_dict()
    elif args.command == "failure-record":
        payload = build_failure_record(
            workflow_run_id=args.workflow_run_id,
            failing_job=args.failing_job,
            message=args.message,
            evidence_pointers=args.evidence,
        )
    else:
        payload = receipt_store_decision()
    _write_json_or_stdout(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
