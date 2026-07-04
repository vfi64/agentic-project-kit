from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *


def _normalize_agentic_command_for_reference(command: str) -> str:
    parts = shlex.split(command)
    if not parts:
        return ""
    if parts[0].endswith("agentic-kit"):
        parts[0] = "agentic-kit"
    elif parts[:2] == ["./.venv/bin/python", "-m"] and len(parts) >= 3 and parts[2] == "agentic_project_kit":
        parts = ["agentic-kit", *parts[3:]]
    else:
        return " ".join(parts)
    return " ".join(parts)

def _load_command_reference_names(root: Path) -> set[str]:
    reference_path = root / "docs/reference/agentic-kit-commands.json"
    payload = json.loads(reference_path.read_text(encoding="utf-8"))
    commands = payload.get("commands", [])
    names: set[str] = set()
    for item in commands:
        if isinstance(item, dict) and isinstance(item.get("qualified_name"), str):
            names.add(str(item["qualified_name"]))
    return names

def _detect_avoidable_low_level_meta_command_sequences(sequence_commands: list[str] | None) -> list[dict[str, object]]:
    if not sequence_commands:
        return []

    meta_command_sequences = {
        "pr-closeout-complete": {
            "meta_command": "agentic-kit transfer pr-closeout-complete",
            "low_level_markers": {
                "agentic-kit transfer pr-wait-ci",
                "agentic-kit transfer pr-merge-safe",
                "agentic-kit transfer post-merge-check",
                "agentic-kit transfer post-merge-complete",
                "agentic-kit transfer repo-status",
            },
        },
        "work-start": {
            "meta_command": "agentic-kit work start",
            "low_level_markers": {
                "agentic-kit transfer sync-main",
                "agentic-kit rules acknowledge",
                "agentic-kit transfer post-merge-check",
                "agentic-kit transfer repo-status",
            },
        },
        "work-check": {
            "meta_command": "agentic-kit work check",
            "low_level_markers": {
                "agentic-kit transfer command-reference-check",
                "agentic-kit docs-audit",
                "agentic-kit audit-doc-currency",
            },
        },
        "work-finish": {
            "meta_command": "agentic-kit work finish",
            "low_level_markers": {
                "agentic-kit transfer protected-diff-plan",
                "agentic-kit transfer commit",
                "agentic-kit transfer push-current",
                "agentic-kit transfer pr-create-complete",
            },
        },
        "work-recover": {
            "meta_command": "agentic-kit work recover",
            "low_level_markers": {
                "agentic-kit transfer restore-known-volatile",
                "agentic-kit transfer normalize-session",
                "agentic-kit transfer conflict-status",
                "agentic-kit transfer patch-cycle-status",
            },
        },
        "release-ready": {
            "meta_command": "agentic-kit release ready",
            "low_level_markers": {
                "agentic-kit transfer standard-error-scan",
                "agentic-kit release-status",
            },
        },
        "release-prepare": {
            "meta_command": "agentic-kit release prepare",
            "low_level_markers": {
                "agentic-kit release-notes-generate",
                "agentic-kit release-prep",
            },
        },
    }

    normalized_sequence = [" ".join(command.split()) for command in sequence_commands]
    sequence_blob = "\n".join(normalized_sequence)
    avoidable: list[dict[str, object]] = []
    for sequence_name, rule in meta_command_sequences.items():
        meta_command = str(rule["meta_command"])
        markers = set(rule["low_level_markers"])
        matched_markers = sorted(marker for marker in markers if marker in sequence_blob)
        if len(matched_markers) >= 2 and meta_command not in sequence_blob:
            avoidable.append(
                {
                    "sequence": sequence_name,
                    "preferred_meta_command": meta_command,
                    "matched_low_level_markers": matched_markers,
                }
            )
    return avoidable

@transfer_app.command("command-composition-check")
def command_composition_check_command(
    test_paths: list[Path] | None = typer.Option(
        None,
        "--test-path",
        help="Repository-relative test path that must exist before composing a pytest command. Repeatable.",
    ),
    commands: list[str] | None = typer.Option(
        None,
        "--command",
        help="agentic-kit command prefix that must exist in docs/reference/agentic-kit-commands.json. Repeatable.",
    ),
    sequence_commands: list[str] | None = typer.Option(
        None,
        "--sequence-command",
        help="Command sequence entry to check for avoidable low-level workflow chains. Repeatable.",
    ),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Block common copied-command mistakes before running patch, transfer, or release gates."""
    project_root = root.resolve()
    avoidable_low_level_sequences = _detect_avoidable_low_level_meta_command_sequences(sequence_commands)
    missing_test_paths: list[str] = []
    existing_test_paths: list[str] = []
    for raw_path in test_paths or []:
        candidate = raw_path if raw_path.is_absolute() else project_root / raw_path
        rel = str(raw_path)
        if candidate.exists():
            existing_test_paths.append(rel)
        else:
            missing_test_paths.append(rel)

    reference_missing = False
    valid_commands: list[str] = []
    invalid_commands: list[str] = []
    try:
        reference_names = _load_command_reference_names(project_root)
    except (OSError, json.JSONDecodeError, ValueError):
        reference_names = set()
        reference_missing = bool(commands)

    for command in commands or []:
        normalized = _normalize_agentic_command_for_reference(command)
        if normalized and normalized in reference_names:
            valid_commands.append(command)
        else:
            invalid_commands.append(command)

    blockers: list[str] = []
    if missing_test_paths:
        blockers.append("missing_test_paths")
    if reference_missing:
        blockers.append("command_reference_unavailable")
    if invalid_commands:
        blockers.append("invalid_agentic_kit_commands")
    if avoidable_low_level_sequences:
        blockers.append("avoidable_low_level_sequences")

    result_status = "PASS" if not blockers else "BLOCKED"
    next_action = (
        "Command composition inputs are valid."
        if result_status == "PASS"
        else "Fix missing test paths or invalid agentic-kit command names before running the composed block."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_command_composition_check_result",
        "action": "command-composition-check",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "blockers": blockers,
        "test_paths": {
            "existing": existing_test_paths,
            "missing": missing_test_paths,
        },
        "commands": {
            "valid": valid_commands,
            "invalid": invalid_commands,
        },
        "avoidable_low_level_sequences": avoidable_low_level_sequences,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_COMMAND_COMPOSITION_CHECK",
            result_status=result_status,
            final_signal="d" if result_status == "PASS" else "f",
            next_action=next_action,
            fields={
                "MISSING_TEST_PATHS": len(missing_test_paths),
                "INVALID_COMMANDS": len(invalid_commands),
                "AVOIDABLE_LOW_LEVEL_SEQUENCES": len(avoidable_low_level_sequences),
            },
        )

    if result_status != "PASS":
        raise typer.Exit(code=2)

def _load_yaml_mapping(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}

def _meta_command_preference_source_paths(root: Path) -> set[Path]:
    """Return the explicit YAML rule sources for active meta-command policy."""
    return {
        root / ".agentic" / "transfer_safety_rules.yaml",
        root / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml",
    }

def _load_transfer_meta_command_preference(root: Path) -> dict[str, object]:
    """Load local-to-LLM meta-command preference dynamically from rule sources."""
    safety = _load_yaml_mapping(root / ".agentic" / "transfer_safety_rules.yaml")
    protocol = _load_yaml_mapping(root / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml")

    safety_pref = safety.get("meta_command_preference")
    protocol_pref = protocol.get("meta_command_preference")

    preferred_commands: list[str] = []
    if isinstance(safety_pref, dict):
        raw = safety_pref.get("preferred_commands")
        if isinstance(raw, dict):
            preferred_commands.extend(str(value) for value in raw.values())
        elif isinstance(raw, list):
            preferred_commands.extend(str(value) for value in raw)
    if isinstance(protocol_pref, dict):
        raw = protocol_pref.get("preferred_entrypoints")
        if isinstance(raw, list):
            preferred_commands.extend(str(value) for value in raw)

    unique_commands: list[str] = []
    seen: set[str] = set()
    for command in preferred_commands:
        if command and command not in seen:
            seen.add(command)
            unique_commands.append(command)

    fallback_rule = ""
    priority = ""
    if isinstance(safety_pref, dict):
        fallback_rule = str(safety_pref.get("fallback_rule") or "")
        priority = str(safety_pref.get("priority") or "")
    if not fallback_rule and isinstance(protocol_pref, dict):
        fallback_rule = str(protocol_pref.get("rule") or "")

    return {
        "status": "active" if unique_commands else "missing",
        "priority": priority or "primary_path",
        "preferred_commands": unique_commands,
        "fallback_rule": fallback_rule,
        "sources": sorted(str(path) for path in _meta_command_preference_source_paths(root)),
    }

def _render_transfer_meta_command_preference_header(root: Path) -> str:
    preference = _load_transfer_meta_command_preference(root)
    if preference["status"] != "active":
        return ""
    lines = [
        "META_COMMAND_PREFERENCE:",
        f"  status: {preference['status']}",
        f"  priority: {preference['priority']}",
        "  source: dynamic-from-rule-files",
        "  preferred_commands:",
    ]
    for command in preference["preferred_commands"]:
        lines.append(f"    - {command}")
    fallback = str(preference.get("fallback_rule") or "").strip()
    if fallback:
        lines.append(f"  fallback_rule: {fallback}")
    lines.append("  low_level_fallback_requires_reason: true")
    return "\n".join(lines)

def _render_local_to_llm_transfer_header(root: Path) -> str:
    """Render the local-to-LLM transfer header from current rule sources."""
    sections: list[str] = []
    meta_header = _render_transfer_meta_command_preference_header(root).strip()
    if meta_header:
        sections.append(meta_header)
    return "\n\n".join(sections).strip()

def _prefix_local_to_llm_transfer_header(content: str, *, root: Path | None = None) -> str:
    """Prefix local-to-LLM transfer content with a dynamically rendered header."""
    effective_root = root or Path(".")
    header = _render_local_to_llm_transfer_header(effective_root).strip()
    if not header:
        return content
    if content.startswith("META_COMMAND_PREFERENCE:"):
        return content
    return f"{header}\n\n{content}"

def _json_contains_static_meta_preference_policy(content: str) -> bool:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return False

    def walk(value: object) -> bool:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"meta_command_preference", "META_COMMAND_PREFERENCE"}:
                    return True
                if walk(nested):
                    return True
        elif isinstance(value, list):
            return any(walk(item) for item in value)
        return False

    return walk(parsed)

def _scan_static_meta_preference_projection_drift(root: Path) -> dict[str, object]:
    """Block static active meta-command policy outside explicit YAML rule sources.

    This scans projections and generated/compiled carriers. It deliberately does
    not scan implementation source code, because renderer code necessarily
    contains marker strings such as META_COMMAND_PREFERENCE.
    """
    allowed_sources = {path.resolve() for path in _meta_command_preference_source_paths(root)}
    scanned_roots = [
        root / ".agentic",
        root / "docs",
    ]
    forbidden_markers = [
        "meta_command_preference:",
        '"meta_command_preference"',
        "META_COMMAND_PREFERENCE:",
        '"META_COMMAND_PREFERENCE"',
    ]
    matches: list[dict[str, object]] = []

    for scan_root in scanned_roots:
        if not scan_root.exists():
            continue
        for candidate in scan_root.rglob("*"):
            if not candidate.is_file():
                continue
            relative_parts = candidate.relative_to(scan_root).parts
            if any(part in {".git", ".venv", "tmp", "__pycache__"} for part in relative_parts):
                continue
            if candidate.suffix not in {"", ".md", ".txt", ".yaml", ".yml", ".json"}:
                continue
            if candidate.resolve() in allowed_sources:
                continue
            try:
                content = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            json_policy_match = candidate.suffix == ".json" and _json_contains_static_meta_preference_policy(content)
            if json_policy_match:
                line_numbers = [
                    index
                    for index, line in enumerate(content.splitlines(), start=1)
                    if "meta_command_preference" in line or "META_COMMAND_PREFERENCE" in line
                ] or [1]
                matches.append(
                    {
                        "path": str(candidate.relative_to(root)),
                        "marker": "json:meta_command_preference",
                        "line_numbers": line_numbers,
                    }
                )
                continue

            for marker in forbidden_markers:
                marker_matches = [marker]
                if marker == "meta_command_preference:":
                    marker_matches.extend([
                        '"meta_command_preference"',
                        "'meta_command_preference'",
                    ])
                if marker == "META_COMMAND_PREFERENCE:":
                    marker_matches.extend([
                        '"META_COMMAND_PREFERENCE"',
                        "'META_COMMAND_PREFERENCE'",
                    ])
                if not any(marker_match in content for marker_match in marker_matches):
                    continue
                line_numbers = [
                    index
                    for index, line in enumerate(content.splitlines(), start=1)
                    if any(marker_match in line for marker_match in marker_matches)
                ]
                matches.append(
                    {
                        "path": str(candidate.relative_to(root)),
                        "marker": marker,
                        "line_numbers": line_numbers,
                    }
                )
    return {
        "status": "PASS" if not matches else "BLOCKED",
        "allowed_static_sources": sorted(str(path.relative_to(root)) for path in _meta_command_preference_source_paths(root)),
        "matches": matches,
    }

def _latest_release_tag() -> str:
    completed = subprocess.run(
        ["git", "tag", "--sort=-creatordate"],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        tag = line.strip()
        if tag.startswith("v"):
            return tag
    return ""

def _run_standard_error_scan_step(
    name: str,
    argv: list[str],
    *,
    allowed_returncodes: set[int] | None = None,
) -> dict[str, object]:
    allowed = allowed_returncodes or {0}
    completed = subprocess.run(argv, text=True, capture_output=True)
    ok = completed.returncode in allowed
    return {
        "name": name,
        "argv": argv,
        "returncode": completed.returncode,
        "ok": ok,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "allowed_returncodes": sorted(allowed),
    }

def _known_bad_pattern_scan(root: Path) -> dict[str, object]:
    # Build these from fragments so repository audits do not flag the scanner's own
    # negative examples as active workflow instructions.
    patterns = [
        "tests/" + "test_release_status.py",
        "agentic-kit " + "command-reference-refresh",
        "_copy_" + "project_fixture",
        "<" + "pr-number>",
        "./" + "ns protected-diff-check",
        "./" + "ns merge-if-green",
        "./" + "ns next-safe-step",
    ]
    # Scan only active workflow surfaces. Historical planning/test-gate docs may
    # legitimately mention old commands as examples or archived failure modes.
    search_roots = [
        root / "src",
        root / "tests",
        root / "docs/reference",
        root / "docs/handoff",
        root / ".agentic",
    ]
    matches: list[dict[str, object]] = []
    for base in search_roots:
        if not base.exists():
            continue
        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in {".git", ".venv", "tmp", "__pycache__"} for part in file_path.parts):
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                for pattern in patterns:
                    if pattern in line:
                        matches.append(
                            {
                                "path": str(file_path.relative_to(root)),
                                "line": line_number,
                                "pattern": pattern,
                                "text": line.strip()[:240],
                            }
                        )
    return {"patterns": patterns, "matches": matches}

def _scan_llm_work_order_contract(root: Path) -> dict[str, object]:
    """Verify that LLM work orders are contractually Python scripts."""
    try:
        header = build_transfer_safety_header(root)
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "error": str(exc),
            "required_format": None,
            "canonical_inbox": None,
            "shell_commands_allowed": None,
        }

    contract = header.get("llm_work_order_contract")
    if not isinstance(contract, dict):
        return {
            "status": "BLOCKED",
            "error": "llm_work_order_contract_missing",
            "required_format": None,
            "canonical_inbox": None,
            "shell_commands_allowed": None,
        }

    transfer_file = contract.get("transfer_file")
    if not isinstance(transfer_file, dict):
        transfer_file = {}

    required_format = contract.get("required_format")
    canonical_inbox = transfer_file.get("canonical_inbox")
    shell_commands_allowed = transfer_file.get("shell_commands_allowed")

    failures: list[str] = []
    if required_format != "python_script":
        failures.append("required_format_not_python_script")
    if not str(canonical_inbox or "").endswith(".py.txt"):
        failures.append("canonical_inbox_not_python_script_file")
    if shell_commands_allowed is not False:
        failures.append("transfer_file_allows_shell_commands")

    return {
        "status": "PASS" if not failures else "BLOCKED",
        "failures": failures,
        "required_format": required_format,
        "canonical_inbox": canonical_inbox,
        "shell_commands_allowed": shell_commands_allowed,
    }

@transfer_app.command("standard-error-scan")
def standard_error_scan_command(
    before_release: bool = typer.Option(
        False,
        "--before-release",
        help="Run the release-oriented standard-error scan bundle.",
    ),
    version: str = typer.Option("", "--version", help="Release version for before-release checks. Required with --before-release."),
    from_tag: str = typer.Option("", "--from-tag", help="Previous release tag for release notes checks. Defaults to the latest local v* git tag."),
    to_ref: str = typer.Option("main", "--to-ref", help="Target ref for release notes checks."),
    date: str = typer.Option("", "--date", help="Release date for release-prep dry-run. Defaults to today."),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Run a bounded scan for known workflow standard errors before patch/transfer/release work."""
    project_root = root.resolve()
    release_date = date or date_cls.today().isoformat()
    effective_from_tag = from_tag or _latest_release_tag()
    steps: list[dict[str, object]] = []

    def step(name: str, argv: list[str], *, allowed_returncodes: set[int] | None = None) -> None:
        steps.append(_run_standard_error_scan_step(name, argv, allowed_returncodes=allowed_returncodes))

    if before_release:
        step("post-merge-check", ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"])
    step("repo-status", ["./.venv/bin/agentic-kit", "transfer", "repo-status"])

    release_tests = [
        "tests/test_release_prepare_command.py",
        "tests/test_release_notes.py",
        "tests/test_release_state.py",
        "tests/test_agentic_kit_command_reference_is_current.py",
    ]
    command_check = [
        "./.venv/bin/agentic-kit",
        "transfer",
        "command-composition-check",
        "--json",
    ]
    for test_path in release_tests:
        command_check.extend(["--test-path", test_path])
    for command in [
        "agentic-kit transfer command-reference-check",
        "agentic-kit transfer command-composition-check",
        "agentic-kit transfer patch-cycle-status",
        "agentic-kit release-status",
        "agentic-kit release-notes-generate",
        "agentic-kit release-prep",
    ]:
        command_check.extend(["--command", command])
    step("command-composition-check", command_check)
    step("command-reference-check", ["./.venv/bin/agentic-kit", "transfer", "command-reference-check", "--json"])
    step("patch-cycle-status", ["./.venv/bin/agentic-kit", "transfer", "patch-cycle-status", "--include-ci", "--json"], allowed_returncodes={0, 2})

    if before_release:
        if not version:
            steps.append(
                {
                    "name": "release-version",
                    "argv": [],
                    "returncode": 2,
                    "ok": False,
                    "allowed_returncodes": [0],
                    "stdout": "",
                    "stderr": "--version is required with --before-release.",
                }
            )
        if not effective_from_tag:
            steps.append(
                {
                    "name": "release-from-tag",
                    "argv": [],
                    "returncode": 2,
                    "ok": False,
                    "allowed_returncodes": [0],
                    "stdout": "",
                    "stderr": "--from-tag was not provided and no local v* git tag could be derived.",
                }
            )
        summary_lines_path = project_root / "tmp" / f"release-{version.replace('.', '')}-summary-lines.json"
        step("release-status", ["./.venv/bin/agentic-kit", "release-status", "--include-remote", "--json"], allowed_returncodes={0, 2})
        step(
            "release-notes-generate",
            [
                "./.venv/bin/agentic-kit",
                "release-notes-generate",
                "--version",
                version,
                "--from-tag",
                effective_from_tag,
                "--to-ref",
                to_ref,
                "--include-github-metadata",
                "--summary-lines-json",
                str(summary_lines_path),
                "--json",
            ],
        )
        step(
            "release-prep-dry-run",
            [
                "./.venv/bin/agentic-kit",
                "release-prep",
                "--version",
                version,
                "--date",
                release_date,
                "--summary-lines-from",
                str(summary_lines_path),
                "--dry-run",
                "--json",
            ],
        )

    step(
        "fresh-context-strict",
        ["./.venv/bin/agentic-kit", "transfer", "require-fresh-llm-context", "--json"],
        allowed_returncodes={0, 2},
    )
    step(
        "fresh-context-clean-post-merge-allowance",
        [
            "./.venv/bin/agentic-kit",
            "transfer",
            "require-fresh-llm-context",
            "--allow-clean-post-merge-carrier-staleness",
            "--json",
        ],
        allowed_returncodes={0} if before_release else {0, 2},
    )
    step("docs-audit", ["./.venv/bin/agentic-kit", "docs-audit"])
    step("audit-doc-currency", ["./.venv/bin/agentic-kit", "audit-doc-currency"])
    step("audit-planning-docs-consolidation", ["./.venv/bin/agentic-kit", "audit-planning-docs-consolidation"])
    step("audit-ns-legacy-references", ["./.venv/bin/agentic-kit", "audit-ns-legacy-references"])
    step("audit-program-redundancy", ["./.venv/bin/agentic-kit", "audit-program-redundancy"])
    step("standard-gates-audit-suite", ["./.venv/bin/agentic-kit", "standard-gates-audit-suite"])

    pattern_scan = _known_bad_pattern_scan(project_root)
    llm_work_order_contract_scan = _scan_llm_work_order_contract(project_root)
    local_to_llm_log_header = render_local_to_llm_log_header(project_root)
    local_to_llm_log_header_contains_meta_preference = (
        "META_COMMAND_PREFERENCE" in local_to_llm_log_header
        or "meta_command_preference" in local_to_llm_log_header
    )
    local_to_llm_log_header_scan = {
        "status": "PASS"
        if local_to_llm_log_header_contains_meta_preference and "dynamic-from-rule-files" in local_to_llm_log_header
        else "BLOCKED",
        "contains_meta_command_preference": local_to_llm_log_header_contains_meta_preference,
        "contains_dynamic_source_marker": "dynamic-from-rule-files" in local_to_llm_log_header,
    }
    static_meta_preference_projection_scan = _scan_static_meta_preference_projection_drift(project_root)
    blockers: list[str] = []
    warnings: list[str] = []

    for item in steps:
        if not item["ok"]:
            blockers.append(str(item["name"]))

    if pattern_scan["matches"]:
        warnings.append("known_bad_patterns_found")
    if llm_work_order_contract_scan["status"] != "PASS":
        blockers.append("llm_work_order_contract_not_python_script")
    if local_to_llm_log_header_scan["status"] != "PASS":
        blockers.append("local_to_llm_log_header_missing_dynamic_meta_preference")
    if static_meta_preference_projection_scan["matches"]:
        blockers.append("static_meta_preference_projection_drift")

    strict_step = next((item for item in steps if item["name"] == "fresh-context-strict"), None)
    allowance_step = next((item for item in steps if item["name"] == "fresh-context-clean-post-merge-allowance"), None)
    if strict_step and strict_step["returncode"] == 2 and allowance_step:
        if allowance_step["returncode"] == 0:
            warnings.append("strict_fresh_context_blocked_but_clean_post_merge_allowance_passed")
        elif not before_release and allowance_step["returncode"] == 2:
            warnings.append("fresh_context_stale_in_feature_branch_diagnostic")

    result_status = "BLOCKED" if blockers else "WARN" if warnings else "PASS"
    next_action = (
        "Fix blocking standard-error scan steps before continuing."
        if blockers
        else "Review warnings, then continue release readiness."
        if warnings
        else "No known standard-error blockers detected."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_standard_error_scan_result",
        "action": "standard-error-scan",
        "result_status": result_status,
        "returncode": 2 if blockers else 0,
        "before_release": before_release,
        "version": version,
        "from_tag": effective_from_tag,
        "to_ref": to_ref,
        "date": release_date,
        "blockers": blockers,
        "warnings": warnings,
        "steps": steps,
        "known_bad_pattern_scan": pattern_scan,
        "llm_work_order_contract_scan": llm_work_order_contract_scan,
        "local_to_llm_log_header_scan": local_to_llm_log_header_scan,
        "static_meta_preference_projection_scan": static_meta_preference_projection_scan,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_STANDARD_ERROR_SCAN",
            result_status=result_status,
            final_signal="f" if blockers else "d",
            next_action=next_action,
            fields={
                "BLOCKERS": len(blockers),
                "WARNINGS": len(warnings),
                "PATTERN_MATCHES": len(pattern_scan["matches"]),
            },
        )

    if blockers:
        raise typer.Exit(code=2)


__all__ = [name for name in globals() if not name.startswith("__")]
