#!/usr/bin/env python3
"""Apply the post-PR883 administrative handoff refresh locally.

This helper is repository-backed to avoid large chat-pasted shell blocks. It
performs only administrative status/handoff updates and writes repo-readable
transfer evidence.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

HEAD = "1ec13cb5283d9b796b667526791eaa94a04073ff"
HEAD_SHORT = "1ec13cb"
SUBJECT = "Merge pull request #883 from vfi64/feature/gui-gatekeeper-inventory-helper"
PROMPT_PATH = Path("docs/reports/terminal/v044-successor-chat-handoff-after-pr883.md")
LOG_PATH = Path("docs/reports/terminal/post-pr883-handoff-refresh.log")
STATE_PATH = Path(".agentic/handoff_state.yaml")
STATUS_PATH = Path("docs/STATUS.md")
CURRENT_HANDOFF_PATH = Path("docs/handoff/CURRENT_HANDOFF.md")

STATUS_SECTION = f"""## Post-PR883 GUI Gatekeeper Inventory State

Current verified main HEAD: `{HEAD}` (`{HEAD_SHORT}`).
Commit subject: `{SUBJECT}`.

PR #883 is merged. It added the GUI gatekeeper implementation inventory as a read-only planning/inventory slice, registered the new planning document, recorded the generator and evidence logs, and captured the recurring failure mode that a helper-local PASS is not a slice PASS until the required repository governance gates also pass.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: implement the smallest temporary Python slice-gate command for planning/documentation slices so helper-local PASS can no longer be confused with slice PASS before PR creation, upload, or merge.
"""

CURRENT_HANDOFF_SECTION = f"""## Post-PR883 GUI Gatekeeper Inventory State

Current verified main HEAD is `{HEAD}` (`{HEAD_SHORT}`).
Commit subject: `{SUBJECT}`.

PR #883 is merged. It added the GUI gatekeeper implementation inventory and records the implementation surface for result/log classification, summary validation, upload/evidence preflight, work-order routing, action registry, GUI display, handoff freshness, PR/merge readiness, and shell-adapter migration.

This is an administrative post-PR883 handoff/status refresh only. No GUI product-code change belongs in this slice.

Next safe step after this refresh is merged and verified: implement the smallest temporary Python slice-gate command for planning/documentation slices. The gate must distinguish helper-local PASS from slice PASS and block missing repository governance gates.
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
        "reason": "post-PR883 GUI gatekeeper inventory handoff refresh",
        "source": "PR883 main verification",
    }
    safe = data.setdefault("safe_state", {})
    safe["branch"] = "main"
    safe["commit"] = HEAD
    safe["commit_subject"] = SUBJECT
    safe["semantics"] = "current_main_head"
    prs = safe.setdefault("administrative_refresh_prs", [])
    if 883 not in prs:
        prs.append(883)
    data.setdefault("open_items", {})["next_expected_chat_action"] = (
        "After this post-PR883 handoff refresh is merged and verified, implement "
        "the smallest temporary Python slice-gate command for planning/documentation "
        "slices so helper-local PASS cannot be confused with slice PASS."
    )
    completed = data.setdefault("completed_since_previous_handoff", [])
    entry = (
        "PR #883 added the GUI gatekeeper implementation inventory and recorded "
        "that helper-local PASS is not slice PASS without matching repository governance gates."
    )
    if entry not in completed:
        completed.insert(0, entry)
    blocked = data.setdefault("blocked_until_closeout", [])
    for item in [
        "Gatekeeper product work before post-PR883 handoff refresh is merged and verified",
        "Treating helper-local PASS as slice PASS before repository governance gates pass",
    ]:
        if item not in blocked:
            blocked.append(item)
    data["first_instruction"] = (
        "After this post-PR883 handoff refresh is merged and verified, implement "
        "the smallest temporary Python slice-gate command for planning/documentation "
        "slices; stop first if handoff freshness, evidence, or status drift reappears."
    )
    maintenance = data.setdefault("handoff_maintenance", {})
    maintenance["latest_successor_prompt"] = str(PROMPT_PATH)
    admin = data.setdefault("administrative_evidence_state", {})
    admin["current_head"] = HEAD
    admin["current_head_subject"] = SUBJECT
    admin["head_subject"] = SUBJECT
    admin["allowed_after_safe_state"] = True
    admin["reason"] = "PR883 GUI gatekeeper inventory merged and verified on main"
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
    log: list[str] = ["POST_PR883_HANDOFF_REFRESH", f"target_head={HEAD}"]
    rc, out = run_capture(["git", "rev-parse", "HEAD"])
    current = out.strip()
    log.append(f"current_head={current}")
    rc, out = run_capture(["git", "merge-base", "--is-ancestor", HEAD, "HEAD"])
    head_is_ancestor = rc == 0
    log.append(f"target_head_is_ancestor={head_is_ancestor}")
    if not head_is_ancestor:
        log.append("result=FAIL")
        log.append("error=helper branch must contain post-PR883 main head before patching")
        LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")
        print(LOG_PATH)
        print("result=FAIL")
        return 1
    update_state()
    status_changed = prepend_once(STATUS_PATH, "## Post-PR883 GUI Gatekeeper Inventory State", STATUS_SECTION)
    handoff_changed = prepend_once(CURRENT_HANDOFF_PATH, "## Post-PR883 GUI Gatekeeper Inventory State", CURRENT_HANDOFF_SECTION)
    rc, prompt = run_capture([sys.executable, "-m", "agentic_project_kit.cli", "handoff", "prompt"])
    PROMPT_PATH.write_text(prompt, encoding="utf-8")
    warning_present = "WARNING: this successor handoff prompt may be stale" in prompt
    log.extend([
        f"status_changed={status_changed}",
        f"current_handoff_changed={handoff_changed}",
        f"prompt_path={PROMPT_PATH}",
        f"prompt_returncode={rc}",
        f"freshness_warning_present={warning_present}",
    ])
    result = "PASS" if rc == 0 and not warning_present else "FAIL"
    log.append(f"result={result}")
    LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(LOG_PATH)
    print(f"result={result}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
