# Post-v1.0.13 GF-009 Private Released-Package Retest

Status: PASS for the bounded external first-cycle closeout
Date: 2026-09-16
Package: `agentic-project-kit==1.0.13` from PyPI
Target repository: private `vfi64/kit-test-01`

## Scope

This report records a real first-cycle execution against a private repository
using only the released PyPI package. The target repository was empty before
the test. No Kit checkout was installed into or mounted into the target.

The test deliberately covered the previously missing GF-009 boundary:

- external workspace initialization;
- a real work branch and mutation;
- commit and push;
- pull request creation;
- a remote CI check using the released package;
- protected merge;
- post-merge successor refresh PR;
- protected merge of the successor refresh PR;
- final post-merge status.

## Evidence

| Step | Result | Evidence |
| --- | --- | --- |
| Private target repository | PASS | `vfi64/kit-test-01`, private, empty at start |
| Released package installation | PASS | PyPI `agentic-project-kit==1.0.13` in isolated Python 3.14 venv |
| Workspace initialization | PASS | `.agentic/config.yaml`, registries, state, transfer files generated |
| External gates | PASS | `check-docs`, `check`, and `doctor`; doctor overall PASS |
| First-cycle work start | PASS | `work start --branch codex/gf009-first-cycle`; no prior successor package correctly treated as not applicable |
| Work PR | PASS | PR #1, `Validate released-package GF-009 first cycle` |
| Remote CI | PASS | `workspace-check` installed `agentic-project-kit==1.0.13` and ran `check` plus `doctor` |
| Work PR merge | PASS | PR #1 merged through `transfer pr-merge-safe` |
| Handoff PR | PASS | PR #2, `Refresh successor package after PR1` |
| Handoff CI and merge | PASS | `workspace-check` SUCCESS; PR #2 merged |
| Final post-merge check | PASS | `post-merge-check`: `result=NOOP`, `STATE=READY`, external handoff state not required |

## Conclusion

`KIT-GF-009` is externally closed for the tested boundary: a fresh private
repository completed a released-package first-cycle work/PR/CI/merge/handoff
closeout. This evidence does not claim general conformance of arbitrary
repositories, nor does it close GF-011, whose target is the broader successor
refresh-loop behavior across mixed refresh conditions.
