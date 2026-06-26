from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.rule_refresh import COMMUNICATION_RULES_OUTPUT, RuleRefreshResult


PENDING_STATE_PATH = Path(".agentic/rule_ack/communication_refresh_pending.json")
ACK_STATE_PATH = Path(".agentic/rule_ack/communication_refresh_ack.json")

REQUIRED_LOADED_SECTIONS = (
    "NO_COPY_TERMINAL_EVIDENCE",
    "CHAT_COMMUNICATION_CONTRACT",
    "PORTABLE_CHAT_EXECUTION_CONTRACT",
    "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT",
)


@dataclass(frozen=True)
class CommunicationRuleCapsule:
    result_status: str
    kind: str
    next_reply: str
    local_path: str
    remote_path: str
    commit: str
    blob_sha: str
    generated_at: str
    must_read_before_continue: bool
    local_only: bool
    remote_readable: bool
    pending_state_path: str | None = None
    next_action: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "result_status": self.result_status,
            "kind": self.kind,
            "next_reply": self.next_reply,
            "local_path": self.local_path,
            "remote_path": self.remote_path,
            "commit": self.commit,
            "blob_sha": self.blob_sha,
            "generated_at": self.generated_at,
            "must_read_before_continue": self.must_read_before_continue,
            "local_only": self.local_only,
            "remote_readable": self.remote_readable,
            "pending_state_path": self.pending_state_path,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class CommunicationContextGateResult:
    result_status: str
    reason: str
    communication_context_fresh: bool
    required_next_reply: str | None
    remote_path: str
    expected_blob_sha: str | None
    generated_at: str | None
    ack_source: str | None = None
    ack_blob_sha: str | None = None
    next_action: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "communication_context_gate",
            "result_status": self.result_status,
            "reason": self.reason,
            "communication_context_fresh": self.communication_context_fresh,
            "required_next_reply": self.required_next_reply,
            "remote_path": self.remote_path,
            "expected_blob_sha": self.expected_blob_sha,
            "generated_at": self.generated_at,
            "ack_source": self.ack_source,
            "ack_blob_sha": self.ack_blob_sha,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class CommunicationRefreshAckResult:
    result_status: str
    reason: str
    ack_path: str
    source: str | None
    blob_sha: str | None
    generated_at: str | None
    loaded_sections: tuple[str, ...]
    rules_loaded: bool
    written_state_path: str | None = None
    next_action: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "communication_rule_refresh_ack_result",
            "result_status": self.result_status,
            "reason": self.reason,
            "ack_path": self.ack_path,
            "source": self.source,
            "blob_sha": self.blob_sha,
            "generated_at": self.generated_at,
            "loaded_sections": list(self.loaded_sections),
            "rules_loaded": self.rules_loaded,
            "written_state_path": self.written_state_path,
            "next_action": self.next_action,
        }


def build_communication_rule_capsule(
    project_root: Path | str,
    result: RuleRefreshResult,
    *,
    publish: bool,
    write_pending: bool = False,
) -> CommunicationRuleCapsule:
    root = Path(project_root).resolve()
    local_path = Path(result.output_path)
    absolute = root / local_path
    data = absolute.read_bytes()
    blob_sha = git_blob_sha(data)
    commit = _git_output(root, "rev-parse", "HEAD") or "UNKNOWN"
    tracked_blob_sha = _git_output(root, "rev-parse", f"HEAD:{local_path.as_posix()}")
    path_dirty = bool(_git_output(root, "status", "--porcelain", "--", local_path.as_posix()))
    remote_readable = bool(publish and tracked_blob_sha == blob_sha and not path_dirty)
    generated_at = _extract_generated_at(absolute)
    pending_path: str | None = None
    next_action = "Rule capsule generated locally."
    if publish:
        next_action = (
            "Send d2 only after the rule capsule is committed and remote-readable."
            if not remote_readable
            else "Send d2; assistant must read the remote rule capsule and ACK it before mutation."
        )
    if write_pending:
        pending = pending_state_from_capsule(
            CommunicationRuleCapsule(
                result_status="PASS",
                kind="communication_rule_refresh",
                next_reply=result.next_reply,
                local_path=result.output_path,
                remote_path=local_path.as_posix(),
                commit=commit,
                blob_sha=blob_sha,
                generated_at=generated_at,
                must_read_before_continue=publish,
                local_only=not publish,
                remote_readable=remote_readable,
                next_action=next_action,
            )
        )
        target = root / PENDING_STATE_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(pending, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pending_path = PENDING_STATE_PATH.as_posix()
    return CommunicationRuleCapsule(
        result_status="PASS",
        kind="communication_rule_refresh",
        next_reply=result.next_reply,
        local_path=result.output_path,
        remote_path=local_path.as_posix(),
        commit=commit,
        blob_sha=blob_sha,
        generated_at=generated_at,
        must_read_before_continue=publish,
        local_only=not publish,
        remote_readable=remote_readable,
        pending_state_path=pending_path,
        next_action=next_action,
    )


def pending_state_from_capsule(capsule: CommunicationRuleCapsule) -> dict[str, object]:
    return {
        "schema_version": 1,
        "required_next_reply": "d2",
        "required_action": "read_remote_communication_rules",
        "remote_path": capsule.remote_path,
        "local_path": capsule.local_path,
        "expected_blob_sha": capsule.blob_sha,
        "generated_at": capsule.generated_at,
        "commit": capsule.commit,
        "blocks_normal_go": True,
        "local_only": capsule.local_only,
        "remote_readable": capsule.remote_readable,
        "next_action": capsule.next_action,
    }


def require_current_communication_context(
    project_root: Path | str = ".",
) -> CommunicationContextGateResult:
    root = Path(project_root).resolve()
    pending = _read_json(root / PENDING_STATE_PATH)
    if not pending:
        ack = _read_json(root / ACK_STATE_PATH)
        return CommunicationContextGateResult(
            result_status="PASS",
            reason="communication_context_current",
            communication_context_fresh=True,
            required_next_reply=None,
            remote_path=str(ack.get("source", COMMUNICATION_RULES_OUTPUT.as_posix())) if ack else COMMUNICATION_RULES_OUTPUT.as_posix(),
            expected_blob_sha=None,
            generated_at=str(ack.get("generated_at")) if ack else None,
            ack_source=str(ack.get("source")) if ack else None,
            ack_blob_sha=str(ack.get("blob_sha")) if ack else None,
            next_action="Communication context is current; mutation may continue.",
        )

    remote_path = str(pending.get("remote_path", COMMUNICATION_RULES_OUTPUT.as_posix()))
    expected_blob_sha = str(pending.get("expected_blob_sha", ""))
    generated_at = str(pending.get("generated_at", ""))
    remote_readable = bool(pending.get("remote_readable", False)) or _pending_capsule_is_remote_readable(
        root,
        remote_path=remote_path,
        expected_blob_sha=expected_blob_sha,
    )
    if not remote_readable:
        return CommunicationContextGateResult(
            result_status="BLOCK",
            reason="communication_rule_refresh_not_remote_readable",
            communication_context_fresh=False,
            required_next_reply="d2",
            remote_path=remote_path,
            expected_blob_sha=expected_blob_sha,
            generated_at=generated_at,
            next_action="Commit and publish the rule capsule before sending d2.",
        )
    return CommunicationContextGateResult(
        result_status="BLOCK",
        reason="communication_rule_refresh_pending",
        communication_context_fresh=False,
        required_next_reply="d2",
        remote_path=remote_path,
        expected_blob_sha=expected_blob_sha,
        generated_at=generated_at,
        next_action="Assistant must read the remote rule capsule and provide RULE_REFRESH_ACK before mutation.",
    )


def _pending_capsule_is_remote_readable(
    root: Path,
    *,
    remote_path: str,
    expected_blob_sha: str,
) -> bool:
    if not remote_path or not expected_blob_sha:
        return False
    if _git_output(root, "status", "--porcelain", "--", remote_path):
        return False
    candidates = ["origin/main"]
    upstream = _git_output(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        candidates.insert(0, upstream)
    for ref in dict.fromkeys(candidates):
        if _git_output(root, "rev-parse", f"{ref}:{remote_path}") == expected_blob_sha:
            return True
    return False


def acknowledge_communication_refresh(
    project_root: Path | str,
    ack_file: Path | str,
) -> CommunicationRefreshAckResult:
    root = Path(project_root).resolve()
    ack_path = Path(ack_file)
    if not ack_path.is_absolute():
        ack_path = root / ack_path
    try:
        ack = parse_ack_text(ack_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return _ack_block(str(ack_path), "ack_file_missing", str(exc))
    pending = _read_json(root / PENDING_STATE_PATH)
    if not pending:
        return _ack_block(str(ack_path), "pending_state_missing", "No communication refresh pending state exists.")

    problems = _ack_problems(ack, pending)
    if problems:
        return _ack_block(str(ack_path), ",".join(problems), "ACK does not match pending communication refresh.", ack=ack)

    state = {
        "schema_version": 1,
        "kind": "communication_rule_refresh_ack",
        "result_status": "PASS",
        "source": ack["source"],
        "remote": ack.get("remote", "main"),
        "blob_sha": ack["blob_sha"],
        "generated_at": ack["generated_at"],
        "loaded_sections": list(ack["loaded_sections"]),
        "rules_loaded": True,
        "acknowledged_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "communication_context_fresh": True,
    }
    target = root / ACK_STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / PENDING_STATE_PATH).unlink(missing_ok=True)
    return CommunicationRefreshAckResult(
        result_status="PASS",
        reason="communication_rule_refresh_acknowledged",
        ack_path=str(ack_path),
        source=str(ack["source"]),
        blob_sha=str(ack["blob_sha"]),
        generated_at=str(ack["generated_at"]),
        loaded_sections=tuple(str(item) for item in ack["loaded_sections"]),
        rules_loaded=True,
        written_state_path=ACK_STATE_PATH.as_posix(),
        next_action="Communication context ACK accepted; mutation may continue.",
    )


def parse_ack_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        data = json.loads(stripped)
    else:
        data: dict[str, Any] = {}
        for line in stripped.splitlines():
            if not line or line == "RULE_REFRESH_ACK" or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    loaded = data.get("loaded_sections", [])
    if isinstance(loaded, str):
        data["loaded_sections"] = [item.strip() for item in loaded.split(",") if item.strip()]
    data["rules_loaded"] = str(data.get("rules_loaded", "")).lower() == "true" or data.get("rules_loaded") is True
    return data


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _ack_problems(ack: dict[str, Any], pending: dict[str, object]) -> list[str]:
    problems: list[str] = []
    if ack.get("source") != pending.get("remote_path"):
        problems.append("source_mismatch")
    if ack.get("blob_sha") != pending.get("expected_blob_sha"):
        problems.append("blob_sha_mismatch")
    if ack.get("generated_at") != pending.get("generated_at"):
        problems.append("generated_at_mismatch")
    if not ack.get("rules_loaded"):
        problems.append("rules_not_loaded")
    loaded = set(str(item) for item in ack.get("loaded_sections", []))
    missing_sections = [section for section in REQUIRED_LOADED_SECTIONS if section not in loaded]
    if missing_sections:
        problems.append("missing_loaded_sections")
    if ack.get("result_status") != "PASS":
        problems.append("result_status_not_pass")
    if ack.get("kind") not in {None, "communication_rule_refresh_ack"}:
        problems.append("kind_mismatch")
    return problems


def _ack_block(
    ack_path: str,
    reason: str,
    next_action: str,
    *,
    ack: dict[str, Any] | None = None,
) -> CommunicationRefreshAckResult:
    ack = ack or {}
    loaded = ack.get("loaded_sections", ())
    if isinstance(loaded, str):
        loaded = tuple(item.strip() for item in loaded.split(",") if item.strip())
    return CommunicationRefreshAckResult(
        result_status="BLOCK",
        reason=reason,
        ack_path=ack_path,
        source=str(ack.get("source")) if ack.get("source") is not None else None,
        blob_sha=str(ack.get("blob_sha")) if ack.get("blob_sha") is not None else None,
        generated_at=str(ack.get("generated_at")) if ack.get("generated_at") is not None else None,
        loaded_sections=tuple(str(item) for item in loaded),
        rules_loaded=bool(ack.get("rules_loaded", False)),
        next_action=next_action,
    )


def _extract_generated_at(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Generated at:"):
            return line.split(":", 1)[1].strip()
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_output(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
