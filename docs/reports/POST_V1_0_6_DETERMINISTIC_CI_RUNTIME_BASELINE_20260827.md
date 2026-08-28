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
serial run. CI2 should therefore treat GUI/Tkinter isolation as the main
parallelization risk rather than assuming simple worker scaling.

## CI2 Shadow Observation

After the runtime policy implementation added `pytest-xdist>=3.6`, the fixed
four-worker shadow command passed locally:

| Command | Status | Elapsed | Result |
|---|---:|---:|---|
| `.venv/bin/python -m pytest -q -n 4 --durations=20` | PASS | 225.30s | 2931 passed, 469 warnings |
| `.venv/bin/python -m pytest -q -n 4 --durations=20` | PASS | 230.23s | 2932 passed, 469 warnings |

These are local shadow PASS observations, not enough to promote parallel pytest
to the required gate. The slowest calls remain GUI/Tkinter tests, so repeated
shadow evidence must still watch for order dependence, shared-state leaks,
live-repo collisions, and marker conflicts before the serial full-suite fallback
is removed.

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

## Optimization Constraints

- CI2 may add parallel pytest only as a shadow run until repeated shadow PASS
  evidence proves parity with serial PASS.
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
