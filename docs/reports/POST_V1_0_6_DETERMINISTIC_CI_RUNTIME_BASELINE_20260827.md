# Post v1.0.6 deterministic CI runtime baseline

Status: measured on 2026-08-27 from branch
`codex/deterministic-ci-runtime-plan`.

This report is the CI1 baseline for `deterministic-ci-runtime-optimization`.
It records runtime cost before changing CI execution mechanics. No gate reduction
is justified by this report alone.

## Scope

- Local branch head at measurement start: `5aa04936`.
- Base `origin/main`: `aa19501e`.
- Local platform: macOS-26.6.1 arm64.
- Local Python: 3.13.1.
- Local tools: pip 26.1.1, pytest 9.0.3, ruff 0.15.14.
- Temporary raw output was written under `tmp/ci-runtime-baseline/` and is not
  intended as retained evidence.

The first local measurement pass exposed generated-output drift after the command
manifest changed. That drift was repaired before the PASS full-suite timing was
recorded:

- Handoff package ACK drift blocked `doctor`.
- `docs/site` fallback projection was stale after command-reference sync.
- A README evidence phrase had been over-shortened during CI0 documentation edits.
- Docs-lifecycle tests were updated to assert the new fail-closed `manual-review`
  behavior for malformed doc-registry scope decision projections.

These are recorded as baseline hazards: generated projections can make repeated
gate runs expensive, and a runtime optimization must not hide that fact.

## Local Timings

| Area | Command | Status | Elapsed |
|---|---|---:|---:|
| install | `.venv/bin/python -m pip install --dry-run -e '.[dev]'` | PASS | 1.48s |
| install sandbox probe | `.venv/bin/python -m pip install --dry-run -e .[dev]` from subprocess | FAIL | 8.10s |
| Ruff | `.venv/bin/ruff check .` | PASS | 0.02s |
| full pytest | `.venv/bin/python -m pytest -q --durations=20` | PASS | 430.72s |
| doc-registry tests | pytest `tests/test_documentation_registry.py` | PASS | 6.14s |
| Pages test group | pytest Pages generator/claims/fallback tests | PASS | 4.70s |
| PR/workflow test group | pytest PR CI, transfer action coverage, standard gates | PASS | 1.00s |
| CLI smoke | `agentic-kit --version` | PASS | 0.36s |
| CLI smoke | `agentic-kit check-docs` | PASS | 0.51s |
| CLI smoke | `agentic-kit doctor` | PASS | 15.91s |
| CLI smoke | `agentic-kit doc-registry reconcile --json` | PASS | 0.57s |
| CLI smoke | `agentic-kit direction validate` | PASS | 0.50s |
| Pages build | `python site/scripts/build.py --output tmp/ci-runtime-baseline/site-dist --json` | PASS | 2.75s |
| Pages fallback build | `python site/scripts/build.py --docs-pages-fallback --json` | PASS | 2.58s |
| Pages CI tests | pytest `tests/test_site_generator.py tests/test_site_claims.py` | PASS | 0.38s |

The sandbox install probe failed because build isolation attempted to resolve
`hatchling>=1.25` from PyPI while DNS was blocked. The quote-safe network-enabled
dry run passed and is the install baseline above.

## Pytest Outliers

The serial full suite passed with `2908 passed, 469 warnings in 430.72s`.
The slowest calls show that total runtime is not caused by the mass of tiny tests
alone.

| Rank | Duration | Test |
|---:|---:|---|
| 1 | 47.56s | `tests/test_gui_cockpit.py::test_visibility_matrix_matches_expected_default_state` |
| 2 | 47.33s | `tests/test_gui_cockpit.py::test_gui_builds_headless_for_every_mode_and_level` |
| 3 | 46.84s | `tests/test_gui_cockpit.py::test_visibility_matrix_core_groups_always_visible` |
| 4 | 31.39s | `tests/test_gui_cockpit.py::test_visibility_matrix_advanced_shows_advanced_groups` |
| 5 | 15.71s | `tests/test_v040_gui_tkinter_shell.py::test_doctor_manual_gui_runner_executes_readonly_action` |
| 6 | 15.54s | `tests/test_gui_cockpit.py::test_visibility_matrix_basic_hides_advanced_groups` |
| 7 | 10.32s | `tests/test_gui_cockpit.py::test_access_level_existence_unchanged` |
| 8-20 | 67.88s | thirteen additional `test_gui_cockpit.py` calls at about 5.16s-5.66s each |

The top 20 recorded slow calls account for about 282.57s of the 430.72s local
serial run. The initial CI2 baseline therefore treated GUI/Tkinter isolation as
the main parallelization risk rather than assuming simple worker scaling.

## CI2 Shadow Observation

After the runtime policy implementation added `pytest-xdist>=3.6`, the fixed
four-worker shadow command passed locally:

| Command | Status | Elapsed | Result |
|---|---:|---:|---|
| `.venv/bin/python -m pytest -q -n 4 --durations=20` | PASS | 225.30s | 2931 passed, 469 warnings |
| `.venv/bin/python -m pytest -q -n 4 --durations=20` | PASS | 230.23s | 2932 passed, 469 warnings |

These were local shadow PASS observations, not enough by themselves to promote
parallel pytest to the required gate. At this stage, the slowest calls still
were GUI/Tkinter tests, so repeated shadow evidence still had to watch for order
dependence, shared-state leaks, live-repo collisions, and marker conflicts
before the serial full-suite fallback could be removed.

## CI2 Promotion and Regression Diagnosis

Follow-up GitHub Actions inspection on 2026-08-28 showed that the first
implementation shortened admin-refresh lanes but regressed ordinary `FULL_CI`
runtime. The regression was concentrated in the serial pytest step after the CI
workflow started using a full-history checkout for diff/tree classification.

| Run | Lane | Required test evidence | Parallel evidence |
|---|---|---:|---:|
| <https://github.com/vfi64/agentic-project-kit/actions/runs/33097211301> | pre-slice main push | `2906 passed` in 152.85s | n/a |
| <https://github.com/vfi64/agentic-project-kit/actions/runs/33141249255> | PR #2197 | `2932 passed` in 403.11s | `2932 passed` in 120.93s |
| <https://github.com/vfi64/agentic-project-kit/actions/runs/33176783563> | PR #2202 | `2935 passed` in 525.89s | `2935 passed` in 100.33s, `PYTEST_PARALLEL_SHADOW_RC=0` |
| <https://github.com/vfi64/agentic-project-kit/actions/runs/33181160222> | PR #2204 | `2935 passed` in 472.72s | `2935 passed` in 121.13s, `PYTEST_PARALLEL_SHADOW_RC=0` |
| <https://github.com/vfi64/agentic-project-kit/actions/runs/33183065798> | post-PR2205 main push | admin-light required job in 35s | `2935 passed` in 123.87s, `PYTEST_PARALLEL_SHADOW_RC=0` |

The added CI-policy tests were not the runtime cause: the touched CI-policy and
documentation-registry test modules ran locally together in about 4s. The
dominant cost was the serial full-suite execution under the changed CI checkout
shape. The follow-up optimization therefore promotes the fixed-worker parallel
pytest command to the branch-protection-visible `test` job and restores shallow
checkout with exact endpoint fetches for changed-path classification.

## GUI/Tkinter Bottleneck Remediation

Targeted profiling on 2026-08-28 showed that the headless Tkinter visibility
matrix was not blocked by Tk widget construction itself. A single matrix test
spent about 47s of 53s in `CockpitGui._manifest_status()`, which called the
full `workspace adopt` analyzer and repeatedly ran the documentation age Git-log
baseline. That full adoption report is useful for `workspace adopt`, but it is
too broad for the GUI chrome label.

The gate-conformant remediation keeps the production gatekeeper live and removes
only irrelevant work from the GUI status path:

- `workspace_adopt` now exposes a lightweight `.agentic/` collision-status
  analysis for callers that do not need a full adoption report.
- `CockpitGui._manifest_status()` uses that lightweight status instead of the
  full `analyze_workspace_adoption()` report.
- Headless GUI tests can inject a deterministic `GuiGatekeeperStatus` snapshot,
  while the default `CockpitGui` constructor path still passes no override and
  remains live.

| Probe | Before | After |
|---|---:|---:|
| `tests/test_gui_cockpit.py::test_gui_builds_headless_for_every_mode_and_level` | 48.27s | 0.75s |
| full `tests/test_gui_cockpit.py` module | previously dominated by multiple 10s-47s calls | 83 passed in 3.56s |
| full local pytest, serial | 430.72s | 145.91s |
| full local pytest, `-n 4` | 206.96s before GUI remediation | 48.11s |
| new injection/default-path protection tests | n/a | 3 passed in 0.50s |

This is not a CI reduction: the GUI assertions still run, and the full adoption
report remains covered by workspace-adoption tests. The change narrows only the
runtime work performed for a GUI label and for deterministic headless GUI
matrix tests.

## Remote CI Baseline

Remote data was fetched read-only from GitHub Actions on 2026-08-27.

| Lane | Run | Event and branch | Overall | Job/step evidence |
|---|---|---|---:|---|
| current branch PR CI | current `5aa04936` | no PR workflow run found | n/a | GitHub commit-workflow lookup returned no PR runs. |
| product PR CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33088860048> | pull_request, `codex/refresh-receipt-feasibility` | 3m54s | test job 3m49s; install 9s; tests 3m31s; CLI smoke 1s. |
| admin-refresh PR CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33097577175> | pull_request, `docs/post-pr2195-handoff-refresh` | 4m07s | test job 4m02s; install 9s; tests 3m41s; CLI smoke 1s. |
| main-push CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33097945702> | push, `main` at `aa19501e` | 2m16s | test job 2m11s; install 5s; tests 1m55s; CLI smoke 1s. |
| Pages main push | <https://github.com/vfi64/agentic-project-kit/actions/runs/33097945840> | push, `main` at `aa19501e` | 49s | pages-state 5s; build 21s; deploy 10s; generated-site build 4s; site tests 1s. |

Recent `CI` runs show that admin-refresh PRs cost about the same order of
magnitude as product PRs even when they carry only generated handoff state.
Recent `Pages` push runs complete in about 29s-53s, with the latest successful
main run at 49s.

## Remote Follow-up Observation

After PR #2197 merged, read-only GitHub Actions inspection on 2026-08-28 showed
that the first implementation stayed safe but did not yet deliver the intended
cycle-time reduction for post-merge administrative refreshes.

| Lane | Run | Event and branch | Overall | Job/step evidence |
|---|---|---|---:|---|
| PR #2197 CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33141249255> | pull_request, `codex/deterministic-ci-runtime-plan` | 7m10s | required `test` job 7m06s; serial pytest step 6m45s; shadow job 2m19s. |
| PR #2197 main push | <https://github.com/vfi64/agentic-project-kit/actions/runs/33141972900> | push, `main` at `90688dd4` | 9m42s | required `test` job 9m38s; serial pytest step 9m23s; shadow job 2m06s. |
| PR #2198 main push | <https://github.com/vfi64/agentic-project-kit/actions/runs/33168537147> | push, `main` at `f17c21c3` | 9m14s | required `test` job 9m10s; serial pytest step 8m52s; shadow job 2m20s. |
| PR #2199 CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33168998555> | pull_request, `docs/post-pr2198-successor-package-refresh` | 7m12s | required `test` job passed; `pytest-parallel-shadow` failed and was still treated as PR-blocking status evidence. |
| PR #2201 CI | <https://github.com/vfi64/agentic-project-kit/actions/runs/33174455297> | pull_request, `docs/post-pr2200-handoff-refresh` | 10m01s | required `test` job 9m55s; shadow job 2m01s; diff contained the combined post-merge settle refresh path set. |
| PR #2203 main push | <https://github.com/vfi64/agentic-project-kit/actions/runs/33179000497> | push, `main` at `abbcf2ef` | 2m12s, failed | required `test` job selected admin-refresh-light but failed in protected-diff-plan setup because PR base/head SHAs are unavailable on push events. |

The run order for `CI #7674` and `CI #7675` is chronologically correct:
`CI #7674` started at 2026-08-28T11:48:13Z as the push run for merge commit
`f17c21c3`, and `CI #7675` started at 2026-08-28T11:55:25Z as the pull-request
run for PR #2199. GitHub lists newer workflow runs first, so #7675 appears above
#7674 even though #7674 started first. The overlap is operationally undesirable:
the successor package PR was opened while the main-push CI for the preceding
admin refresh was still running.

The observations identify two corrective constraints:

- `admin-refresh-light` must accept only exact generated refresh variants, but
  those variants must match the actual deterministic refresh PRs:
  `current-handoff-refresh`, `successor-package-refresh`, and the combined
  `post-merge-settle-refresh` emitted by the settle wrapper.
- `pytest-parallel-shadow` must remain diagnostic-only in branch-protection
  evidence. It may record and warn on the real xdist exit code, but it must not
  block PR readiness while serial pytest remains the authoritative gate.
- Admin-light workflow evidence must use pull-request base/head SHAs on PR
  events and push `before..current` SHAs on main-push events. Empty PR-only SHAs
  on a push event are a workflow adapter bug, not safe proof input.

Main-push dedupe remains fail-closed until tested-tree and successful-PR-check
proof inputs are wired. The long main-push runs above are therefore expected for
now, but they are not acceptable evidence that the optimization slice is
complete for administrative refresh PR cycle time.

## Optimization Constraints

- CI2 required parallel pytest promotion is allowed only after repeated shadow
  PASS evidence proves parity with serial PASS.
- CI3 must keep a branch-protection-visible deterministic check and may dedupe
  main-push CI only with a fail-closed tree equivalence proof.
- CI4 may narrow admin-refresh PR CI only when an exact generated-handoff
  classifier accepts the diff and package validation is PASS.
- CI5 may gate Pages only from a maintained path manifest, never from an ad hoc
  YAML path guess.
- CI6 starts diagnostic-only; repair proposals must not mutate `main`.
- CI7 remains a design/prototype decision until exactly-one receipt, append-only
  enforcement, and successor read-path discovery are proven.

## Decision

Proceed to CI2-CI7. The baseline supports runtime optimization work, but it also
shows that generated projection freshness and GUI/Tkinter test isolation are
the primary risk areas. Any reduced path must fall back to the existing full
suite on ambiguity.
