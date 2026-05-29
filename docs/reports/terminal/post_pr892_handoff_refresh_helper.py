from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import yaml

TARGET_HEAD = "64f5c4d49e4012e42170b47e6bcf48bf383e8a94"
TARGET_SHORT = "64f5c4d"
TARGET_SUBJECT = "Merge pull request #892 from vfi64/feature/post-merge-gate-visibility-inventory"
PROMPT_PATH = Path("docs/reports/terminal/v044-successor-chat-handoff-after-pr892.md")
LOG_PATH = Path("docs/reports/terminal/post-pr892-handoff-refresh.log")
STATUS_PATH = Path("docs/STATUS.md")
CURRENT_HANDOFF_PATH = Path("docs/handoff/CURRENT_HANDOFF.md")
HANDOFF_STATE_PATH = Path(".agentic/handoff_state.yaml")


def run(args: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=capture, check=False)


def current_head() -> str:
    return run(["git", "rev-parse", "HEAD"]).stdout.strip()


def current_subject() -> str:
    return run(["git", "log", "-1", "--format=%s"]).stdout.strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing expected text for {label}")
    return text.replace(old, new, 1)


def prepend_section(path: Path, title: str, body: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if title in text:
        return False
    path.write_text(body.rstrip() + "\n\n" + text, encoding="utf-8")
    return True


def update_handoff_state() -> bool:
    text = HANDOFF_STATE_PATH.read_text(encoding="utf-8")
    original = text
    yaml.safe_load(text)

    text = replace_once(text, "reason: post-PR888 handoff refresh", "reason: post-PR892 handoff refresh", "updated.reason")
    text = replace_once(text, "source: PR888 main verification", "source: PR892 main verification", "updated.source")
    text = replace_once(text, "commit: 508f3dfa2be50d4f369f31e270cc930c24873015", f"commit: {TARGET_HEAD}", "safe_state.commit")
    text = replace_once(text, "commit_subject: 'Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean'", f"commit_subject: '{TARGET_SUBJECT}'", "safe_state.commit_subject")
    text = replace_once(text, "  - 888\n", "  - 888\n  - 892\n", "administrative_refresh_prs")
    text = replace_once(
        text,
        "next_expected_chat_action: Continue with post-PR888 stabilized planning-document slice workflow; run the post-merge refresh status gate after future PR merges before deciding whether another administrative refresh is required.",
        "next_expected_chat_action: Continue after PR892 with post-merge gate visibility follow-up work only after the post-merge refresh status gate reports NOOP.",
        "next_expected_chat_action",
    )
    insert = "- 'PR #892 recorded the post-merge handoff refresh status gate visibility inventory so the workflow can move the gate into more visible kit/ns paths.'\n"
    if insert not in text:
        text = replace_once(text, "completed_since_previous_handoff:\n", "completed_since_previous_handoff:\n" + insert, "completed_since_previous_handoff")
    text = replace_once(text, "latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr888.md", "latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr892.md", "handoff_maintenance.latest_successor_prompt")
    text = replace_once(text, "current_head: 508f3dfa2be50d4f369f31e270cc930c24873015", f"current_head: {TARGET_HEAD}", "admin.current_head")
    text = replace_once(text, "current_head_subject: 'Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean'", f"current_head_subject: '{TARGET_SUBJECT}'", "admin.current_head_subject")
    text = replace_once(text, "head_subject: 'Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean'", f"head_subject: '{TARGET_SUBJECT}'", "admin.head_subject")
    text = replace_once(text, "reason: PR888 patch preflight slice-gate requirement merged on main", "reason: PR892 post-merge gate visibility inventory merged on main", "admin.reason")
    text = replace_once(text, "latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr888.md", "latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr892.md", "admin.latest_successor_prompt")
    text = replace_once(text, "current_subject: 'Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean'", f"current_subject: '{TARGET_SUBJECT}'", "admin.current_subject")

    if text != original:
        yaml.safe_load(text)
        HANDOFF_STATE_PATH.write_text(text, encoding="utf-8")
        return True
    return False


def update_status_docs() -> tuple[bool, bool]:
    section = f"""## Post-PR892 Handoff Refresh State

Current verified main HEAD: `{TARGET_HEAD}` (`{TARGET_SHORT}`).
Commit subject: `{TARGET_SUBJECT}`.

PR #892 is merged. It recorded a read-only inventory of where the post-merge handoff refresh status gate is visible.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: move the post-merge refresh status gate into a more visible kit/ns workflow path without broad product-code changes.
"""
    current_handoff_section = f"""## Post-PR892 Handoff Refresh State

Current verified main HEAD is `{TARGET_HEAD}` (`{TARGET_SHORT}`).
Commit subject: `{TARGET_SUBJECT}`.

PR #892 is merged. It recorded a read-only inventory of where the post-merge handoff refresh status gate is visible.

Current verified release remains v0.4.4.
Verified Zenodo version DOI remains `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: move the post-merge refresh status gate into a more visible kit/ns workflow path without broad product-code changes.
"""
    return (
        prepend_section(STATUS_PATH, "## Post-PR892 Handoff Refresh State", section),
        prepend_section(CURRENT_HANDOFF_PATH, "## Post-PR892 Handoff Refresh State", current_handoff_section),
    )


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    head_before = current_head()
    subject_before = current_subject()
    state_changed = update_handoff_state()
    status_changed, current_handoff_changed = update_status_docs()
    prompt = run([".venv/bin/python", "-m", "agentic_project_kit.cli", "handoff", "prompt"])
    PROMPT_PATH.write_text(prompt.stdout, encoding="utf-8")
    warning = "WARNING: this successor handoff prompt may be stale" in prompt.stdout
    markers_ok = all(x in prompt.stdout for x in [TARGET_HEAD, "0.4.4", "10.5281/zenodo.20431326", "PR #892"])
    # On this pre-merge refresh branch, a warning can be expected because the helper commit is newer than TARGET_HEAD.
    branch_has_expected_admin_delta = head_before != TARGET_HEAD
    result = "PASS" if prompt.returncode == 0 and markers_ok and (not warning or branch_has_expected_admin_delta) else "FAIL"
    LOG_PATH.write_text(
        "POST_PR892_HANDOFF_REFRESH\n"
        f"target_head={TARGET_HEAD}\n"
        f"current_head={head_before}\n"
        f"current_subject={subject_before}\n"
        f"branch_has_expected_admin_delta={branch_has_expected_admin_delta}\n"
        f"status_changed={status_changed}\n"
        f"current_handoff_changed={current_handoff_changed}\n"
        f"handoff_state_changed={state_changed}\n"
        f"prompt_path={PROMPT_PATH}\n"
        f"prompt_returncode={prompt.returncode}\n"
        f"freshness_warning_present={warning}\n"
        f"markers_ok={markers_ok}\n"
        f"result={result}\n",
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(f"result={result}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
