"""Bounded K0 static report; reuses the historical analyzer, never runs Kit actions.

This is a developer report generator, not a new public CLI or classification authority.
Usage: .venv/bin/python scripts/command_composition_audit.py --source-commit <sha> --out <dir>
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import contextlib
import hashlib
import inspect
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile


def closure(start, edges):
    seen, pending = {start}, [start]
    while pending:
        for child in edges.get(pending.pop(), ()):
            if child not in seen:
                seen.add(child)
                pending.append(child)
    return seen


def compare_views(commands, classify):
    rows = []
    for command in sorted(commands, key=lambda c: c["qualified_name"]):
        entry = classify(command).as_dict()
        rows.append(
            {
                **entry,
                **{k: command.get(k) for k in ("surface", "safety", "task_tags", "remote_effects")},
            }
        )
    return rows


def inventory_diff(current_commands, historical):
    """Compare command names, not old dynamic tiers or observed usage."""
    before = {row["command"] for row in historical["commands"]}
    after = {row["qualified_name"] for row in current_commands}
    return {
        "source_path": "docs/reports/COMMAND_USAGE_AUDIT_20261015.json",
        "source_commit": historical["base_commit"],
        "manifest_sha": historical["manifest_sha"],
        "command_count": len(before),
        "added": sorted(after - before),
        "removed": sorted(before - after),
    }


def website_selections(source, known):
    """Only literal argument tuples to the actual selection helper; no execution."""
    selections = []
    for node in ast.walk(ast.parse(source)):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_quickstart_commands"
            and len(node.args) > 1
        ):
            continue
        try:
            names = ast.literal_eval(node.args[1])
        except (ValueError, TypeError):
            selections.append({"line": node.lineno, "unresolved": True})
            continue
        selections.append(
            {"line": node.lineno, "commands": list(names), "missing": sorted(set(names) - known)}
        )
    return sorted(selections, key=lambda r: r["line"])


def shared_candidates(callbacks, edges, locations):
    owners, callers = defaultdict(set), defaultdict(set)
    for caller, targets in edges.items():
        for target in targets:
            callers[target].add(caller)
    for command, callback in callbacks.items():
        for target in edges.get(callback, ()):
            if target not in callbacks.values():
                owners[target].add(command)
    return [
        dict(
            function=target,
            module=target.split(":")[0],
            direct_command_callers=sorted(owners[target]),
            function_callers=sorted(callers[target]),
            location=locations[target],
            uncertainty="Static potential calls, including passed callbacks/closures; not execution or core authority.",
        )
        for target in sorted(owners)
        if len({callbacks[command] for command in owners[target]}) >= 2
    ]


def checked(argv, root):
    done = subprocess.run(argv, cwd=root, text=True, capture_output=True, check=False)
    if done.returncode:
        raise RuntimeError(f"{argv[0]} rc={done.returncode}: {done.stderr[-1000:]}")
    return done.stdout.strip()


def generate(root, source_commit):
    from agentic_project_kit.command_taxonomy import classify_command
    from typer.main import get_command
    from agentic_project_kit.cli import app

    source_commit = checked(["git", "rev-parse", source_commit], root)
    # A report about a pinned source must not silently inspect edited product code.
    drift = checked(
        [
            "git",
            "diff",
            "--name-only",
            source_commit,
            "--",
            "src",
            "tools",
            "docs/reference/agentic-kit-commands.json",
        ],
        root,
    )
    if drift:
        raise ValueError(f"audited source differs from pinned commit: {drift}")
    manifest_path = root / "docs/reference/agentic-kit-commands.json"
    manifest = json.loads(manifest_path.read_text())
    commands = manifest["commands"]
    known = {c["qualified_name"] for c in commands}
    callbacks = {}

    def walk(command, path):
        children = getattr(command, "commands", None)
        if children:
            for name, child in sorted(children.items()):
                walk(child, [*path, name])
        else:
            fn = inspect.unwrap(command.callback)
            callbacks["agentic-kit " + " ".join(path)] = {
                "module": fn.__module__,
                "qualname": fn.__qualname__,
                "file": Path(inspect.getsourcefile(fn)).relative_to(root).as_posix(),
                "line": inspect.getsourcelines(fn)[1],
            }

    walk(get_command(app), [])
    if set(callbacks) != known:
        raise ValueError(f"CLI/manifest mismatch: {sorted(set(callbacks) ^ known)}")
    legacy = root / "docs/reports/command_usage_audit_20261015/scripts/analyze.py"
    with tempfile.TemporaryDirectory(prefix="k0-static-") as tmp:
        cb, output = Path(tmp) / "callbacks.json", Path(tmp) / "static.json"
        cb.write_text(json.dumps(callbacks))
        old_argv = sys.argv
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            sys.argv = [str(legacy), str(root), str(cb), str(output)]
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                graph = runpy.run_path(str(legacy))
        finally:
            sys.argv = old_argv
        if stderr.getvalue() or len(graph["cb_fid"]) != len(known):
            raise ValueError("unresolved legacy callbacks: " + stderr.getvalue())
    nodes, edges, cb_fids = graph["func_nodes"], graph["edges"], graph["cb_fid"]
    locations = {
        fid: {
            "file": graph["modules"][graph["func_module"][fid]].relative_to(root).as_posix(),
            "line": node.lineno,
        }
        for fid, node in nodes.items()
    }
    by_fid = defaultdict(list)
    for command, fid in cb_fids.items():
        by_fid[fid].append(command)
    records = []
    for view in compare_views(commands, classify_command):
        command, start = view["qualified_name"], cb_fids[view["qualified_name"]]
        reachable = closure(start, edges)
        internal = {c for f in reachable - {start} for c in by_fid.get(f, ())}
        argv = {c for f in reachable for c in graph["cmd_refs"][f]} - {command}
        records.append(
            {
                **view,
                "callback": callbacks[command],
                "direct_callback_callees": sorted(edges[start]),
                "direct_callback_argv_candidates": sorted(graph["cmd_refs"][start]),
                "internal_callback_targets": sorted(internal),
                "transitive_argv_candidates": sorted(argv),
                "reachable_function_count": len(reachable),
                "text_mentions_only": graph["result"][command]["text_mentions_only"],
            }
        )
    # Do not promote legacy core_owner links: reaching shared code != invoking its CLI.
    shared = shared_candidates(cb_fids, edges, locations)
    dispatch_sites = []
    for fid, node in nodes.items():
        for call in ast.walk(node):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "getattr"
            ):
                dispatch_sites.append(
                    {
                        "function": fid,
                        "location": {**locations[fid], "line": call.lineno},
                        "expression": ast.unparse(call)[:200],
                    }
                )
    dispatch_sites.sort(
        key=lambda site: (
            site["location"]["file"],
            site["location"]["line"],
            site["expression"],
            site["function"],
        )
    )
    # Explicit table path, resolved without running the suite or its subprocess runner.
    table_file = root / "src/agentic_project_kit/standard_gates_audit_suite.py"
    tables = []
    for node in ast.parse(table_file.read_text()).body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id
            in {"REQUIRED_STANDARD_GATE_COMMANDS", "EXTERNAL_STANDARD_GATE_COMMANDS"}
        ):
            values = ast.literal_eval(node.value)
            targets = []
            for parts in values:
                matches = [
                    c for c in commands if tuple(parts[: len(c["path"])]) == tuple(c["path"])
                ]
                if not matches:
                    raise ValueError(f"unknown table route: {parts}")
                targets.append(max(matches, key=lambda c: len(c["path"]))["qualified_name"])
            tables.append({"table": node.target.id, "line": node.lineno, "commands": targets})
    command_edges = {
        row["qualified_name"]: set(row["transitive_argv_candidates"])
        | set(row["internal_callback_targets"])
        for row in records
    }
    command_edges["agentic-kit standard-gates-audit-suite"].update(
        command for table in tables for command in table["commands"]
    )
    for row in records:
        row["potential_command_closure"] = sorted(
            closure(row["qualified_name"], command_edges) - {row["qualified_name"]}
        )
    historical_path = root / "docs/reports/COMMAND_USAGE_AUDIT_20261015.json"
    historical = inventory_diff(commands, json.loads(historical_path.read_text()))
    inputs = sorted(
        set(root.glob("src/agentic_project_kit/**/*.py"))
        | {
            manifest_path,
            historical_path,
            root / "tools/next-step.py",
            legacy,
            root / "scripts/command_composition_audit.py",
            root / "scripts/command_composition_render.py",
        }
    )
    unresolved = Counter()
    for fid, node in nodes.items():
        graph["LOCAL_INSTANCES"].clear()
        for call in ast.walk(node):
            if isinstance(call, ast.Call) and graph["resolve_call"](fid, call.func) is None:
                unresolved[graph["func_module"][fid]] += 1
    return {
        "schema_version": 1,
        "kind": "bounded_command_composition_audit",
        "source_commit": source_commit,
        "manifest_sha": manifest["meta"]["manifest_sha"],
        "input_sha256": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in inputs
        },
        "execution": {
            "callback_mapping_rc": 0,
            "legacy_static_rc": 0,
            "reconciliation_rc": 0,
            "inventory_status": "COMPLETE",
            "analysis_status": "PARTIAL_STATIC",
            "test_trace": "NOT_RUN",
            "simulation": "NOT_RUN",
            "remote_effects": "NOT_RUN",
        },
        "counts": {
            "commands": len(commands),
            "callbacks": len(callbacks),
            "distinct_callback_functions": len(set(cb_fids.values())),
            "functions": len(nodes),
            "manifest_surface": dict(sorted(Counter(c["surface"] for c in commands).items())),
            "composition_level": dict(
                sorted(Counter(c["composition_level"] for c in records).items())
            ),
            "shared_direct_candidates": len(shared),
        },
        "historical_inventory": historical,
        "commands": records,
        "shared_core_candidates": shared,
        "same_callback_alias_groups": [sorted(v) for v in by_fid.values() if len(v) > 1],
        "website_selections": website_selections(
            (root / "src/agentic_project_kit/site_generator.py").read_text(), known
        ),
        "data_driven_tables": tables,
        "dynamic_dispatch_sites": dispatch_sites,
        "unresolved_or_external_ast_call_counts_by_module": dict(sorted(unresolved.items())),
        "limits": [
            "Static may-call graph, not runtime coverage, frequency, necessity or semantic equivalence.",
            "Legacy analyzer over-approximates passed callbacks, nested closures and getattr prefixes.",
            "Literal argv candidates can occur in construction/guidance; they are not execution proof.",
            "Unknown/external calls include Python builtins, external libraries and dynamic receivers; counts are not defect counts.",
            "Legacy resolver is name-based and path-insensitive; shadowing and object aliasing can produce false edges.",
            "Shared candidates use at least two direct CLI owners; deeper shared mechanisms can be missed.",
            "Only the named standard-gate tables are explicitly resolved; arbitrary tables/configuration are not complete.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = generate(root, args.source_commit)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "composition.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    from command_composition_render import render_report

    (args.out / "README.md").write_text(render_report(report))
    print(json.dumps({"execution": report["execution"], "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
