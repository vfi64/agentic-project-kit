from __future__ import annotations

from typing import Any

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.handoff_state import active_rules

MANDATORY_SUCCESSOR_CHAT_SOURCES = list(MANDATORY_BOOT_SOURCES) + [
    "docs/TEST_GATES.md",
    "relevant source files and tests for the requested slice",
]

COMMUNICATION_SHORTCUTS = [
    "d/D: local block appears finished; verify evidence before treating it as success",
    "f/F: failure reported; inspect or upload evidence before asking for pasted output",
    "w/W: continue within the current governance and evidence rules",
    "paste-output: manual paste only when repo-backed or local evidence is unavailable or unusable",
    "stop: no further mutation or terminal instructions",
]

FORBIDDEN_PATTERNS = [
    "mutating before reading the mandatory successor-chat sources",
    "treating d as proof of success",
    "asking for pasted output while usable local or remote evidence exists",
    "using shell-only snippets as canonical cross-platform execution",
    "using POSIX tools as correctness dependencies for portable workflows",
    "printing REMOTE_EVIDENCE: PENDING in a final summary",
    "adding handwritten legacy summary footers after the summary renderer",
    "continuing product work after unresolved contract or evidence drift",
]

SUMMARY_VOCABULARY = [
    "WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND",
    "EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED",
    "OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND",
    "REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED",
    "NEXT_CHAT_REPLY: p|f|paste-output|continue|stop",
]


def _bullet_lines(items: list[Any]) -> list[str]:
    return [f"- {item}" for item in items]


def _rule_texts(data: dict[str, Any]) -> list[str]:
    return [f"`{rule.get('id')}`: {rule.get('text')}" for rule in active_rules(data)]


def render_handoff_prompt(data: dict[str, Any]) -> str:
    repo = data.get("repo", {})
    safe_state = data.get("safe_state", {})
    release = data.get("release", {})
    admin_state = data.get("administrative_evidence_state", {})
    if isinstance(data.get("open_items"), dict):
        open_prs = data.get("open_items", {}).get("prs", [])
    else:
        open_prs = []
    lines: list[str] = []
    lines.extend([
        "# Übergabeprompt",
        "",
        "## 1. Arbeitsumgebung",
        "",
        f"Local path: `{repo.get('local_path', '')}`",
        f"Remote: `{repo.get('remote', '')}`",
        f"Default branch: `{repo.get('default_branch', 'main')}`",
    ])
    lines.extend([
        "",
        "## 2. Sicherer Stand",
        "",
        f"Branch: `{safe_state.get('branch', '')}`",
        f"Commit: `{safe_state.get('commit', '')}`",
        f"Subject: {safe_state.get('commit_subject', '')}",
        f"Semantics: `{safe_state.get('semantics', 'last_substantive_work_state')}`",
        f"Working tree expected clean: `{safe_state.get('working_tree_expected_clean', '')}`",
    ])
    if isinstance(admin_state, dict) and admin_state:
        admin_current_head = admin_state.get("current_head", "")
        admin_current_head_subject = admin_state.get("current_head_subject", "")
        admin_allowed_after_safe_state = admin_state.get("allowed_after_safe_state", "")
        admin_reason = admin_state.get("reason", "")
        lines.extend([
            "",
            "## 2a. Administrative Evidence State",
            "",
            "Administrative Evidence Commits nach dem fachlichen Safe-State sind erlaubt, wenn sie nur Logs, Handoff, Summary oder Evidence aktualisieren. Sie ändern den fachlichen Safe-State nicht.",
            "",
            f"Current HEAD at generation time: `{admin_current_head}`",
            f"HEAD subject: {admin_current_head_subject}",
            f"Allowed after safe state: `{admin_allowed_after_safe_state}`",
            f"Reason: {admin_reason}",
        ])
    lines.extend([
        "",
        "## 3. Release- und Produktstand",
        "",
        f"Current version: `{release.get('current_version', '')}`",
        f"Previous version: `{release.get('previous_version', '')}`",
        f"Tag: `{release.get('tag', '')}`",
        f"Zenodo concept DOI: `{release.get('zenodo_concept_doi', '')}`",
        f"Zenodo version DOI: `{release.get('zenodo_version_doi', '')}`",
        f"Post-release check: `{release.get('post_release_check', '')}`",
    ])
    lines.extend([
        "",
        "## 4. Pflichtquellen vor jeder Mutation",
        "",
        "Lies diese Quellen zuerst. Wenn eine Quelle fehlt, widersprüchlich ist oder nicht gelesen werden kann, melde Drift und mutiere nicht außer zur Drift-Reparatur.",
        "",
    ])
    lines.extend(_bullet_lines(MANDATORY_SUCCESSOR_CHAT_SOURCES))
    lines.extend([
        "",
        "## 4a. Bootloader",
        "",
        "Beim Chatwechsel zuerst den Bootloader ausführen: `agentic-kit boot prompt` oder `./ns chat-bootloader`.",
        "",
        "## 5. Kommunikations- und Summary-Regeln",
        "",
        "User-Kürzel sind Kommunikationssignale, keine Evidence:",
        "",
    ])
    lines.extend(_bullet_lines(COMMUNICATION_SHORTCUTS))
    lines.extend(["", "Final-Summary-Vokabular:", ""])
    lines.extend(_bullet_lines(SUMMARY_VOCABULARY))
    lines.extend([
        "",
        "## 6. Aktive Regeln aus handoff_state",
        "",
    ])
    lines.extend(_bullet_lines(_rule_texts(data)))
    lines.extend(["", "## 7. Offene Punkte", ""])
    if open_prs:
        for pr in open_prs:
            lines.append(f"- PR #{pr.get('number')}: {pr.get('title', '')}")
    else:
        lines.append("- Keine offenen PRs im handoff_state.")
    lines.extend(["", "## 8. Abgeschlossen seit letzter Übergabe", ""])
    completed = data.get("completed_since_previous_handoff", [])
    if completed:
        lines.extend(_bullet_lines(completed))
    else:
        lines.append("- Keine Einträge.")
    lines.extend(["", "## 9. Letzte bekannte Fehler- und Driftmuster", ""])
    for item in data.get("recent_failure_patterns", []):
        if isinstance(item, dict):
            lines.append(f"- `{item.get('id')}`: {item.get('prevention') or item.get('description', '')}")
    lines.extend(["", "## 10. Verbotene Muster", ""])
    lines.extend(_bullet_lines(FORBIDDEN_PATTERNS))
    lines.extend(["", "## 11. Nächste erlaubte Aufgaben", ""])
    tasks = data.get("next_allowed_tasks", [])
    if tasks:
        for task in tasks:
            if isinstance(task, dict):
                lines.append(f"- {task.get('priority', '?')}. `{task.get('id', '')}` — {task.get('title', '')}")
    else:
        lines.append("- Keine Aufgaben im handoff_state eingetragen.")
    lines.extend(["", "## 12. Gesperrte Aufgaben", ""])
    blocked = data.get("blocked_until_closeout", [])
    if blocked:
        lines.extend(_bullet_lines(blocked))
    else:
        lines.append("- Keine gesperrten Aufgaben im handoff_state eingetragen.")
    lines.extend([
        "",
        "## 13. Erste Arbeitsanweisung",
        "",
        data.get("first_instruction", ""),
        "",
        "## 14. Arbeitsmodus für den Nachfolge-Chat",
        "",
        "1. Führe zuerst den Bootloader aus.",
        "2. Lies danach alle Pflichtquellen aus Abschnitt 4.",
        "3. Rekonstruiere den aktuellen Stand aus Repo, PR/CI, Logs und Summary, nicht aus Chat-Erinnerung.",
        "4. Prüfe Drift zwischen Regeln, Tests, Summary-Renderer, Status und Handoff.",
        "5. Bei Drift: warnen, keine Produktmutation, Handoff-Prompt oder Drift-Fix anbieten.",
        "6. Arbeite nur in kleinen, testbaren Slices mit ehrlicher Evidence.",
    ])
    return "\n".join(lines).rstrip() + "\n"
