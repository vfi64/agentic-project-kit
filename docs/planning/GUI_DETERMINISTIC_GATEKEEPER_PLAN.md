
GUI Deterministic Gatekeeper Plan
Status: proposed Decision status: proposed
Scope: planning only Target baseline: post-PR873 main Next release checkpoint: v0.4.4 Product-code changes in this planning PR: none
Purpose
This document records the migration plan for turning the GUI from a remote-control surface into a deterministic gatekeeper for repository-backed AI-assisted work.
The GUI must not become a remote control for the LLM. It must become a deterministic gatekeeper over repository state, evidence, summaries, communication contracts, and allowed actions.
The working principle is:
The LLM proposes. The kit decides. The GUI displays and blocks when rules are violated.
The repository remains the long-term memory and source of truth. Chat memory and ad-hoc assistant judgement are not sufficient evidence. Durable state must live in repository files, deterministic checks, committed logs, generated summaries, and explicit handoff state.
Required sequencing
The work must happen in this order:
1. Planning PR: record this plan in planning and state documents only, with no product-code change.
2. Safety release v0.4.4: freeze the current stable post-PR873 baseline.
3. Successor-chat handoff: generate a fresh handoff prompt according to the governed handoff rules.
4. Migration PR series: implement the gatekeeper work in small, reversible PRs, each with its own tests and evidence.
No further GUI feature expansion should happen before this path is planned and the v0.4.4 safety checkpoint is complete.
Current post-PR873 baseline
After PR873, the basic upload-button path exists and the GUI no-window smoke passes on main. The evidence available in the post-PR873 closeout indicates:
* PR873 was merged into main.
* Main contains 23532a0 Add GUI work order upload strip (#873).
* The final closeout evidence was committed in 5b30fe3 Record PR873 final main closeout evidence.
* Targeted GUI/work-order tests passed on main.
* The GUI no-window smoke passed on main.
* docs/reports/terminal/next-turn-latest.log is not supposed to be a tracked persistent file.
This means the upload button exists as a basic mechanism, but it is not yet a professional deterministic gatekeeper. The missing part is not execution. The missing part is strict classification, summary validation, dirty-state validation, evidence validation, and policy enforcement.
The GUI currently also has a compact top toolbar. The post-PR873 smoke output records:
toolbar_button_count=8
toolbar_icons=branch,status,history,handoff,stethoscope,document-check,audit,guard
action_button_count=32
That means the toolbar exists, but not all workflow actions are top-level toolbar actions. Remaining actions still live in the action area.
Target state
The GUI must become a deterministic control layer. It must not merely call commands and display their output. It must decide whether an action is allowed, blocked, uploadable, committable, pushable, mergeable, releasable, or handoff-ready.
The GUI must make this decision through agentic-kit Python code and repository-backed gates, not through LLM judgement.
The target states should include clear machine-derived classifications such as:
READY_TO_CONTINUE
BLOCKED_BY_FAIL
BLOCKED_BY_PENDING
BLOCKED_BY_DIRTY_WORKTREE
BLOCKED_BY_BAD_SUMMARY
BLOCKED_BY_HIDDEN_FAIL
BLOCKED_BY_MISSING_EVIDENCE
BLOCKED_BY_STALE_HANDOFF
BLOCKED_BY_PROTECTED_FILE_CHANGE
BLOCKED_BY_RED_OR_UNKNOWN_CI
BLOCKED_BY_FORBIDDEN_SHELL_PATTERN
AMBIGUOUS
The user should not need to manually distinguish d, f, w, or Pending. A deterministic command should classify the last result and derive the next safe action.
Core goals
1. Replace manual
d
,
f
,
w
, and
Pending
interpretation
The user should eventually only say done or press the relevant GUI button. The system must inspect the last result log and derive:
result=PASS | FAIL | PENDING | BLOCKED | AMBIGUOUS
next_safe_action=...
chat_reply=done | fail | pending | blocked
reason=...
evidence=...
The LLM must not decide from impression whether a d is justified. That decision must come from a deterministic result classifier.
2. Upload only after deterministic preflight
The upload button must not blindly upload a log. It must first check:
* Does a current result log exist?
* Does the log contain exactly one valid standard summary?
* Does the summary use the current standard format?
* Does the log contain hidden FAIL, ERROR, tracebacks, Ruff failures, pytest failures, shell syntax failures, missing-module failures, or aborted steps before a later PASS?
* Does the final marker match the summary result?
* Is the worktree clean or dirty only with exactly allowed upload artifacts?
* Are transient logs such as docs/reports/terminal/next-turn-latest.log not tracked as durable evidence?
* Are evidence paths repo-readable or remote-readable when they are claimed as evidence?
* Were forbidden shell-script, heredoc, risky quote, or long inline patch patterns used where the policy blocks them?
* Is PR or CI state machine-readable and clean before any merge-related state is accepted?
Only if the preflight passes may upload proceed.
3. Enforce the standard summary
Every evidence-bearing run must contain a valid summary with at least these sections:
SUMMARY COMM-LOCAL | ...
SLICE
EXECUTION
RESULT
INTERPRETATION
REMOTE
EVIDENCE FILES
NEXT
The gatekeeper must block on:
* missing summary,
* old summary format,
* wrong section structure,
* missing evidence path,
* contradictory final result,
* PENDING followed by upload attempt,
* PASS despite earlier hard errors,
* CHAT_REPLY: d or equivalent when classification is fail, pending, blocked, or ambiguous.
The repeated failure mode to eliminate is: a final PASS or PENDING appears while visible earlier steps failed.
4. Python commands become canonical
The long-term direction is:
* New logic must be implemented as Python code inside agentic-kit.
* Every relevant action should have an agentic-kit command.
* The GUI should call registered Python actions or agentic-kit commands.
* ./ns remains temporarily as a compatibility layer only.
* Shell wrappers must not contain new workflow logic.
* Shell heredocs, long inline shell scripts, python -c monoliths, and risky multiline patch blocks should be detected by policy gates and initially warned, later blocked for evidence-bearing upload, merge, release, and handoff workflows.
This does not forbid Git as a subprocess. It means workflow logic should not live in untested ad-hoc shell blocks. Python may call Git through a tested subprocess wrapper.
5. Drift detection
The GUI cannot read the LLM’s thoughts, but it can detect drift symptoms deterministically:
* summary missing or wrong,
* chat answer says PASS while log contains FAIL,
* log contains PENDING while next action claims done,
* terminal block contains forbidden heredoc or quote-risk patterns,
* worktree is dirty while summary claims clean state,
* CI or PR status is red or unknown while summary recommends merge,
* protected files changed without a protected-change plan,
* handoff state points to stale main commits,
* generated handoff prompt is older than the current verified main state,
* transient log is tracked as durable evidence.
This is not an AI judge. It is a repository rule checker.
Rule model
Not every rule can be enforced in the same way. Each rule must be categorized.
deterministic
heuristic
advisory
Only deterministic rules may hard-block automatically.
Heuristic rules may warn, or block only in explicitly scoped workflows after review.
Advisory rules are displayed but must not be treated as proof.
The GUI must not create a second governance universe. The rules must live in agentic-kit and repository-backed configuration. The GUI displays and invokes those gates.
PR roadmap
PR 1 — Planning and state refresh only
Goal: Record this plan and refresh stale state documents after PR873.
Allowed files include planning and state documents such as:
* docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md
* docs/STATUS.md
* docs/handoff/CURRENT_HANDOFF.md
* .agentic/handoff_state.yaml
No product-code change is allowed in this PR.
Required content:
* GUI-as-gatekeeper target state,
* migration roadmap,
* non-goals,
* risk analysis,
* stability criteria,
* release order: plan first, then v0.4.4, then implementation PRs.
PR 2 — Safety release v0.4.4
Goal: Freeze the current stable post-PR873 baseline before the migration begins.
Tasks:
* set version to 0.4.4,
* update CHANGELOG,
* update release metadata,
* run existing release gates,
* merge release-prep PR,
* tag and publish through the existing release process,
* verify GitHub release and Zenodo archival through the existing post-release check.
No gatekeeper migration work belongs in the v0.4.4 release-prep PR.
PR 3 — Deterministic result classifier
Goal: Add a Python module that classifies terminal and evidence logs.
Possible command:
agentic-kit evidence classify-log <path>
Expected output:
LOG_CLASSIFICATION
state=BLOCKED_BY_FAIL
summary_valid=false
hidden_fail=true
final_marker=PASS
decision=fail
Must detect:
* clean PASS log,
* clean FAIL log,
* PENDING log,
* PASS with hidden earlier FAIL,
* missing summary,
* invalid summary,
* old summary format,
* test failure,
* Ruff failure,
* Python traceback,
* shell syntax failure,
* dirty-state contradiction.
This PR introduces the classifier but does not yet force all uploads through it.
PR 4 — Standard summary validator hardening
Goal: Make the standard summary contract machine-checkable and stricter.
Validate at least:
* SUMMARY COMM-...,
* SLICE,
* EXECUTION,
* RESULT,
* INTERPRETATION,
* REMOTE,
* EVIDENCE FILES,
* NEXT,
* final result marker,
* evidence path presence,
* consistency between summary result and hidden-failure scan.
This PR may report failures without yet changing upload behavior.
PR 5 — Upload preflight for CLI and GUI
Goal: Add an upload preflight command.
Possible command:
agentic-kit work-order upload-preflight
It checks:
* log exists,
* summary valid,
* classification coherent,
* no tracked transient logs,
* no forbidden shell patterns where blocking applies,
* no disallowed dirty paths,
* evidence paths are acceptable.
The GUI upload button must call this preflight before upload.
PR 6 — Upload uses classifier and preflight
Goal: The upload path must stop being a blind upload path.
Output should include:
WORK_ORDER_UPLOAD_RESULT
classification=...
ok=...
blocked_reason=...
next_safe_action=...
At this stage, policy may still be moderately strict, but the decision must be machine-derived.
PR 7 — Upload blocks invalid summaries and hidden failures
Goal: Make the upload gate strict for deterministic failures.
Blocking cases:
* hidden FAIL before final PASS,
* missing or invalid summary,
* old summary format,
* PENDING with upload attempt,
* dirty non-evidence paths,
* tracked transient next-turn log,
* protected file change without protected-change plan,
* red or unknown CI for merge-related claims,
* forbidden shell pattern in an evidence-bearing workflow.
PR 8 — Machine-derived next action replaces manual
d/f/w/pending
Goal: Introduce a command that derives the next action from the last result.
Possible command:
agentic-kit next-action from-last-result
Example output:
NEXT_ACTION
decision=continue
chat_reply=done
reason=last log passed and evidence is valid
or:
NEXT_ACTION
decision=blocked
chat_reply=fail
reason=hidden failure before final PASS
The GUI should display this decision. The LLM may repeat it, but must not invent it.
PR 9 — Shell usage inventory
Goal: Inventory all shell-based workflow routes.
Possible command:
agentic-kit ns-inventory
It should report:
* all ./ns commands,
* all ./ns-menu paths,
* shell-only routes,
* Python-equivalent routes,
* deprecated routes,
* migration priority.
No shell removal happens in this PR.
PR 10 — Python replacements for core
./ns
routes
Goal: Provide native agentic-kit commands for the important workflows.
Priority:
1. status and state,
2. evidence inspect/finalize/classify,
3. work-order validate/run/upload/preflight,
4. PR status and merge readiness,
5. handoff prompt/check,
6. protected-change-plan,
7. docs and governance gates.
./ns may still delegate, but new logic belongs in Python.
PR 11 — GUI uses only registered Python actions
Goal: The GUI must execute only registered actions with explicit safety classes.
Safety classes should include:
read-only
bounded-local-mutation
bounded-upload
remote-mutation
release
destructive
Unregistered actions are not displayed or not executable.
Remote mutation, release, and destructive actions remain blocked unless a later explicit policy enables them.
PR 12 — Deterministic drift status line
Goal: The GUI displays gate status as machine results, not as reminders.
Example:
Rule state:
- summary_contract: PASS
- shell_policy: PASS
- evidence_visibility: PASS
- dirty_worktree: PASS
- protected_files: PASS
- transient_logs: PASS
- handoff_freshness: PASS
- next_action: READY_TO_CONTINUE
This is a deterministic rule-status display, not motivational text for the LLM.
PR 13 — Deprecate
./ns
Goal: Mark ./ns as compatibility-only.
Rules:
* new documentation should prefer agentic-kit ...,
* GUI should not call ./ns as its primary route,
* shell wrappers must not gain new logic,
* warnings may point users to Python commands.
PR 14 — Freeze or minimize
./ns
Goal: Once the Python command surface is complete, either remove ./ns or reduce it to a minimal delegating stub.
This must happen late. Removing it too early risks breaking working workflows.
PR 15 — Handoff preflight with machine-readable freshness
Goal: Handoff prompts must include machine-derived state.
The handoff prompt generation path should include:
* main HEAD,
* current branch,
* dirty status,
* last evidence log,
* open PRs,
* safe next action,
* blocking policy state,
* handoff-state freshness,
* status-document freshness.
PR 16 — Handoff generation blocks stale state
Goal: If docs/STATUS.md, docs/handoff/CURRENT_HANDOFF.md, .agentic/handoff_state.yaml, or the latest generated handoff prompt do not match the current verified main state, handoff generation must fail or prominently report:
handoff_staleness=FAIL
This directly addresses the repeated stale-handoff failure mode.
Non-goals
This plan does not:
* immediately remove ./ns,
* immediately forbid every shell command,
* make the GUI independently own governance rules,
* replace repository evidence with GUI state,
* trust LLM-generated summaries without validation,
* perform release work inside the planning PR,
* implement new GUI features before the gatekeeper migration plan is recorded.
Risks and mitigations
Risk 1: Removing
./ns
too early
Mitigation: inventory first, then parallel Python commands, then deprecate, then freeze or remove.
Risk 2: Overly strict shell blocking disrupts diagnosis
Mitigation: start warning-only for general diagnosis. Block only in upload, merge, release, evidence, and handoff contexts where deterministic policy applies.
Risk 3: GUI becomes a second governance system
Mitigation: rules live in agentic-kit and repository configuration. GUI only invokes and displays them.
Risk 4: Not all rules are deterministic
Mitigation: classify rules as deterministic, heuristic, or advisory. Only deterministic rules hard-block.
Risk 5: Large migration PRs become hard to revert
Mitigation: keep PRs small, each with tests, evidence, and clean handoff.
Stability criteria
Before starting implementation after v0.4.4:
* planning document is merged,
* state documents point to the current post-PR873 or post-planning baseline,
* v0.4.4 is released and post-release verified,
* successor-chat handoff is generated from fresh repo state,
* no tracked transient next-turn log exists,
* current gates pass for the chosen slice.
For each migration PR:
* no product code outside the stated scope,
* targeted tests pass,
* relevant docs updated,
* terminal evidence committed,
* PR machine status clean before merge,
* main verified after merge,
* handoff/state updated when needed.
Immediate next step
Complete PR 1 as a planning-only PR. Then prepare and publish the v0.4.4 safety release. Only after that begins the gatekeeper migration series.

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
