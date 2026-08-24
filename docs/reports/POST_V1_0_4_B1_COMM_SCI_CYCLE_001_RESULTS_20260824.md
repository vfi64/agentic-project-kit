# Post-v1.0.4 B1 Comm-SCI Cycle 001 Results

Status: cycle_001_recorded  
Status date: 2026-08-24  
Kit baseline when recorded: `6308fb13` (`Refresh handoff state after PR2153 (#2154)`)  
Target repository: `vfi64/Comm-SCI-Control-private`  
Target branch: `codex/b1-modularize-comm-sci-app2`  
Target PR: <https://github.com/vfi64/Comm-SCI-Control-private/pull/3>  
Cycle ID: `B1-COMM-SCI-20260824-001`

## Scope

This report imports the first real B1 Comm-SCI work-cycle evidence into the Kit
repository. It records findings and planning state only.

It does not merge the Comm-SCI PR, publish a Kit release, fix the observed Kit
defects, close GitHub issues or PRs, declare `B1_EVALUABLE`, or decide B2.

## Source Evidence

The primary work artifacts remain in the foreign repository:

- foreign report:
  `.agentic/state/handoff/reports/b1-cycle-20260824-modularize-app2.md`;
- successor validation:
  `.agentic/state/handoff/packages/latest/validation_report.json`;
- PR:
  `vfi64/Comm-SCI-Control-private#3`.

Directly verified source facts:

- Comm-SCI report records cycle `B1-COMM-SCI-20260824-001`.
- Comm-SCI handoff validation reports `status: PASS` at head
  `b667df6e69ea8a7040249674b646c63cbdb8b3cc`.
- PR #3 is open, base `feature/ui-access-levels-v2`, head
  `codex/b1-modularize-comm-sci-app2`, head SHA
  `b667df6e69ea8a7040249674b646c63cbdb8b3cc`, and merge state `CLEAN`.
- `gh pr checks` for PR #3 reports no checks on the PR branch.
- The Comm-SCI local worktree remains dirty because pre-existing `Logs/*`
  changes and generated handoff files are intentionally outside the committed
  PR scope.

## Real Work Outcome

The B1 cycle performed real Comm-SCI maintenance work, not a synthetic Kit
exercise:

- initialized the external Kit workspace;
- added `src/app/main_window_runtime.py`;
- moved App2 bridge helpers away from legacy delegation;
- removed five names from `_LEGACY_EXPLICIT_DELEGATIONS`;
- reduced the legacy seam count from 72 to 67;
- opened PR #3 with a handoff-PASS package.

Recorded target-repository validation:

- focused seam tests: 21 passed;
- manual-test/App2 bridge corridor: 5 passed;
- expanded modularization corridor: 259 passed;
- full Comm-SCI pytest: 1483 passed;
- Comm-SCI quality gate: PASS;
- App2 selftest: PASS;
- Kit doctor in the external workspace: Overall PASS;
- Kit check-docs in the external workspace: PASS;
- legacy seam counter: `legacy_seams_remaining=67`.

The cycle therefore proves that the Kit operating layer can support a real
foreign-repository work slice without breaking the target repository's own
governance gates. It does not yet prove post-merge refresh cost.

## B0 Metric Position

B0 defines B1 evaluability as at least five real cycles, including at least
three merge-boundary cycles with measurable post-merge refresh outcomes.

Cycle 001 status against that metric:

| Metric field | Value |
| --- | --- |
| real B1 work cycles recorded | 1 |
| merge-boundary cycles recorded | 0 |
| pure administrative refresh PRs | not measurable yet |
| B1 current state | `realbetrieb_running` |
| B1 evaluability | not reached |

PR #3 is open and unmerged, so no post-merge handoff refresh boundary has been
crossed. The cycle remains useful friction and bypass evidence, but it does not
enter the primary refresh-rate denominator yet.

## Kit Findings

### B1-KIT-001: `doctor --json` Is Not Available In PyPI 1.0.4

Finding type: automation gap  
Observed severity: low  
Reproducibility: confirmed

Evidence:

- `/tmp/agentic-kit-pypi-1.0.4-b1/bin/agentic-kit --version` reports
  `agentic-kit 1.0.4`.
- `agentic-kit doctor --help` lists only `--root` and `--help`.
- `agentic-kit doctor --json` exits with "No such option: --json".

Impact:

- External automation cannot consume doctor output as structured data.
- The fallback human-readable doctor output still reported Overall PASS, so
  this did not block Cycle 001.

Follow-up:

- Add a structured `doctor --json` output contract or document that doctor is
  text-only while another command owns machine-readable health output.

### B1-KIT-002: Command Manifest Is Not Portable To External PyPI Workspaces

Finding type: external-workspace defect  
Observed severity: high  
Reproducibility: confirmed

Evidence:

- PyPI 1.0.4 package resource scan found no
  `agentic-kit-commands.json` inside `site-packages`.
- Running `agentic-kit command-for --raw 'agentic-kit doctor' --json` in the
  external Comm-SCI workspace raises `FileNotFoundError` for
  `docs/reference/agentic-kit-commands.json`.
- Source scan in the Kit checkout found 12 source files importing
  `command_manifest.load_manifest`; 26 focused source files either load,
  evaluate, or directly reference `agentic-kit-commands.json`.
- In the external workspace, `agentic-kit doctor --root .` reports Overall PASS
  while explicitly skipping the `standard audit suite` outside the
  `agentic-project-kit` development checkout. `agentic-kit check --root .`
  also passes.

Impact:

- `command-for` is unusable after external `workspace init`, which weakens the
  manifest-ACK workflow in exactly the brownfield/PyPI scenario B1 is intended
  to exercise.
- The external doctor/check PASS should not be interpreted as proof that command
  manifest auditing passed. The missing-manifest path is currently outside that
  PASS surface.
- The defect is broader than one CLI command because multiple Kit modules load
  or depend on the command manifest.

Follow-up:

- Prefer a packaged manifest resource fallback for installed Kit commands, while
  preserving self-hosting drift checks against the checked-in
  `docs/reference/agentic-kit-commands.json`.
- Add an external-workspace regression test where `command-for` succeeds from a
  PyPI-style install without requiring the target repository to contain Kit
  reference docs.
- Decide whether external doctor/check should expose a WARN when a command
  manifest audit is unavailable, instead of reporting only PASS/SKIP lines.

### B1-KIT-003: External PR #3 Has No Check Runs

Finding type: remote-CI limitation  
Observed severity: medium  
Reproducibility: confirmed for PR #3

Evidence:

- GitHub PR metadata for `vfi64/Comm-SCI-Control-private#3` reports
  `statusCheckRollup: []`.
- `gh pr checks 3 --repo vfi64/Comm-SCI-Control-private` reports no checks on
  the branch.

Impact:

- The Kit can record local target-repository gates, but it cannot claim remote
  PR green status when GitHub has no checks configured or attached.
- This matches the existing public boundary that remote CI is not always
  claimed for external repositories.

Follow-up:

- Keep PR #3 merge maintainer-owned.
- Treat local gates as bounded evidence, not as remote CI equivalence.
- Consider a future external-repo readiness warning that distinguishes "checks
  green" from "no checks reported".

## Hygiene Notes

The Comm-SCI `Logs/*` modifications were pre-existing and were not staged into
PR #3. Generated `.agentic/state/handoff/...` files are present locally in
Comm-SCI after the handoff command, but only the committed cycle report and PR
metadata are imported as Kit evidence here.

No broad logs, credentials, private runtime state, or raw personal data were
copied into the Kit repository.

## Decision

Record Cycle 001 as the first real B1 work cycle and move B1 from
`B1_SETUP_COMPLETE` to `realbetrieb_running`.

B1 remains not evaluable. B2 remains blocked until the B0 threshold is met or a
maintainer explicitly accepts a low-denominator interim report.
