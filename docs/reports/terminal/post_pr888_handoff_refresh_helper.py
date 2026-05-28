#!/usr/bin/env python3
"""Apply the post-PR888 administrative handoff refresh locally."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

HEAD = "508f3dfa2be50d4f369f31e270cc930c24873015"
HEAD_SHORT = "508f3df"
SUBJECT = "Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean"
PROMPT_PATH = Path("docs/reports/terminal/v044-successor-chat-handoff-after-pr888.md")
LOG_PATH = Path("docs/reports/terminal/post-pr888-handoff-refresh.log")
STATE_PATH = Path(".agentic/handoff_state.yaml")
STATUS_PATH = Path("docs/STATUS.md")
CURRENT_HANDOFF_PATH = Path("docs/handoff/CURRENT_HANDOFF.md")

STATUS_SECTION = f"""## Post-PR888 Patch Preflight Slice-Gate State

Current verified main HEAD: `{HEAD}` (`{HEAD_SHORT}`).
Commit subject: `{SUBJECT}`.

PR #888 is merged. It adds the optional `agentic-kit patch-preflight --require-slice-gate planning-doc` path so patch preflight can require deterministic slice-gate evidence and a clean worktree before accepting planning-document preflight readiness.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, using the slice gate and patch preflight before PR creation or merge claims.
"""

CURRENT_HANDOFF_SECTION = f"""## Post-PR888 Patch Preflight Slice-Gate State

Current verified main HEAD is `{HEAD}` (`{HEAD_SHORT}`).
Commit subject: `{SUBJECT}`.

PR #888 is merged. It hardens patch preflight with an optional required slice gate, preventing helper-local PASS from being confused with slice readiness when the worktree is dirty or slice governance gates fail.

This is an administrative post-PR888 handoff/status refresh only. No product-code change belongs in this slice.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, with slice-gate evidence and patch-preflight evidence rather than helper-local PASS claims.
"""


def run_capture(argv: list[str]) -> tuple[int, str]:
    proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def prepend_once(path: Path, heading: str, section: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if heading in text:
        return False
    path.write_text(section.rstrip() + "\n\n" + text, encoding="utf-8")
    return True


def update_state() -> None:
    data = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))
    data["updated"] = {
        "date": "2026-05-28",
        "reason": "post-PR888 patch preflight slice-gate handoff refresh",
        "source": "PR888 main verification",
    }
    safe = data.setdefault("safe_state", {})
    safe["branch"] = "main"
    safe["commit"] = HEAD
    safe["commit_subject"] = SUBJECT
    safe["semantics"] = "current_main_head"
    prs = safe.setdefault("administrative_refresh_prs", [])
    if 888 not in prs:
        prs.append(888)
    data.setdefault("open_items", {})["next_expected_chat_action"] = (
        "After this post-PR888 handoff refresh is merged and verified, continue "
        "with the smallest gatekeeper-hardening slice using slice-gate and patch-preflight evidence."
    )
    completed = data.setdefault("completed_since_previous_handoff", [])
    entry = (
        "PR #888 added optional patch-preflight slice-gate enforcement so planning-document "
        "preflight can require deterministic slice readiness and a clean worktree."
    )
    if entry not in completed:
        completed.insert(0, entry)
    blocked = data.setdefault("blocked_until_closeout", [])
    for item in [
        "Gatekeeper product work before post-PR888 handoff refresh is merged and verified",
        "Treating helper-local PASS as slice PASS without patch-preflight slice-gate evidence",
    ]:
        if item not in blocked:
            blocked.append(item)
    data["first_instruction"] = (
        "After this post-PR888 handoff refresh is merged and verified, continue "
        "with the smallest gatekeeper-hardening slice; stop first if handoff freshness, "
        "evidence, or status drift reappears."
    )
    maintenance = data.setdefault("handoff_maintenance", {})
    maintenance["latest_successor_prompt"] = str(PROMPT_PATH)
    admin = data.setdefault("administrative_evidence_state", {})
    admin["current_head"] = HEAD
    admin["current_head_subject"] = SUBJECT
    admin["head_subject"] = SUBJECT
    admin["allowed_after_safe_state"] = True
    admin["reason"] = "PR888 patch preflight slice-gate enforcement merged and verified on main"
    admin["latest_successor_prompt"] = str(PROMPT_PATH)
    admin["current_subject"] = SUBJECT
    admin["safe_state_semantics"] = "current_main_head"
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    anchors = "# preservation-anchor: use d for log-backed PASS and f for log-backed FAIL\n# preservation-anchor: nested shell/Python quote layers\n"
    if "# preservation-anchor: use d for log-backed PASS" not in rendered:
        rendered += anchors
    STATE_PATH.write_text(rendered, encoding="utf-8")
    yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log: list[str] = ["POST_PR888_HANDOFF_REFRESH", f"target_head={HEAD}"]
    _rc, out = run_capture(["git", "rev-parse", "HEAD"])
    current = out.strip()
    log.append(f"current_head={current}")
    rc, _out = run_capture(["git", "merge-base", "--is-ancestor", HEAD, "HEAD"])
    head_is_ancestor = rc == 0
    log.append(f"target_head_is_ancestor={head_is_ancestor}")
    if not head_is_ancestor:
        log.append("result=FAIL")
        log.append("error=helper branch must contain post-PR888 main head before patching")
        LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")
        print(LOG_PATH)
        print("result=FAIL")
        return 1
    update_state()
    status_changed = prepend_once(STATUS_PATH, "## Post-PR888 Patch Preflight Slice-Gate State", STATUS_SECTION)
    handoff_changed = prepend_once(CURRENT_HANDOFF_PATH, "## Post-PR888 Patch Preflight Slice-Gate State", CURRENT_HANDOFF_SECTION)
    rc, prompt = run_capture([sys.executable, "-m", "agentic_project_kit.cli", "handoff", "prompt"])
    PROMPT_PATH.write_text(prompt, encoding="utf-8")
    warning_present = "WARNING: this successor handoff prompt may be stale" in prompt
    required_markers_present = HEAD in prompt and "PR #888" in prompt and "patch preflight" in prompt
    log.extend([
        f"status_changed={status_changed}",
        f"current_handoff_changed={handoff_changed}",
        f"prompt_path={PROMPT_PATH}",
        f"prompt_returncode={rc}",
        f"freshness_warning_present={warning_present}",
        f"required_markers_present={required_markers_present}",
        "note=freshness_warning_present may be expected before the refresh PR is committed and merged; post-merge main verification must require it to be absent",
    ])
    result = "PASS" if rc == 0 and required_markers_present else "FAIL"
    log.append(f"result={result}")
    LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(LOG_PATH)
    print(f"result={result}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
