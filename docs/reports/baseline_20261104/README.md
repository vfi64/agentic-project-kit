# Kit strategy baseline — 2026-11-04

Status: measurement report; no target values, policy change, or release decision.  
Pinned `origin/main` and local HEAD: `a2e4528820f7729ce248313a8ef4decdc1b6f81e`.  
Machine-readable measurements and step return codes: [`baseline.json`](baseline.json). The working branch contains this report only; measurements refer to the pinned main commit.

## B1 — administrative work

`git log --first-parent --since=2026-10-01 --format='%H%x09%cI%x09%s' origin/main` returned 0. Commits were grouped by the Monday of their local commit-date week; the first bucket therefore includes only commits from October 1 onward. Classification uses anchored subject prefixes, not changed files. The exact handoff and successor-refresh templates are in `src/agentic_project_kit/transfer_repo_actions.py:2570,2757`; `src/agentic_project_kit/dpa_wrt_ch001_evidence.py:97` checks the handoff PR title, and `src/agentic_project_kit/status_current_state_audit.py:778` recognizes the handoff merge subject. Release, DOI and archive prefixes were matched to the subjects on the pinned first-parent history. “Other” is a **subject-signature remainder**, not proof that every such PR changes product content.

| Week beginning | Handoff refresh | Successor refresh | Release | DOI | Archive | Other | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-09-28 | 22 | 1 | 0 | 0 | 0 | 22 | 45 |
| 2026-10-05 | 44 | 0 | 5 | 3 | 0 | 37 | 89 |
| 2026-10-12 | 37 | 0 | 3 | 2 | 2 | 29 | 73 |
| 2026-10-19 | 44 | 0 | 6 | 5 | 5 | 28 | 88 |
| 2026-10-26 | 39 | 0 | 5 | 5 | 6 | 23 | 78 |
| 2026-11-02 | 12 | 0 | 1 | 1 | 1 | 9 | 24 |
| **Total** | **198** | **1** | **20** | **16** | **14** | **148** | **397** |

The 199 refresh and 50 release/DOI/archive subjects together account for 249/397 (62.7%) of these commits. At `4e952bd5`, the same command and classifier yield 395 total, 198 refresh, 50 release/DOI/archive. The two later commits are the GF-102/103 reconciliation PR #2745 and its handoff refresh PR #2746; thus only the total and refresh count rose by one each. The strategy draft's rounded 63% remains consistent, while its counts are pinned to an older HEAD.

**PR-head CI observation.** GitHub REST `pulls?state=closed&per_page=100&sort=updated&direction=desc`, filtered to merged `main` PRs on 2026-11-04 UTC, returned six PRs. For each, the pull request's final `head.sha` was used with the commit workflow-runs API; the completed `CI` run's `run_started_at` to `updated_at` is the measured wall interval. This excludes queue time and sums no individual jobs. All six runs concluded `success`; #2741 was attempt 2, so its first attempt is outside this sample.

| Group | PRs | Durations (seconds) | Median | Range |
|---|---|---:|---:|---:|
| Handoff administration | #2742, #2744, #2746 | 78, 79, 79 | 79 s | 78–79 s |
| Content/planning by non-refresh title | #2741, #2743, #2745 | 453, 480, 395 | 453 s | 395–480 s |

The three non-refresh PRs include planning and maintenance, not just product code. Six runs on one day establish a bounded observation, not a stable CI baseline or removable-time estimate. Run IDs and timestamps are in `baseline.json`.

## B2 — context size

At the pinned HEAD, `agentic-kit context report --json` and `context render --profile` for `handoff`, `planning`, `release`, and `slice` each returned 0. `context_report` calculates estimated tokens as `ceil(characters / 4)` (`src/agentic_project_kit/context_budget.py:301-325`). These are **ESTIMATED**, not agent-billed or actually consumed tokens.

| Material | Bytes or characters | Estimated tokens | Status |
|---|---:|---:|---|
| Nine successor required reads | 871,866 bytes | 217,961 | bytes MEASURED; tokens ESTIMATED |
| Context packet: handoff | 13,996 characters | 3,499 | characters MEASURED; tokens ESTIMATED |
| Context packet: planning | 14,807 characters | 3,702 | characters MEASURED; tokens ESTIMATED |
| Context packet: release | 14,800 characters | 3,700 | characters MEASURED; tokens ESTIMATED |
| Context packet: slice | 15,071 characters | 3,768 | characters MEASURED; tokens ESTIMATED |

The four `context render` calls produced those packet bodies plus one terminal newline. The packet totals are additional views, not savings that can be subtracted from the required-read baseline. `wc -c` measured `docs/reference/agentic-kit-commands.json` at 566,079 bytes, `docs/STATUS.md` at 33,458, `docs/handoff/CURRENT_HANDOFF.md` at 35,483, and `docs/planning/PROJECT_DIRECTION.yaml` at 314,556 (all return code 0). Actual agent consumption is **NOT_MEASURED**; no paid model run was performed.

## B3 — CLI surface and usage evidence

The manifest at this HEAD contains **275** commands: 37 orchestrators and 238 others (131 diagnostic, 107 primitive). The existing static stages of `docs/reports/command_usage_audit_20261015/scripts/run_usage_audit.py` returned 0 without `--with-tests`, `--with-sim`, or a history clone. They find 80 of the 238 non-orchestrators statically reachable from an orchestrator. No new test trace or simulation was run. The October 15 audit at `ef78a255` covered 266 commands, with its then-current test trace, simulation and historical evidence (`docs/reports/COMMAND_USAGE_AUDIT_20261015.md`; `.json` appendix).

To refresh the A–D table, the October dynamic evidence was retained for unchanged command names, while current static reachability takes precedence over old B/C/D placement. This is a **mixed-date classification**, not a fresh observation of current execution. New commands receive B only when statically reachable; otherwise they remain UNKNOWN. The tier algorithm is `docs/reports/command_usage_audit_20261015/scripts/compare_sources.py:49-59`.

| Tier | October 15 | Mixed-date at pinned HEAD | Evidence limit |
|---|---:|---:|---|
| A: simulation/history use | 76 | 76 | Historical evidence only; no fresh dynamic trace |
| B: statically reachable, no recorded dynamic use | 15 | 21 | Current static graph + historical dynamic evidence |
| C: only test-invoked | 116 | 114 | Historical test trace; cannot assert no later use |
| D: no invocation in available trace | 25 | 22 | Historical trace only; cannot assert current non-use |
| UNKNOWN | 0 | 5 | New commands with no fresh trace and no static orchestrator reachability |
| Orchestrators | 34 | 37 | Current manifest |
| **Total** | **266** | **275** | |

The nine new names are three orchestrators (`kit return-install`, `kit return-revert`, `release abandon`), one statically reachable B (`greenfield retest`), and five UNKNOWN (`audit-drift-signals`, `context render`, `context report`, `ledger report`, `transfer merge-upstream`). Five older commands shift to B under current static analysis: `check`, `ci runtime-plan`, `greenfield export`, `greenfield status`, and `transfer branch-delete`. No command is proposed for removal or concealment based on this mixed-date table.

Unlike the 2026-10-15 audit, this checkout has an enabled, ignored local ledger (`src/agentic_project_kit/invocation_ledger.py:18,53`). `agentic-kit ledger report --json` returned PASS/0 with 7,561 records, 1,984 root invocations, 104 distinct command names and zero ledger parse errors at measurement time. It includes nested calls, past work on this machine and failed attempts; it is not a cross-user usage frequency. The full local ledger and raw report are not committed.

## B4 — strategy draft fact check

1. **`work start` sync-main is conditional.** `src/agentic_project_kit/cli_commands/human_workflows.py:576-607` calls `transfer sync-main` only when `_is_main_start_ref(base_ref)` is true. Other refs take the fetch branch. Thus the draft's unqualified “work start includes sync-main” needs the main-ref condition.
2. **`work finish --execute` has a composite post-merge route by default.** In `human_workflows.py:800-846` its `merge=True` path calls `transfer pr-create-complete --post-merge-complete`, then checks a completion receipt or performs sync-main, post-merge-check and repo-status. A separate `transfer post-merge-settle` is not required after successful verified default completion. With `--no-merge`, `human_workflows.py:847-896` leaves the PR open and handoff pending; any later merge still needs governed closeout.
3. **`release run` invokes ready and prepare itself.** `src/agentic_project_kit/release_run.py:122-136` shows A2 `release ready`, A3 `release prepare` as dry run, and B2 `release prepare --write`; A1 first syncs main. These steps need not be separately repeated during that run.
4. **The repository lifecycle table is broadly correct but compresses distinct layers.** `init` creates a project skeleton and may call GitHub creation (`cli_commands/init.py:38-115`); `github-create` creates/pushes a repository (`cli_commands/github.py:21-40`). `workspace adopt` analyzes read-only, while `workspace init` plans/writes operating-layer files (`cli_commands/workspace.py:50-77,120-177`). `kit update` changes the pinned Kit; `workspace upgrade` is a workspace manifest schema migration; `workspace ci-update` changes the managed CI template (`cli_commands/kit.py:60-89`, `cli_commands/workspace.py:230-323`). Return is the bounded `return-revert` then `return-install` sequence in `docs/KIT_UPDATE_RETURN.md:1-32`; `workspace remove` removes exact generated workspace files (`cli_commands/workspace.py:188-228`); `kit status` is diagnostic (`cli_commands/kit.py:43-59`). Therefore “three commands for one update” is misleading: they address different state and are not automatically all required for every update. “Wiederfreigabe” means removal only under the draft's stated assumption.
5. **The return-install help is stale.** `cli_commands/kit.py:112` hardcodes `1.1.10`, while `docs/KIT_UPDATE_RETURN.md:1-5,20-32` and the receipt-bound flow describe the exact prior pinned version. This report does not change the help text.

## Method limits and decision boundary

The manifest and context counts are exact for the pinned checkout. GitHub CI values are a one-day sample. The CLI tiers combine current static data and older dynamic evidence. Actual agent token use, a fresh full-suite command trace and cross-repository invocation frequency are **NOT_MEASURED**. `docs/DOCUMENTATION_COVERAGE.yaml` needs no new rule here because this slice adds a dated evidence report and changes no public command, workflow, gate, or concept. The report is registered in the documentation registry. Thresholds and strategy decisions remain with the Owner.
