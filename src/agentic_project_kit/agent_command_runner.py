"""Repository-backed command runner for agent handoff.

The runner executes exactly one repo-local command file described by
.agentic/commands/current.yaml and .agentic/commands/current.sh.

It is intentionally conservative:
- no command file means no-op failure,
- duplicate command_id is refused,
- shell syntax is checked before execution,
- execution is delegated to terminal_logging.run_logged(),
- reports are written under docs/reports/command_runs/,
- executed command ids are tracked in .agentic/commands/executed.jsonl.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from agentic_project_kit import terminal_logging
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace


def _clean_git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(key, None)
    return env

COMMAND_DIR = Path(".agentic/commands")
CURRENT_YAML = COMMAND_DIR / "current.yaml"
CURRENT_SCRIPT = COMMAND_DIR / "current.sh"
INBOX_DIR = COMMAND_DIR / "inbox"
EXECUTED_JSONL = COMMAND_DIR / "executed.jsonl"
REPORT_DIR = Path(LEGACY_DEFAULTS.command_runs_root)
LATEST_COMMAND_RUN_POINTER = REPORT_DIR / "LATEST_COMMAND_RUN.txt"

ALLOWED_SAFETY_CLASSES = {
    "read-only",
    "local-only",
    "remote-mutation", "local-verification",
}


def normalize_safety_class(value: str) -> str:
    if value == "local-verification":
        return "local-only"
    return value


OUTCOME_PASS_EXECUTED = "PASS_EXECUTED"
OUTCOME_FAIL_NO_COMMAND = "FAIL_NO_COMMAND"
OUTCOME_FAIL_ALREADY_EXECUTED = "FAIL_ALREADY_EXECUTED"
OUTCOME_FAIL_INVALID_COMMAND = "FAIL_INVALID_COMMAND"
OUTCOME_FAIL_SHELL_SYNTAX = "FAIL_SHELL_SYNTAX"
OUTCOME_FAIL_COMMAND = "FAIL_COMMAND"
OUTCOME_FAIL_UPLOAD = "FAIL_UPLOAD"
OUTCOME_FAIL_AMBIGUOUS_COMMANDS = "FAIL_AMBIGUOUS_COMMANDS"
OUTCOME_FAIL_PULL = "FAIL_PULL"
OUTCOME_FAIL_POSTCONDITION = "FAIL_POSTCONDITION"


@dataclasses.dataclass(frozen=True)
class AgentCommand:
    command_id: str
    title: str
    safety_class: str
    expected_branch: str | None = None
    description: str = ""


def _parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid YAML line without colon: {raw}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid YAML line without key: {raw}")
        if (value.startswith("\'") and value.endswith("\'")) or (value.startswith(chr(34)) and value.endswith(chr(34))):
            value = value[1:-1]
        data[key] = value
    return data



def inbox_yaml_files() -> list[Path]:
    if not INBOX_DIR.exists():
        return []
    return sorted(INBOX_DIR.glob("*.yaml"))


def pending_inbox_command_pair() -> tuple[Path, Path]:
    pairs: list[tuple[Path, Path]] = []
    for yaml_path in inbox_yaml_files():
        script_path = yaml_path.with_suffix(".sh")
        if script_path.exists():
            pairs.append((yaml_path, script_path))
    if not pairs:
        raise FileNotFoundError("No complete pending command pair in .agentic/commands/inbox")
    if len(pairs) > 1:
        names = ", ".join(path.name for path, _ in pairs)
        raise RuntimeError("Multiple pending commands: " + names)
    return pairs[0]


def prepare_current_from_inbox() -> tuple[Path, Path]:
    yaml_path, script_path = pending_inbox_command_pair()
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_YAML.write_text(yaml_path.read_text(encoding="utf-8"), encoding="utf-8")
    CURRENT_SCRIPT.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")
    CURRENT_SCRIPT.chmod(0o755)
    yaml_path.unlink()
    script_path.unlink()
    return yaml_path, script_path

def remove_current_files() -> None:
    for item in (CURRENT_YAML, CURRENT_SCRIPT):
        if item.exists():
            item.unlink()

def load_current_command() -> AgentCommand:
    if not CURRENT_YAML.exists() or not CURRENT_SCRIPT.exists():
        raise FileNotFoundError("Missing .agentic/commands/current.yaml or current.sh")
    data = _parse_simple_yaml(CURRENT_YAML)
    required = ("command_id", "title", "safety_class")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError("Missing required command fields: " + ", ".join(missing))
    safety = data["safety_class"]
    safety = normalize_safety_class(safety)
    if safety not in ALLOWED_SAFETY_CLASSES:
        raise ValueError(f"Unsupported safety_class: {safety}")
    return AgentCommand(
        command_id=data["command_id"],
        title=data["title"],
        safety_class=safety,
        expected_branch=data.get("expected_branch") or None,
        description=data.get("description", ""),
    )


def read_executed_ids() -> set[str]:
    if not EXECUTED_JSONL.exists():
        return set()
    ids: set[str] = set()
    for raw in EXECUTED_JSONL.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        command_id = item.get("command_id")
        if isinstance(command_id, str):
            ids.add(command_id)
    return ids


def script_sha256(path: Path = CURRENT_SCRIPT) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_branch() -> str:
    # Do not let inherited Git environment or an enclosing repository leak into
    # temporary test directories. For this runner, the current directory must
    # itself be a Git worktree root or an unknown branch is safer.
    cwd = Path.cwd().resolve()
    if not (cwd / ".git").exists():
        return "unknown"

    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
        check=False,
        env=_clean_git_env(),
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return "unknown"

    top_level = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
        env=_clean_git_env(),
    )
    if top_level.returncode != 0 or Path(top_level.stdout.strip()).resolve() != cwd:
        return "unknown"

    proc = subprocess.run(
        ["git", "branch", "--show-current"],
        text=True,
        capture_output=True,
        check=False,
        env=_clean_git_env(),
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def validate_command(command: AgentCommand) -> tuple[str, str]:
    if command.command_id in read_executed_ids():
        return OUTCOME_FAIL_ALREADY_EXECUTED, command.command_id
    if command.expected_branch and command.expected_branch != current_branch():
        return OUTCOME_FAIL_INVALID_COMMAND, f"Expected branch {command.expected_branch}, got {current_branch()}"
    syntax = subprocess.run(["sh", "-n", CURRENT_SCRIPT.as_posix()], text=True, capture_output=True, check=False)
    if syntax.returncode != 0:
        return OUTCOME_FAIL_SHELL_SYNTAX, syntax.stderr.strip() or syntax.stdout.strip()
    return OUTCOME_PASS_EXECUTED, "valid"


def _report_dir(project_root: Path = Path(".")) -> Path:
    if REPORT_DIR != Path(LEGACY_DEFAULTS.command_runs_root):
        return REPORT_DIR
    return load_workspace(project_root).command_runs_dir()


def _latest_command_run_pointer(project_root: Path = Path(".")) -> Path:
    if LATEST_COMMAND_RUN_POINTER != REPORT_DIR / "LATEST_COMMAND_RUN.txt":
        return LATEST_COMMAND_RUN_POINTER
    return load_workspace(project_root).latest_command_run_pointer()


def report_path(command_id: str, project_root: Path = Path(".")) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in command_id)
    return _report_dir(project_root) / f"{safe}.md"


def write_report(command: AgentCommand, outcome: str, exit_code: int, log_path: Path | None, detail: str = "") -> Path:
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_path(command.command_id)
    lines = [
        f"# Agent command run: {command.command_id}",
        "",
        f"- Title: {command.title}",
        f"- Safety class: {command.safety_class}",
        f"- Outcome: {outcome}",
        f"- Exit code: {exit_code}",
        f"- Branch: {current_branch()}",
        f"- Script SHA256: {script_sha256()}",
    ]
    if log_path is not None:
        lines.append(f"- Terminal log: {log_path.as_posix()}")
    if detail:
        lines.extend(["", "## Detail", "", detail])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest = _latest_command_run_pointer()
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(path.as_posix() + "\n", encoding="utf-8")
    return path


def append_executed(command: AgentCommand, outcome: str, exit_code: int) -> None:
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "command_id": command.command_id,
        "outcome": outcome,
        "exit_code": exit_code,
        "script_sha256": script_sha256(),
        "timestamp_utc": _dt.datetime.now(_dt.UTC).isoformat(),
    }
    with EXECUTED_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")



def _git_path_is_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def stage_commit_push(paths: list[Path], message: str, *, required_branch: str = "", allow_main: bool = False) -> int:
    branch = current_branch()
    if required_branch and branch != required_branch:
        print(f"FAIL_BRANCH_MISMATCH actual={branch} required={required_branch}")
        return 1
    if branch == "main" and not allow_main:
        print("FAIL_MAIN_MUTATION_NOT_ALLOWED")
        return 1
    if branch in {"", "unknown"}:
        print("FAIL_NO_CURRENT_BRANCH")
        return 1
    add_paths = [path for path in paths if path.exists() or _git_path_is_tracked(path)]
    if add_paths:
        subprocess.run(["git", "add", *[path.as_posix() for path in add_paths]], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    push = subprocess.run(["git", "push", "-u", "origin", branch], check=False)
    return push.returncode

def logged_script_has_fail_result_marker(log_path: Path | None) -> bool:
    if log_path is None or not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="replace")
    fail_pos = text.rfind("### RESULT: FAIL ###")
    pass_pos = text.rfind("### RESULT: PASS ###")
    return fail_pos != -1 and fail_pos > pass_pos


def agent_run(extra_upload_paths: list[Path] | None = None) -> int:
    extra_upload_paths = list(extra_upload_paths or [])
    try:
        command = load_current_command()
    except (FileNotFoundError, ValueError) as exc:
        print(OUTCOME_FAIL_NO_COMMAND if isinstance(exc, FileNotFoundError) else OUTCOME_FAIL_INVALID_COMMAND)
        print(str(exc))
        return 1

    validation_outcome, validation_detail = validate_command(command)
    if validation_outcome == OUTCOME_FAIL_ALREADY_EXECUTED:
        print(validation_outcome)
        print(validation_detail)
        write_report(command, validation_outcome, 0, None, validation_detail)
        return 0
    if validation_outcome != OUTCOME_PASS_EXECUTED:
        print(validation_outcome)
        print(validation_detail)
        write_report(command, validation_outcome, 1, None, validation_detail)
        return 1

    print(f"COMMAND_ID={command.command_id}")
    print(f"TITLE={command.title}")
    print(f"SAFETY_CLASS={command.safety_class}")

    exit_code = terminal_logging.run_logged(command.command_id, ["sh", CURRENT_SCRIPT.as_posix()])
    log_path = terminal_logging.read_latest_pointer()
    fail_marker = logged_script_has_fail_result_marker(log_path)
    outcome = OUTCOME_PASS_EXECUTED if exit_code == 0 and not fail_marker else OUTCOME_FAIL_COMMAND
    if fail_marker and exit_code == 0:
        exit_code = 1

    report = write_report(command, outcome, exit_code, log_path)
    append_executed(command, outcome, exit_code)

    upload_paths = [report, _latest_command_run_pointer(), EXECUTED_JSONL, *extra_upload_paths]
    if log_path is not None:
        upload_paths.append(log_path)
    upload_paths.append(terminal_logging.LATEST_POINTER)

    pushed = stage_commit_push(
        upload_paths,
        f"Record agent command run {command.command_id}",
        required_branch=command.expected_branch or "",
    )
    if pushed != 0:
        print(OUTCOME_FAIL_UPLOAD)
        return pushed

    print(outcome)
    return 0 if outcome == OUTCOME_PASS_EXECUTED else exit_code or 1




def print_agent_next_footer(outcome: str, reply: str, reason: str = "") -> None:
    print("")
    print(f"### AGENT-NEXT RESULT: {outcome} ###")
    print(f"reply={reply}")
    if reply == "p":
        print("### NEXT CHAT REPLY: PASS -> p ###")
    elif reply == "f":
        print("### NEXT CHAT REPLY: FAIL -> f ###")
    elif reply == "paste-output":
        print("### NEXT CHAT REPLY: HARD-FAIL -> paste output ###")
    else:
        print("### NEXT CHAT REPLY: NO-COMMAND -> ask agent to queue command ###")
    if reason:
        print(f"reason={reason}")
    latest_command_run = _latest_command_run_pointer()
    if latest_command_run.exists():
        print(f"latest_command_run={latest_command_run.as_posix()}")
    print("### END AGENT-NEXT RESULT ###")
    if outcome == "PASS":
        work_result = "PASS"
        evidence_result = "PASS"
        overall_result = "PASS"
    elif outcome == "FAIL":
        work_result = "FAIL"
        evidence_result = "PASS"
        overall_result = "FAIL"
    elif outcome == "NO-COMMAND":
        work_result = "NO-COMMAND"
        evidence_result = "PASS"
        overall_result = "NO-COMMAND"
    else:
        work_result = "HARD-FAIL"
        evidence_result = "FAIL"
        overall_result = "HARD-FAIL"
    print("================================================================")
    print("SUMMARY")
    print(f"WORK RESULT: {work_result}")
    print(f"EVIDENCE RESULT: {evidence_result}")
    print(f"OVERALL RESULT: {overall_result}")
    if reason:
        print(f"REASON: {reason}")
    print(f"NEXT CHAT REPLY: {reply}")
    print("================================================================")

def git_porcelain_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True, check=False)
    paths: list[str] = []
    for raw in proc.stdout.splitlines():
        if raw.strip():
            paths.append(raw[3:])
    return paths


def agent_next_postcondition_failures() -> list[str]:
    failures: list[str] = []
    for item in (CURRENT_YAML, CURRENT_SCRIPT):
        if item.exists():
            failures.append("active current file remains: " + item.as_posix())
    complete_pairs: list[str] = []
    if INBOX_DIR.exists():
        for yaml_path in inbox_yaml_files():
            if yaml_path.with_suffix(".sh").exists():
                complete_pairs.append(yaml_path.name)
    if complete_pairs:
        failures.append("complete inbox command remains: " + ", ".join(complete_pairs))
    unstaged_deletions = [path for path in git_porcelain_paths() if path.startswith(".agentic/commands/inbox/")]
    if unstaged_deletions:
        failures.append("inbox path still dirty after run: " + ", ".join(unstaged_deletions))
    return failures


def git_pull_ff_only() -> int:
    branch = current_branch()
    return subprocess.run(["git", "pull", "--ff-only", "origin", branch], check=False).returncode


def agent_next() -> int:
    pulled = git_pull_ff_only()
    if pulled != 0:
        print(OUTCOME_FAIL_PULL)
        print_agent_next_footer("HARD-FAIL", "paste-output", OUTCOME_FAIL_PULL)
        return pulled
    try:
        consumed_paths = list(prepare_current_from_inbox())
    except FileNotFoundError as exc:
        print(OUTCOME_FAIL_NO_COMMAND)
        print(str(exc))
        print_agent_next_footer("NO-COMMAND", "ask-agent-to-queue-command", str(exc))
        return 1
    except RuntimeError as exc:
        print(OUTCOME_FAIL_AMBIGUOUS_COMMANDS)
        print(str(exc))
        print_agent_next_footer("HARD-FAIL", "paste-output", OUTCOME_FAIL_AMBIGUOUS_COMMANDS)
        return 1
    try:
        result = agent_run(extra_upload_paths=consumed_paths)
    finally:
        remove_current_files()
    failures = agent_next_postcondition_failures()
    if failures:
        print(OUTCOME_FAIL_POSTCONDITION)
        for item in failures:
            print(item)
        print_agent_next_footer("HARD-FAIL", "paste-output", OUTCOME_FAIL_POSTCONDITION)
        return 1
    if result == 0:
        print_agent_next_footer("PASS", "p")
    else:
        print_agent_next_footer("FAIL", "f")
    return result

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "next":
        return agent_next()
    return agent_run()


if __name__ == "__main__":
    raise SystemExit(main())
