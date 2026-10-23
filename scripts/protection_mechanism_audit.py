"""K0c: bounded static reachability, existing lock audit and consumer source check.

Developer report only. Does not execute Kit callbacks or change safety decisions.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, deque
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

MECHANISMS = (
    "agentic_project_kit.rule_ack:validate_rule_acknowledgement",
    "agentic_project_kit.workspace_lock:workspace_mutation_lock",
    "agentic_project_kit.safe_push:safe_push",
    "agentic_project_kit.evidence_guard:check_change_scope",
    "agentic_project_kit.evidence_guard:check_terminal_log",
)
LOCK_BASE = "agentic_project_kit.workspace_lock:acquire_workspace_lock"


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if done.returncode:
        raise RuntimeError(f"git {args[0]} rc={done.returncode}: {done.stderr[-500:]}")
    return done.stdout.strip()


def shortest_paths(start, edges):
    parents, queue = {start: None}, deque([start])
    while queue:
        current = queue.popleft()
        for target in sorted(edges.get(current, ())):
            if target not in parents:
                parents[target] = current
                queue.append(target)
    return parents


def witness(parents, target):
    if target not in parents:
        return []
    path = []
    while target is not None:
        path.append(target)
        target = parents[target]
    return list(reversed(path))


def mechanism_rows(commands, callbacks, edges, locations):
    targets = (*MECHANISMS, LOCK_BASE)
    rows = {
        target: {"function": target, "location": locations[target], "reached_by": []}
        for target in targets
    }
    for command in sorted(commands, key=lambda item: item["qualified_name"]):
        name = command["qualified_name"]
        paths = shortest_paths(callbacks[name], edges)
        for target in targets:
            path = witness(paths, target)
            if path:
                rows[target]["reached_by"].append(
                    {
                        "command": name,
                        "safety": command["safety"],
                        "surface": command["surface"],
                        "witness": path,
                    }
                )
    for row in rows.values():
        row["count"] = len(row["reached_by"])
        row["safety_counts"] = dict(sorted(Counter(c["safety"] for c in row["reached_by"]).items()))
    return rows


def regression_references(root, paths, targets):
    """Direct imported calls in named tests; not a claim of exhaustive coverage."""
    found = {target: [] for target in targets}
    for path in paths:
        tree = ast.parse((root / path).read_text())
        imports = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    imports[alias.asname or alias.name] = f"{node.module}:{alias.name}"
        tests = [
            (node, node.name)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef) and cls.name.startswith("Test"):
                tests.extend(
                    (node, f"{cls.name}::{node.name}")
                    for node in cls.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
        for test, node_name in tests:
            if not test.name.startswith("test_"):
                continue
            # Local imports override module imports; other tests cannot supply aliases.
            aliases = dict(imports)
            for node in ast.walk(test):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        aliases[alias.asname or alias.name] = f"{node.module}:{alias.name}"
            called = {
                aliases.get(node.func.id)
                for node in ast.walk(test)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            for target in sorted(called & set(targets)):
                found[target].append(
                    {
                        "node_id": f"{path}::{node_name}",
                        "line": test.lineno,
                        "meaning": "syntactic imported call in test body; nested helpers, assertions and fixtures need source review",
                    }
                )
    return found


def consumer_check(root):
    commit = git(root, "rev-parse", "HEAD")
    tracked = git(root, "ls-files").splitlines()
    paths = [
        p
        for p in tracked
        if not p.startswith(("docs/", "Download/", ".agentic/"))
        and Path(p).suffix in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".sh"}
    ]
    changed = set(git(root, "diff", "--name-only", "HEAD").splitlines()) & set(paths)
    if changed:
        raise ValueError("consumer runtime/test source has tracked changes; snapshot not pinned")
    tokens = (
        "command-taxonomy-check",
        "command_taxonomy",
        "composition_level",
        "recommendation_weight",
    )
    matches = {token: 0 for token in tokens}
    generic_manifest_files = 0
    digest = hashlib.sha256()
    for rel in sorted(paths):
        data = (root / rel).read_bytes()
        text = data.decode("utf-8", errors="replace")
        for token in tokens:
            matches[token] += text.count(token)
        generic_manifest_files += bool(
            "agentic-kit-commands.json" in text or "command_manifest" in text
        )
        digest.update(rel.encode() + b"\0" + hashlib.sha256(data).digest())
    return {
        "repository": "agp-cockpit",
        "commit": commit,
        "tracked_source_files_scanned": len(paths),
        "snapshot_sha256": digest.hexdigest(),
        "dedicated_taxonomy_token_occurrences": matches,
        "generic_manifest_reference_files": generic_manifest_files,
        "limits": "Tracked runtime/config/test text, excluding docs, Download and .agentic. No dynamic execution, history scan or claim that generic manifest dispatch cannot invoke taxonomy. No private source content published.",
    }


def build_report(root, source_commit, consumer_root):
    from agentic_project_kit.mutation_lock_audit import audit_mutation_lock_coverage

    source_commit = git(root, "rev-parse", source_commit)
    tests = [
        p
        for p in git(
            root, "ls-tree", "-r", "--name-only", source_commit, "--", "tests"
        ).splitlines()
        if p.endswith(".py")
    ]
    changed = git(
        root,
        "diff",
        "--name-only",
        source_commit,
        "--",
        "src",
        "tools",
        "docs/reference/agentic-kit-commands.json",
        *tests,
    )
    if changed:
        raise ValueError(f"audited source differs from pinned revision: {changed}")
    manifest_path = root / "docs/reference/agentic-kit-commands.json"
    manifest = json.loads(manifest_path.read_text())
    scripts = root / "docs/reports/command_usage_audit_20261015/scripts"
    with tempfile.TemporaryDirectory(prefix="k0c-") as tmp:
        callbacks_path, raw = Path(tmp) / "callbacks.json", Path(tmp) / "static.json"
        mapped = subprocess.run(
            [sys.executable, str(scripts / "map_callbacks.py"), str(callbacks_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if mapped.returncode:
            raise RuntimeError(f"callback mapper rc={mapped.returncode}: {mapped.stderr[-500:]}")
        callbacks_data = json.loads(callbacks_path.read_text())
        if set(callbacks_data) != {c["qualified_name"] for c in manifest["commands"]}:
            raise ValueError("callback/manifest mismatch")
        saved = sys.argv
        out, err = io.StringIO(), io.StringIO()
        try:
            sys.argv = [str(scripts / "analyze.py"), str(root), str(callbacks_path), str(raw)]
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                graph = runpy.run_path(str(scripts / "analyze.py"))
        finally:
            sys.argv = saved
        if err.getvalue() or set(graph["cb_fid"]) != set(callbacks_data):
            raise ValueError("incomplete callback graph: " + err.getvalue())
    locations = {
        fid: {
            "file": graph["modules"][graph["func_module"][fid]].relative_to(root).as_posix(),
            "line": node.lineno,
        }
        for fid, node in graph["func_nodes"].items()
    }
    rows = mechanism_rows(manifest["commands"], graph["cb_fid"], graph["edges"], locations)
    refs = regression_references(root, tests, rows)
    for target, row in rows.items():
        row["regression_references"] = refs[target]
    base_reached = {c["command"] for c in rows[LOCK_BASE]["reached_by"]}
    alias_reached = {c["command"] for c in rows[MECHANISMS[1]]["reached_by"]}
    non_read_only = {
        c["qualified_name"] for c in manifest["commands"] if c["safety"] != "READ_ONLY"
    }
    audit = audit_mutation_lock_coverage(root).to_dict()
    inputs = sorted(
        set(root.glob("src/agentic_project_kit/**/*.py"))
        | {
            manifest_path,
            scripts / "map_callbacks.py",
            scripts / "analyze.py",
            Path(__file__).resolve(),
        }
        | {root / p for p in tests}
    )
    return {
        "schema_version": 1,
        "kind": "protection_mechanism_reachability",
        "source_commit": source_commit,
        "manifest_sha": manifest["meta"]["manifest_sha"],
        "counts": {"commands": len(manifest["commands"]), "non_read_only": len(non_read_only)},
        "mechanisms": [rows[t] for t in MECHANISMS],
        "underlying_lock": rows[LOCK_BASE],
        "lock_comparison": {
            "alias_reached": sorted(alias_reached),
            "base_reached": sorted(base_reached),
            "alias_only": sorted(alias_reached - base_reached),
            "base_without_alias": sorted(base_reached - alias_reached),
            "non_read_only_reached_by_either": sorted(
                non_read_only & (base_reached | alias_reached)
            ),
            "non_read_only_without_static_lock_path": sorted(
                non_read_only - (base_reached | alias_reached)
            ),
        },
        "existing_mutation_lock_audit": audit,
        "consumer_check": consumer_check(consumer_root),
        "execution": {
            "callback_mapper_returncode": mapped.returncode,
            "analyzer_completion": "COMPLETE",
            "lock_audit_result_status": audit["result_status"],
            "test_trace": "NOT_RUN",
            "simulation": "NOT_RUN",
        },
        "input_sha256": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in inputs
        },
        "limits": [
            "Static in-process may-reachability, not mandatory execution, coverage or a count of unprotected mutators.",
            "Does not cross subprocess boundaries or distinguish recommendations from executable argv. No execution diagram can be inferred.",
            "BOUNDED is not a mutator classification. tmp/report writes, aliases and primitive delegation need separate adjudication.",
            "Existing LC3 audit uses textual markers and blocks only its declared core runtime-mutator bodies; PASS is not universal lock proof.",
            "Lock reentrancy is same-process (PID/depth). Cross-process inheritance is not supplied by workspace_lock.py.",
            "Direct imported test calls omit helpers/module-attribute calls and do not prove every branch tested.",
        ],
    }


def render_report(r):
    lines = [
        "# K0c — Protection mechanisms and their static reach",
        "",
        f"Product source `{r['source_commit']}`; manifest `{r['manifest_sha']}`.",
        "",
        "Working vocabulary: orchestrators; primitives and diagnostics; protection mechanisms. Kernel still means L0. No Microkernel claim or architecture-contract change.",
        "",
        "| Mechanism | Static command roots | Non-READ_ONLY roots | Direct test references |",
        "|---|---:|---:|---:|",
    ]
    for row in [*r["mechanisms"], r["underlying_lock"]]:
        lines.append(
            f"| {row['function']} | {row['count']} | {row['count'] - row['safety_counts'].get('READ_ONLY', 0)} | {len(row['regression_references'])} |"
        )
    comparison = r["lock_comparison"]
    audit = r["existing_mutation_lock_audit"]
    lines += [
        "",
        "## Interpretation",
        "",
        f"Of {r['counts']['non_read_only']} non-READ_ONLY entries, {len(comparison['non_read_only_reached_by_either'])} statically reach either named lock entry point. {len(comparison['non_read_only_without_static_lock_path'])} have no such in-process witness in this graph. Neither denominator nor complement is a count of mutators or confirmed defects.",
        "",
        f"The semantic alias reaches the same underlying lock via its implementation; {len(comparison['alias_only'])} alias-only roots and {len(comparison['base_without_alias'])} roots using the underlying entry without the alias are recorded. Looking only for workspace_mutation_lock misses legitimate acquire_workspace_lock calls.",
        "",
        f"The unchanged mutation_lock_audit reports {audit['result_status']}: {audit['blocking_finding_count']} blocking and {audit['non_blocking_finding_count']} review-visible findings. Its classification summary and original findings remain in the JSON. The LC3 blocking scope is enforced core runtime mutators, while other categories are explicitly advisory; text-marker acceptance is not proof of runtime execution.",
        "",
        "The lock source uses holder PID and process-local reentrancy depth. It does not grant subprocesses inherited lock ownership. Existing ensure_remote_head regression explicitly prevents an outer lock around a child push. Do not use generic child-inheritance as an explanation without a concrete path.",
        "",
        "The JSON includes every reached command with a shortest potential function witness. The five named mechanisms are a review focus, not an exhaustive safety core. No claim that every mutation necessarily passes a common kernel can be made from these data.",
        "",
        "## Regression mapping",
        "",
        "Direct imported calls in named tests are linked in each mechanism record; test-node names and lines allow review of assertions and fixtures. The underlying-lock row includes family-level tests for the semantic alias. Contract tests in tests/test_mutation_lock_enforcement_contract.py and classifier tests in tests/test_mutation_lock_audit.py and tests/test_mutation_lock_finding_taxonomy.py cover a different, source-marker boundary. Ordinary regression execution is recorded separately in validation.json.",
        "",
        "## Consumer check",
        "",
        f"Owner-local Cockpit source at `{r['consumer_check']['commit']}`: {r['consumer_check']['tracked_source_files_scanned']} tracked runtime/config/test files scanned; dedicated taxonomy-token occurrences: `{json.dumps(r['consumer_check']['dedicated_taxonomy_token_occurrences'], sort_keys=True)}`. Generic manifest references occur in {r['consumer_check']['generic_manifest_reference_files']} files. This is a bounded literal source search, not proof that generic dispatch or external callers never use taxonomy; private source content and local paths are omitted.",
        "",
        "## Remaining boundary",
        "",
        "K0 literal argv and potential_command_closure still mix runner-bound calls, data construction, dry-run options and recommendations. K0c deliberately does not convert those fields into execution edges. G0 remains blocked on this distinction and an explicit terminology decision. W0a evidence-integrity repair is independent.",
        "",
        *["- " + limit for limit in r["limits"]],
        "",
        "Reproduce with scripts/protection_mechanism_audit.py using the pinned product source and an owner-local --consumer-root; historical map_callbacks.py and analyze.py are reused unchanged. No Kit callbacks, simulations, paid agents or remote consumer actions are run.",
        "",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--consumer-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = build_report(root, args.source_commit, args.consumer_root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "reachability.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.out / "README.md").write_text(render_report(report))
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "mechanisms": {r["function"]: r["count"] for r in report["mechanisms"]},
                "underlying_lock": report["underlying_lock"]["count"],
                "lock_audit": report["existing_mutation_lock_audit"]["result_status"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
