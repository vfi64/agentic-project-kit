#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'docs/gui-transfer-basic-mvp-plan-update'
TMP_DIFF = Path('/tmp/gui-transfer-basic-mvp-plan-update.diff')
PLAN = Path('docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md')

PLAN_SECTION = r'''

Post-PR934 basic GUI transfer MVP update
Status: planned
Decision status: accepted direction
Scope: planning only
Baseline: after the rn/rnc transfer path and the rnc no-closeout status are merged
Purpose
This update narrows the next GUI gatekeeper work toward a didactic Basic-MVP that removes normal shell copy-and-paste from the LLM/local workflow. The goal is not more unrestricted GUI power. The goal is a small deterministic control surface over repository-backed state, rule capsules, typed work orders, evidence, CI, and handoff readiness.

Problem statement
The workflow is functional but still too fragile because it has too many manual transfer points. Shell copy-and-paste can break through indentation, raw separator lines, PATH drift, zsh continuation prompts, and the wrong Python environment. The LLM still needs periodic repo-backed rule refreshes. Local logs and evidence files can block branch switches when they are not committed or cleaned through a safe path. GitHub, CI, command files, and local gatekeeper facts are not yet reduced into one canonical local state snapshot for the GUI.

Target outcome
The Basic GUI should let the user open the GUI, read one large state indicator, press only one of a few allowed buttons, and let repository-backed transfer files carry the state, rule capsule, next action, and evidence paths to the LLM. Copy-and-paste remains a recovery-only fallback after hard failures such as terminal loss, Python startup failure, filesystem failure, network failure before push, or explicitly broken logging.

Visible states
The Basic GUI exposes only four primary states:
* READY: safe progress is possible.
* WAIT: nothing is broken, but the system is waiting for CI, GitHub, a remote update, or a command file.
* BLOCKED: progress would be risky because a deterministic blocker exists.
* FAILED: an action failed and must be diagnosed or recovered.

Internal state model
The GUI must not infer safety from button labels or chat text. It must read a canonical machine-readable snapshot produced by agentic-kit. The snapshot should include at least:
* schema_version,
* transfer_id,
* sequence,
* created_at,
* source,
* repository identity,
* base_commit,
* primary state: READY, WAIT, BLOCKED, or FAILED,
* reasons,
* next_action,
* capabilities,
* last known good anchor,
* last result summary,
* rule capsule metadata.

Capabilities, not state names alone, control buttons. Examples include refresh_rules, fetch_remote, run_next_command, closeout_last_run, upload_evidence, diagnose, check_ci, prepare_handoff, cleanup_local_logs, and merge_pr. Every button click must re-run the same gatekeeper check before it mutates state, because a stale GUI view must not authorize work.

Rule capsule requirement
Every local-to-LLM transfer artifact should carry or reference a current rule capsule. The capsule should be generated from repository-backed communication, bootstrap, portable execution, and handoff rules. It must at least encode that local work uses the repository virtual environment, Python scripts or agentic-kit commands are preferred over shell blocks, remote repo transfer is preferred over manual copy-and-paste, copy-and-paste is fallback-only, d/f/g are the preferred dialog signals with w as legacy, and failed gates must not be followed by mutation.

Canonical transfer state
The preferred long-term path is a single canonical transfer state, for example `.agentic/transfer/state.json`. If that directory does not yet exist, the first implementation may introduce it in a small PR. State changes must be committed as Git snapshots, not treated as individually atomic GitHub file edits. Each transfer must include a base_commit and transfer_id. Before push, the local tool must check that origin/main is still the expected base or abort and recompute. Writes should be temporary-file plus rename locally, then git add, commit, and push.

Basic GUI structure
The Basic window should show only:
* a large READY, WAIT, BLOCKED, or FAILED indicator,
* the next action in plain language,
* a few buttons derived from capabilities,
* the last result.
Technical detail belongs in collapsible panels for Rules, Transfer, GitHub/CI, Gatekeeper, Logs, and Details. Expert mode adds transparency, not bypass power. Maintainer mode may expose guarded governance, handoff, release, evidence, and cleanup tools, but it must not leak into Basic mode.

Initial Basic buttons
The first Basic buttons should be:
* Status Refresh,
* Communication Rules Refresh,
* Run Next Work Order (`agentic-kit rn`),
* Close Out Last Run (`agentic-kit rnc`),
* Diagnose.
Later buttons may add Handoff Rules Refresh, Prepare Handoff, CI Check, Evidence Transfer, and Log-GC Dry Run. Remote-mutation buttons must remain indirect and stricter than local-only actions.

Watcher model
The Basic-MVP should use polling, not webhooks. A Tkinter background worker may poll GitHub/CI every 20 to 30 seconds while WAIT is active and more slowly, around 60 to 120 seconds, when no wait state exists. Worker threads must not update Tk widgets directly. They should enqueue events for the main thread, such as STATE_REFRESHED, CI_PENDING, CI_PASSED, CI_FAILED, NEW_COMMAND_AVAILABLE, TRANSFER_UPLOADED, BLOCKER_DETECTED, ACTION_FAILED, and RULES_REFRESHED. The GUI state engine translates these events into READY, WAIT, BLOCKED, or FAILED.

Slice roadmap
Slice A: canonical transfer state and capabilities. Add an agentic-kit command that emits the Basic state JSON with primary_state, reasons, next_action, capabilities, last known good anchor, and last result. Tests cover clean main, dirty worktree, no command, command available, failed log, handoff stale, and CI pending where possible.

Slice B: rule capsule integration. Extend the rules refresh path so transfer preparation embeds or references the current capsule. Add tests for venv Python, shell fallback, remote transfer, d/f/g with w legacy, and gate-failure no-mutation rules.

Slice C: Basic GUI shell. Show the four-state indicator, next action, capability-derived buttons, and last result. The GUI must call registered agentic-kit actions and must re-check capability before each mutation.

Slice D: background watcher. Add the worker/event queue model for GitHub/CI, command availability, and transfer updates. Keep Tkinter updates on the main thread only.

Slice E: safe log garbage collection, after the Basic gatekeeper. Start with inventory and dry-run only. Allowed scopes must be explicit and must exclude `.venv`, `.git`, Python environments, GitHub internals, arbitrary external logs, and non-kit files.

Additional required anchors
The GUI should display last_known_good data, including last clean main, last verified gates, and last successful transfer. FAILED should offer a recovery path that secures the log, creates a recovery state, and transfers the failure context to the LLM without manual paste when possible. The GUI remains a didactic control layer; agentic-kit, gatekeeper checks, tests, and repository evidence remain the safety anchor.
'''


def run(label: str, argv: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print()
    print(f'### {label} ###')
    print('$ ' + ' '.join(str(a) for a in argv))
    proc = subprocess.run([str(a) for a in argv], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.stdout:
        print(proc.stdout.rstrip())
    print(f'status={proc.returncode}')
    if check and proc.returncode != 0:
        print('### RESULT: FAIL ###')
        raise SystemExit(proc.returncode)
    return proc


def main() -> int:
    for _ in range(20):
        print()
    print('=' * 51)
    print('=' * 51)
    print('=' * 51)
    print('TRANSFER TASK: GUI transfer Basic-MVP planning update')

    run('SYNC MAIN', ['git', 'switch', 'main'])
    run('PULL MAIN', ['git', 'pull', '--ff-only', 'origin', 'main'])
    dirty = run('PRE-BRANCH STATUS', ['git', 'status', '--porcelain'], check=False).stdout.strip()
    if dirty:
        print('dirty worktree before feature branch:')
        print(dirty)
        print('### RESULT: FAIL ###')
        return 1

    exists = subprocess.run(['git', 'rev-parse', '--verify', BRANCH], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if exists.returncode == 0:
        run('SWITCH EXISTING BRANCH', ['git', 'switch', BRANCH])
        run('RESET BRANCH TO MAIN', ['git', 'reset', '--hard', 'main'])
    else:
        run('CREATE BRANCH', ['git', 'switch', '-c', BRANCH])

    plan_path = ROOT / PLAN
    text = plan_path.read_text(encoding='utf-8')
    marker = 'Post-PR934 basic GUI transfer MVP update'
    if marker in text:
        before = text.split(marker, 1)[0].rstrip()
        text = before + PLAN_SECTION
    else:
        text = text.rstrip() + PLAN_SECTION
    plan_path.write_text(text.rstrip() + '\n', encoding='utf-8')
    print(f'patched={PLAN}')

    run('TARGETED DOC CHECK', [ROOT / '.venv/bin/agentic-kit', 'check-docs'])
    run('DOC LIFECYCLE AUDIT', [ROOT / '.venv/bin/agentic-kit', 'doc-lifecycle-audit'])
    run('DOCTOR', [ROOT / '.venv/bin/agentic-kit', 'doctor'])
    TMP_DIFF.write_text(run('CAPTURE DIFF', ['git', 'diff', '--binary']).stdout, encoding='utf-8')
    run('PROTECTED CHANGE PLAN', ['./ns', 'protected-change-plan', '--diff-file', str(TMP_DIFF)])
    run('GIT ADD', ['git', 'add', str(PLAN)])
    run('GIT COMMIT', ['git', 'commit', '-m', 'Update GUI transfer Basic MVP plan'])
    run('GIT PUSH', ['git', 'push', '-u', 'origin', BRANCH])
    print()
    print('SUMMARY COMM-LOCAL | gui-transfer-basic-mvp-plan-update')
    print('RESULT')
    print('  WORK: PASS')
    print('  EVIDENCE: PASS')
    print('  OVERALL: PASS')
    print('NEXT')
    print('  SAFE_STEP: create PR for GUI transfer Basic-MVP planning update')
    print('  CHAT_REPLY: d')
    print('### RESULT: PASS ###')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
