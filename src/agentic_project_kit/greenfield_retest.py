"""Executable external retests (KIT-GF-070).

Every catalog retest gets an execution class derived from the installed Kit's command manifest:

- ``local``: every route declares only ``none``, ``fetch`` or ``push`` effects, which a disposable
  workspace with a local bare origin satisfies;
- ``owner_remote``: a route needs GitHub, PyPI or another network service (pull requests, merges,
  CI, releases, remote deletes, network reads);
- ``kit_release``: the retest needs a Kit release run.

A ``local`` retest may carry a machine contract (``external_retest.machine``): a fixture the Kit
builds and steps with exact expectations. ``agentic-kit greenfield retest`` runs it with the
installed Kit in a temporary directory and reports PASS or FAIL per finding. A retest without a
contract reports NO_MACHINE_CONTRACT and a non-local one NOT_RUN_LOCALLY: neither is a PASS, so a
consumer can never reach VERIFIED_FIXED from a run that proved nothing.

The runner never reads or writes the consumer workspace; Git runs with an isolated configuration.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

EXECUTION_CLASSES = ("local", "owner_remote", "kit_release")
LOCAL_EFFECTS = frozenset({"none", "fetch", "push"})
MANIFEST_FIXTURES = frozenset({
    "external_manifest", "external_owned_runtime", "external_owned_interpreter", "external_release",
})
OWNED_FIXTURES = MANIFEST_FIXTURES - {"external_manifest"}
FIXTURES = ("git_repository", *sorted(MANIFEST_FIXTURES))
STEP_KINDS = ("run", "write", "append", "replace", "assert")
EXPECT_KEYS = frozenset(
    {"returncode", "returncode_nonzero", "json", "json_contains", "stdout_contains", "stdout_equals"}
)
RESULTS = ("PASS", "FAIL", "NO_MACHINE_CONTRACT", "NOT_RUN_LOCALLY")
STEP_TIMEOUT_SECONDS = 600
_PLACEHOLDER = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
# Built-in variables every contract may use: the interpreter and the version of the installed Kit
# that runs the retest (kit.interpreter, version pins in CI templates) and, with ``origin: true``,
# the local bare origin. fixture_head is the baseline commit (empty in an unborn Git fixture).
BUILTIN_VARIABLES = ("kit_python", "kit_version", "fixture_head")
_PATH_TOKEN = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


@lru_cache(maxsize=1)
def _packaged_routes() -> dict[tuple[str, ...], dict[str, Any]]:
    from agentic_project_kit.command_manifest import load_packaged_manifest

    return {tuple(c["path"]): c for c in load_packaged_manifest()["commands"]}


def resolve_route(argv: list[str], routes: dict[tuple[str, ...], dict[str, Any]] | None = None):
    """Return (manifest entry, remaining tokens) for an ``agentic-kit`` argv, or (None, argv)."""
    routes = _packaged_routes() if routes is None else routes
    if not argv or argv[0] != "agentic-kit":
        return None, argv
    tokens = argv[1:]
    for size in range(len(tokens), 0, -1):
        entry = routes.get(tuple(tokens[:size]))
        if entry:
            return entry, tokens[size:]
    return None, tokens


def _declared_options(entry: dict[str, Any]) -> set[str]:
    return {
        str(o)
        for p in entry.get("params") or []
        for o in [*(p.get("opts") or []), *(p.get("secondary_opts") or [])]
        if str(o).startswith("-")
    }


def check_route(command: str | list[str], routes=None) -> dict[str, Any]:
    """Raise ValueError unless the command names a manifest route with declared options only."""
    argv = shlex.split(command) if isinstance(command, str) else list(command)
    entry, rest = resolve_route(argv, routes)
    if entry is None:
        raise ValueError(f"retest names no route of the installed Kit: {' '.join(argv)}")
    options = _declared_options(entry)
    for token in rest:
        if token.startswith("-") and token.split("=", 1)[0] not in options:
            raise ValueError(f"retest uses an undeclared option {token}: {' '.join(argv)}")
    return entry


def execution_class(retest: dict[str, Any], routes=None) -> tuple[str, list[str]]:
    effects: set[str] = set()
    for command in retest["commands"]:
        effects.update(check_route(command, routes).get("remote_effects") or ["none"])
    if retest["workspace_kind"] == "kit_release":
        return "kit_release", sorted(effects)
    return ("local" if effects <= LOCAL_EFFECTS else "owner_remote"), sorted(effects)


def _placeholders(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(_PLACEHOLDER.findall(value))
    if isinstance(value, list):
        return set().union(*(_placeholders(v) for v in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(_placeholders(v) for v in value.values())) if value else set()
    return set()


def _relative(path: Any) -> str:
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError(f"machine contract path must be relative and confined: {path!r}")
    return path


def validate_machine(finding_id: str, retest: dict[str, Any], routes=None) -> None:
    machine = retest.get("machine")
    if machine is None:
        return
    if retest.get("execution_class", execution_class(retest, routes)[0]) != "local":
        raise ValueError(f"{finding_id}: only a local retest may carry a machine contract")
    if not isinstance(machine, dict) or set(machine) - {"fixture", "origin", "steps", "covers"}:
        raise ValueError(f"{finding_id}: invalid machine contract keys")
    if machine.get("fixture") not in FIXTURES or not isinstance(machine.get("origin", False), bool):
        raise ValueError(f"{finding_id}: unknown fixture")
    if machine["fixture"] == "external_release" and not machine.get("origin"):
        raise ValueError(f"{finding_id}: external_release requires a local origin")
    if not isinstance(machine.get("covers"), str) or not machine["covers"].strip():
        raise ValueError(f"{finding_id}: a machine contract states what it covers")
    steps = machine.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{finding_id}: a machine contract needs steps")
    known = {*BUILTIN_VARIABLES, *(("origin",) if machine.get("origin") else ())}
    ran_retest_route = False
    for step in steps:
        if not isinstance(step, dict) or len(set(step) & set(STEP_KINDS)) != 1:
            raise ValueError(f"{finding_id}: every step has exactly one kind")
        if set(step) - {*STEP_KINDS, "expect", "capture"}:
            raise ValueError(f"{finding_id}: unknown step keys")
        unknown = _placeholders(step) - known
        if unknown:
            raise ValueError(f"{finding_id}: unbound placeholders {sorted(unknown)}")
        if "run" in step:
            argv = step["run"]
            if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
                raise ValueError(f"{finding_id}: run takes an argv list")
            if argv[0] == "agentic-kit":
                entry = check_route(argv, routes)
                if tuple(entry["path"]) == ("greenfield", "retest") and (
                    "--all" in argv or finding_id in argv
                ):
                    raise ValueError(f"{finding_id}: a contract may not retest itself or all findings")
                if set(entry.get("remote_effects") or ["none"]) - LOCAL_EFFECTS:
                    raise ValueError(f"{finding_id}: a step needs a remote service: {' '.join(argv)}")
                ran_retest_route |= any(
                    check_route(c, routes)["path"] == entry["path"] for c in retest["commands"]
                )
            elif argv[0] != "git":
                raise ValueError(f"{finding_id}: steps run only agentic-kit or git")
            expect = step.get("expect", {})
            if not isinstance(expect, dict) or set(expect) - EXPECT_KEYS:
                raise ValueError(f"{finding_id}: unknown expectation")
            capture = step.get("capture", {})
            if not isinstance(capture, dict):
                raise ValueError(f"{finding_id}: capture maps names to JSON paths")
            for name in capture:
                if not re.fullmatch(r"[a-z_][a-z0-9_]*", name) or name in {"origin", *BUILTIN_VARIABLES}:
                    raise ValueError(f"{finding_id}: invalid capture name {name!r}")
            known |= set(capture)
        elif "assert" in step:
            spec = step["assert"]
            if not isinstance(spec, dict) or set(spec) - {"exists", "absent"} or not spec:
                raise ValueError(f"{finding_id}: assert takes exists and absent path lists")
            for paths in spec.values():
                for path in paths:
                    _relative(path)
        else:
            kind = next(k for k in STEP_KINDS if k in step)
            spec = step[kind]
            fields = {"write": {"path", "text"}, "append": {"path", "text"}, "replace": {"path", "old", "new"}}[kind]
            if not isinstance(spec, dict) or set(spec) != fields:
                raise ValueError(f"{finding_id}: {kind} takes {sorted(fields)}")
            _relative(spec["path"])
        if ("expect" in step or "capture" in step) and "run" not in step:
            raise ValueError(f"{finding_id}: only run steps carry expectations")
    if not ran_retest_route:
        raise ValueError(f"{finding_id}: the contract must run a route of the retest commands")


# --- running --------------------------------------------------------------------------------


def json_path(document: Any, path: str) -> Any:
    """Resolve ``a.b[0].c``; raise KeyError when a part is missing."""
    value = document
    for name, index in _PATH_TOKEN.findall(path):
        if name:
            if not isinstance(value, dict) or name not in value:
                raise KeyError(path)
            value = value[name]
        else:
            position = int(index)
            if not isinstance(value, list) or position >= len(value):
                raise KeyError(path)
            value = value[position]
    return value


def _substitute(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda m: variables[m.group(1)], value)
    if isinstance(value, list):
        return [_substitute(v, variables) for v in value]
    if isinstance(value, dict):
        return {k: _substitute(v, variables) for k, v in value.items()}
    return value


def _environment(home: Path) -> dict[str, str]:
    config = home / "gitconfig"
    config.write_text(
        "[user]\n\tname = Agentic Kit Retest\n\temail = retest@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n",
        encoding="utf-8",
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "AGENTIC_KIT_RETEST_PYTHON"}
    env.update({"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
    # The OS temp root is the run's own directory, so a contract never sees or touches other
    # programs' temporary files (KIT-GF-028).
    temp = home / "os-tmp"
    temp.mkdir(exist_ok=True)
    env.update({"TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp)})
    return env


def _argv(argv: list[str], interpreter: str = sys.executable) -> list[str]:
    if argv[0] == "agentic-kit":
        return [interpreter, "-m", "agentic_project_kit.cli", *argv[1:]]
    return argv


def _run(argv: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            _argv(argv, env.get("AGENTIC_KIT_RETEST_PYTHON", sys.executable)),
            cwd=cwd, env=env, capture_output=True, text=True, timeout=STEP_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(argv, 124, "", f"timed out after {STEP_TIMEOUT_SECONDS}s")
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 127, "", f"could not be started: {exc}")


def _check(expect: dict[str, Any], completed: subprocess.CompletedProcess) -> list[str]:
    failures = []
    if "returncode" in expect and completed.returncode != expect["returncode"]:
        failures.append(f"returncode {completed.returncode} != {expect['returncode']}")
    if expect.get("returncode_nonzero") and completed.returncode == 0:
        failures.append("returncode 0, expected a failure")
    if "stdout_contains" in expect and expect["stdout_contains"] not in completed.stdout:
        failures.append(f"stdout lacks {expect['stdout_contains']!r}")
    if "stdout_equals" in expect and completed.stdout.strip() != expect["stdout_equals"]:
        failures.append(f"stdout {completed.stdout.strip()[:200]!r} != {expect['stdout_equals']!r}")
    if "json" in expect or "json_contains" in expect:
        try:
            document = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return [*failures, "stdout is not one JSON document"]
        for path, wanted in expect.get("json", {}).items():
            try:
                actual = json_path(document, path)
            except KeyError:
                failures.append(f"{path} missing")
                continue
            if actual != wanted:
                failures.append(f"{path}={json.dumps(actual)[:200]} != {json.dumps(wanted)}")
        for path, wanted in expect.get("json_contains", {}).items():
            try:
                actual = json_path(document, path)
            except KeyError:
                failures.append(f"{path} missing")
                continue
            if not isinstance(actual, (list, str)) or wanted not in actual:
                failures.append(f"{path} does not contain {json.dumps(wanted)}")
    return failures


def _fixture(machine: dict[str, Any], base: Path, env: dict[str, str]) -> tuple[Path, dict[str, str], list[str]]:
    root = base / "workspace"
    root.mkdir()
    from agentic_project_kit import __version__

    variables: dict[str, str] = {"kit_python": sys.executable, "kit_version": __version__}
    setup = [["git", "init", "-b", "main"]]
    if machine["fixture"] in MANIFEST_FIXTURES:
        setup += [
            ["agentic-kit", "workspace", "init", "--root", ".", "--name", "external", "--execute", "--json"],
            ["agentic-kit", "commands", "sync-entrypoints", "--execute", "--json"],
            ["git", "add", "-A"],
            ["git", "commit", "-m", "baseline"],
        ]
    if machine.get("origin"):
        # Generic setup clones the baseline and sets its tracking ref locally.
        # The release fixture later seeds this local origin from its prepared commits.
        origin = base / "origin.git"
        variables["origin"] = str(origin)
        if machine["fixture"] in MANIFEST_FIXTURES:
            setup += [
                ["git", "clone", "--bare", "--quiet", ".", str(origin)],
                ["git", "remote", "add", "origin", str(origin)],
                ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
                ["git", "branch", "--set-upstream-to=origin/main", "main"],
            ]
        else:
            setup += [["git", "init", "--bare", "-b", "main", str(origin)], ["git", "remote", "add", "origin", str(origin)]]
    for argv in setup:
        completed = _run(argv, root, env)
        if completed.returncode != 0:
            return root, variables, [f"fixture step {' '.join(argv)} failed: {(completed.stderr or completed.stdout)[-400:]}"]
    head = _run(["git", "rev-parse", "HEAD"], root, env)
    variables["fixture_head"] = head.stdout.strip() if head.returncode == 0 else ""
    if machine["fixture"] in OWNED_FIXTURES:
        from agentic_project_kit.greenfield_retest_runtime import prepare_owned_runtime

        try:
            python = prepare_owned_runtime(base, env, console=machine["fixture"] != "external_owned_interpreter")
            variables["kit_python"] = str(python)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            return root, variables, [f"owned runtime fixture failed: {exc}"]
    if machine["fixture"] == "external_release":
        from agentic_project_kit.greenfield_retest_release import prepare_release_fixture

        failures = prepare_release_fixture(root, variables, env, _run)
        if failures:
            return root, variables, failures
    return root, variables, []


def run_machine(machine: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agentic-kit-retest-") as directory:
        base = Path(directory).resolve()
        env = _environment(base)
        root, variables, failures = _fixture(machine, base, env)
        steps: list[dict[str, Any]] = []
        if failures:
            return {"result": "FAIL", "failures": failures, "steps": steps}
        for index, raw in enumerate(machine["steps"]):
            step = _substitute({k: v for k, v in raw.items() if k != "capture"}, variables)
            record: dict[str, Any] = {"index": index}
            failed: list[str] = []
            if "run" in step:
                record["argv"] = raw["run"]
                completed = _run(step["run"], root, env)
                record["returncode"] = completed.returncode
                failed = _check(step.get("expect", {}), completed)
                if not failed and raw.get("capture"):
                    try:
                        document = json.loads(completed.stdout)
                        for name, path in raw["capture"].items():
                            variables[name] = str(json_path(document, path))
                    except (json.JSONDecodeError, KeyError) as exc:
                        failed.append(f"capture failed: {exc}")
                if failed:
                    record["stderr_tail"] = completed.stderr[-400:]
                    record["stdout_tail"] = completed.stdout[-1600:]
            elif "assert" in step:
                record["assert"] = raw["assert"]
                failed += [f"{p} missing" for p in step["assert"].get("exists", []) if not (root / p).exists()]
                failed += [f"{p} present" for p in step["assert"].get("absent", []) if (root / p).exists()]
            else:
                kind = next(k for k in ("write", "append", "replace") if k in step)
                spec = step[kind]
                target = root / spec["path"]
                record[kind] = raw[kind]["path"]
                if kind == "write":
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(spec["text"], encoding="utf-8")
                elif not target.is_file():
                    failed.append(f"{spec['path']} missing")
                elif kind == "append":
                    with target.open("a", encoding="utf-8") as stream:
                        stream.write(spec["text"])
                else:
                    text = target.read_text(encoding="utf-8")
                    if text.count(spec["old"]) != 1:
                        failed.append(f"{spec['path']}: replace text occurs {text.count(spec['old'])} times")
                    else:
                        target.write_text(text.replace(spec["old"], spec["new"]), encoding="utf-8")
            record["failures"] = failed
            steps.append(record)
            if failed:
                return {"result": "FAIL", "failures": failed, "steps": steps}
        return {"result": "PASS", "failures": [], "steps": steps}


def retest(finding_ids: list[str] | None = None, *, run_all: bool = False) -> dict[str, Any]:
    from agentic_project_kit import __version__
    import agentic_project_kit
    from agentic_project_kit.greenfield_status import read_status

    if bool(finding_ids) == run_all:
        raise ValueError("name findings with --id or choose --all")
    status = read_status()
    by_id = {f["id"]: f for f in status["findings"]}
    unknown = [i for i in finding_ids or [] if i not in by_id]
    if unknown:
        raise ValueError(f"unknown finding id: {', '.join(unknown)}")
    selected = sorted(by_id) if run_all else list(dict.fromkeys(finding_ids or []))
    results = []
    for finding_id in selected:
        finding = by_id[finding_id]
        retest_contract = finding["external_retest"]
        record = {
            "id": finding_id,
            "kit_state": finding["kit_state"],
            "fixed_in": finding["fixed_in"],
            "execution_class": retest_contract["execution_class"],
            "remote_effects": retest_contract["remote_effects"],
        }
        machine = retest_contract.get("machine")
        if retest_contract["execution_class"] != "local":
            record.update(result="NOT_RUN_LOCALLY", commands=retest_contract["commands"])
        elif machine is None:
            record.update(result="NO_MACHINE_CONTRACT", commands=retest_contract["commands"])
        else:
            record.update(run_machine(machine), covers=machine["covers"])
        results.append(record)
    counts = {r: sum(x["result"] == r for x in results) for r in RESULTS}
    if counts["FAIL"]:
        overall = "FAIL"
    elif counts["PASS"] == len(results):
        overall = "PASS"
    else:
        overall = "INCOMPLETE"
    return {
        "schema_version": 1,
        "kind": "external_findings_retest",
        "result_status": overall,
        "authority": "Kit retest of the installed Kit; VERIFIED_FIXED belongs to the consuming workspace",
        "kit_version": __version__,
        "executed_from": str(Path(agentic_project_kit.__file__).resolve().parent),
        "catalog_sha256": status["source_sha256"],
        "counts": counts,
        "results": results,
    }


def exit_code(result: dict[str, Any]) -> int:
    return {"PASS": 0, "FAIL": 1, "INCOMPLETE": 3}[result["result_status"]]
